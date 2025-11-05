import numpy as np
from tunits.units import ns
from mt_util.tunits_util import TimeType
from mt_quel_util.constant import InstrumentConstantQuEL


def get_available_averaging_window_sample(constant: InstrumentConstantQuEL) -> int:
    ADC_decimated_freq = constant.ADC_decimated_freq
    start_window_step = constant.ACQ_first_window_position_timestep 
    num_sample_window_available = np.rint((constant.ACQ_window_length_max - start_window_step)*ADC_decimated_freq).astype(int).item()
    return num_sample_window_available

def adjust_acquisition_window_position(acquisition_point_list: list[float], constant: InstrumentConstantQuEL) -> tuple[list[float], TimeType]:
    if len(acquisition_point_list) == 0:
        raise ValueError("No acquisition window found")
    start_window_time = (sorted(acquisition_point_list)[0]) * ns
    start_window_step = constant.ACQ_first_window_position_timestep 
    decim_time_step = 1./constant.ADC_decimated_freq
        
    preceding_time = start_window_time - np.floor(start_window_time["ns"]/start_window_step["ns"])*start_window_step
    adjusted_acquisition_point_list: list[float] = []
    for acq_point_ns in acquisition_point_list:
        acq_point = acq_point_ns*ns
        adjusted_acq_point = np.round((acq_point - preceding_time)/decim_time_step) * decim_time_step
        adjusted_acquisition_point_list.append(adjusted_acq_point["ns"])
    return adjusted_acquisition_point_list, preceding_time

def adjust_averaging_window(averaging_window: np.ndarray, preceding_time: TimeType, constant: InstrumentConstantQuEL) -> np.ndarray:
    ADC_decimated_freq = constant.ADC_decimated_freq
    num_sample_precede = np.rint(preceding_time*ADC_decimated_freq).astype(int)
    num_sample_window_actual = np.rint(constant.ACQ_window_length_max*ADC_decimated_freq).astype(int)
    adjusted_averaging_window = np.zeros(num_sample_window_actual, dtype=complex)
    if len(averaging_window) > num_sample_precede+len(averaging_window):
        raise ValueError("Averaging window is too long and cannot adjust the position to mutiple of 128ns")
    adjusted_averaging_window[num_sample_precede:num_sample_precede+len(averaging_window)] = averaging_window
    return adjusted_averaging_window

def adjust_readout_waveform(readout_waveform: np.ndarray, preceding_time: TimeType, constant: InstrumentConstantQuEL) -> np.ndarray:
    ADC_decimated_freq = constant.ADC_decimated_freq
    num_sample_precede = np.rint(preceding_time*ADC_decimated_freq).astype(int)
    num_sample_window_available = np.rint( (constant.ACQ_window_length_max-constant.ACQ_first_window_position_timestep) * ADC_decimated_freq).astype(int)
    adjusted_readout_waveform = readout_waveform[num_sample_precede:num_sample_precede+num_sample_window_available]
    return adjusted_readout_waveform
