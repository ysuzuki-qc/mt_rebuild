from __future__ import annotations
import json
import datetime
from typing import Any, Self
import numpy as np
import tunits
import pydantic


class NoteEncoder(json.JSONEncoder):
    @pydantic.validate_call
    def default(self, obj: Any) -> Any:
        if isinstance(obj, tunits.Value):
            return {"__tunits__value__": True, "value": obj.value, "unit": obj.units}
        if isinstance(obj, tunits.ValueArray):
            return {"__tunits__valuearray__": True, "value": obj.value, "unit": obj.units}
        if isinstance(obj, Note):
            return obj._internal_dict
        if isinstance(obj, np.ndarray):
            if np.iscomplexobj(obj):
                return {"__numpy__complex__": True, "real": np.real(obj).tolist(), "imag": np.imag(obj).tolist()}
            else:
                return {"__numpy__real__": True, "value": obj.tolist()}
        return super().default(obj)


@pydantic.validate_call
def _note_object_hook(obj: Any) -> Any:
    if isinstance(obj, dict) and "__tunits__value__" in obj:
        return tunits.Value(obj["value"], obj["unit"])
    if isinstance(obj, dict) and "__tunits__valuearray__" in obj:
        return tunits.ValueArray(obj["value"], obj["unit"])
    if isinstance(obj, dict) and "__numpy__real__" in obj:
        return np.array(obj["value"])
    if isinstance(obj, dict) and "__numpy__complex__" in obj:
        return np.array(obj["real"]) + 1j * np.array(obj["imag"])
    return obj


@pydantic.dataclasses.dataclass(frozen=True, slots=True)
class Action:
    tag: str
    time: datetime.datetime
    update: dict[str, Any]
    item_created: list[str]
    item_old: dict[str, Any]


@pydantic.dataclasses.dataclass(slots=True)
class Note:
    lock: bool = False
    _action_log: list[Action] = pydantic.Field(default_factory=list)
    _internal_dict: dict[str, Any] = pydantic.Field(default_factory=dict)

    @pydantic.validate_call
    def to_json_str(self) -> str:
        return json.dumps(self._internal_dict, cls=NoteEncoder)

    @classmethod
    @pydantic.validate_call
    def from_json_str(cls, json_str: str) -> Self:
        _internal_dict = json.loads(json_str, object_hook=_note_object_hook)
        note = cls()
        note._update_internal(_internal_dict)
        return note

    @pydantic.validate_call
    def copy(self) -> Self:
        note = type(self).from_json_str(self.to_json_str())
        return note

    @pydantic.validate_call
    def _update_internal(self, data: dict[str, Any]) -> None:
        # if dict is added, it is converted to rewindable note
        for key, value in data.items():
            if not isinstance(value, dict):
                self._internal_dict[key] = value
            else:
                item = Note()
                item._update_internal(value)
                self._internal_dict[key] = item

    @pydantic.validate_call
    def update(self, data: dict[str, Any], tag: str = "") -> None:
        # check updated and created items
        item_created: list[str] = []
        item_old: dict[str, Any] = {}
        for key in data:
            if key in self._internal_dict:
                item_old[key] = self._internal_dict[key]
            else:
                if self.lock:
                    raise ValueError(f"Notes are locked but try to create new item {key}")
                item_created.append(key)
        action = Action(
            tag=tag, update=data, item_created=item_created, item_old=item_old, time=datetime.datetime.now()
        )
        self._action_log.append(action)
        self._update_internal(data)

    @pydantic.validate_call
    def rewind(self) -> None:
        if len(self._action_log) == 0:
            raise ValueError("Nothing to rewind")
        action = self._action_log.pop()
        for key in action.item_created:
            self._internal_dict.pop(key)
        for key, value in action.item_old.items():
            self._internal_dict[key] = value

    @pydantic.validate_call
    def __getattr__(self, key: str) -> Any:
        if key not in self._internal_dict:
            raise ValueError(f"{key} not found")
        else:
            return self._internal_dict[key]

    @pydantic.validate_call
    def __getitem__(self, key: str) -> Any:
        return self.__getattr__(key)

    @pydantic.validate_call
    def erase_action_log(self) -> None:
        self._action_log.clear()

    @pydantic.validate_call
    def show_log(self) -> None:
        for action in self._action_log:
            print(f"{action.time} {action.tag} : {action.update}")

    @pydantic.validate_call
    def __str__(self) -> str:
        return self._internal_dict.__str__()

    @pydantic.validate_call
    def __repr__(self) -> str:
        return self._internal_dict.__repr__()
