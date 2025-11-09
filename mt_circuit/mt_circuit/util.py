import numpy as np


def pauli_exp(pauli: np.ndarray, angle: float) -> np.ndarray:
    """Compute exponential of Pauli operator exp(- i angle/2 pauli)

    Args:
        pauli (np.ndarray): pauli matrix
        angle (float): rotation angle

    Returns:
        np.ndarray: result matrix
    """
    return np.cos(angle / 2) * np.eye(*pauli.shape) - 1.0j * np.sin(angle / 2) * pauli


def check_unitary_equal_up_to_phase(u1: np.ndarray, u2: np.ndarray) -> bool:
    if u1.shape != u2.shape:
        return False
    if u1.shape[0] != u1.shape[1]:
        return False

    u = u1 @ u2.T.conj()
    if not np.allclose(np.abs(u[0, 0]), 1):
        return False

    u /= u[0, 0]
    return np.allclose(u, np.eye(u.shape[0]))
