import numpy as np
from .util import pauli_exp

# list of basic gates
I: np.ndarray = np.eye(2, dtype=complex)
X: np.ndarray = np.array([[0, 1], [1, 0]], dtype=complex)
Z: np.ndarray = np.array([[1, 0], [0, -1]], dtype=complex)
Y: np.ndarray = 1.0j * X @ Z
SX: np.ndarray = pauli_exp(X, np.pi / 2)
SZ: np.ndarray = pauli_exp(Z, np.pi / 2)
SXdag: np.ndarray = pauli_exp(X, -np.pi / 2)
SZdag: np.ndarray = pauli_exp(Z, -np.pi / 2)
H_XY: np.ndarray = (X + Y) / np.sqrt(2)
H_YZ: np.ndarray = (Y + Z) / np.sqrt(2)
H_ZX: np.ndarray = (Z + X) / np.sqrt(2)
