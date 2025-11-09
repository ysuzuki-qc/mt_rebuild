from typing import Optional
import numpy as np
from scipy.stats import unitary_group
import stim
from mt_circuit.gate import I, X, Y, Z


def sample_pauli(num_qubit: int, seed: Optional[int] = None):
    if num_qubit < 1:
        raise ValueError("num qubit must be no less than 1")
    random_state = np.random.RandomState(seed)
    matrix = np.eye(1, dtype=np.complex128)
    pauli_list = {"I": I, "X": X, "Y": Y, "Z": Z}
    sampled_chars = random_state.choice(list(pauli_list.keys()), size=num_qubit)
    for pauli_char in sampled_chars:
        matrix = np.kron(matrix, pauli_list[pauli_char])
    return matrix


def _get_nearest_value(val_list, val):
    if np.abs(val) < np.min(val_list) / 2:
        return 0.0
    dif_list = np.abs(val_list - np.abs(val))
    idx = np.argmin(dif_list)
    sign = 1 if val > 0 else -1
    new_val = val_list[idx] * sign
    return new_val


def sample_clifford(num_qubit: int, seed: Optional[int] = None):
    if num_qubit < 1:
        raise ValueError("num qubit must be no less than 1")
    if seed is not None:
        raise ValueError("Current impl does not support seeded sampling")
    tableau = stim.Tableau.random(num_qubit)
    matrix = tableau.to_unitary_matrix(endian="little")

    # convert complex64 values to complex128 of Clifford elements
    val_list = np.array([1 / np.sqrt(2) ** i for i in range(num_qubit * 4)])
    matrix_prec = np.zeros(matrix.shape, dtype=complex)
    for y in range(matrix.shape[0]):
        for x in range(matrix.shape[1]):
            val = matrix[y, x]
            val_r = _get_nearest_value(val_list, np.real(val))
            val_i = _get_nearest_value(val_list, np.imag(val))
            matrix_prec[y, x] = val_r + 1.0j * val_i
            assert np.abs(matrix_prec[y, x] - matrix[y, x]) < 1e-7

    return matrix_prec


def sample_unitary(num_qubit: int, seed: Optional[int] = None):
    if num_qubit < 1:
        raise ValueError("num qubit must be no less than 1")
    random_state = np.random.RandomState(seed)
    matrix = unitary_group.rvs(2**num_qubit, random_state=random_state)
    return matrix
