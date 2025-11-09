import math


class QubitLattice:
    def __init__(self, num_qubit: int, target_index_list: list[int] | None = None) -> None:
        self.num_qubit = num_qubit
        self.chip_width = self.get_chip_width(num_qubit)
        self.target_index_list: list[int] = []
        if target_index_list is None:
            self.target_index_list.extend(list(range(num_qubit)))
        else:
            self.target_index_list.extend(target_index_list)

    def get_chip_width(self, num_qubit: int) -> int:
        chip_width = math.isqrt(num_qubit)
        if chip_width**2 != num_qubit or chip_width % 2 == 1:
            raise ValueError(f"num_qubit must be square of an even number, but {num_qubit} is provided.")
        return chip_width

    def index_to_position(self, index: int) -> tuple[int, int]:
        mux_index = index // 4
        index_in_mux = index % 4
        chip_mux_width = self.chip_width // 2
        mux_x, mux_y = mux_index % chip_mux_width, mux_index // chip_mux_width
        x = mux_x * 2 + index_in_mux % 2
        y = mux_y * 2 + index_in_mux // 2
        return x, y

    def is_low_frequency(self, index: int) -> bool:
        index_in_mux = index % 4
        flag = index_in_mux in [0, 3]
        return flag

    def position_to_index(self, x: int, y: int) -> int:
        mux_x = x // 2
        mux_y = y // 2
        index_in_mux = x % 2 + 2 * (y % 2)
        chip_mux_width = self.chip_width // 2
        mux_index = mux_x + mux_y * chip_mux_width
        index = mux_index * 4 + index_in_mux
        return index

    def check_position_exist(self, x: int, y: int) -> bool:
        return 0 <= x and x < self.chip_width and 0 <= y and y < self.chip_width

    def get_CNOT_pair_list(self) -> list[tuple[int, int, str]]:
        result: list[tuple[int, int, str]] = []
        dx = [1, 0, -1, 0]
        dy = [0, 1, 0, -1]
        ds = ["R", "D", "L", "U"]
        for index_control in self.target_index_list:
            if not self.is_low_frequency(index_control):
                continue
            x, y = self.index_to_position(index_control)
            for di in range(4):
                nx = x + dx[di]
                ny = y + dy[di]
                if not self.check_position_exist(nx, ny):
                    continue
                index_target = self.position_to_index(nx, ny)
                if index_target not in self.target_index_list:
                    continue
                result.append((index_control, index_target, ds[di]))
        return result
