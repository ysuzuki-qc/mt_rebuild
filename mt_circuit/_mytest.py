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