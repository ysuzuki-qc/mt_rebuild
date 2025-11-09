from dataclasses import dataclass
from typing import Literal
import numpy as np
from mt_util.tunits_util import FrequencyType, TimeType


@dataclass(frozen=True, slots=True)
class AcquisitionConfigQubeServer:
    num_shot: int
    waveform_length: TimeType
    repetition_time: TimeType
    acquisition_timeout: TimeType
    acquisition_synchronization_delay: TimeType
    acquisition_duration: TimeType
    flag_average_waveform: bool
    flag_average_shots: bool


@dataclass(frozen=True, slots=True)
class PhysicalUnitIdentifier:
    box_port: str
    unit_index: int


@dataclass(frozen=True, slots=True)
class JobQubeServer:
    # common config
    acquisition_config: AcquisitionConfigQubeServer

    sequence_channel_to_awg_channel: dict[str, str]
    sequence_chanenl_to_capture_channel: dict[str, str]
    sequence_channel_to_frequency_modulation: dict[str, FrequencyType]

    awg_channel_to_dac_unit: dict[str, PhysicalUnitIdentifier]
    awg_channel_to_waveform: dict[str, np.ndarray]
    awg_channel_to_FNCO_frequency: dict[str, FrequencyType]

    boxport_to_CNCO_frequency: dict[str, FrequencyType]
    boxport_to_LO_frequency: dict[str, FrequencyType]
    boxport_to_LO_sideband: dict[str, Literal["USB", "LSB", "Direct"]]

    capture_channel_to_adc_unit: dict[str, PhysicalUnitIdentifier]
    capture_channel_to_capture_point_list: dict[str, list[TimeType]]
    capture_channel_to_preceding_time: dict[str, TimeType]
    capture_channel_to_FIR_coefficients: dict[str, np.ndarray]
    capture_channel_to_averaging_window_coefficients: dict[str, np.ndarray]
