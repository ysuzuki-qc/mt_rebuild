from __future__ import annotations
from typing import Any, Callable
from dataclasses import dataclass
import sympy as sp


@dataclass(frozen=True, slots=True)
class Shape:
    name: str
    shape_expr: sp.Expr
    progress_time_ns: sp.Expr

    def __post_init__(self):
        def get_symbol_names(symbol_list: list[sp.Expr]) -> set[str]:
            return set([s.name for s in symbol_list])

        symbol_names = set()
        symbol_names |= get_symbol_names(self.progress_time_ns.free_symbols)
        if "t" in symbol_names:
            raise ValueError(
                "variable 't' is registered for time and cannot be used except for shape_expr, but used in description."
            )

    def to_json_dict(self) -> dict:
        return {
            "name": self.name,
            "shape_expr": sp.srepr(self.shape_expr),
            "progress_time_ns": sp.srepr(self.progress_time_ns),
        }

    @staticmethod
    def from_json_dict(json_dict: dict) -> Shape:
        pulse = Shape(
            name=json_dict["name"],
            shape_expr=sp.sympify(json_dict["shape_expr"]),
            progress_time_ns=sp.sympify(json_dict["progress_time_ns"]),
        )
        return pulse

    def get_symbol_name_set(self) -> set[str]:
        symbol_names = set()

        def get_symbol_names(symbol_list: list[sp.Expr]) -> set[str]:
            return set([s.name for s in symbol_list])

        symbol_names |= get_symbol_names(self.shape_expr.free_symbols)
        symbol_names |= get_symbol_names(self.progress_time_ns.free_symbols)
        return symbol_names

    def get_function(self, variable_dict: dict[str, Any]) -> Callable:
        if "t" in variable_dict:
            raise ValueError("t is special variable and cannot be provided when generating time function.")
        time_expr = self.shape_expr.subs(variable_dict)
        symbol_name_set = set([s.name for s in time_expr.free_symbols])
        if len(symbol_name_set) == 0:
            time_expr = sp.Symbol("t") * 0 + time_expr
            symbol_name_set.add("t")
        symbol_name_set.remove("t")
        if len(symbol_name_set) >= 1:
            raise ValueError(f"variables except for t must be provided, but {symbol_name_set} are left as free symbols")
        time_func = sp.lambdify("t", time_expr, modules="numpy")
        return time_func

    def get_progress(self, variable_dict: dict[str, Any]) -> float:
        value = self.progress_time_ns.subs(variable_dict)
        free_symbols = value.free_symbols
        if len(free_symbols) >= 1:
            raise ValueError(f"{free_symbols} are left as free symbols")
        value = float(value)
        return value
