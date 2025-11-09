from typing import Literal
import numpy as np
from tunits.units import ns
from mt_util.tunits_util import FrequencyType, TimeType
from mt_quel_util.mux_assignment import get_multiplex_config, MultiplexingResult
from mt_quel_util.demux_filter import get_gaussian_FIR_coefficients
from mt_quel_util.mod_demod import modulate_waveform, modulate_averaging_window
from mt_quel_util.acq_window_shift import adjust_acquisition_window_position, adjust_averaging_window
from mt_quel_util.constant import InstrumentConstantQuEL
from mt_quel_meas.job import Job, TranslationInfo
from mt_quel_meas.labrad.labrad_job import JobLabrad, PhysicalUnitIdentifier, AcquisitionConfigLabrad


def _box_port_name(device_name: str, port_index: int) -> str:
    if port_index in [0,1]:
        return f"{device_name}-readout_{port_index}"
    elif port_index in [6,7,8,9]:
        return f"{device_name}-control_{port_index}"
    else:
        raise ValueError(f"Unexpected qube device specified: {device_name, port_index}")

def _awg_channel_name(device_name: str, port_index: int, awg_channel: int) -> str:
    return f"{_box_port_name(device_name,port_index)}-AWG_{awg_channel}"

def _capture_channel_name(device_name: str, port_index: int, capture_channel: int) -> str:
    return f"{_box_port_name(device_name,port_index)}-Capture_{capture_channel}"

def _map_sequence_channel_to_awg_channel(translate: TranslationInfo, mux_result: MultiplexingResult) -> dict[str, str]:
    sequence_channel_to_awg_channel: dict[str, str] = {}
    for sequence_channel in translate.sequence_channel_to_device:
        device = translate.sequence_channel_to_device[sequence_channel]
        port_index = translate.sequence_channel_to_port_index[sequence_channel]
        dac_index = mux_result.channel_to_dac_index[sequence_channel]
        awg_channel = _awg_channel_name(device, port_index, dac_index)
        sequence_channel_to_awg_channel[sequence_channel] = awg_channel
    return sequence_channel_to_awg_channel

def _get_awg_channel_to_dac_unit(translate: TranslationInfo, mux_result: MultiplexingResult) -> dict[str, PhysicalUnitIdentifier]:
    awg_channel_to_dac_unit: dict[str, PhysicalUnitIdentifier] = {}
    for sequence_channel in translate.sequence_channel_to_device:
        device = translate.sequence_channel_to_device[sequence_channel]
        port_index = translate.sequence_channel_to_port_index[sequence_channel]
        dac_index = mux_result.channel_to_dac_index[sequence_channel]
        awg_channel = _awg_channel_name(device, port_index, dac_index)
        if awg_channel not in awg_channel_to_dac_unit:
            box_port = _box_port_name(device, port_index)
            awg_channel_to_dac_unit[awg_channel] = PhysicalUnitIdentifier(box_port, dac_index)
    return awg_channel_to_dac_unit

def _get_sequence_channel_to_mux_index(awg_channel_list: list[str], sequence_to_physical: dict[str, str]) -> dict[str, int]:
    sequence_to_mux_index: dict[str, int] = {}
    mux_counter: dict[str, int] = {}
    for awg_channel in awg_channel_list:
        mux_counter[awg_channel] = 0
    for sequence_channel, awg_channel in sequence_to_physical.items():
        sequence_to_mux_index[sequence_channel] = mux_counter[awg_channel]
        mux_counter[awg_channel] += 1
    return sequence_to_mux_index

