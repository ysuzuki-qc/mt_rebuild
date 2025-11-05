from __future__ import annotations
from typing import Any
from dataclasses import dataclass, field
import numpy as np
from mt_pulse.pulse import Pulse
from mt_pulse.shape_library import ShapeLibrary

@dataclass(frozen=True, slots=True)
class PulseLibrary():
    shape_library: ShapeLibrary
    _pulse_dict: dict[str, Pulse] = field(default_factory=dict)
    def to_json_dict(self) -> dict[str, dict]:
        data: dict[str, dict] = {"_pulse_dict": {}}
        data["shape_library"] = self.shape_library.to_json_dict()
        for key, value in self._pulse_dict.items():
            data["_pulse_dict"][key] = value.to_json_dict()
        return data

    @staticmethod
    def from_json_dict(data: dict[str, dict]) -> PulseLibrary:
        new_data: dict[str, Any] = {"_pulse_dict": {}}
        new_data["shape_library"] = ShapeLibrary.from_json_dict(data["shape_library"])
        for key, value in data["_pulse_dict"].items():
            new_data["_pulse_dict"][key] = Pulse.from_json_dict(value)
        return PulseLibrary(**new_data)
    
    def add_pulse(self, pulse: Pulse) -> None:
        pulse.validate_shape_list(self.shape_library)
        self._pulse_dict[pulse.name] = pulse

    def get_pulse_name_list(self) -> list[str]:
        return list(self._pulse_dict.keys())
    
    def get_channel_list(self, name: str) -> list[str]:
        return self._pulse_dict[name].channel_list

    def get_config(self, pulse_name: str) -> dict[str, Any]:
        if pulse_name not in self._pulse_dict:
            raise ValueError(f"pulse {pulse_name} not found in pulse library list {list(self._pulse_dict.keys())}")
        return self._pulse_dict[pulse_name].get_config()

    def get_description(self) -> dict[str, dict[str, str]]:
        desc: dict[str, dict[str, str]] = {}
        for pulse_name in self._pulse_dict:
            desc[pulse_name] = self._pulse_dict[pulse_name].get_description()
        return desc
       
    def get_waveform(self, pulse_name: str, time_slots: np.ndarray, current_time: float, config: dict[str, float]) -> tuple[dict[str, np.ndarray], float]:
        if pulse_name not in self._pulse_dict:
            raise ValueError(f"pulse {pulse_name} not found in pulse library list {list(self._pulse_dict.keys())}")
        return self._pulse_dict[pulse_name].get_waveform(time_slots, current_time, config, self.shape_library)

    def get_duration(self, pulse_name: str, config: dict[str, float]) -> float:
        if pulse_name not in self._pulse_dict:
            raise ValueError(f"pulse {pulse_name} not found in pulse library list {list(self._pulse_dict.keys())}")
        return self._pulse_dict[pulse_name].get_duration(config, self.shape_library)
    

