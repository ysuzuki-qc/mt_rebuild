from __future__ import annotations
from typing import Optional
from dataclasses import dataclass, asdict, field

import numpy as np
import cirq


@dataclass(frozen=True)
class QuantumCircuit:
    num_qubit: int
    gate_list: list[dict] = field(default_factory=list)

    def add_gate(
        self, name: str, targets: list[int], *, angle: Optional[float] = None, matrix: Optional[np.ndarray] = None
    ) -> None:
        gate_name_list = ["RX", "RY", "RZ"]
        gate_name_list += ["u2", "u4"]
        gate_name_list += ["HPI", "CHPI"]
        gate_name_list += ["MZ", "BARRIER"]
        gate_name_list += ["SYNC"]
        if name not in gate_name_list:
            raise ValueError(f"gate name: {name} is not in known gate list. Available gates are {gate_name_list}")
        if isinstance(targets, int):
            targets = list([targets])
        if name in ["RX", "RY", "RZ"]:
            expect_angle = True
            expect_matrix = False
            expect_num_target = 1
        elif name in ["u2"]:
            expect_angle = False
            expect_matrix = True
            expect_num_target = 1
        elif name in ["u4"]:
            expect_angle = False
            expect_matrix = True
            expect_num_target = 2
        elif name in ["HPI"]:
            expect_angle = True
            expect_matrix = False
            expect_num_target = 1
        elif name in ["CHPI"]:
            expect_angle = True
            expect_matrix = False
            expect_num_target = 2
        elif name in ["MZ", "BARRIER"]:
            expect_angle = False
            expect_matrix = False
            expect_num_target = 1
        elif name in ["SYNC"]:
            expect_angle = False
            expect_matrix = False
            expect_num_target = -1

        # check angle
        if expect_angle and (angle is None):
            raise ValueError(f"angle must be given for {name}")
        if (not expect_angle) and (angle is not None):
            raise ValueError(f"angle must be None for {name}")

        # check matrix
        if expect_matrix and (matrix is None):
            raise ValueError(f"matrix must be given for {name}")
        if (not expect_matrix) and (matrix is not None):
            raise ValueError(f"matrix must be None for {name}")

        if expect_num_target != -1:
            # check target count
            if len(targets) != expect_num_target:
                raise ValueError(f"length of targets must be {expect_num_target}, but given count is {len(targets)}")
            # check matrix shape
            if expect_matrix and np.array(matrix).shape != (2**expect_num_target, 2**expect_num_target):
                raise ValueError(f"size of matrix is inconsistent to gate {name}")

        self.gate_list.append({"name": name, "targets": targets, "angle": angle, "matrix": matrix})

    def to_json_dict(self) -> dict:
        dict_form = asdict(self)
        # convert complex matrix to two real matries
        for gate in dict_form["gate_list"]:
            if gate["matrix"] is not None:
                real = np.real(gate["matrix"]).astype(float).tolist()
                imag = np.imag(gate["matrix"]).astype(float).tolist()
                gate["matrix"] = [real, imag]
        return dict_form

    @staticmethod
    def from_json_dict(data: dict) -> QuantumCircuit:
        qc = QuantumCircuit(**data)
        # convert two real matrices to complex matrix
        for gate in qc.gate_list:
            if gate["matrix"] is not None:
                real, imag = gate["matrix"]
                matrix = np.array(real, dtype=complex) + 1.0j * np.array(imag, dtype=complex)
                gate["matrix"] = matrix
        return qc

    def to_matrix(self) -> np.ndarray:
        q = cirq.LineQubit.range(self.num_qubit)
        gates = []
        for qi in q:
            gates.append(cirq.I(qi))
        for gate in self.gate_list:
            gate_name = gate["name"]
            targets = gate["targets"]
            angle = gate["angle"]
            matrix = gate["matrix"]

            if gate_name == "RX":
                gates.append(cirq.rx(angle)(q[targets[0]]))
            elif gate_name == "RY":
                gates.append(cirq.ry(angle)(q[targets[0]]))
            elif gate_name == "RZ":
                gates.append(cirq.rz(angle)(q[targets[0]]))

            elif gate_name == "u2":
                gates.append(cirq.MatrixGate(matrix)(q[targets[0]]))
            elif gate_name == "u4":
                gates.append(cirq.MatrixGate(matrix)(q[targets[0]], q[targets[1]]))

            elif gate_name == "HPI":
                gates.append(cirq.rz(angle)(q[targets[0]]))
                gates.append(cirq.rx(np.pi / 2)(q[targets[0]]))
                gates.append(cirq.rz(-angle)(q[targets[0]]))
            elif gate_name == "CHPI":
                gates.append(cirq.H(q[targets[0]]))
                gates.append(cirq.rz(angle)(q[targets[1]]))
                gates.append(cirq.CX(q[targets[1]], q[targets[0]]))
                gates.append(cirq.rx(np.pi / 2)(q[targets[1]]))
                gates.append(cirq.CX(q[targets[1]], q[targets[0]]))
                gates.append(cirq.rz(-angle)(q[targets[1]]))
                gates.append(cirq.H(q[targets[0]]))

            elif gate_name == "MZ":
                raise ValueError("Circuit with measurement cannot be converted to unitary")

            elif gate_name in ["SYNC", "BLANK", "SYNC_ALL"]:
                pass

            else:
                raise ValueError(f"Unknown gate: {gate}")
        U = cirq.unitary(cirq.Circuit(gates))
        dim = 2**self.num_qubit
        assert U.shape == (dim, dim)
        return U