def _get_awg_channel_to_waveform(time_slots: np.ndarray,
                                      awg_channel_list: list[str],
                                      sequence_channel_to_awg_channel: dict[str, str],
                                      sequence_channel_to_waveform: dict[str, np.ndarray], 
                                      sequence_channel_to_frequency_shift: dict[str, FrequencyType],
                                      sequence_channel_to_residual_frequency: dict[str, FrequencyType],
                                      constant: InstrumentConstantQuEL):

    # create zero waveform
    awg_channel_to_waveform: dict[str, np.ndarray] = {}
    for awg_channel in awg_channel_list:
        awg_channel_to_waveform[awg_channel] = np.zeros_like(time_slots, dtype=complex)

    # add each sequence channel to physical channel
    for sequence_channel, awg_channel in sequence_channel_to_awg_channel.items():
        waveform = sequence_channel_to_waveform[sequence_channel]

        freq_residual = sequence_channel_to_residual_frequency[sequence_channel]
        freq_shift = sequence_channel_to_frequency_shift[sequence_channel]
        freq_modulate =  freq_residual + freq_shift
        modulated_waveform = modulate_waveform(waveform, freq_modulate, constant)

        awg_channel_to_waveform[awg_channel] += modulated_waveform
    return awg_channel_to_waveform

def _get_awg_channel_to_FNCO_frequency(mux_result: MultiplexingResult) -> dict[str, FrequencyType]:
    awg_channel_to_FNCO_frequency: dict[str, FrequencyType] = {}
    for device, FNCO_port in mux_result.FNCO_setting.items():
        for port_index, FNCO_dac in FNCO_port.items():
            for dac_index, freq in FNCO_dac.items():
                awg_channel = _awg_channel_name(device, port_index, dac_index)
                awg_channel_to_FNCO_frequency[awg_channel] = freq
    return awg_channel_to_FNCO_frequency

def _get_boxport_to_CNCO_frequency(mux_result: MultiplexingResult) -> dict[str, FrequencyType]:
    boxport_to_CNCO_frequency: dict[str, FrequencyType] = {}
    for device in mux_result.CNCO_setting:
        for port_index in mux_result.CNCO_setting[device]:
            boxport = _box_port_name(device, port_index)
            boxport_to_CNCO_frequency[boxport] = mux_result.CNCO_setting[device][port_index]
    return boxport_to_CNCO_frequency

def _get_boxport_to_LO_frequency(mux_result: MultiplexingResult, translate: TranslationInfo) -> dict[str, FrequencyType]:
    boxport_to_LO_frequency: dict[str, FrequencyType] = {}
    for device in mux_result.CNCO_setting:
        for port_index in mux_result.CNCO_setting[device]:
            boxport = _box_port_name(device, port_index)
            # TODO: check with port index
            if "readout" in boxport:
                boxport_to_LO_frequency[boxport] = translate.instrument_const.LO_freq_resonator
            elif "control" in boxport:
                boxport_to_LO_frequency[boxport] = translate.instrument_const.LO_freq_qubit
            elif "pump" in boxport:
                boxport_to_LO_frequency[boxport] = translate.instrument_const.LO_freq_jpa
            else:
                raise ValueError(f"Unknown boxport type: {boxport}")
    return boxport_to_LO_frequency

def _get_boxport_to_LO_sideband(mux_result: MultiplexingResult, translate: TranslationInfo) -> dict[str, Literal["USB", "LSB", "Direct"]]:
    boxport_to_LO_sideband: dict[str, Literal["USB", "LSB", "Direct"]] = {}
    for device in mux_result.CNCO_setting:
        for port_index in mux_result.CNCO_setting[device]:
            boxport = _box_port_name(device, port_index)
            # TODO: check with port index
            if "readout" in boxport:
                boxport_to_LO_sideband[boxport] = translate.instrument_const.LO_sideband_resonator
            elif "control" in boxport:
                boxport_to_LO_sideband[boxport] = translate.instrument_const.LO_sideband_qubit
            elif "pump" in boxport:
                boxport_to_LO_sideband[boxport] = translate.instrument_const.LO_sideband_jpa
            else:
                raise ValueError(f"Unknown boxport type: {boxport}")
    return boxport_to_LO_sideband


