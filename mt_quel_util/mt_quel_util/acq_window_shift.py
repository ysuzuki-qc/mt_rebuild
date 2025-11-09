import numpy as np
from tunits.units import ns
from mt_util.tunits_util import TimeType
from mt_quel_util.constant import InstrumentConstantQuEL


def get_available_averaging_window_sample(constant: InstrumentConstantQuEL) -> int:
    ADC_decimated_freq = constant.ADC_decimated_freq
    first_window_step = constant.ACQ_first_window_position_timestep
    num_sample_window_available = (
        np.rint((constant.ACQ_window_length_max - first_window_step) * ADC_decimated_freq).astype(int).item()
    )
    return num_sample_window_available


def adjust_capture_point_list(
    capture_point_list: list[TimeType], constant: InstrumentConstantQuEL
) -> tuple[list[TimeType], TimeType]:
    if len(capture_point_list) == 0:
        raise ValueError("No acquisition window found")
    first_window_time = sorted(capture_point_list)[0]
    first_window_step = constant.ACQ_first_window_position_timestep
    decim_time_step = (1.0 / constant.ADC_decimated_freq)["ns"] * ns

    preceding_time: TimeType = (
        first_window_time - np.floor(first_window_time["ns"] / first_window_step["ns"]) * first_window_step
    )
    adjusted_capture_point_list: list[TimeType] = []
    for acq_point in capture_point_list:
        adjusted_acq_point = np.round((acq_point - preceding_time)["ns"] / decim_time_step["ns"]) * decim_time_step
        adjusted_capture_point_list.append(adjusted_acq_point)
    return adjusted_capture_point_list, preceding_time


def adjust_averaging_window(
    averaging_window: np.ndarray, preceding_time: TimeType, constant: InstrumentConstantQuEL
) -> np.ndarray:
    ADC_decimated_freq = constant.ADC_decimated_freq
    num_sample_precede = np.rint(preceding_time * ADC_decimated_freq).astype(int)
    num_sample_window_actual = np.rint(constant.ACQ_window_length_max * ADC_decimated_freq).astype(int)
    adjusted_averaging_window = np.zeros(num_sample_window_actual, dtype=complex)
    if len(averaging_window) > num_sample_precede + len(averaging_window):
        raise ValueError("Averaging window is too long and cannot adjust the position to mutiple of 128ns")
    sample_start, sample_end = num_sample_precede, num_sample_precede + len(averaging_window)
    adjusted_averaging_window[sample_start:sample_end] = averaging_window
    return adjusted_averaging_window
