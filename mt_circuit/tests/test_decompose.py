from scipy.stats import unitary_group
from mt_circuit.decompose import (
    u2_matrix_to_HPI_RZ_form,
    u4_matrix_to_CHPI_u2_form,
)
from mt_circuit.util import check_unitary_equal_up_to_phase


def test_decompose_HPI_form():
    count = 100
    for _ in range(count):
        u = unitary_group.rvs(2)
        qc = u2_matrix_to_HPI_RZ_form(u)
        u_test = qc.to_matrix()
        assert check_unitary_equal_up_to_phase(u, u_test)


def test_decompose_CHPI_form():
    count = 100
    for _ in range(count):
        u = unitary_group.rvs(4)
        qc = u4_matrix_to_CHPI_u2_form(u)
        u_test = qc.to_matrix()
        assert check_unitary_equal_up_to_phase(u, u_test)
