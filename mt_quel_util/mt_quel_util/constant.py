from typing import Literal
from pydantic.dataclasses import dataclass
from tunits.units import GHz, MHz, ns, ms
from mt_util.tunits_util import FrequencyType, TimeType


@dataclass(frozen=True, slots=True)
class InstrumentConstantQuEL:
    # list of port types
    port_type: list[Literal["Unused", "ReadIn", "ReadOut", "Pump", "Control"]]

    # num of DAC channels for each port
    num_dac_channel: list[int]

    # LO Frequency for resonator contorl
    LO_freq_qubit: FrequencyType
    # LO Sideband resonator control
    LO_sideband_qubit: Literal["LSB", "USB", "Direct"]
    # LO Frequency for resonator contorl
    LO_freq_resonator: FrequencyType
    # LO Sideband resonator control
    LO_sideband_resonator: Literal["LSB", "USB", "Direct"]
    # LO Frequency for jpa pump
    LO_freq_jpa: FrequencyType
    # LO Sideband for jpa control
    LO_sideband_jpa: Literal["LSB", "USB", "Direct"]

    # Step frequency of NCO
    NCO_step_freq: FrequencyType
    # Sampling frequency of NCO
    NCO_sampling_freq: FrequencyType

    # Effective Bandwidth by NCO
    NCO_bandwidth_effective: FrequencyType
    # Effective Bandwidth of DAC channel
    DAC_bandwidth_effective: FrequencyType

    # Decimtion frequency of ADC channel
    ADC_decimated_freq: FrequencyType

    # Baseband frequency of DAC channel
    DACBB_sampling_freq: FrequencyType
    # Baseband frequency of ADC channel
    ADCBB_sampling_freq: FrequencyType

    # The number of FIR filters
    ACQ_max_fir_coeff: int

    # Acquisitoin window
    ACQ_first_window_position_timestep: TimeType
    ACQ_window_length_min: TimeType
    ACQ_window_length_max: TimeType
    ACQ_window_length_step: TimeType

    # Waveform length
    waveform_length_maximum: TimeType
    waveform_length_step: TimeType
    repetition_time_step: TimeType

    # unit synchronization delay
    synchronization_delay: TimeType


CONST_QuEL1SE_LOW_FREQ = InstrumentConstantQuEL(
    port_type=[
        "ReadIn",
        "ReadOut",
        "Pump",
        "Unused",
        "Unused",
        "Unused",
        "Control",
        "Control",
        "Control",
        "Control",
        "Unused",
        "Unused",
    ],
    num_dac_channel=[0, 1, 1, 0, 0, 0, 1, 3, 3, 1, 0, 0],
    LO_freq_qubit=0.0 * GHz,
    LO_sideband_qubit="Direct",
    # LO_freq_resonator = 8.5 * GHz,
    LO_freq_resonator=9.0 * GHz,
    LO_sideband_resonator="LSB",
    LO_freq_jpa=9.0 * GHz,
    LO_sideband_jpa="LSB",
    NCO_sampling_freq=2000 * MHz,
    NCO_step_freq=(12000 / (2**9)) * MHz,  # 23.4375 MHz
    NCO_bandwidth_effective=1600 * MHz,
    DAC_bandwidth_effective=400 * MHz,
    ADC_decimated_freq=125 * MHz,
    DACBB_sampling_freq=500 * MHz,
    ADCBB_sampling_freq=500 * MHz,
    ACQ_max_fir_coeff=16,
    ACQ_first_window_position_timestep=128 * ns,
    ACQ_window_length_min=64 * ns,
    ACQ_window_length_max=2048 * ns,
    ACQ_window_length_step=8 * ns,
    waveform_length_maximum=2000000 * ns,
    waveform_length_step=128 * ns,
    repetition_time_step=10240 * ns,
    synchronization_delay=100 * ms,
)
