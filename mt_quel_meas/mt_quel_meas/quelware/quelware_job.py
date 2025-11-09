from dataclasses import dataclass
import numpy as np
from tunits.units import us, ms
from mt_util.tunits_util import TimeType, FrequencyType


@dataclass(frozen=True, slots=True)
class AcquisitionConfig:
    num_shot: int = 1000
    repetition_margin: TimeType = 100 * us
    acquisition_duration: TimeType = 1920 * us
    acquisition_delay: TimeType = 0 * us
    acquisition_timeout: TimeType = 5 * 1e6 * us
    acquisition_synchronization_delay: TimeType = 100 * ms
    flag_average_waveform: bool = False
    flag_average_shots: bool = False

@dataclass(frozen=True, slots=True)
class ChannelIdentifier:
    box: str
    port: int
    dac: int

@dataclass(frozen=True, slots=True)
class QuelwareJob:
    # BOX - Port - DAC
    acquisition_config: AcquisitionConfig
    ID_to_box_port_dac: dict[str, ChannelIdentifier]

    # waveform setting
    ID_to_waveform: dict[str, np.ndarray] | None

    # frequency setting
    ID_to_NCO_frequency: dict[str, tuple[FrequencyType, list[FrequencyType]]] | None

    # capture point setting
    ID_to_capture_point: dict[str, list[TimeType]]

    # averaging setting
    ID_to_averaging_window_coefficients: dict[str, np.ndarray] | None

    # demodulation setting
    ID_to_FIR_coefficients: dict[str, list[np.ndarray]] | None

    # constant
    # ID_to_LO_frequency: dict[str, FrequencyType] | None
    # ID_to_LO_sideband: dict[str, FrequencyType] | None
