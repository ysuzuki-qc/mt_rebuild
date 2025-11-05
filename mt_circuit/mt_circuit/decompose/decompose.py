import numpy as np
from mt_circuit.gate import X, Z, H_ZX, SX, SZ, SXdag, SZdag
from mt_circuit.util import pauli_exp
from mt_circuit.circuit import QuantumCircuit
import cirq

def u2_matrix_to_HPI_RZ_form(u: np.ndarray) -> QuantumCircuit:
    """decompose 2x2 unitary to the form of (Z-rot X-half-pi Z-rot X-half-pi Z-rot)

    The decomposition is based on U3-decomposition in QASM's U3 gates.
    See https://arxiv.org/abs/1707.03429 for definition.
    Then, intermediate RY is converted to RZ conjugated by X-half-pi

    Args:
        u (np.ndarray): 2*2 unitary matrix

    Returns:
        list[float]: list of three Z rotation angle
    """

    u = np.array(u,dtype=complex)
    assert(u.shape == (2,2))
    u = u/np.sqrt(np.linalg.det(u))
    angle1 = np.angle(u[1,1])
    angle2 = np.angle(u[1,0])
    t2 = angle1+angle2
    t3 = angle1-angle2
    cv = u[1,1]/np.exp(1.j*angle1)
    sv = u[1,0]/np.exp(1.j*angle2)

    cv_real = np.real(cv)

    # avoid cv_real becomes out of the domain of arccos due to rounding error
    cv_real_safety = max(min(cv_real, 1.), -1.)
    t1 = np.arccos(cv_real_safety)*2
    if(sv<0):
        t1 = -t1

    z1 = t3
    z2 = t1 + np.pi
    z3 = t2 + np.pi
    circuit = QuantumCircuit(1)
    circuit.add_gate(name="RZ", targets=[0,], angle=z1)
    circuit.add_gate(name="HPI", targets=[0,], angle=0)
    circuit.add_gate(name="RZ", targets=[0,], angle=z2)
    circuit.add_gate(name="HPI", targets=[0,], angle=0)
    circuit.add_gate(name="RZ", targets=[0,], angle=z3)
    return circuit


def u4_matrix_to_CHPI_u2_form(U: np.ndarray) -> QuantumCircuit:
    """Decompose 4x4 unitary matrix to a sequence of ZX rotations and single-qubit gates

    Modifying CNOT form by decomposing CNOT = RZX(pi/2) (RZ(-pi/2) otimes RX(-pi/2))

    Args:
        U (np.ndarray): matrix to decompose

    Returns:
        QuantumCircuit: circuit with RZX and single-qubit rotations
    """
    kak_form = cirq.linalg.kak_decomposition(U)
    bef = kak_form.single_qubit_operations_before
    aft = kak_form.single_qubit_operations_after
    Cartan_param = kak_form.interaction_coefficients
    circuit = QuantumCircuit(2)
    circuit.add_gate(name="u2", targets=[0,], matrix=SZdag @ bef[0])
    circuit.add_gate(name="u2", targets=[1,], matrix=SXdag @ bef[1])
    circuit.add_gate(name="CHPI", targets=[0,1], angle=0)
    circuit.add_gate(name="u2", targets=[0,], matrix=SZdag @ H_ZX @ pauli_exp(X,-2*Cartan_param[0]))
    circuit.add_gate(name="u2", targets=[1,], matrix=SXdag @ pauli_exp(Z,-2*Cartan_param[2]))
    circuit.add_gate(name="CHPI", targets=[0,1], angle=0)
    circuit.add_gate(name="u2", targets=[0,], matrix=SZdag @ H_ZX @ SZ)
    circuit.add_gate(name="u2", targets=[1,], matrix=SXdag @ pauli_exp(Z,2*Cartan_param[1]))
    circuit.add_gate(name="CHPI", targets=[0,1], angle=0)
    circuit.add_gate(name="u2", targets=[0,], matrix=aft[0] @ SXdag)
    circuit.add_gate(name="u2", targets=[1,], matrix=aft[1] @ SX)
    return circuit
