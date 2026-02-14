from logging import getLogger
from typing import Literal
import numpy as np
from tunits.units import ns
from mt_util.tunits_util import FrequencyType, TimeType
from mt_quel_util.mux_assignment import get_multiplex_config, MultiplexingResult
from mt_quel_util.demux_filter import get_gaussian_FIR_coefficients
from mt_quel_util.mod_demod import modulate_waveform, modulate_averaging_window
from mt_quel_util.acq_window_shift import adjust_capture_point_list, adjust_averaging_window
from mt_quel_util.constant import InstrumentConstantQuEL
from mt_quel_meas.job import Job, AssignmentQuel
from mt_quel_meas.qubeserver.job import JobQubeServer, PhysicalUnitIdentifier, AcquisitionConfigQubeServer
from mt_quel_meas.qubeserver.util import (
    _awg_channel_name,
    _capture_channel_name,
    _boxport_name,
)

logger = getLogger(__name__)


def _map_sequence_channel_to_awg_channel(assign: AssignmentQuel, mux_result: MultiplexingResult) -> dict[str, str]:
    sequence_channel_to_awg_channel: dict[str, str] = {}
    for sequence_channel in assign.sequence_channel_to_box_name:
        device = assign.sequence_channel_to_box_name[sequence_channel]
        port_index = assign.sequence_channel_to_port_index[sequence_channel]
        dac_index = mux_result.channel_to_dac_index[sequence_channel]
        awg_channel = _awg_channel_name(device, port_index, assign.instrument_const.port_type[port_index], dac_index)
        sequence_channel_to_awg_channel[sequence_channel] = awg_channel
    return sequence_channel_to_awg_channel


def _get_awg_channel_to_dac_unit(
    assign: AssignmentQuel, mux_result: MultiplexingResult
) -> dict[str, PhysicalUnitIdentifier]:
    awg_channel_to_dac_unit: dict[str, PhysicalUnitIdentifier] = {}
    for sequence_channel in assign.sequence_channel_to_box_name:
        device = assign.sequence_channel_to_box_name[sequence_channel]
        port_index = assign.sequence_channel_to_port_index[sequence_channel]
        dac_index = mux_result.channel_to_dac_index[sequence_channel]
        awg_channel = _awg_channel_name(device, port_index, assign.instrument_const.port_type[port_index], dac_index)
        print(awg_channel)
        if awg_channel not in awg_channel_to_dac_unit:
            box_port = _boxport_name(device, port_index, assign.wiring_dict)
            awg_channel_to_dac_unit[awg_channel] = PhysicalUnitIdentifier(box_port, dac_index)

        logger.info(
            f"job translate | awg channel assign | seq-ch: {sequence_channel} - awg-ch: {awg_channel}"
        )
    return awg_channel_to_dac_unit


def _get_sequence_channel_to_mux_index(
    awg_channel_list: list[str], sequence_to_physical: dict[str, str]
) -> dict[str, int]:
    sequence_to_mux_index: dict[str, int] = {}
    mux_counter: dict[str, int] = {}
    for awg_channel in awg_channel_list:
        mux_counter[awg_channel] = 0
    for sequence_channel, awg_channel in sequence_to_physical.items():
        sequence_to_mux_index[sequence_channel] = mux_counter[awg_channel]
        mux_counter[awg_channel] += 1
    return sequence_to_mux_index


