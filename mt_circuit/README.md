# MT Circuit

Library for describing quantum circuits and translate it for qubits controlled by X90, ZX90, virtual-Z gates and Z-basis measurement.

## Overview

This library offers several functions that is useful for manipulating quantum circuits.

- Random sampling form the following groups
  - Pauli Group
  - Clifford Group
  - Unitary group

- Quantum Circuit
  - Supported gates
    - u2: 2x2 unitary matrix (usage: `qc.add_gate("u2", [0,], matrix=U)`)
    - u4: 4x4 unitary matrix (usage: `qc.add_gate("u4", [0,1], matrix=U)`)
    - RX/RY/RZ: single-qubit Pauli rotation (usage: `qc.add_gate("RX", [0,], angle=np.pi/2)`)
    - HPI: half-pi rotation with the axis on XY-plane (usage: `qc.add_gate("HPI", [0,], angle=np.pi)`)
    - CHPI: controlled half-pi rotation where the axis of the target qubit is on XY-plane (usage: `qc.add_gate("CHPI", [0,1], angle=np.pi)`)
    - MZ: Z measurement (usage: `qc.add_gate("MZ", [0,])`)
    - SYNC: optimization barrier and synchronization (usage: `qc.add_gate("SYNC", [0,1,2])`)
  - Conversion to matrix
    - Can convert to unitary matrix if circuit does not contain `MZ` (usage: `qc.to_matrix()`)
  - Serialization
    - Support save/load as jsonalizable dict (usage: `data = qc.to_json_dict()` / `QuantumCircuit.from_json_dict(data)`)
  - Printable
    - write circuit as readable ascii (usage: `print_circuit(qc)`)

- Gate Decomposition
  - Decompose `u4` to `u2xu2-CHPI(0)-u2xu2-CHPI(0)-u2xu2-CHPI(0)-u2xu2`
  - Decompose `u2` to `RZ-HPI(0)-RZ-HPI(0)-RZ`

- Circiut Decomposition
  - 1Q/2Q gate circuit into a sequence of `HPI, CR, RZ, MZ, SYNC`
    - step1: Decompose `u4`
    - step2: Fuse neighboring single-qubit gates if not protected by barrier
    - step3: Decompose `u2,RX,RY`
    - step4: Send `RZ` to the end of circuit, which can be ignored

## Examples

### Sampling unitary matrix
- Example
```python
import numpy as np
np.set_printoptions(linewidth=np.inf)

from mt_circuit.group import sample_pauli, sample_clifford, sample_unitary
num_qubit = 2
p = sample_pauli(num_qubit=2)
c = sample_clifford(num_qubit=2)
u = sample_unitary(num_qubit=2)
print(p)
print(c)
print(u)
```

- Output
```python
[[ 0.+0.j  0.-1.j  0.+0.j  0.+0.j]
 [ 0.+1.j  0.+0.j  0.+0.j  0.+0.j]
 [ 0.+0.j  0.+0.j -0.+0.j  0.+1.j]
 [ 0.+0.j  0.+0.j -0.-1.j -0.+0.j]]
[[ 0.        +0.j          0.        +0.j          0.70710677+0.j         -0.70710677+0.j        ]
 [ 0.        +0.70710677j  0.        +0.70710677j  0.        +0.j          0.        +0.j        ]
 [ 0.        +0.70710677j  0.        -0.70710677j  0.        +0.j          0.        +0.j        ]
 [ 0.        +0.j          0.        +0.j          0.70710677+0.j          0.70710677+0.j        ]]
[[-0.54821558-0.28639584j  0.32860386-0.26211725j  0.09911463-0.53947611j -0.1157483 -0.35566177j]
 [ 0.38816738+0.22095103j  0.65230588-0.0228427j  -0.41619606+0.10133905j  0.02951908-0.43602962j]
 [ 0.63061686-0.04315949j -0.27447716-0.00321315j  0.03164695-0.67390703j -0.25366191-0.07493346j]
 [ 0.13362999+0.02337709j  0.3070096 -0.47716492j -0.03253632-0.24380776j  0.46235817+0.62078931j]]
```

