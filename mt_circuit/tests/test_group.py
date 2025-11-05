import itertools
import numpy as np
from mt_circuit.group import sample_pauli, sample_clifford, sample_unitary, enumerate_pauli

def test_pauli_enumerate():
    for num_qubit in [1,2]:
        m_list = enumerate_pauli(num_qubit)
        assert(len(m_list) == 4**num_qubit)
        index_list = np.arange(4**num_qubit)
        for i1, i2 in itertools.product(index_list, index_list):
            m1 = m_list[i1]
            m2 = m_list[i2]
            if i1 == i2 and i1 == 0:
                is_identity = np.allclose(m1, np.eye(2**num_qubit))
                assert(is_identity)
            elif i1 == i2:
                is_traceless = np.allclose(np.trace(m1), 0)
                is_hermite = np.allclose(m1, m1.T.conj())
                is_self_inv = np.allclose(m1@m1, np.eye(2**num_qubit))
                assert(is_traceless and is_hermite and is_self_inv)
            else:
                m3 = m1 @ m2
                is_different = not np.allclose(m1, m2)
                is_traceless = np.allclose(np.trace(m3), 0)
                is_hermite_or_anti_hermite = np.allclose(m3, m3.T.conj()) or np.allclose(m3, -m3.T.conj())
                is_self_inv_or_imag = np.allclose(m3@m3, np.eye(2**num_qubit)) or np.allclose(-m3@m3, np.eye(2**num_qubit))
                assert(is_different and is_traceless and is_hermite_or_anti_hermite and is_self_inv_or_imag)


def test_pauli_sampling():
    count = 100
    for num_qubit in [1,2]:
        for _ in range(count):
            m = sample_pauli(num_qubit)
            is_identity = np.allclose(m, np.eye(2**num_qubit))
            is_traceless = np.allclose(np.trace(m), 0)
            is_hermite = np.allclose(m, m.T.conj())
            is_self_inv = np.allclose(m@m, np.eye(2**num_qubit))
            assert((is_identity or is_traceless) and is_hermite and is_self_inv)

def test_unitary_sampling():
    count = 100
    for num_qubit in [1,2]:
        for _ in range(count):
            m = sample_unitary(num_qubit)
            is_unitary = np.allclose(m@m.T.conj(), np.eye(2**num_qubit))
            assert(is_unitary)

def test_clifford_sampling():
    count = 100
    for num_qubit in [1,2]:
        for _ in range(count):
            m = sample_clifford(num_qubit)

            # check unitarity
            is_unitary = np.allclose(m@m.T.conj(), np.eye(2**num_qubit,), atol=1e-5)
            assert(is_unitary)

            # check pauli is mapped to pauli
            pauli_list = enumerate_pauli(num_qubit)
            for pauli in pauli_list:
                mapped_pauli = m @ pauli @ m.T.conj()
                found = False
                for check in pauli_list:
                    found = found or np.allclose(mapped_pauli @ check, np.eye(2**num_qubit), atol=1e-5)
                    found = found or np.allclose(-mapped_pauli @ check, np.eye(2**num_qubit), atol=1e-5)
                assert(found)

