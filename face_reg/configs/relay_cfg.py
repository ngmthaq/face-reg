from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RelayCfg(BaseModel):
    # "log": only logs the pulse (dry run). "gpio": Raspberry Pi / Jetson pin via gpiozero.
    # "command": runs `command` as an argument list, no shell (e.g. a USB relay CLI),
    # waits pulse_s, then runs `off_command` if set.
    mode: Literal["log", "gpio", "command"] = "log"
    gpio_pin: int = 17
    command: list[str] = Field(default_factory=list)
    off_command: list[str] = Field(default_factory=list)
    pulse_s: float = 1.0