### Serializable Quantum Circuit
- Example
```python
import numpy as np
np.set_printoptions(threshold=np.inf)
np.set_printoptions(linewidth=np.inf)
import json
from mt_circuit.circuit import QuantumCircuit
from mt_circuit.convert import print_circuit
from mt_circuit.group import sample_unitary

# compose circuit
num_qubit = 2
qc = QuantumCircuit(num_qubit)
qc.add_gate(name="RX", targets=[0,], angle=np.pi/3)
qc.add_gate(name="RY", targets=[0,], angle=np.pi/2)
qc.add_gate(name="RZ", targets=[0,], angle=-np.pi/2)
qc.add_gate(name="HPI", targets=[0,], angle=np.pi*2/3)
qc.add_gate(name="CHPI", targets=[0,1], angle=0)
qc.add_gate(name="u2", targets=[0,], matrix=sample_unitary(num_qubit=1))
qc.add_gate(name="u4", targets=[0,1], matrix=sample_unitary(num_qubit=2))

# convert to json
json_str = json.dumps(qc.to_json_dict())
print("Json dump\n", json_str, "\n")

# load from json
qc_load = QuantumCircuit.from_json_dict(json.loads(json_str))

# convert to numpy matrix
mat = qc.to_matrix()
print("Circuit unitary matrix\n", mat, "\n")
assert(np.allclose(qc.to_matrix(), qc_load.to_matrix()))

print("Print circuit")
print_circuit(qc)
```

- Output
```python
Json dump
 {"num_qubit": 2, "gate_list": [{"name": "RX", "targets": [0], "angle": 1.0471975511965976, "matrix": null}, {"name": "RY", "targets": [0], "angle": 1.5707963267948966, "matrix": null}, {"name": "RZ", "targets": [0], "angle": -1.5707963267948966, "matrix": null}, {"name": "HPI", "targets": [0], "angle": 2.0943951023931953, "matrix": null}, {"name": "CHPI", "targets": [0, 1], "angle": 0, "matrix": null}, {"name": "u2", "targets": [0], "angle": null, "matrix": [[[-0.2809295306072867, 0.9129759135939095], [-0.0713487983198489, 0.2160378430244948]], [[0.16700148153059652, 0.2442623286483645], [-0.9423897564053147, -0.24523161782683822]]]}, {"name": "u4", "targets": [0, 1], "angle": null, "matrix": [[[-0.6574579305992112, -0.1913863950283839, -0.10031871299552737, -0.38461979899036836], [0.04348843489802851, -0.24708391191242682, -0.4254720481189322, 0.15108504792073948], [-0.3823098995465464, 0.26386154293817476, -0.0741287137781896, -0.17861157159684107], [-0.3241967182310649, -0.3656069018068713, -0.1076712639801709, -0.032284355278506136]], [[-0.03837680604074275, 0.06423642713391549, 0.2954167978399103, 0.5293901218184617], [-0.009574947944801893, -0.08743262992818968, -0.7421786680183964, 0.4178992957670239], [0.21678379731517694, 0.642287856746562, -0.3897509867204016, -0.367946096324294], [0.5157846260512403, -0.5241421500989737, -0.04260790351368676, -0.4538926008799077]]]}]}

Circuit unitary matrix
 [[ 0.28318498+0.3552967j   0.0209909 +0.05300589j -0.51555587-0.55479398j -0.07497792-0.45946097j]
 [-0.34624898+0.02468898j  0.0867938 +0.31218692j -0.20032468+0.484447j    0.4035558 -0.58037238j]
 [ 0.05105457+0.81413241j -0.14391076+0.10273491j -0.13407457+0.31612095j  0.10130397+0.41850464j]
 [ 0.04674546-0.07395494j -0.67132356+0.64016859j  0.17930674-0.03908398j -0.30005635-0.09023356j]]

Print circuit
               |               |
      RX(0.33pi)               |
               |               |
---------------|---------------|---------------
               |               |
      RY(0.50pi)               |
               |               |
---------------|---------------|---------------
               |               |
      RZ(1.50pi)               |
               |               |
---------------|---------------|---------------
               |               |
     HPI(0.67pi)               |
               |               |
---------------|---------------|---------------
               |               |
    CHPI(0.00pi)    CHPI(0.00pi)
               |               |
---------------|---------------|---------------
               |               |
              u2               |
               |               |
---------------|---------------|---------------
               |               |
              u4              u4
               |               |
```


