import numpy as np
import itertools
from mt_circuit.gate import I, X, Y, Z


def enumerate_pauli(num_qubit: int) -> list[np.ndarray]:
    if num_qubit < 1:
        raise ValueError("num qubit must be no less than 1")
    assert num_qubit >= 1
    pauli_list = [I, X, Y, Z]
    current_list = [I, X, Y, Z]
    next_list = []
    for _ in range(num_qubit - 1):
        for i1, i2 in itertools.product(current_list, pauli_list):
            next_list.append(np.kron(i1, i2))
        current_list = next_list
        next_list = []
    return current_list
