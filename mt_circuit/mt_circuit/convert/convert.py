import numpy as np
from mt_circuit.circuit import QuantumCircuit
from mt_circuit.util import pauli_exp
from mt_circuit.gate import X, Y, Z
from mt_circuit.decompose.decompose import u2_matrix_to_HPI_RZ_form, u4_matrix_to_CHPI_u2_form


def remove_u4(circuit: QuantumCircuit) -> QuantumCircuit:
    new_circuit = QuantumCircuit(circuit.num_qubit)
    for gate in circuit.gate_list:
        gate_name = gate["name"]
        assert gate_name in ["MZ", "HPI", "CHPI", "SYNC", "RZ", "u2", "RX", "RY", "u4"]
        if gate_name in ["u4"]:
            c = u4_matrix_to_CHPI_u2_form(gate["matrix"])
            for temp_gate in c.gate_list:
                temp_gate["targets"] = [gate["targets"][idx] for idx in temp_gate["targets"]]
                new_circuit.add_gate(**temp_gate)
        else:
            new_circuit.add_gate(**gate)
    return new_circuit


def bundle_1q(circuit: QuantumCircuit) -> QuantumCircuit:
    new_circuit = QuantumCircuit(circuit.num_qubit)
    cache: dict[int, np.ndarray | None] = {}
    for idx in range(circuit.num_qubit):
        cache[idx] = None

    for gate in circuit.gate_list:
        gate_name = gate["name"]
        assert gate_name in ["MZ", "HPI", "CHPI", "SYNC", "RZ", "u2", "RX", "RY"]

        # if there is cache, multiply matrix. If not, add as gate
        if gate_name in ["RZ"]:
            idx = gate["targets"][0]
            if cache[idx] is not None:
                u = pauli_exp(Z, gate["angle"])
                cache[idx] = u @ cache[idx]
            else:
                new_circuit.add_gate(**gate)

        # if there is cache, multiply matrix. If not, create cache
        elif gate_name in ["RX", "RY", "u2"]:
            idx = gate["targets"][0]
            if gate_name == "RX":
                u = pauli_exp(X, gate["angle"])
            elif gate_name == "RY":
                u = pauli_exp(Y, gate["angle"])
            elif gate_name == "u2":
                u = gate["matrix"]
            else:
                assert False

            if cache[idx] is None:
                cache[idx] = u
            else:
                cache[idx] = u @ cache[idx]

        # For other gates, if there is cache, flash it. If not, ignore.
        else:
            for idx in gate["targets"]:
                if cache[idx] is not None:
                    new_circuit.add_gate(name="u2", targets=[idx], matrix=cache[idx])
                    cache[idx] = None
            new_circuit.add_gate(**gate)

    # flash residual cache
    for idx in range(circuit.num_qubit):
        if cache[idx] is not None:
            new_circuit.add_gate(name="u2", targets=[idx], matrix=cache[idx])

    return new_circuit


def remove_u2(circuit: QuantumCircuit) -> QuantumCircuit:
    new_circuit = QuantumCircuit(circuit.num_qubit)
    for gate in circuit.gate_list:
        gate_name = gate["name"]
        assert gate_name in ["MZ", "HPI", "CHPI", "SYNC", "RZ", "u2"]
        if gate_name in ["u2"]:
            u = gate["matrix"]
            c = u2_matrix_to_HPI_RZ_form(u)
            for temp_gate in c.gate_list:
                temp_gate["targets"] = gate["targets"]
                new_circuit.add_gate(**temp_gate)
        else:
            new_circuit.add_gate(**gate)
    return new_circuit


def push_rz(circuit: QuantumCircuit) -> QuantumCircuit:
    new_circuit = QuantumCircuit(circuit.num_qubit)
    phase_accum = np.zeros(circuit.num_qubit, dtype=float)
    for gate in circuit.gate_list:
        gate_name = gate["name"]
        assert gate_name in ["MZ", "HPI", "CHPI", "SYNC", "RZ"]
        if gate_name in ["RZ"]:
            phase_accum[gate["targets"][0]] += gate["angle"]
        elif gate_name in ["HPI"]:
            gate["angle"] = phase_accum[gate["targets"][0]]
            new_circuit.add_gate(**gate)
        elif gate_name in ["CHPI"]:
            gate["angle"] = phase_accum[gate["targets"][1]]
            new_circuit.add_gate(**gate)
        else:
            new_circuit.add_gate(**gate)
    for idx in range(circuit.num_qubit):
        new_circuit.add_gate(name="RZ", targets=[idx,], angle=phase_accum[idx])
    return new_circuit


def convert_to_HPI_CHPI(circuit: QuantumCircuit) -> QuantumCircuit:
    circuit = remove_u4(circuit)
    circuit = bundle_1q(circuit)
    circuit = remove_u2(circuit)
    circuit = push_rz(circuit)
    return circuit
