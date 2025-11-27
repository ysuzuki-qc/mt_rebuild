# MT Note

Note for experimental logs

## Overview

This library provides dictionary with the following features.

- Attribution access: item `a` can be accessed via `note["a"]` or `note.a`
- Serializable: real/complex ndarray of numpy and Value/ValueArray of tunits can be saved/loaded as json string
- Rewindable: Recent updates can be reverted, which is useful when some wrong fitting was done
- Type-hinted: All the functions are decorated with pydantic and checked by mypy
- Item lock: Item creation can be prohibited via `note.lock=True`

- Restriction compared to `dict`:
  - Dictionary key must be `str`
  - Item-update must be performed via `update` function.
    - OK: `note.update({"a": 10})`
    - NG: `note["a"]=10`


## Examples

- Example
```python
import numpy as np
from mt_note import Note
from tunits.units import GHz

note = Note()

# data update
note.update({"a": 20, "b": 30 * GHz, "c": np.array([0, 1.0j]), "d": {"d1": 0, "d2": 2}})
print("items", note)

# attribute access
print("attr-access", note.c)
print("item-access", note["c"])

# item set is not allowed. Please update via `update` func
try:
    note["b"] = 10
except Exception as e:
    print(e)

# subdict also becomes Note obj
note.d.update({"d1": 10})

# rewind recent updaets
note.update({"b": 10})
print("update", note)
note.rewind()
print("rewind", note)

# json serializable
dump_str = note.to_json_str()
note2: Note = Note.from_json_str(dump_str)
print("json", note2)

# make prohibit item add
note.lock = True
note.update({"b": 20})
try:
    note.update({"e": 20})
except Exception as e:
    print(e)

# show recent log
note.show_log()
print(note)

# make copy
print(note.copy())

# check rewind limit
note3 = Note()
try:
    note3.rewind()
except Exception as e:
    print(e)

```

- Output
```
items {'a': 20, 'b': Value(30, 'GHz'), 'c': array([0.+0.j, 0.+1.j]), 'd': {'d1': 0, 'd2': 2}}
attr-access [0.+0.j 0.+1.j]
item-access [0.+0.j 0.+1.j]
'Note' object does not support item assignment
update {'a': 20, 'b': 10, 'c': array([0.+0.j, 0.+1.j]), 'd': {'d1': 10, 'd2': 2}}
rewind {'a': 20, 'b': Value(30, 'GHz'), 'c': array([0.+0.j, 0.+1.j]), 'd': {'d1': 10, 'd2': 2}}
json {'a': 20, 'b': Value(30, 'GHz'), 'c': array([0.+0.j, 0.+1.j]), 'd': {'d1': 10, 'd2': 2}}
Notes are locked but try to create new item e
2025-11-28 04:58:22.600193  : {'a': 20, 'b': Value(30, 'GHz'), 'c': array([0.+0.j, 0.+1.j]), 'd': {'d1': 0, 'd2': 2}}
2025-11-28 04:58:22.601193  : {'b': 20}
{'a': 20, 'b': 20, 'c': array([0.+0.j, 0.+1.j]), 'd': {'d1': 10, 'd2': 2}}
{'a': 20, 'b': 20, 'c': array([0.+0.j, 0.+1.j]), 'd': {'d1': 10, 'd2': 2}}
Nothing to rewind
```