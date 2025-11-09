from scipy.stats import unitary_group
from mt_circuit.circuit import QuantumCircuit
from mt_circuit.util import check_unitary_equal_up_to_phase
from mt_circuit.convert.convert import (
    remove_u4,
    bundle_1q,
    remove_u2,
    push_rz,
)


def test_convert_U2():
    u = unitary_group.rvs(2)
    qc = QuantumCircuit(1)
    qc.add_gate(
        name="u2",
        targets=[
            0,
        ],
        matrix=u,
    )
    u0 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u)

    qc = remove_u4(qc)
    u1 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u1)

    qc = bundle_1q(qc)
    u2 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u2)

    qc = remove_u2(qc)
    u3 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u3)

    qc = push_rz(qc)
    u4 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u4)


def test_convert_U4():
    u = unitary_group.rvs(4)
    qc = QuantumCircuit(2)
    qc.add_gate(name="u4", targets=[0, 1], matrix=u)
    u0 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u)

    qc = remove_u4(qc)
    u1 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u1)

    qc = bundle_1q(qc)
    u2 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u2)

    qc = remove_u2(qc)
    u3 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u3)

    qc = push_rz(qc)
    u4 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u4)


def test_convert_random():
    qc = QuantumCircuit(3)
    qc.add_gate(name="u4", targets=[0, 1], matrix=unitary_group.rvs(4))
    qc.add_gate(name="u4", targets=[0, 2], matrix=unitary_group.rvs(4))
    qc.add_gate(
        name="u2",
        targets=[
            0,
        ],
        matrix=unitary_group.rvs(2),
    )
    qc.add_gate(
        name="u2",
        targets=[
            1,
        ],
        matrix=unitary_group.rvs(2),
    )
    qc.add_gate(
        name="u2",
        targets=[
            2,
        ],
        matrix=unitary_group.rvs(2),
    )
    qc.add_gate(name="u4", targets=[1, 0], matrix=unitary_group.rvs(4))
    qc.add_gate(name="u4", targets=[1, 2], matrix=unitary_group.rvs(4))
    qc.add_gate(
        name="u2",
        targets=[
            0,
        ],
        matrix=unitary_group.rvs(2),
    )
    qc.add_gate(
        name="u2",
        targets=[
            1,
        ],
        matrix=unitary_group.rvs(2),
    )
    qc.add_gate(
        name="u2",
        targets=[
            2,
        ],
        matrix=unitary_group.rvs(2),
    )
    qc.add_gate(name="u4", targets=[2, 0], matrix=unitary_group.rvs(4))
    qc.add_gate(name="u4", targets=[2, 1], matrix=unitary_group.rvs(4))
    qc.add_gate(
        name="u2",
        targets=[
            0,
        ],
        matrix=unitary_group.rvs(2),
    )
    qc.add_gate(
        name="u2",
        targets=[
            1,
        ],
        matrix=unitary_group.rvs(2),
    )
    qc.add_gate(
        name="u2",
        targets=[
            2,
        ],
        matrix=unitary_group.rvs(2),
    )
    u0 = qc.to_matrix()

    qc = remove_u4(qc)
    u1 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u1)

    qc = bundle_1q(qc)
    u2 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u2)

    qc = remove_u2(qc)
    u3 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u3)

    qc = push_rz(qc)
    u4 = qc.to_matrix()
    assert check_unitary_equal_up_to_phase(u0, u4)
