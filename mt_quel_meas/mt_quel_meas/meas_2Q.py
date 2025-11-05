import numpy as np
from tunits.units import GHz
from mt_pulse.sequence import Sequence
from mt_pulse.pulse_preset import get_preset_pulse_library
from mt_util.tunits_util import FrequencyType
from mt_util.lattice_util import QubitLattice
from mt_quel_util.constant import InstrumentConstantQuEL
from mt_quel_util.acq_window_shift import get_available_averaging_window_sample
from mt_quel_meas.job import TranslationInfo

def _qubit_index_to_group_name(qubit_index: int) -> str:
    return f"Q{qubit_index}"

def _qubit_index_and_role_to_channel(qubit_index: int, role: str) -> str:
    return f"Q{qubit_index}_{role}"

def _create_2Q_sequence(num_qubit: int, target_qubit_list: list[int]) -> Sequence:
    sequence = Sequence(get_preset_pulse_library())
    role_list = ["qubit", "resonator"]
    for qubit_index in target_qubit_list:
        group = _qubit_index_to_group_name(qubit_index)
        for role in role_list:
            channel = _qubit_index_and_role_to_channel(qubit_index, role)
            sequence.add_channel(channel, group)

    qubit_lattice = QubitLattice(num_qubit, target_qubit_list)
    for control_index, _, direction_str in qubit_lattice.get_CNOT_pair_list():
        group = _qubit_index_to_group_name(control_index)
        role = f"CR_{direction_str}"
        channel = _qubit_index_and_role_to_channel(control_index, role)
        sequence.add_channel(channel, group)
    return sequence

def _create_2Q_frequency_dict(target_qubit_list: list[int]) -> dict[str, FrequencyType]:
    default_frequency_dict = {"qubit": 4.5*GHz, "resonator": 6.6*GHz}
    frequency_dict: dict[str, FrequencyType] = {}
    role_list = ["qubit", "resonator"]
    for qubit_index in target_qubit_list:
        for role in role_list:
            channel = _qubit_index_and_role_to_channel(qubit_index, role)
            frequency_dict[channel] = default_frequency_dict[role]
    return frequency_dict

def _create_2Q_frequency_shift_dict(target_qubit_list: list[int]) -> dict[str, FrequencyType]:
    frequency_dict: dict[str, FrequencyType] = {}
    role_list = ["qubit", "resonator"]
    for qubit_index in target_qubit_list:
        for role in role_list:
            channel = _qubit_index_and_role_to_channel(qubit_index, role)
            frequency_dict[channel] = 0*GHz
    return frequency_dict

def _create_2Q_averaging_window_dict(target_qubit_list: list[int], constant: InstrumentConstantQuEL) -> dict[str, np.ndarray]:
    num_averaging_window_sample = get_available_averaging_window_sample(constant)
    averaging_window_dict: dict[str, np.ndarray] = {}
    role = "resonator"
    for qubit_index in target_qubit_list:
        channel = _qubit_index_and_role_to_channel(qubit_index, role)
        averaging_window_dict[channel] = np.ones(num_averaging_window_sample, dtype=complex) * 0.5
    return averaging_window_dict

def _create_2Q_translation_info(target_qubit_list: list[int], wiring_dict: dict, constant: InstrumentConstantQuEL) -> TranslationInfo:
    role_list = ["qubit", "resonator"]
    channel_to_device: dict[str, str] = {}
    channel_to_port_index: dict[str, int] = {}
    for qubit_index in target_qubit_list:
        for role in role_list:
            channel = _qubit_index_and_role_to_channel(qubit_index, role)
            if role == "qubit":
                target = f"Q{qubit_index}"
                channel_to_device[channel] = wiring_dict[role][target]["device_name"]
                channel_to_port_index[channel] = wiring_dict[role][target]["port_index"]
            elif role == "resonator":
                target = f"M{qubit_index//4}"
                channel_to_device[channel] = wiring_dict[role][target]["device_name"]
                channel_to_port_index[channel] = wiring_dict[role][target]["port_index"]
            else:
                raise ValueError(f"Unknown channel specifier: {channel}")
    translation = TranslationInfo(
        sequence_channel_to_device=channel_to_device,
        sequence_channel_to_port_index=channel_to_port_index,
        wiring_dict=wiring_dict,
        instrument_const=constant,
    )
    return translation

def create_2Q_objects(num_qubit: int, target_qubit_list: list[int], wiring_dict: dict, constant: InstrumentConstantQuEL) -> tuple[Sequence, dict, dict, dict, TranslationInfo]:
    sequence = _create_2Q_sequence(num_qubit, target_qubit_list)
    channel_to_frequency = _create_2Q_frequency_dict(target_qubit_list)
    channel_to_frequency_shift = _create_2Q_frequency_shift_dict(target_qubit_list)
    channel_to_averaging_window = _create_2Q_averaging_window_dict(target_qubit_list, constant)
    translation = _create_2Q_translation_info(target_qubit_list, wiring_dict, constant)
    return sequence, channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translation