def _map_sequence_channel_to_capture_channel(translate: TranslationInfo, mux_result:MultiplexingResult, sequence_channel_to_mux_index: dict[str, int]) -> dict[str, str]:
    sequence_channel_to_capture_channel: dict[str, str] = {}
    for sequence_channel in translate.sequence_channel_to_device:
        port_index = translate.sequence_channel_to_port_index[sequence_channel]
        if translate.instrument_const.port_type[port_index] != "ReadOut":
            continue
        dac_index = mux_result.channel_to_dac_index[sequence_channel]
        if dac_index != 0:
            raise ValueError(f"ReadOut port is assumed to have a single DAC, but index {dac_index} is specified")

        device = translate.sequence_channel_to_device[sequence_channel]
        mux_index = sequence_channel_to_mux_index[sequence_channel]
        capture_channel = _capture_channel_name(device, port_index, mux_index)
        sequence_channel_to_capture_channel[sequence_channel] = capture_channel
    return sequence_channel_to_capture_channel

def _get_capture_channel_to_adc_unit(translate: TranslationInfo, sequence_channel_to_capture_channel: dict[str, str], sequence_channel_to_mux_index: dict[str, int]) -> dict[str, PhysicalUnitIdentifier]:
    capture_channel_to_adc_unit: dict[str, PhysicalUnitIdentifier] = {}
    for sequence_channel, capture_channel in sequence_channel_to_capture_channel.items():
        if capture_channel in capture_channel_to_adc_unit:
            continue

        device = translate.sequence_channel_to_device[sequence_channel]
        port_index = translate.sequence_channel_to_port_index[sequence_channel]
        mux_index = sequence_channel_to_mux_index[sequence_channel]
        capture_channel = _capture_channel_name(device, port_index, mux_index)
        assert(capture_channel not in capture_channel_to_adc_unit)
        box_port = _box_port_name(device, port_index)
        capture_channel_to_adc_unit[capture_channel] = PhysicalUnitIdentifier(box_port, mux_index)
    return capture_channel_to_adc_unit


def _get_capture_channel_to_capture_points_and_preceding_time(
        sequence_channel_to_capture_channel: dict[str, str],
        sequence_channel_to_capture_points: dict[str, list[TimeType]],
        instrument_const: InstrumentConstantQuEL) -> tuple[dict[str, list[TimeType]], dict[str, TimeType]]:

    capture_channel_to_capture_points: dict[str, list[TimeType]] = {}
    capture_channel_to_preceding_time: dict[str, TimeType] = {}

    for sequence_channel, capture_channel in sequence_channel_to_capture_channel.items():
        capture_points = sequence_channel_to_capture_points[sequence_channel]
        adjusted_capture_points, preceding_time = adjust_acquisition_window_position(capture_points, instrument_const)
        assert(capture_channel not in capture_channel_to_capture_points)
        capture_channel_to_capture_points[capture_channel] = adjusted_capture_points
        capture_channel_to_preceding_time[capture_channel] = preceding_time
    return capture_channel_to_capture_points, capture_channel_to_preceding_time


def _get_capture_channel_to_FIR_coefficients(
        sequence_channel_to_capture_channel: dict[str, str],
        sequence_channel_to_frequency_shift: dict[str, FrequencyType],
        sequence_channel_to_residual_frequency: dict[str, FrequencyType],
        constant: InstrumentConstantQuEL) -> dict[str, np.ndarray]:

    capture_channel_to_FIR_coefficients: dict[str, np.ndarray] = {}
    for sequence_channel, capture_channel in sequence_channel_to_capture_channel.items():
        freq_residual = sequence_channel_to_residual_frequency[sequence_channel]
        freq_shift = sequence_channel_to_frequency_shift[sequence_channel]
        freq_modulate =  freq_residual + freq_shift

        FIR_coefficients = get_gaussian_FIR_coefficients(freq_modulate, constant)
        capture_channel_to_FIR_coefficients[capture_channel] = FIR_coefficients
    return capture_channel_to_FIR_coefficients

