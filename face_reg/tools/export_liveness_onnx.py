"""Export the Silent-Face-Anti-Spoofing (MiniFASNet) PyTorch models to ONNX.

Run once on a laptop (needs PyTorch), from the project root; the edge device only needs onnxruntime.

    git clone https://github.com/minivision-ai/Silent-Face-Anti-Spoofing
    pip install torch onnx
    python -m face_reg.tools.export_liveness_onnx --repo ../Silent-Face-Anti-Spoofing --out models/

Writes models/minifasnet_v2_2.7_80x80.onnx and models/minifasnet_v1se_4.0_80x80.onnx
(the crop scale is kept in the file name; config.yaml lists each model with its scale).
"""
from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="path to a Silent-Face-Anti-Spoofing checkout")
    ap.add_argument("--out", default="models")
    ap.add_argument("--opset", type=int, default=13)
    args = ap.parse_args()

    import numpy as np
    import torch

    repo = Path(args.repo).resolve()
    sys.path.insert(0, str(repo))
    from src.model_lib.MiniFASNet import MiniFASNetV1, MiniFASNetV1SE, MiniFASNetV2, MiniFASNetV2SE
    from src.utility import get_kernel, parse_model_name

    mapping = {"MiniFASNetV1": MiniFASNetV1, "MiniFASNetV2": MiniFASNetV2,
               "MiniFASNetV1SE": MiniFASNetV1SE, "MiniFASNetV2SE": MiniFASNetV2SE}
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    for pth in sorted((repo / "resources" / "anti_spoof_models").glob("*.pth")):
        h, w, model_type, scale = parse_model_name(pth.name)
        model = mapping[model_type](conv6_kernel=get_kernel(h, w))
        state = torch.load(pth, map_location="cpu")
        state = OrderedDict((k[7:] if k.startswith("module.") else k, v) for k, v in state.items())
        model.load_state_dict(state)
        model.eval()
        dummy = torch.randn(1, 3, h, w) * 60 + 120      # BGR 0-255 range, like real input
        name = f"{model_type.lower().replace('minifasnet', 'minifasnet_')}_{scale}_{h}x{w}.onnx"
        dst = out_dir / name
        torch.onnx.export(model, dummy, str(dst), input_names=["input"], output_names=["logits"],
                          opset_version=args.opset, dynamic_axes={"input": {0: "n"}, "logits": {0: "n"}},
                          dynamo=False)
        # verify ONNX matches PyTorch
        import onnxruntime as ort
        sess = ort.InferenceSession(str(dst), providers=["CPUExecutionProvider"])
        with torch.no_grad():
            ref = model(dummy).numpy()
        got = sess.run(None, {"input": dummy.numpy()})[0]
        diff = float(np.abs(ref - got).max())
        print(f"{pth.name} -> {dst}  (scale={scale}, max |diff| vs torch = {diff:.2e})")
        if diff > 1e-3:
            print("  WARNING: ONNX output differs from PyTorch", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
