import json
import numpy as np
from scipy.stats import unitary_group
from mt_circuit.circuit import QuantumCircuit


def test_circuit_equivalence():
    num_qubit = 2
    qc = QuantumCircuit(num_qubit)
    qc.add_gate(
        name="RX",
        targets=[
            0,
        ],
        angle=0.01,
    )
    qc.add_gate(
        name="RY",
        targets=[
            0,
        ],
        angle=0.02,
    )
    qc.add_gate(
        name="RZ",
        targets=[
            0,
        ],
        angle=0.03,
    )

    u2 = unitary_group.rvs(2)
    u4 = unitary_group.rvs(4)
    qc.add_gate(
        name="u2",
        targets=[
            0,
        ],
        matrix=u2,
    )
    qc.add_gate(name="u4", targets=[0, 1], matrix=u4)

    qc.add_gate(
        name="HPI",
        targets=[
            0,
        ],
        angle=0.04,
    )
    qc.add_gate(name="CHPI", targets=[0, 1], angle=0.05)

    # check dumped json string is equivalence
    json_str1 = json.dumps(qc.to_json_dict())
    qc2 = QuantumCircuit.from_json_dict(json.loads(json_str1))
    json_str2 = json.dumps(qc2.to_json_dict())
    assert json_str1 == json_str2

    # check converted matrix is equivalent
    mat1 = qc.to_matrix()
    mat2 = qc2.to_matrix()
    assert np.allclose(mat1, mat2)
