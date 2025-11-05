from typing import Any, Annotated
from tunits import Frequency, Value, UnitMismatchError, Time
from pydantic import PlainValidator, PlainSerializer
import json

# create validator for tunits frequency
def _serialize_typedunits(v: Value):
    return {"value": v.value, "units": v.units}
def _validate_frequency_type(v: Any) -> Value:
    if not isinstance(v, Value):
        raise ValueError(f"{v} is not tunits value")
    try:
        _ = v["GHz"]
    except UnitMismatchError as e:
        raise e
    return v
FrequencyType = Annotated[Frequency, PlainValidator(_validate_frequency_type), PlainSerializer(_serialize_typedunits)]
def _validate_time_type(v: Any) -> Value:
    if not isinstance(v, Value):
        raise ValueError(f"{v} is not tunits value")
    try:
        _ = v["ns"]
    except UnitMismatchError as e:
        raise e
    return v
TimeType = Annotated[Frequency, PlainValidator(_validate_time_type), PlainSerializer(_serialize_typedunits)]


# functions for Json encoder and decoder
class JSON_TypedUnitsEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Value):
            return {"__typedunits__value__": True, "value": obj.value, "units": obj.units}
        return super().default(obj)
    
def JSON_typedunits_hook(v: Any) -> Any:
    if isinstance(v, dict) and ("__typedunits__value__" in v):
        return Value(v["value"], v["units"])
    return v