def _get_awg_channel_to_waveform(
    time_slots: np.ndarray,
    awg_channel_list: list[str],
    sequence_channel_to_awg_channel: dict[str, str],
    sequence_channel_to_waveform: dict[str, np.ndarray],
    sequence_channel_to_frequency_modulation: dict[str, FrequencyType],
    sequence_channel_to_boxport: dict[str, str],
    boxport_to_LO_sideband: dict[str, Literal["USB", "LSB", "Direct"]],
    constant: InstrumentConstantQuEL,
):

    # create zero waveform
    awg_channel_to_waveform: dict[str, np.ndarray] = {}
    for awg_channel in awg_channel_list:
        awg_channel_to_waveform[awg_channel] = np.zeros_like(time_slots, dtype=complex)

    # add each sequence channel to physical channel
    for sequence_channel, awg_channel in sequence_channel_to_awg_channel.items():
        waveform = sequence_channel_to_waveform[sequence_channel]

        freq_modulate = sequence_channel_to_frequency_modulation[sequence_channel]
        modulated_waveform = modulate_waveform(waveform, freq_modulate, constant)
        awg_channel_to_waveform[awg_channel] += modulated_waveform
        logger.info(
            f"job translate | modulate waveform | v: {freq_modulate} "
            f"seq-ch: {sequence_channel} - awg-ch: {awg_channel}"
        )

    # take adjoint if signal is used as LSB
    for awg_channel in awg_channel_to_waveform:
        sequence_channel_filter = [_sequence_channel for _sequence_channel, _awg_channel in sequence_channel_to_awg_channel.items() if awg_channel == _awg_channel]
        assert(len(sequence_channel_filter)>=1)
        sequence_channel = sequence_channel_filter[0]
        boxport = sequence_channel_to_boxport[sequence_channel]
        if boxport_to_LO_sideband[boxport] == "LSB":
            np.conj(awg_channel_to_waveform[awg_channel], out=awg_channel_to_waveform[awg_channel])

    return awg_channel_to_waveform


def _get_awg_channel_to_FNCO_frequency(
    mux_result: MultiplexingResult, assign: AssignmentQuel
) -> dict[str, FrequencyType]:
    awg_channel_to_FNCO_frequency: dict[str, FrequencyType] = {}
    for device, FNCO_port in mux_result.FNCO_setting.items():
        for port_index, FNCO_dac in FNCO_port.items():
            for dac_index, freq in FNCO_dac.items():
                awg_channel = _awg_channel_name(
                    device, port_index, assign.instrument_const.port_type[port_index], dac_index
                )
                awg_channel_to_FNCO_frequency[awg_channel] = freq
    return awg_channel_to_FNCO_frequency


def _get_boxport_to_CNCO_frequency(mux_result: MultiplexingResult, assign: AssignmentQuel) -> dict[str, FrequencyType]:
    boxport_to_CNCO_frequency: dict[str, FrequencyType] = {}
    for device in mux_result.CNCO_setting:
        for port_index in mux_result.CNCO_setting[device]:
            boxport = _boxport_name(device, port_index, assign.wiring_dict)
            boxport_to_CNCO_frequency[boxport] = mux_result.CNCO_setting[device][port_index]
    return boxport_to_CNCO_frequency


def _get_boxport_to_LO_frequency(mux_result: MultiplexingResult, assign: AssignmentQuel) -> dict[str, FrequencyType]:
    boxport_to_LO_frequency: dict[str, FrequencyType] = {}
    for device in mux_result.CNCO_setting:
        for port_index in mux_result.CNCO_setting[device]:
            boxport = _boxport_name(device, port_index, assign.wiring_dict)
            port_type = assign.instrument_const.port_type[port_index]
            if port_type == "ReadOut":
                boxport_to_LO_frequency[boxport] = assign.instrument_const.LO_freq_resonator
            elif port_type == "Control":
                boxport_to_LO_frequency[boxport] = assign.instrument_const.LO_freq_qubit
            elif port_type == "Pump":
                boxport_to_LO_frequency[boxport] = assign.instrument_const.LO_freq_jpa
            else:
                raise ValueError(f"Unknown boxport type: {boxport}")
    return boxport_to_LO_frequency