def _get_capture_channel_to_averaging_window_coefficients(
        sequence_channel_to_capture_channel: dict[str, str],
        sequence_channel_to_averaging_window_coefficients: dict[str, np.ndarray],
        sequence_channel_to_frequency_shift: dict[str, FrequencyType],
        sequence_channel_to_residual_frequency: dict[str, FrequencyType],
        capture_channel_to_preceding_time: dict[str, TimeType],
        constant: InstrumentConstantQuEL) -> dict[str, np.ndarray]:

    capture_channel_to_averaging_window_coefficients: dict[str, np.ndarray] = {}
    for sequence_channel, capture_channel in sequence_channel_to_capture_channel.items():
        freq_residual = sequence_channel_to_residual_frequency[sequence_channel]
        freq_shift = sequence_channel_to_frequency_shift[sequence_channel]
        freq_modulate =  freq_residual + freq_shift

        averaging_window_coefficients = sequence_channel_to_averaging_window_coefficients[sequence_channel]
        preceding_time = capture_channel_to_preceding_time[capture_channel]
        adjusted_averaging_window_coefficients = adjust_averaging_window(averaging_window_coefficients, preceding_time, constant)
        adjusted_modulated_averaging_window_coefficients = modulate_averaging_window(adjusted_averaging_window_coefficients, freq_modulate, constant)
        capture_channel_to_averaging_window_coefficients[capture_channel] = adjusted_modulated_averaging_window_coefficients
    return capture_channel_to_averaging_window_coefficients

