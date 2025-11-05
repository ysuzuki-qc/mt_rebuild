import numpy as np
from mt_circuit.util import check_unitary_equal_up_to_phase

def test_equal_check():
    X = np.array([[0,1],[1,0]],dtype=complex)
    Z = np.array([[1,0],[0,-1]],dtype=complex)
    assert(check_unitary_equal_up_to_phase(Z,Z))
    assert(check_unitary_equal_up_to_phase(X,X))
    assert(check_unitary_equal_up_to_phase(X,-X))
    assert(check_unitary_equal_up_to_phase(X,1.j*X))
    assert(check_unitary_equal_up_to_phase(X,np.exp(1.j*np.pi/5)*X))
    assert(not check_unitary_equal_up_to_phase(Z,X))
    assert(not check_unitary_equal_up_to_phase(X,0.5*X))