### Matrix Decomposition
- Example
```python
import json
from mt_circuit.decompose import (
    u2_matrix_to_HPI_RZ_form,
    u4_matrix_to_CHPI_u2_form,
)
from mt_circuit.convert import print_circuit
from mt_circuit.util import check_unitary_equal_up_to_phase
from mt_circuit.group import sample_unitary

u2 = sample_unitary(num_qubit=1)
q_u2 = u2_matrix_to_HPI_RZ_form(u2)
assert(check_unitary_equal_up_to_phase(u2, q_u2.to_matrix()))
print("*** u2 circuit ***")
print_circuit(q_u2)
print()

u4 = sample_unitary(num_qubit=2)
q_u4 = u4_matrix_to_CHPI_u2_form(u4)
assert(check_unitary_equal_up_to_phase(u4, q_u4.to_matrix()))
print("*** u4 circuit ***")
print_circuit(q_u4)
print()
```

- Output
```
*** u2 circuit ***
               |
      RZ(1.04pi)
               |
---------------|---------------
               |
     HPI(0.00pi)
               |
---------------|---------------
               |
      RZ(1.21pi)
               |
---------------|---------------
               |
     HPI(0.00pi)
               |
---------------|---------------
               |
      RZ(1.49pi)
               |

*** u4 circuit ***
               |               |
              u2               |
               |               |
               |              u2
               |               |
---------------|---------------|---------------
               |               |
    CHPI(0.00pi)    CHPI(0.00pi)
               |               |
---------------|---------------|---------------
               |               |
              u2               |
               |               |
               |              u2
               |               |
---------------|---------------|---------------
               |               |
    CHPI(0.00pi)    CHPI(0.00pi)
               |               |
---------------|---------------|---------------
               |               |
              u2               |
               |               |
               |              u2
               |               |
---------------|---------------|---------------
               |               |
    CHPI(0.00pi)    CHPI(0.00pi)
               |               |
---------------|---------------|---------------
               |               |
              u2               |
               |               |
               |              u2
               |               |
```



### Circuit Decomposition
- Example
```python
import json
from mt_circuit.circuit import QuantumCircuit
from mt_circuit.convert import convert_to_HPI_CHPI, print_circuit
from mt_circuit.group import sample_unitary
from mt_circuit.util import check_unitary_equal_up_to_phase

qc = QuantumCircuit(3)
qc.add_gate(name="u4", targets=[0,1], matrix=sample_unitary(2))
qc.add_gate(name="u2", targets=[1,], matrix=sample_unitary(1))
qc.add_gate(name="u4", targets=[2,1], matrix=sample_unitary(2))
qc_conv = convert_to_HPI_CHPI(qc)

assert(check_unitary_equal_up_to_phase(qc.to_matrix(), qc_conv.to_matrix()))
print("*** qc before conv ***")
print_circuit(qc)
print()
print("*** qc after conv ***")
print_circuit(qc_conv)
print()
```

- Output
```
*** qc before conv ***
               |               |               |
              u4              u4               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |              u2               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |              u4              u4
               |               |               |

*** qc after conv ***
               |               |               |
     HPI(1.36pi)               |               |
               |               |               |
               |     HPI(1.80pi)               |
               |               |               |
               |               |     HPI(0.67pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
     HPI(0.41pi)               |               |
               |               |               |
               |     HPI(1.52pi)               |
               |               |               |
               |               |     HPI(0.08pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
    CHPI(0.68pi)    CHPI(0.68pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
     HPI(0.53pi)               |               |
               |               |               |
               |     HPI(0.18pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
     HPI(0.03pi)               |               |
               |               |               |
               |     HPI(1.68pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
    CHPI(1.18pi)    CHPI(1.18pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
     HPI(1.55pi)               |               |
               |               |               |
               |     HPI(0.97pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
     HPI(1.05pi)               |               |
               |               |               |
               |     HPI(0.47pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
    CHPI(1.97pi)    CHPI(1.97pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
     HPI(1.14pi)               |               |
               |               |               |
               |     HPI(0.69pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
     HPI(0.41pi)               |               |
               |               |               |
               |     HPI(0.02pi)               |
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
      RZ(1.01pi)               |               |
               |               |               |
               |    CHPI(1.30pi)    CHPI(1.30pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |     HPI(0.70pi)               |
               |               |               |
               |               |     HPI(1.69pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |     HPI(0.20pi)               |
               |               |               |
               |               |     HPI(1.19pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |    CHPI(1.70pi)    CHPI(1.70pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |     HPI(1.43pi)               |
               |               |               |
               |               |     HPI(0.78pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |     HPI(0.93pi)               |
               |               |               |
               |               |     HPI(0.28pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |    CHPI(0.43pi)    CHPI(0.43pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |     HPI(0.83pi)               |
               |               |               |
               |               |     HPI(1.60pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |     HPI(0.38pi)               |
               |               |               |
               |               |     HPI(1.21pi)
               |               |               |
---------------|---------------|---------------|---------------
               |               |               |
               |      RZ(1.11pi)               |
               |               |               |
               |               |      RZ(1.67pi)
               |               |               |
```


