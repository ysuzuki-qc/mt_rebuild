from dataclasses import dataclass
import numpy as np
from typing import Any
from tunits.units import us, ms, ns
import mt_pulse
from mt_pulse.sequence import Sequence, SequenceConfig
from mt_util.tunits_util import FrequencyType, TimeType
from mt_quel_util.constant import InstrumentConstantQuEL


@dataclass(frozen=True, slots=True)
class AcquisitionConfig:
    num_shot: int = 1000
    repetition_margin: TimeType = 100 * us

    waveform_length: TimeType = 128 * 1024 * ns
    acquisition_duration: TimeType = 1920 * us
    acquisition_delay: TimeType = 0 * us
    acquisition_timeout: TimeType = 5 * 1e6 * us
    acquisition_synchronization_delay: TimeType = 100 * ms
    flag_average_waveform: bool = False
    flag_average_shots: bool = False

@dataclass(frozen=True, slots=True)
class Job:
    sequence: Sequence
    sequence_config: SequenceConfig
    sequence_channel_to_frequency: dict[str, FrequencyType]
    sequence_channel_to_frequency_shift: dict[str, FrequencyType]
    sequence_channel_to_averaging_window: dict[str, np.ndarray]
    acquisition_config: AcquisitionConfig

@dataclass(frozen=True, slots=True)
class TranslationInfo:
    sequence_channel_to_device: dict[str, str]
    sequence_channel_to_port_index: dict[str, int]
    wiring_dict: dict[str, dict[str, str]]
    instrument_const: InstrumentConstantQuEL

@dataclass(frozen=True, slots=True)
class MeasurementDataset:
    shape: list[int]
    dataarray: list[complex]
