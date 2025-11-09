import numpy as np
from mt_quel_util.constant import InstrumentConstantQuEL
from mt_util.tunits_util import FrequencyType, TimeType


def modulate_waveform(
    channel_waveform: np.ndarray, frequency_modulate: FrequencyType, constant: InstrumentConstantQuEL
) -> np.ndarray:
    assert channel_waveform.ndim == 1
    DAC_baseband_freq = constant.DACBB_sampling_freq
    phase_factor = 2 * np.pi * (frequency_modulate["MHz"] / DAC_baseband_freq["MHz"]) * np.arange(len(channel_waveform))
    coef_factor = np.exp(1j * phase_factor)
    corrected_channel_waveform = channel_waveform * coef_factor
    return corrected_channel_waveform


def demodulate_waveform(
    readout_waveform: np.ndarray,
    frequency_modulate: FrequencyType,
    constant: InstrumentConstantQuEL,
    acquisition_start_time: TimeType,
):
    # readout waveform might be 2dim [#sample, #time] or 1dim [#time]
    assert readout_waveform.ndim in [1, 2]
    num_sample = readout_waveform.shape[-1]

    ADC_decimated_freq = constant.ADC_decimated_freq
    acquisition_sample_position = acquisition_start_time["ns"] * ADC_decimated_freq["GHz"]
    phase_factor = (
        2
        * np.pi
        * (frequency_modulate["MHz"] / ADC_decimated_freq["MHz"])
        * (np.arange(num_sample) + acquisition_sample_position)
    )
    coef_factor = np.exp(-1j * phase_factor)
    corrected_readout_waveform = readout_waveform * coef_factor
    return corrected_readout_waveform


def modulate_averaging_window(
    averaging_window_coefficients: np.ndarray, frequency_modulate: FrequencyType, constant: InstrumentConstantQuEL
):
    ADC_decimated_freq = constant.ADC_decimated_freq
    phase_factor = (
        2
        * np.pi
        * (frequency_modulate["MHz"] / ADC_decimated_freq["MHz"])
        * np.arange(len(averaging_window_coefficients))
    )
    coef_factor = np.exp(-1j * phase_factor)
    corrected_averaging_window_coefficients = averaging_window_coefficients * coef_factor
    return corrected_averaging_window_coefficients


def demodulate_averaged_sample(
    sample_list: np.ndarray,
    frequency_modulate: FrequencyType,
    constant: InstrumentConstantQuEL,
    acquisition_start_time: TimeType,
):
    ADC_decimated_freq = constant.ADC_decimated_freq
    acquisition_sample_position = acquisition_start_time["ns"] * ADC_decimated_freq["GHz"]
    phase_factor = 2 * np.pi * (frequency_modulate["MHz"] / ADC_decimated_freq["MHz"]) * acquisition_sample_position
    coef_factor = np.exp(-1j * phase_factor)
    corrected_sample_list = sample_list * coef_factor
    return corrected_sample_list
