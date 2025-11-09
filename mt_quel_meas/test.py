from logging import DEBUG, basicConfig, getLogger
import json
import tunits
import numpy as np
import matplotlib.pyplot as plt
from mt_quel_meas.generate_job import generate_template, assign_to_quel
from mt_quel_meas.job import Job, AcquisitionConfig
from mt_quel_meas.qubeserver.translate import translate_job_qube_server
from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
from mt_quel_meas.qubeserver.extract import extract_dataset
from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
from mt_quel_util.acq_window_shift import get_available_averaging_window_sample


format_str = "%(levelname)-7s : %(asctime)s : %(message)s"
basicConfig(format=format_str)
getLogger("mt_quel_meas").setLevel(DEBUG)

with open("wiring_dict.json") as fin:
    wiring_dict_16Q = json.load(fin)


def example1():
    target_qubit_list = [1, 2, 3, 6, 9]
    num_qubit = 16
    executor = JobExecutorQubeServer()
    num_averageing_window_sample = get_available_averaging_window_sample(CONST_QuEL1SE_LOW_FREQ)
    enable_CR = True
    (
        sequence,
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_frequency_reference,
        channel_to_averaging_window,
    ) = generate_template(num_qubit, target_qubit_list, num_averageing_window_sample, enable_CR)

    # create translator
    quel_assignment = assign_to_quel(
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency_reference,
        wiring_dict_16Q,
        CONST_QuEL1SE_LOW_FREQ,
    )

    acquisition_config = AcquisitionConfig()

    # set frequency
    for i, q in enumerate(target_qubit_list):
        channel_to_frequency[f"Q{q}_qubit"] = (4.0 + 0.1 * i) * tunits.units.GHz
        channel_to_frequency[f"Q{q}_resonator"] = (6.1 + 0.1 * i) * tunits.units.GHz

    # create seqeunce
    sequence.add_blank_command([f"Q{target_qubit_list[0]}_resonator"], 100)
    sequence.add_synchronize_all_command()
    num_window = 3
    for _ in range(num_window):
        sequence.add_capture_command([f"Q{q}_resonator" for q in target_qubit_list])
        for q in target_qubit_list:
            sequence.add_pulse("FLATTOP", {"channel": f"Q{q}_resonator"})
            sequence.add_blank_command([f"Q{q}_resonator"], 2500)
        sequence.add_synchronize_all_command()

    # create seqeunce config
    sequence_config = sequence.get_config()
    for q in target_qubit_list:
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_width"] = 500
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_amplitude"] = 0.24
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.1)

    # create config
    acquisition_config.flag_average_shots = True
    acquisition_config.flag_average_waveform = True
    acquisition_config.num_shot = 100
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1030 * tunits.units.ns

    plt.figure(figsize=(4, 9))
    num_job = 2
    for job_idx in range(num_job):

        # modify parameters for job
        for q in target_qubit_list:
            param = sequence_config.get_parameter((f"Q{q}",))
            phase = np.pi * (0.44) + (2 * np.pi / num_job) * job_idx
            param["FLATTOP"]["flattop_phase"] = phase

        # create job
        job = Job(
            sequence,
            sequence_config,
            channel_to_frequency,
            channel_to_frequency_shift,
            channel_to_averaging_window,
            acquisition_config,
        )

        # bind to qube server
        job_qube_server = translate_job_qube_server(job, quel_assignment)

        # do measurement
        result_qube_server = executor.do_measurement(job_qube_server)

        # extract data
        result = extract_dataset(job, job_qube_server, quel_assignment, result_qube_server)

        # plot
        for ch, data in result.items():
            assert data.ndim == 1
            for capture_point_index, value in enumerate(data):
                plt.subplot(num_window, 1, capture_point_index + 1)
                plt.xlim(-1e10, 1e10)
                plt.ylim(-1e10, 1e10)
                plt.grid()
                label = f"job{job_idx}_" + ch + f"_w{capture_point_index}"
                plt.scatter(np.real(value), np.imag(value), label=label)
                plt.legend()
    plt.tight_layout()
    plt.show()


example1()
