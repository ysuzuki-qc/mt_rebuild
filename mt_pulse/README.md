# MT Pulse

Pulse synthesizer for microwave experiments

## Overview

This library provides pulse-definition with the following features.

- Preset pulses (blank, flattop, flattop_cosrise, gaussian, gaussian_drag)
- User-custom pulses can be generated with text serialization
- Parametric treatment of pulse shapes
- Convert pulses to paramter-fixed form; data-point array or numpy time-function

## Examples

### Serializable pulse expression
- Example
```python
import json
from mt_pulse import Shape
from mt_pulse.preset_pulse import gaussian_drag

# create pulse instances with equations
pulse = gaussian_drag()
print("expression\n", pulse.shape_expr, "\n")
print("symbols\n", pulse.get_symbol_name_set(), "\n")

# can be saved as json
json_str = json.dumps(pulse.to_json_dict())
pulse_load = Shape.from_json_dict(json.loads(json_str))
print("json\n", json_str, "\n")
assert(json_str == json.dumps(pulse_load.to_json_dict()))
```

- Output
```python
expression
 amplitude*(5.54517744447956*I*drag*t*exp(-2.77258872223978*t**2/width**2)/width**2 + exp(-2.77258872223978*t**2/width**2))*exp(1.0*I*phase) 

symbols
 {'amplitude', 'width', 'phase', 'drag', 't'}

json
 {"name": "gaussian_drag", "shape_expr": "Mul(Symbol('amplitude'), Add(Mul(Float('5.5451774444795623', precision=53), I, Symbol('drag'), Symbol('t'), Pow(Symbol('width'), Integer(-2)), exp(Mul(Integer(-1), Float('2.7725887222397811', precision=53), Pow(Symbol('t'), Integer(2)), Pow(Symbol('width'), Integer(-2))))), exp(Mul(Integer(-1), Float('2.7725887222397811', precision=53), Pow(Symbol('t'), Integer(2)), Pow(Symbol('width'), Integer(-2))))), exp(Mul(Float('1.0', precision=53), I, Symbol('phase'))))", "progress_time_ns": "Float('0.0', precision=53)", "pulse_start_time_ns": "Mul(Float('4.0', precision=53), Symbol('width'))", "pulse_end_time_ns": "Mul(Float('4.0', precision=53), Symbol('width'))"}
```


### Pulse save
- Example
```python
import numpy as np
import matplotlib.pyplot as plt
from mt_pulse.preset_pulse import gaussian_drag

pulse = gaussian_drag()

# create time slots
cursor = 400
time_slots = np.arange(0, 1000, 8)

# instantiate waveform
param = {"width": 200, "amplitude": 0.5, "drag": 40, "phase": np.pi/10}
pulse_func = pulse.get_time_function(param)
pulse_waveform = pulse_func(time_slots-cursor)

# plot waveform
plt.plot(time_slots, np.real(pulse_waveform), ".-", label=f"I")
plt.plot(time_slots, np.imag(pulse_waveform), ".-", label=f"Q")
plt.xlim(np.min(time_slots), np.max(time_slots))
plt.ylim(-1, 1)
plt.xlabel("Time [ns]")
plt.ylabel("Amplitude [a.u.]")
plt.legend()
plt.show()
```

- Output



### Pulse sequence
- Example
```python
import numpy as np
import matplotlib.pyplot as plt
from mt_pulse import get_preset_pulse_function_library

pulse_lib = get_preset_pulse_function_library()

pulse_sequence = [
    ("blank", {"width": 200}),
    ("gaussian", {"width": 50, "amplitude": 0.9, "phase": 0}),
    ("blank", {"width": 200}),
    ("flattop_cosrise", {"width": 200, "amplitude": 0.5, "phase": np.pi*2/3, "risetime": 40}),
]

# create time slots
cursor = 0
time_slots = np.arange(0, 1000, 8)
waveform = np.zeros_like(time_slots, dtype=complex)

# sequentially process pulses
for pulse in pulse_sequence:
    time_func = pulse_lib.get_time_function(pulse[0], pulse[1])
    waveform += time_func(time_slots-cursor)
    cursor += pulse_lib.get_time_progress(pulse[0], pulse[1])

# plot waveform
plt.plot(time_slots, np.real(waveform), ".-", label=f"I")
plt.plot(time_slots, np.imag(waveform), ".-", label=f"Q")
plt.xlim(np.min(time_slots), np.max(time_slots))
plt.ylim(-1, 1)
plt.xlabel("Time [ns]")
plt.ylabel("Amplitude [a.u.]")
plt.legend()
plt.show()
```

- Output

### User's custom pulse
- Example
```python
import json
import numpy as np
import sympy as sp
import matplotlib.pyplot as plt
from mt_pulse import Shape, ShapeLibrary
from mt_pulse.preset import gaussian

# create libs
pulse_lib = ShapeLibrary()

# add preset pulse
pulse_lib.add_pulse(gaussian())

# add user's custom pulse
t, width, amplitude = sp.symbols(["t", "width", "amplitude"])
shape = sp.Piecewise(
    (amplitude*(1-sp.Abs(t)/width), sp.And(-width<t, t<width)),
    (0, True),
)
pulse = Shape(
    name="triangle",
    shape_expr=shape,
    progress_time_ns=sp.Float(0),
    pulse_start_time_ns=-width,
    pulse_end_time_ns=width,
)
pulse_lib.add_pulse(pulse)

# user's custom pulse library can be serializable
json_str = json.dumps(pulse_lib.to_json_dict())
pulse_lib_load = ShapeLibrary.from_json_dict(json.loads(json_str))

# create time slots
cursor = 400
time_slots = np.arange(0, 1000, 8)

# instantiate waveform
pulse_func = pulse_lib_load.get_time_function("triangle", {"width": 100, "amplitude": 0.5})
pulse_waveform = pulse_func(time_slots-cursor)

# plot waveform
plt.plot(time_slots, np.real(pulse_waveform), ".-", label=f"I")
plt.plot(time_slots, np.imag(pulse_waveform), ".-", label=f"Q")
plt.xlim(np.min(time_slots), np.max(time_slots))
plt.ylim(-1, 1)
plt.xlabel("Time [ns]")
plt.ylabel("Amplitude [a.u.]")
plt.legend()
plt.show()
```