def translate_job_labrad(job: Job, translate: TranslationInfo) -> JobLabrad:
    # create waveform and capture points
    ## get waveform
    waveform_duration = job.sequence.get_duration(job.sequence_config, job.acquisition_config.acquisition_duration["ns"]) * ns

    ## adjust length
    waveform_length_step = translate.instrument_const.waveform_length_step
    waveform_length = np.ceil(waveform_duration/waveform_length_step) * waveform_length_step
    waveform_length_maximum = translate.instrument_const.waveform_length_maximum
    if waveform_length > waveform_length_maximum:
        raise ValueError(f"waveform is too long: provided {waveform_duration} but maximum: {waveform_length_maximum}")
    
    ## adjust repetition time
    repetition_time_step = translate.instrument_const.repetition_time_step
    repetition_time = waveform_length + job.acquisition_config.repetition_margin
    repetition_time = np.ceil(repetition_time/repetition_time_step)*repetition_time_step

    ## create timeslots
    delta_time = (1/translate.instrument_const.DACBB_sampling_freq)
    num_sample_waveform = np.ceil(waveform_length/delta_time).astype(int)
    time_slots_ns = np.arange(num_sample_waveform) * delta_time["ns"]
    sequence_channel_to_waveform, sequence_channel_to_capture_points_ns = job.sequence.get_waveform(time_slots_ns, job.sequence_config)
    sequence_channel_to_capture_points: dict[str, list[TimeType]] = {}
    for sequence_channel, capture_points_ns in sequence_channel_to_capture_points_ns.items():
        sequence_channel_to_capture_points[sequence_channel] = [capture_point_ns*ns for capture_point_ns in capture_points_ns]

    # TODO: modify sequence_channel_to_frequency to make CR frequency refer to qubit frequency
    mux_result = get_multiplex_config(job.sequence_channel_to_frequency, translate.sequence_channel_to_device, translate.sequence_channel_to_port_index, translate.instrument_const)

    # map Sequence -> DAC
    sequence_channel_to_awg_channel = _map_sequence_channel_to_awg_channel(translate, mux_result)
    awg_channel_list = list(set(sequence_channel_to_awg_channel.values()))

    # create DAC -> DAC Unit
    awg_channel_to_dac_unit = _get_awg_channel_to_dac_unit(translate, mux_result)

    # create DAC -> Waveform
    awg_channel_to_waveform = _get_awg_channel_to_waveform(
        time_slots_ns,
        awg_channel_list,
        sequence_channel_to_awg_channel,
        sequence_channel_to_waveform,
        job.sequence_channel_to_frequency_shift,
        mux_result.channel_to_residual_frequency,
        translate.instrument_const)

    # create DAC -> FNCO
    awg_channel_to_FNCO_frequency = _get_awg_channel_to_FNCO_frequency(mux_result)

    # create BoxPort -> CNCO
    boxport_to_CNCO_frequency = _get_boxport_to_CNCO_frequency(mux_result)

    boxport_to_LO_frequency = _get_boxport_to_LO_frequency(mux_result, translate)

    boxport_to_LO_sideband = _get_boxport_to_LO_sideband(mux_result, translate)


    # map Sequence -> ADC
    sequence_channel_to_mux_index = _get_sequence_channel_to_mux_index(awg_channel_list, sequence_channel_to_awg_channel)
    sequence_channel_to_capture_channel = _map_sequence_channel_to_capture_channel(translate, mux_result, sequence_channel_to_mux_index)

    # create ADC -> ADC Unit
    capture_channel_to_adc_unit = _get_capture_channel_to_adc_unit(
        translate,
        sequence_channel_to_capture_channel, 
        sequence_channel_to_mux_index)

    # create ADC -> capture points
    capture_channel_to_capture_points, capture_channel_to_preceding_time = _get_capture_channel_to_capture_points_and_preceding_time(
        sequence_channel_to_capture_channel,
        sequence_channel_to_capture_points,
        translate.instrument_const,)
    
    # check capture duration
    duration = job.acquisition_config.acquisition_duration
    duration_max = translate.instrument_const.ACQ_window_length_max
    duration_min = translate.instrument_const.ACQ_window_length_min
    duration_step = translate.instrument_const.ACQ_window_length_step
    if duration > duration_max:
        raise ValueError(f"acquisition duration is too long: obtained: {duration}, max: {duration_max}")
    if duration < duration_min:
        raise ValueError(f"acquisition duration is too short: obtained: {duration}, min: {duration_min}")
    duration_res = duration["ns"] % duration_step["ns"]
    if duration_res >= 0.5:
        raise ValueError(f"acquisition duration must be mutiple of {duration_step}: obtained: {duration}")

    # create ADC -> FIR coefficients
    capture_channel_to_FIR_coefficients = _get_capture_channel_to_FIR_coefficients(
        sequence_channel_to_capture_channel,
        job.sequence_channel_to_frequency_shift,
        mux_result.channel_to_residual_frequency,
        translate.instrument_const,)

    # create ADC -> averaging window coefficients
    capture_channel_to_averaging_window_coefficients = _get_capture_channel_to_averaging_window_coefficients(
        sequence_channel_to_capture_channel,
        job.sequence_channel_to_averaging_window,
        job.sequence_channel_to_frequency_shift,
        mux_result.channel_to_residual_frequency,
        capture_channel_to_preceding_time,
        translate.instrument_const,)
    
    acquisition_config_labrad = AcquisitionConfigLabrad(
        num_shot = job.acquisition_config.num_shot,
        repetition_time = repetition_time,
        waveform_length = waveform_length,
        acquisition_timeout = job.acquisition_config.acquisition_timeout,
        acquisition_synchronization_delay = translate.instrument_const.synchronization_delay,
        acquisition_duration = job.acquisition_config.acquisition_duration,
        flag_average_waveform = job.acquisition_config.flag_average_waveform,
        flag_average_shots = job.acquisition_config.flag_average_shots,
    )

    job_labrad = JobLabrad(
        acquisition_config=acquisition_config_labrad,
        awg_channel_to_dac_unit = awg_channel_to_dac_unit,
        awg_channel_to_waveform = awg_channel_to_waveform,
        awg_channel_to_FNCO_frequency = awg_channel_to_FNCO_frequency,

        boxport_to_CNCO_frequency = boxport_to_CNCO_frequency,
        boxport_to_LO_frequency = boxport_to_LO_frequency,
        boxport_to_LO_sideband = boxport_to_LO_sideband,

        capture_channel_to_adc_unit = capture_channel_to_adc_unit,
        capture_channel_to_capture_point = capture_channel_to_capture_points,
        capture_channel_to_preceding_time = capture_channel_to_preceding_time,
        capture_channel_to_FIR_coefficients = capture_channel_to_FIR_coefficients,
        capture_channel_to_averaging_window_coefficients = capture_channel_to_averaging_window_coefficients,
    )
    return job_labrad


