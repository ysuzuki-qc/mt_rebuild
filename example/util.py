import sys

path_list = ["./mt_circuit/", "./mt_note/", "./mt_pulse/", "./mt_util/", "./mt_quel_util/", "./mt_quel_meas/"]
for path in path_list:
    sys.path.append(path)
    sys.path.append("../" + path)


def example():
    from mt_util.lattice_util import QubitLattice

    def check(num_qubit: int) -> None:
        lattice = QubitLattice(num_qubit)
        print("num_qubit:", num_qubit)
        for index in range(num_qubit):
            x, y = lattice.index_to_position(index)
            print(f"{index}: {(x, y)}")
            assert lattice.position_to_index(x, y) == index
        print(lattice.get_CNOT_pair_list())

    check(2 * 2)
    check(4 * 4)
    check(6 * 6)


example()
