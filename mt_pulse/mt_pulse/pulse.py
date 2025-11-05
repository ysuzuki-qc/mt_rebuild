from __future__ import annotations
from typing import Union, Any
from dataclasses import dataclass, field
import numpy as np
import sympy as sp
from mt_pulse.shape_library import ShapeLibrary

@dataclass(frozen=True, slots=True)
class Pulse():
    name: str
    channel_list: list[str]
    _shape_list: list[tuple[str, str, dict[str, sp.Expr]]] = field(default_factory=list)
    _variable_description: dict[str, str] = field(default_factory=dict)
    _variable_default_value: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict:
        data: dict[str, Any] = {}
        data["name"] = self.name
        data["channel_list"] = self.channel_list
        data["_shape_list"] = []
        for item in self._shape_list:
            new_item = (item[0], item[1], sp.srepr(item[2]))
            data["_shape_list"].append(new_item)
        data["_variable_description"] = self._variable_description
        data["_variable_default_value"] = self._variable_default_value
        return data
    
    @staticmethod
    def from_json_dict(data: dict) -> Pulse:
        data_init = {}
        data_init["name"] = data["name"]
        data_init["channel_list"] = tuple(data["channel_list"])
        data_init["_shape_list"] = []
        for item in data["_shape_list"]:
            new_item = (item[0], item[1], sp.sympify(item[2]))
            data_init["_shape_list"].append(new_item)
        data_init["_variable_description"] = data["_variable_description"]
        data_init["_variable_default_value"] = data["_variable_default_value"]
        return Pulse(**data_init)


    def add_variable(self, variable_name: str, default_value: Any, description: str) -> sp.Symbol:
        variable = sp.Symbol(variable_name)
        self._variable_description[variable_name] = description
        self._variable_default_value[variable_name] = default_value
        return variable

    def _verify_sympy_expr(self, shape_param: dict[str, Union[float, sp.Expr]]) -> dict[str, sp.Expr]:
        verified_dict = {}
        for key, value in shape_param.items():
            if not isinstance(value, sp.Expr):
                try:
                    value = sp.sympify(value)
                except sp.SympifyError:
                    raise ValueError(f"value {value} in key {key} cannot be converted to sympy obj. Please check the value is sympify-able objects such as sympy expr and python/numpy basic objects.")
            verified_dict[key] = value
        return verified_dict

    def add_shape(self, channel_name: str, shape_name: str, shape_param: dict[str, Union[float, sp.Expr]]) -> None:
        self._shape_list.append((channel_name, shape_name, shape_param))

    def validate_shape_list(self, shape_library: ShapeLibrary) -> None:
        for channel_name, shape_name, shape_param in self._shape_list:
            # valdate
            if shape_name not in shape_library._shape_dict:
                raise ValueError(f"shape {shape_name} is not listed in shape library list {list(shape_library._shape_dict.keys())}")
            if channel_name not in self.channel_list:
                raise ValueError(f"channnel name {channel_name} not found in channnel list {self.channel_list}")
            shape_param = self._verify_sympy_expr(shape_param)
            param_set_given = set(shape_param.keys())
            param_set_required = shape_library._shape_dict[shape_name].get_symbol_name_set()
            param_set_undefined = param_set_required - param_set_given - set(["t"])
            if len(param_set_undefined) > 0:
                raise ValueError(f"paramter {param_set_undefined} for shape {shape_name} is not provided.")

    def get_config(self) -> dict[str, Any]:
        config: dict[str, Any] = {}
        for variable_name in self._variable_default_value:
            config[variable_name] = self._variable_default_value[variable_name]
        return config

    def get_description(self) -> dict[str, str]:
        desc: dict[str, str] = {}
        for variable_name in self._variable_default_value:
            desc[variable_name] = self._variable_description[variable_name]
        return desc

    def _evaluate_shape_param(self, config: dict[str, float], shape_param: dict[str, Union[float, sp.Expr]]) -> dict[str, float]:
        config_symbol_names = set(config.keys())
        assigned_params = {}
        for key, value in shape_param.items():
            if isinstance(value, sp.Expr):
                free_symbol_names = set([s.name for s in value.free_symbols])
                undefined_symbols = free_symbol_names - config_symbol_names
                if len(undefined_symbols) > 0:
                    raise ValueError(f"undefined key {undefined_symbols} in {self.name}")
                assigned_params[key] = value.subs(config)
            else:
                assigned_params[key] = value
        return assigned_params


    def get_waveform(self, time_slots: np.ndarray, current_time: float, config: dict[str, float], shape_library: ShapeLibrary) -> tuple[dict[str, np.ndarray], float]:
        if time_slots.ndim != 1:
            raise ValueError(f"time_slots must be 1D array, but {time_slots.ndim}-dim array is provided")
        
        waveform_dict = {}
        cursor_dict = {}
        for channel_name in self.channel_list:
            waveform_dict[channel_name] = np.zeros_like(time_slots, dtype=complex)
            cursor_dict[channel_name] = current_time

        for channel_name, shape_name, shape_param in self._shape_list:
            assigned_params = self._evaluate_shape_param(config, shape_param)
            shape_func = shape_library.get_function(shape_name, assigned_params)
            assert(channel_name in self.channel_list)
            waveform_dict[channel_name] += shape_func(time_slots - cursor_dict[channel_name])
            cursor_dict[channel_name] += shape_library.get_progress(shape_name, assigned_params)
        duration = max(cursor_dict.values()) - current_time
        return waveform_dict, duration
    
    def get_duration(self, config: dict[str, float], shape_library: ShapeLibrary) -> float:
        cursor_dict: dict[str, float] = {}
        for channel_name in self.channel_list:
            cursor_dict[channel_name] = 0.
        for channel_name, shape, shape_param in self._shape_list:
            assigned_params = self._evaluate_shape_param(config, shape_param)
            assert(channel_name in self.channel_list)
            cursor_dict[channel_name] += shape_library.get_progress(shape, assigned_params)
        duration = max(cursor_dict.values())
        return duration

