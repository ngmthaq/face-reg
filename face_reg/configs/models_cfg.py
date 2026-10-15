from __future__ import annotations

from pydantic import BaseModel, Field

from face_reg.configs.liveness_model_cfg import LivenessModelCfg


class ModelsCfg(BaseModel):
    detector: str = "models/face_detection_yunet_2023mar.onnx"
    recognizer: str = "models/face_recognition_sface_2021dec.onnx"
    # Empty list = liveness disabled (useful for build steps 1-4; never in production)
    liveness: list[LivenessModelCfg] = Field(default_factory=lambda: [
        LivenessModelCfg(path="models/minifasnet_v2_2.7_80x80.onnx", scale=2.7),
        LivenessModelCfg(path="models/minifasnet_v1se_4.0_80x80.onnx", scale=4.0),
    ])
    # ONNX Runtime providers for the liveness models.
    # e.g. [OpenVINOExecutionProvider], [CUDAExecutionProvider], [TensorrtExecutionProvider]
    providers: list[str] = Field(default_factory=lambda: ["CPUExecutionProvider"])
