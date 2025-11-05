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