### Generate RB description
- Example
```python
import json
import numpy as np
from mt_circuit.circuit import QuantumCircuit
from mt_circuit.convert import convert_to_HPI_CHPI, print_circuit
from mt_circuit.group import sample_clifford

rep = 2
targets = [0,1]
num_qubit = len(targets)

qc = QuantumCircuit(num_qubit)
u = np.eye(2**num_qubit, dtype=complex)

assert(num_qubit in [1,2])
gate_name = "u4" if num_qubit==2 else "u2"
for _ in range(rep):
    c = sample_clifford(num_qubit)
    u = c @ u
    qc.add_gate(name=gate_name, targets=targets, matrix=c)
    qc.add_gate(name="SYNC", targets=targets)
qc.add_gate(name=gate_name, targets=targets, matrix=u.T.conj())
for target in targets:
    qc.add_gate(name="MZ", targets=[target,])

qc_conv = convert_to_HPI_CHPI(qc)
rb_json = json.dumps(qc_conv.to_json_dict())

print("*** qc before conv ***")
print_circuit(qc)
print()
print("*** qc after conv ***")
print_circuit(qc_conv)
print()

```

- Output
```
*** qc before conv ***
               |               |
              u4              u4
               |               |
---------------|---------------|---------------
               |               |
            SYNC            SYNC
               |               |
---------------|---------------|---------------
               |               |
              u4              u4
               |               |
---------------|---------------|---------------
               |               |
            SYNC            SYNC
               |               |
---------------|---------------|---------------
               |               |
              u4              u4
               |               |
---------------|---------------|---------------
               |               |
              MZ               |
               |               |
               |              MZ
               |               |

*** qc after conv ***
               |               |
     HPI(0.50pi)               |
               |               |
               |     HPI(1.50pi)
               |               |
---------------|---------------|---------------
               |               |
     HPI(0.39pi)               |
               |               |
               |     HPI(0.89pi)
               |               |
---------------|---------------|---------------
               |               |
    CHPI(0.39pi)    CHPI(0.39pi)
               |               |
---------------|---------------|---------------
               |               |
     HPI(1.39pi)               |
               |               |
               |     HPI(1.89pi)
               |               |
---------------|---------------|---------------
               |               |
     HPI(0.89pi)               |
               |               |
               |     HPI(1.39pi)
               |               |
---------------|---------------|---------------
               |               |
    CHPI(0.89pi)    CHPI(0.89pi)
               |               |
---------------|---------------|---------------
               |               |
     HPI(0.39pi)               |
               |               |
               |     HPI(0.39pi)
               |               |
---------------|---------------|---------------
               |               |
     HPI(1.89pi)               |
               |               |
               |     HPI(1.89pi)
               |               |
---------------|---------------|---------------
               |               |
    CHPI(1.39pi)    CHPI(1.39pi)
               |               |
---------------|---------------|---------------
               |               |
     HPI(0.39pi)               |
               |               |
               |     HPI(0.89pi)
               |               |
---------------|---------------|---------------
               |               |
     HPI(1.89pi)               |
               |               |
               |     HPI(0.00pi)
               |               |
---------------|---------------|---------------
               |               |
            SYNC            SYNC
               |               |
---------------|---------------|---------------
               |               |
     HPI(1.28pi)               |
               |               |
               |     HPI(1.00pi)
               |               |
.....(omitted).....
```
