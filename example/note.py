import sys
path_list = ["./mt_circuit/", "./mt_note/", "./mt_pulse/" , "./mt_util/", "./mt_quel_util/", "./mt_quel_meas/"]
for path in path_list:
    sys.path.append(path)
    sys.path.append("../"+path)

import json
import pprint
import numpy as np
from mt_note import Note
from tunits.units import ns, GHz

note = Note()

# data update
note.update({"a": 20, "b": 30*GHz, "c": np.array([0, 1.j]), "d": {"d1": 0, "d2": 2}})
print("items", note)

# attribute access
print("attr-access", note.c)
print("item-access", note["c"])

# item set is not allowed
try:
    note["b"] = 10
except Exception as e:
    print(e)

# subdict also becomes a noet
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
note.lock=True
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
