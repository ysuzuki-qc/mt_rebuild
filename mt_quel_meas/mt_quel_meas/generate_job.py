from typing import Literal, Any
import numpy as np
import tunits
from mt_pulse.sequence import Sequence
from mt_pulse.pulse_preset import get_preset_pulse_library
from mt_util.tunits_util import FrequencyType
from mt_util.lattice_util import QubitLattice
from mt_quel_util.constant import InstrumentConstantQuEL
from mt_quel_meas.job import AssignmentQuel

_default_frequency_dict = {"qubit": 4.5 * tunits.units.GHz, "resonator": 6.6 * tunits.units.GHz}


def _qubit_index_to_group_name(qubit_index: int) -> str:
    return f"Q{qubit_index}"


def _qubit_index_and_role_to_channel(qubit_index: int, role: str) -> str:
    return f"Q{qubit_index}_{role}"


def _two_qubit_index_and_role_to_channel(qubit_index1: int, qubit_index2: int, role: str) -> str:
    return f"Q{qubit_index1}_Q{qubit_index2}_{role}"


def generate_template(
    num_qubit: int, target_qubit_list: list[int], num_averaging_window_sample: int, enable_CR: bool
) -> tuple[
    Sequence,
    dict[str, Literal["qubit", "resonator", "CR", "pump"]],
    dict[str, tuple[int, ...]],
    dict[str, FrequencyType],
    dict[str, FrequencyType],
    dict[str, str],
    dict[str, np.ndarray],
]:
    qubit_lattice = QubitLattice(num_qubit, target_qubit_list)
    channel_to_role: dict[str, Literal["qubit", "resonator", "CR", "pump"]] = {}
    channel_to_qubit_index_list: dict[str, tuple[int, ...]] = {}
    channel_to_frequency: dict[str, FrequencyType] = {}
    channel_to_frequency_shift: dict[str, FrequencyType] = {}
    channel_to_frequency_reference: dict[str, str] = {}
    channel_to_averaging_window: dict[str, np.ndarray] = {}

    sequence = Sequence(get_preset_pulse_library())
    role_list: list[Literal["qubit", "resonator", "CR", "pump"]] = ["qubit", "resonator"]
    for qubit_index in qubit_lattice.target_index_list:
        group = _qubit_index_to_group_name(qubit_index)
        for role in role_list:
            channel = _qubit_index_and_role_to_channel(qubit_index, role)
            sequence.add_channel(channel, group)
            channel_to_role[channel] = role
            channel_to_qubit_index_list[channel] = (qubit_index,)
            channel_to_frequency[channel] = _default_frequency_dict[role]
            channel_to_frequency_reference[channel] = channel
            channel_to_frequency_shift[channel] = 0 * tunits.units.GHz
            if role == "resonator":
                default_window = np.ones(num_averaging_window_sample, dtype=complex) * 0.5
                channel_to_averaging_window[channel] = default_window

    if enable_CR:
        for control_index, target_index, _ in qubit_lattice.get_CNOT_pair_list():
            group = _qubit_index_to_group_name(control_index)
            role = "CR"
            channel = _two_qubit_index_and_role_to_channel(control_index, target_index, role)
            sequence.add_channel(channel, group)
            channel_to_role[channel] = role
            channel_to_qubit_index_list[channel] = (control_index, target_index)
            channel_to_frequency_reference[channel] = _qubit_index_and_role_to_channel(target_index, "qubit")
            channel_to_frequency_shift[channel] = 0 * tunits.units.GHz

    return (
        sequence,
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_frequency_reference,
        channel_to_averaging_window,
    )


def assign_to_quel(
    channel_to_role: dict[str, str],
    channel_to_qubit_index_list: dict[str, tuple[int, ...]],
    channel_to_frequency_reference: dict[str, str],
    wiring_dict: dict[str, dict[str, dict[str, Any]]],
    instrument_const: InstrumentConstantQuEL,
) -> AssignmentQuel:
    channel_to_device: dict[str, str] = {}
    channel_to_port_index: dict[str, int] = {}
    for channel, role in channel_to_role.items():
        qubit_index_list = channel_to_qubit_index_list[channel]
        if role == "qubit":
            assert len(qubit_index_list) == 1
            name = f"Q{qubit_index_list[0]}"
            channel_to_device[channel] = wiring_dict[role][name]["device_name"]
            channel_to_port_index[channel] = wiring_dict[role][name]["port_index"]
        elif role == "resonator":
            assert len(qubit_index_list) == 1
            name = f"M{qubit_index_list[0]//4}"
            channel_to_device[channel] = wiring_dict[role][name]["device_name"]
            channel_to_port_index[channel] = wiring_dict[role][name]["port_index"]
        elif role == "CR":
            assert len(qubit_index_list) == 2
            name = f"Q{qubit_index_list[0]}"
            role = "qubit"
            channel_to_device[channel] = wiring_dict[role][name]["device_name"]
            channel_to_port_index[channel] = wiring_dict[role][name]["port_index"]
        else:
            raise ValueError(f"Unknown channel specifier: {channel}")

    assignment = AssignmentQuel(
        sequence_channel_to_device=channel_to_device,
        sequence_channel_to_port_index=channel_to_port_index,
        sequence_channel_frequency_reference=channel_to_frequency_reference,
        wiring_dict=wiring_dict,
        instrument_const=instrument_const,
    )
    return assignment