def _get_boxport_to_LO_sideband(
    mux_result: MultiplexingResult, assign: AssignmentQuel
) -> dict[str, Literal["USB", "LSB", "Direct"]]:
    boxport_to_LO_sideband: dict[str, Literal["USB", "LSB", "Direct"]] = {}
    for device in mux_result.CNCO_setting:
        for port_index in mux_result.CNCO_setting[device]:
            boxport = _boxport_name(device, port_index, assign.wiring_dict)
            port_type = assign.instrument_const.port_type[port_index]
            if port_type == "ReadOut":
                boxport_to_LO_sideband[boxport] = assign.instrument_const.LO_sideband_resonator
            elif port_type == "Control":
                boxport_to_LO_sideband[boxport] = assign.instrument_const.LO_sideband_qubit
            elif port_type == "Pump":
                boxport_to_LO_sideband[boxport] = assign.instrument_const.LO_sideband_jpa
            else:
                raise ValueError(f"Unknown port type: {port_type} for dev: {device} port: {port_index}")
    return boxport_to_LO_sideband


def _map_sequence_channel_to_capture_channel(
    assign: AssignmentQuel, mux_result: MultiplexingResult, sequence_channel_to_mux_index: dict[str, int]
) -> dict[str, str]:
    sequence_channel_to_capture_channel: dict[str, str] = {}
    for sequence_channel in assign.sequence_channel_to_box_name:
        port_index = assign.sequence_channel_to_port_index[sequence_channel]
        if assign.instrument_const.port_type[port_index] != "ReadOut":
            continue
        dac_index = mux_result.channel_to_dac_index[sequence_channel]
        if dac_index != 0:
            raise ValueError(f"ReadOut port is assumed to have a single DAC, but index {dac_index} is specified")

        device = assign.sequence_channel_to_box_name[sequence_channel]
        mux_index = sequence_channel_to_mux_index[sequence_channel]
        capture_channel = _capture_channel_name(
            device, port_index, assign.instrument_const.port_type[port_index], mux_index
        )
        sequence_channel_to_capture_channel[sequence_channel] = capture_channel
    return sequence_channel_to_capture_channel


def _get_capture_channel_to_adc_unit(
    assign: AssignmentQuel,
    sequence_channel_to_capture_channel: dict[str, str],
    sequence_channel_to_mux_index: dict[str, int],
) -> dict[str, PhysicalUnitIdentifier]:
    capture_channel_to_adc_unit: dict[str, PhysicalUnitIdentifier] = {}
    for sequence_channel, capture_channel in sequence_channel_to_capture_channel.items():
        if capture_channel in capture_channel_to_adc_unit:
            continue

        device = assign.sequence_channel_to_box_name[sequence_channel]
        port_index = assign.sequence_channel_to_port_index[sequence_channel]
        mux_index = sequence_channel_to_mux_index[sequence_channel]
        capture_channel = _capture_channel_name(
            device, port_index, assign.instrument_const.port_type[port_index], mux_index
        )
        assert capture_channel not in capture_channel_to_adc_unit
        box_port = _boxport_name(device, port_index, assign.wiring_dict)
        capture_channel_to_adc_unit[capture_channel] = PhysicalUnitIdentifier(box_port, mux_index)
        logger.info(
            f"job translate | capture channel assign | seq-ch: {sequence_channel} - cap-ch: {capture_channel}"
        )
    return capture_channel_to_adc_unit


def _get_capture_channel_to_capture_point_list_and_preceding_time(
    sequence_channel_to_capture_channel: dict[str, str],
    sequence_channel_to_capture_point_list: dict[str, list[TimeType]],
    acquisition_delay: TimeType,
    instrument_const: InstrumentConstantQuEL,
) -> tuple[dict[str, list[TimeType]], dict[str, TimeType]]:

    capture_channel_to_capture_point_list: dict[str, list[TimeType]] = {}
    capture_channel_to_preceding_time: dict[str, TimeType] = {}

    for sequence_channel, capture_channel in sequence_channel_to_capture_channel.items():
        capture_point_list = sequence_channel_to_capture_point_list[sequence_channel]
        if len(capture_point_list) == 0:
            capture_channel_to_capture_point_list[capture_channel] = []
            capture_channel_to_preceding_time[capture_channel] = 0 * ns
            logger.info(
                f"job translate | adjust capture point | no capture point "
                f"seq-ch: {sequence_channel} - cap-ch: {capture_channel}"
            )
        else:
            delayed_capture_point_list = [capture_point + acquisition_delay for capture_point in capture_point_list]
            delayed_adjusted_capture_point_list, preceding_time = adjust_capture_point_list(
                delayed_capture_point_list, instrument_const
            )
            capture_channel_to_capture_point_list[capture_channel] = delayed_adjusted_capture_point_list
            capture_channel_to_preceding_time[capture_channel] = preceding_time
            for capture_point, adjust_capture_point in zip(capture_point_list, delayed_adjusted_capture_point_list):
                logger.info(
                    f"job translate | adjust capture point | "
                    f"org: {capture_point} adj: {adjust_capture_point} "
                    f"precede: {preceding_time} delay: {acquisition_delay} "
                    f"seq-ch: {sequence_channel} - cap-ch: {capture_channel}"
                )
    return capture_channel_to_capture_point_list, capture_channel_to_preceding_time


