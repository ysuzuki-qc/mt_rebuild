
import sys
from typing import TextIO
import numpy as np
from mt_circuit.circuit import QuantumCircuit

def _add_empty_wire(line_list: list[str], space: int, repeat: int, qubit_count: int) -> None:
    line = (" " * space + "|") * qubit_count + " " * space
    line_list.extend([line,]*repeat)

def _add_moment_wire(line_list: list[str], space: int, repeat: int, qubit_count: int) -> None:
    line = ("-" * space + "|") * qubit_count + "-" * space
    line_list.extend([line,]*repeat)

def _add_gate_wire(line_list: list[str], space: int, qubit_list: list[int], gate: dict) -> None:
    line = ""
    for qubit_index in qubit_list:
        if qubit_index in gate["targets"]:
            short_name = gate["name"]
            if gate["name"] in ["RX", "RY", "RZ", "HPI", "CHPI"]:
                short_angle = (gate['angle']/np.pi)%2.0
                short_name += f"({short_angle:.2f}pi)"

            space_str = " " * (space + 1 - len(short_name))
            line += space_str + short_name
        else:
            line += " " * space + "|"
    line_list.append(line)

def get_moment_point_list(circuit: QuantumCircuit):
    """Calcualte moment points

    Returns:
        list[int]: gate indices of moment points
    """
    locked_qubit_set: set[int] = set()
    moment_point_list: list[int] = []
    for gate_idx, gate in enumerate(circuit.gate_list):
        qubit_set = set(gate["targets"])
        if( len(locked_qubit_set & qubit_set) != 0):
            moment_point_list.append(gate_idx)
            locked_qubit_set = qubit_set
        else:
            locked_qubit_set = locked_qubit_set | qubit_set
    return moment_point_list

def reorder_gates(circuit: QuantumCircuit) -> tuple[QuantumCircuit, list[int]]:
    front = np.zeros(circuit.num_qubit, dtype=int)
    result = {}
    for gate_idx, gate in enumerate(circuit.gate_list):
        targets = gate["targets"]
        largest_depth = max([front[target] for target in targets])
        min_idx = min(targets)
        result[(largest_depth, min_idx)] = gate_idx
        for target in targets:
            front[target] = largest_depth+1

    new_circuit = QuantumCircuit(circuit.num_qubit)
    moment_point_list: list[int] = []
    last_depth = 0
    for new_gate_idx, key in enumerate(sorted(result.keys())):
        gate_idx = result[key]
        new_circuit.add_gate(**(circuit.gate_list[gate_idx]))
        if key[0] > last_depth:
            moment_point_list.append(new_gate_idx)
            last_depth = key[0]
    return new_circuit, moment_point_list

def print_circuit(circuit: QuantumCircuit, stream: TextIO = sys.stdout, space:int = 15, repeat:int = 1) -> None:
    """Print circuit description

    Args:
        circuit (QuantumCircuit): quantum circuit
        stream (TextIO, optional): output stream. Defaults to sys.stdout.
    """
    qubit_list: list[int] = list(np.arange(circuit.num_qubit))
    circuit, moment_point_list = reorder_gates(circuit)

    line_list: list[str] = []
    for gate_idx, gate in enumerate(circuit.gate_list):
        if gate_idx in moment_point_list:
            _add_empty_wire(line_list, space, repeat, len(qubit_list))
            _add_moment_wire(line_list, space, repeat, len(qubit_list))
        _add_empty_wire(line_list, space, repeat, len(qubit_list))
        _add_gate_wire(line_list, space, qubit_list, gate)
    _add_empty_wire(line_list, space, repeat, len(qubit_list))
    for line in line_list:
        print(line, file=stream)

