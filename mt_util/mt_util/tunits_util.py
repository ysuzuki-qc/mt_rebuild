import numpy as np
from typing import Any, Annotated
from tunits import Value, UnitMismatchError, ValueArray
from pydantic import PlainValidator, PlainSerializer
import json


# create validator for tunits frequency
def _serialize_typedunits(v: Value):
    return {"value": v.value, "units": v.units}


# frequency validator
def _validate_frequency_type(v: Any) -> Any:
    if not isinstance(v, Value):
        raise ValueError(f"{v} is not tunits value")
    try:
        _ = v["GHz"]
    except UnitMismatchError as e:
        raise e
    return v


# time validator
def _validate_time_type(v: Any) -> Any:
    if not isinstance(v, Value):
        raise ValueError(f"{v} is not tunits value")
    try:
        _ = v["ns"]
    except UnitMismatchError as e:
        raise e
    return v


# NOTE: use of tunits.Frequency and tunits.Time incur errors in mypy check.
# Thus, we use Value instead and check with pydantic if we need.
FrequencyType = Annotated[Value, PlainValidator(_validate_frequency_type), PlainSerializer(_serialize_typedunits)]
TimeType = Annotated[Value, PlainValidator(_validate_time_type), PlainSerializer(_serialize_typedunits)]


# functions for Json encoder and decoder for tuyped units
class JSON_TypedUnitsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Value):
            return {"__typedunits__value__": True, "value": obj.value, "units": obj.units}
        if isinstance(obj, ValueArray):
            return {"__typedunits__valuearray__": True, "value": obj.value, "units": obj.units}
        if isinstance(obj, np.ndarray):
            if np.iscomplexobj(obj):
                return {"__numpy__complex__": True, "real": np.real(obj).tolist(), "imag": np.imag(obj).tolist()}
            else:
                return {"__numpy__real__": True, "value": obj.tolist()}
        return super().default(obj)


def JSON_typedunits_hook(v: Any) -> Any:
    if isinstance(v, dict) and ("__typedunits__value__" in v):
        return Value(v["value"], v["units"])
    if isinstance(v, dict) and ("__typedunits__valuearray__" in v):
        return ValueArray(v["value"], v["units"])
    if isinstance(v, dict) and "__numpy__real__" in v:
        return np.array(v["value"])
    if isinstance(v, dict) and "__numpy__complex__" in v:
        return np.array(v["real"]) + 1j * np.array(v["imag"])
    return v