def _get_capture_channel_to_FIR_coefficients(
    sequence_channel_to_capture_channel: dict[str, str],
    sequence_channel_to_frequency_shift: dict[str, FrequencyType],
    sequence_channel_to_residual_frequency: dict[str, FrequencyType],
    constant: InstrumentConstantQuEL,
) -> dict[str, np.ndarray]:

    capture_channel_to_FIR_coefficients: dict[str, np.ndarray] = {}
    for sequence_channel, capture_channel in sequence_channel_to_capture_channel.items():
        freq_residual = sequence_channel_to_residual_frequency[sequence_channel]
        freq_shift = sequence_channel_to_frequency_shift[sequence_channel]
        freq_modulate = freq_residual + freq_shift

        FIR_coefficients = get_gaussian_FIR_coefficients(freq_modulate, constant)
        capture_channel_to_FIR_coefficients[capture_channel] = FIR_coefficients
        logger.info(
            f"job translate | modulate FIR coeffs | "
            f"v: {freq_modulate} (residual: {freq_residual}, shift: {freq_shift}) "
            f"seq-ch: {sequence_channel} awg-ch: {capture_channel}"
        )
    return capture_channel_to_FIR_coefficients


def _get_capture_channel_to_averaging_window_coefficients(
    sequence_channel_to_capture_channel: dict[str, str],
    sequence_channel_to_averaging_window_coefficients: dict[str, np.ndarray],
    sequence_channel_to_frequency_modulation: dict[str, FrequencyType],
    sequence_channel_to_boxport_name: dict[str, str],
    capture_channel_to_preceding_time: dict[str, TimeType],
    boxport_to_LO_sideband: dict[str, Literal["USB", "LSB", "Direct"]],
    constant: InstrumentConstantQuEL,
) -> dict[str, np.ndarray]:

    capture_channel_to_averaging_window_coefficients: dict[str, np.ndarray] = {}
    for sequence_channel, capture_channel in sequence_channel_to_capture_channel.items():
        freq_modulate = sequence_channel_to_frequency_modulation[sequence_channel]

        averaging_window_coefficients = sequence_channel_to_averaging_window_coefficients[sequence_channel]
        preceding_time = capture_channel_to_preceding_time[capture_channel]
        adjusted_averaging_window_coefficients = adjust_averaging_window(
            averaging_window_coefficients, preceding_time, constant
        )
        adjusted_modulated_averaging_window_coefficients = modulate_averaging_window(
            adjusted_averaging_window_coefficients, freq_modulate, constant
        )

        boxport = sequence_channel_to_boxport_name[sequence_channel]
        sideband = boxport_to_LO_sideband[boxport]
        if sideband == "LSB":
            np.conj(
                adjusted_modulated_averaging_window_coefficients, out=adjusted_modulated_averaging_window_coefficients
            )

        capture_channel_to_averaging_window_coefficients[capture_channel] = (
            adjusted_modulated_averaging_window_coefficients
        )
        logger.info(
            f"job translate | adjust averaging window | precede: {preceding_time} "
            f"seq-ch: {sequence_channel} - cap-ch: {capture_channel}"
        )
        logger.info(
            f"job translate | modulate averaging window | v: {freq_modulate} "
            f"seq-ch: {sequence_channel} - cap-ch: {capture_channel}"
        )
    return capture_channel_to_averaging_window_coefficients


