from logging import getLogger
import numpy as np
from mt_util.tunits_util import FrequencyType
from mt_quel_util.mod_demod import demodulate_waveform, demodulate_averaged_sample
from mt_quel_util.acq_window_shift import restore_waveform_position
from mt_quel_meas.job import MeasurementDataset, Job, TranslationInfo
from mt_quel_meas.qubeserver.job import JobQubeServer
from mt_quel_meas.qubeserver.util import _capture_channel_to_boxport

logger = getLogger(__name__)

def _get_sequence_channel_from_capture_channel(capture_channel: str, sequence_channel_to_capture_channel: dict[str, str]) -> str:
    hit: list[str] = []
    for _temp_sequence_channel, _temp_capture_channel in sequence_channel_to_capture_channel.items():
        if capture_channel == _temp_capture_channel:
            hit.append(_temp_sequence_channel)
    if len(hit) == 0:
        raise ValueError(f"{capture_channel} does not have sequence")
    elif len(hit) > 1:
        raise ValueError(f"{capture_channel} is assigned with multiple sequence channels {hit}")
    return hit[0]

def extract_dataset(job: Job, job_qube_server: JobQubeServer, translate: TranslationInfo, dataset: dict[str, np.ndarray]) -> MeasurementDataset:
    result = {}
    for capture_channel, data in dataset.items():
        sequence_channel = _get_sequence_channel_from_capture_channel(capture_channel, job_qube_server.sequence_chanenl_to_capture_channel)
        freq_modulate = job_qube_server.sequence_channel_to_frequency_modulation[sequence_channel]

        capture_point_list = job_qube_server.capture_channel_to_capture_point_list[capture_channel]
        num_capture_point = len(capture_point_list)
        preceding_time = job_qube_server.capture_channel_to_preceding_time[capture_channel]

        boxport = _capture_channel_to_boxport(capture_channel)
        sideband = job_qube_server.boxport_to_LO_sideband[boxport]

        num_shot = job.acquisition_config.num_shot
        num_time_slot = np.rint((job.acquisition_config.acquisition_duration*translate.instrument_const.ADC_decimated_freq)[""]).astype(int)
        num_sample_precede = np.rint(preceding_time*translate.instrument_const.ADC_decimated_freq).astype(int)
        num_time_slot_reduced = np.rint(((job.acquisition_config.acquisition_duration - translate.instrument_const.ACQ_first_window_position_timestep)*translate.instrument_const.ADC_decimated_freq)[""]).astype(int)

        # take adjoint if readout is LSB
        if sideband == "LSB":
            np.conj(data, out=data)

        if job.acquisition_config.flag_average_shots and job.acquisition_config.flag_average_waveform:
            # shape data
            sample_list = data.reshape((num_capture_point, ))

            # perform demodulation for each capture point
            for capture_point_index, capture_point in enumerate(capture_point_list):
                sample_list[capture_point_index] = demodulate_averaged_sample(sample_list[capture_point_index], freq_modulate, translate.instrument_const, capture_point)

            # returned data is sum of shots, so divide it by num_shots to take average
            sample_list /= num_shot

            result[sequence_channel] = sample_list

        elif job.acquisition_config.flag_average_shots and (not job.acquisition_config.flag_average_waveform):
            # shape data
            shaped_data = data.reshape([num_capture_point, num_time_slot])

            # perform demodulation for each capture point
            for capture_point_index, capture_point in enumerate(capture_point_list):
                shaped_data[capture_point_index] = demodulate_waveform(shaped_data[capture_point_index], freq_modulate, translate.instrument_const, capture_point)

            # adjust preceding window
            result_data = shaped_data[:,num_sample_precede:num_sample_precede+num_time_slot_reduced]
            assert(result_data.shape == (num_capture_point, num_time_slot_reduced))

            # returned data is sum of shots, so divide it by num_shots to take average
            result_data /= num_shot

            result[sequence_channel] = result_data

        elif (not job.acquisition_config.flag_average_shots) and job.acquisition_config.flag_average_waveform:
            # shape data and swap axis of shot and capture_points
            shot_list_pre_transpose = data.reshape((num_shot, num_capture_point))
            shot_list = shot_list_pre_transpose.transpose([1,0])
            assert(shot_list.shape == ((num_capture_point, num_shot)))

            # perform demodulation for each capture point
            for capture_point_index, capture_point in enumerate(capture_point_list):
                shot_list[capture_point_index] = demodulate_averaged_sample(shot_list[capture_point_index], freq_modulate, translate.instrument_const, capture_point)

            result[sequence_channel] = shot_list

        elif (not job.acquisition_config.flag_average_shots) and (not job.acquisition_config.flag_average_waveform):
            # shape data and swap axis of shot and capture_points
            shaped_data_pre_transpose = data.reshape((num_shot, num_capture_point, num_time_slot))
            shaped_data = shaped_data_pre_transpose.transpose([1,0,2])
            assert(shaped_data.shape == ((num_capture_point, num_shot, num_time_slot)))
            

            # perform demodulation for each capture point
            for capture_point_index, capture_point in enumerate(capture_point_list):
                shaped_data[capture_point_index] = demodulate_waveform(shaped_data[capture_point_index], freq_modulate, translate.instrument_const, capture_point)

            # adjust preceding window
            result_data = shaped_data[:,:,num_sample_precede:num_sample_precede+num_time_slot_reduced]
            assert(result_data.shape == (num_capture_point, num_shot, num_time_slot_reduced))

            result[sequence_channel] = result_data
        else:
            assert(False)
    return result
    # translate_dataset = MeasurementDataset(shape = [], dataarray = [])
    # return translate_dataset


