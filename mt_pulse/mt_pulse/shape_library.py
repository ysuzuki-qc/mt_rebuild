from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
import numpy as np
from mt_pulse.shape import Shape

@dataclass(frozen=True, slots=True)
class ShapeLibrary:
    _shape_dict: dict[str, Shape] = field(default_factory=dict)

    def add_shape(self, pulse: Shape) -> None:
        self._shape_dict[pulse.name] = pulse

    def get_shape_name_list(self) -> list[str]:
        return list(self._shape_dict.keys())

    def get_function(self, pulse_name: str, variable_dict: dict[str, Any]) -> Callable[[np.ndarray], np.ndarray]:
        if pulse_name not in self._shape_dict:
            raise ValueError(f"pulse {pulse_name} not defined")
        time_function = self._shape_dict[pulse_name].get_function(variable_dict)
        return time_function

    def get_progress(self, pulse_name: str, variable_dict: dict[str, Any]) -> float:
        if pulse_name not in self._shape_dict:
            raise ValueError(f"pulse {pulse_name} not defined")
        value = self._shape_dict[pulse_name].get_progress(variable_dict)
        return value

    def to_json_dict(self) -> dict:
        shape_dict = {}
        for name, shape in self._shape_dict.items():
            shape_dict[name] = shape.to_json_dict()
        json_dict = {
            "_shape_dict": shape_dict,
        }
        return json_dict

    @staticmethod
    def from_json_dict(json_dict: dict) -> ShapeLibrary:
        shape_dict = {}
        for name, shape in json_dict["_shape_dict"].items():
            shape_dict[name] = Shape.from_json_dict(shape)
        lib = ShapeLibrary(
            _shape_dict = shape_dict,
        )
        return lib