def translate_job_qube_server(job: Job, assign: AssignmentQuel) -> JobQubeServer:
    # get waveform
    waveform_duration = (
        job.sequence.get_duration(job.sequence_config, job.acquisition_config.acquisition_duration["ns"]) * ns
    )

    # adjust length
    waveform_length_step = assign.instrument_const.waveform_length_step
    waveform_length = np.ceil(waveform_duration / waveform_length_step) * waveform_length_step
    waveform_length_maximum = assign.instrument_const.waveform_length_maximum
    if waveform_length > waveform_length_maximum:
        raise ValueError(f"waveform is too long: provided {waveform_duration} but maximum: {waveform_length_maximum}")

    # adjust repetition time
    repetition_time_step = assign.instrument_const.repetition_time_step
    repetition_time = waveform_length + job.acquisition_config.repetition_margin
    repetition_time = np.ceil(repetition_time / repetition_time_step) * repetition_time_step

    # create timeslots
    delta_time = 1 / assign.instrument_const.DACBB_sampling_freq
    num_sample_waveform = np.ceil(waveform_length / delta_time).astype(int)
    time_slots_ns = np.arange(num_sample_waveform) * delta_time["ns"]
    sequence_channel_to_waveform, sequence_channel_to_capture_point_list_ns = job.sequence.get_waveform(
        time_slots_ns, job.sequence_config
    )

    # convert float values to TimeType items
    sequence_channel_to_capture_point_list: dict[str, list[TimeType]] = {}
    for sequence_channel, capture_point_list_ns in sequence_channel_to_capture_point_list_ns.items():
        sequence_channel_to_capture_point_list[sequence_channel] = [
            capture_point_ns * ns for capture_point_ns in capture_point_list_ns
        ]

    # resolve frequency reference (e.g., Q0_Q2_CR refers to freq of Q2_qubit)
    sequence_channel_to_frequency: dict[str, FrequencyType] = {}
    for sequence_channel in assign.sequence_channel_to_box_name:
        sequence_channel_reference = assign.sequence_channel_frequency_reference[sequence_channel]
        freq_ref = job.sequence_channel_to_frequency[sequence_channel_reference]
        sequence_channel_to_frequency[sequence_channel] = freq_ref

    # find assignment
    mux_result = get_multiplex_config(
        sequence_channel_to_frequency,
        assign.sequence_channel_to_box_name,
        assign.sequence_channel_to_port_index,
        assign.instrument_const,
    )

    # calculate modulation
    sequence_channel_to_frequency_modulation: dict[str, FrequencyType] = {}
    for sequence_channel in assign.sequence_channel_to_box_name:
        freq_shift = job.sequence_channel_to_frequency_shift[sequence_channel]
        freq_residual = mux_result.channel_to_residual_frequency[sequence_channel]
        freq_modulate = freq_shift + freq_residual
        sequence_channel_to_frequency_modulation[sequence_channel] = freq_modulate

    # create BoxPort -> CNCO frequency
    boxport_to_CNCO_frequency = _get_boxport_to_CNCO_frequency(mux_result, assign)

    # create BoxPort -> LO frequency
    boxport_to_LO_frequency = _get_boxport_to_LO_frequency(mux_result, assign)

    # create BoxPort -> LO sideband
    boxport_to_LO_sideband = _get_boxport_to_LO_sideband(mux_result, assign)

    # map Sequence -> DAC
    sequence_channel_to_awg_channel = _map_sequence_channel_to_awg_channel(assign, mux_result)
    awg_channel_list = list(set(sequence_channel_to_awg_channel.values()))

    # create DAC -> DAC Unit
    awg_channel_to_dac_unit = _get_awg_channel_to_dac_unit(assign, mux_result)

    # create DAC -> Waveform
    awg_channel_to_waveform = _get_awg_channel_to_waveform(
        time_slots_ns,
        awg_channel_list,
        sequence_channel_to_awg_channel,
        sequence_channel_to_waveform,
        sequence_channel_to_frequency_modulation,
        assign.sequence_channel_to_boxport_name,
        boxport_to_LO_sideband,
        assign.instrument_const,
    )

    # create DAC -> FNCO frequency
    awg_channel_to_FNCO_frequency = _get_awg_channel_to_FNCO_frequency(mux_result, assign)

    # map Sequence -> ADC
    sequence_channel_to_mux_index = _get_sequence_channel_to_mux_index(
        awg_channel_list, sequence_channel_to_awg_channel
    )
    sequence_channel_to_capture_channel = _map_sequence_channel_to_capture_channel(
        assign, mux_result, sequence_channel_to_mux_index
    )

    # create ADC -> ADC Unit
    capture_channel_to_adc_unit = _get_capture_channel_to_adc_unit(
        assign, sequence_channel_to_capture_channel, sequence_channel_to_mux_index
    )

    # create ADC -> capture points
    capture_channel_to_capture_point_list, capture_channel_to_preceding_time = (
        _get_capture_channel_to_capture_point_list_and_preceding_time(
            sequence_channel_to_capture_channel,
            sequence_channel_to_capture_point_list,
            job.acquisition_config.acquisition_delay,
            assign.instrument_const,
        )
    )

    # check capture duration
    duration = job.acquisition_config.acquisition_duration
    duration_max = assign.instrument_const.ACQ_window_length_max
    duration_min = assign.instrument_const.ACQ_window_length_min
    duration_step = assign.instrument_const.ACQ_window_length_step
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
        assign.instrument_const,
    )

    # create ADC -> averaging window coefficients
    capture_channel_to_averaging_window_coefficients = _get_capture_channel_to_averaging_window_coefficients(
        sequence_channel_to_capture_channel,
        job.sequence_channel_to_averaging_window,
        sequence_channel_to_frequency_modulation,
        assign.sequence_channel_to_boxport_name,
        capture_channel_to_preceding_time,
        boxport_to_LO_sideband,
        assign.instrument_const,
    )

    # create QubeServer job
    acquisition_config_qube_server = AcquisitionConfigQubeServer(
        num_shot=job.acquisition_config.num_shot,
        repetition_time=repetition_time,
        waveform_length=waveform_length,
        acquisition_timeout=job.acquisition_config.acquisition_timeout,
        acquisition_synchronization_delay=assign.instrument_const.synchronization_delay,
        acquisition_duration=job.acquisition_config.acquisition_duration,
        flag_average_waveform=job.acquisition_config.flag_average_waveform,
        flag_average_shots=job.acquisition_config.flag_average_shots,
    )

    job_qube_server = JobQubeServer(
        sequence_channel_to_awg_channel=sequence_channel_to_awg_channel,
        sequence_chanenl_to_capture_channel=sequence_channel_to_capture_channel,
        sequence_channel_to_frequency_modulation=sequence_channel_to_frequency_modulation,
        acquisition_config=acquisition_config_qube_server,
        awg_channel_to_dac_unit=awg_channel_to_dac_unit,
        awg_channel_to_waveform=awg_channel_to_waveform,
        awg_channel_to_FNCO_frequency=awg_channel_to_FNCO_frequency,
        boxport_to_CNCO_frequency=boxport_to_CNCO_frequency,
        boxport_to_LO_frequency=boxport_to_LO_frequency,
        boxport_to_LO_sideband=boxport_to_LO_sideband,
        capture_channel_to_adc_unit=capture_channel_to_adc_unit,
        capture_channel_to_capture_point_list=capture_channel_to_capture_point_list,
        capture_channel_to_preceding_time=capture_channel_to_preceding_time,
        capture_channel_to_FIR_coefficients=capture_channel_to_FIR_coefficients,
        capture_channel_to_averaging_window_coefficients=capture_channel_to_averaging_window_coefficients,
    )
    return job_qube_server
