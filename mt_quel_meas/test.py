import logging
import json
import tunits
import numpy as np
import matplotlib.pyplot as plt
from mt_quel_meas.generate_job import generate_template, assign_to_quel
from mt_quel_meas.job import Job, AcquisitionConfig
from mt_quel_meas.execute import execute, execute_sweep
from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
from mt_quel_util.acq_window_shift import get_available_averaging_window_sample


format_str = "%(levelname)-7s : %(asctime)s : %(message)s"
logging.basicConfig(format=format_str)
logging.getLogger("mt_quel_meas").setLevel(logging.DEBUG)

with open("wiring_dict.json") as fin:
    wiring_dict_16Q = json.load(fin)


def plot_both_average(result: dict[str, np.ndarray], job_idx: int):
    num_channel = len(result)
    num_point = max([len(data) for data in result.values()])
    value_range = max([np.max(np.abs(data)) for data in result.values()]) * 1.01
    for channel_index, channel in enumerate(result):
        data = result[channel]
        assert data.ndim == 1
        for capture_point_index, shot in enumerate(data):
            ax = plt.subplot(num_point, num_channel, capture_point_index * num_channel + channel_index + 1)
            label = f"job{job_idx}_" + channel + f"_w{capture_point_index}"
            plt.scatter(np.real(shot), np.imag(shot), label=label)
            plt.xlim(-value_range, value_range)
            plt.ylim(-value_range, value_range)
            ax.set_aspect("equal", adjustable="box")
            plt.grid(which="major", color="black", linestyle="-", alpha=0.2)
            plt.grid(which="minor", color="black", linestyle="-", alpha=0.2)
            plt.legend()


def plot_average_shot(result: dict[str, np.ndarray], job_idx: int):
    num_channel = len(result)
    num_point = max([len(data) for data in result.values()])
    value_range = max([np.max(np.abs(data)) for data in result.values()]) * 1.01
    cmap = plt.get_cmap("tab20")
    for channel_index, channel in enumerate(result):
        data = result[channel]
        assert data.ndim == 2
        for capture_point_index, waveform in enumerate(data):
            plt.subplot(num_point, num_channel, capture_point_index * num_channel + channel_index + 1)
            time_slots = np.arange(len(waveform)) * 8
            label = f"job{job_idx}_" + channel + f"_w{capture_point_index}"
            plt.plot(time_slots, np.real(waveform), ".-", label=label + "_I", markersize=1, color=cmap(job_idx * 2))
            plt.plot(time_slots, np.imag(waveform), ".-", label=label + "_Q", markersize=1, color=cmap(job_idx * 2 + 1))
            plt.ylim(-value_range, value_range)
            plt.grid(which="major", color="black", linestyle="-", alpha=0.2)
            plt.grid(which="minor", color="black", linestyle="-", alpha=0.2)
            plt.legend(loc="lower right", fontsize=8)


def plot_average_waveform(result: dict[str, np.ndarray], job_idx: int):
    num_channel = len(result)
    num_point = max([len(data) for data in result.values()])
    value_range = max([np.max(np.abs(data)) for data in result.values()]) * 1.01
    for channel_index, channel in enumerate(result):
        data = result[channel]
        assert data.ndim == 2
        for capture_point_index, shot_list in enumerate(data):
            ax = plt.subplot(num_point, num_channel, capture_point_index * num_channel + channel_index + 1)
            label = f"job{job_idx}_" + channel + f"_w{capture_point_index}"
            plt.scatter(np.real(shot_list), np.imag(shot_list), label=label)
            plt.xlim(-value_range, value_range)
            plt.ylim(-value_range, value_range)
            ax.set_aspect("equal", adjustable="box")
            plt.grid(which="major", color="black", linestyle="-", alpha=0.2)
            plt.grid(which="minor", color="black", linestyle="-", alpha=0.2)
            plt.legend()


def plot_no_average(result: dict[str, np.ndarray], job_idx: int):
    num_channel = len(result)
    num_point = max([len(data) for data in result.values()])
    value_range = max([np.max(np.abs(data)) for data in result.values()]) * 1.01
    max_sample = 5
    cmap = plt.get_cmap("tab20")
    for channel_index, channel in enumerate(result):
        data = result[channel]
        assert data.ndim == 3
        for capture_point_index, waveform_list in enumerate(data):
            sample = min(max_sample, len(waveform_list))
            alpha = 1.0 / sample
            for shot_index, waveform in enumerate(waveform_list[:sample]):
                plt.subplot(num_point, num_channel, capture_point_index * num_channel + channel_index + 1)
                time_slots = np.arange(len(waveform)) * 8
                if shot_index == 0:
                    label_I = f"job{job_idx}_" + channel + f"_w{capture_point_index}_I"
                    label_Q = f"job{job_idx}_" + channel + f"_w{capture_point_index}_Q"
                else:
                    label_I = None
                    label_Q = None
                plt.plot(
                    time_slots,
                    np.real(waveform),
                    ".-",
                    label=label_I,
                    markersize=1,
                    color=cmap(job_idx * 2),
                    alpha=alpha,
                )
                plt.plot(
                    time_slots,
                    np.imag(waveform),
                    ".-",
                    label=label_Q,
                    markersize=1,
                    color=cmap(job_idx * 2 + 1),
                    alpha=alpha,
                )
            plt.ylim(-value_range, value_range)
            plt.grid(which="major", color="black", linestyle="-", alpha=0.2)
            plt.grid(which="minor", color="black", linestyle="-", alpha=0.2)
            plt.legend(loc="lower right", fontsize=8)


def example1():
    # config
    enable_CR = True
    num_averageing_window_sample = get_available_averaging_window_sample(CONST_QuEL1SE_LOW_FREQ)
    num_qubit = 16

    target_qubit_list = [0]
    # create template
    (
        sequence,
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_frequency_reference,
        channel_to_averaging_window,
    ) = generate_template(num_qubit, target_qubit_list, num_averageing_window_sample, enable_CR)

    # config center frequency
    channel_to_frequency["Q0_qubit"] = 4 * tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6 * tunits.units.GHz
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence_config = sequence.get_config()
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_width"] = 500
    acquisition_config = AcquisitionConfig()
    acquisition_config.num_shot = 100

    # create job
    job = Job(
        sequence,
        sequence_config,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_averaging_window,
        acquisition_config,
    )

    # create translator
    assignment_quel = assign_to_quel(
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency_reference,
        wiring_dict_16Q,
        CONST_QuEL1SE_LOW_FREQ,
    )

    result = execute(job, assignment_quel)


def example2():
    # config
    target_qubit_list = [0, 1, 2, 3]
    num_qubit = 16
    num_window = 3
    num_job = 2
    num_shot = 10
    flag_average_shots = True
    flag_average_waveform = False
    enable_CR = True

    # create template
    num_averageing_window_sample = get_available_averaging_window_sample(CONST_QuEL1SE_LOW_FREQ)
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
    assignment_quel = assign_to_quel(
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency_reference,
        wiring_dict_16Q,
        CONST_QuEL1SE_LOW_FREQ,
    )

    # set frequency
    for i, q in enumerate(target_qubit_list):
        freq = (4.0 + 0.1 * i) * tunits.units.GHz
        if i != 0:
            freq += 0.2 * tunits.units.GHz
        channel_to_frequency[f"Q{q}_qubit"] = freq
        channel_to_frequency[f"Q{q}_resonator"] = (6.1 + 0.1 * i) * tunits.units.GHz

    # create seqeunce
    sequence.add_blank_command([f"Q{target_qubit_list[0]}_resonator"], 100)
    sequence.add_synchronize_all_command()
    for _ in range(num_window):
        sequence.add_capture_command([f"Q{q}_resonator" for q in target_qubit_list])
        for q in target_qubit_list:
            sequence.add_pulse("FLATTOP", {"channel": f"Q{q}_resonator"})
            sequence.add_blank_command([f"Q{q}_resonator"], 2500)
        sequence.add_synchronize_all_command()

    # create seqeunce config
    sequence_config = sequence.get_config()
    for q in target_qubit_list:
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_width"] = 300
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_amplitude"] = 0.24
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.1)

    # create acquisition config
    acquisition_config = AcquisitionConfig()
    acquisition_config.flag_average_shots = flag_average_shots
    acquisition_config.flag_average_waveform = flag_average_waveform
    acquisition_config.num_shot = num_shot
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1000 * tunits.units.ns

    plt.figure(figsize=(20, 10))
    for job_idx in range(num_job):

        # modify parameters for job
        for i, q in enumerate(target_qubit_list):
            param = sequence_config.get_parameter((f"Q{q}",))
            # phase = np.pi * (0.44) + (2 * np.pi / num_job) * job_idx
            width = 200 + 100 * i
            param["FLATTOP"]["flattop_width"] = width

        # create job
        job = Job(
            sequence,
            sequence_config,
            channel_to_frequency,
            channel_to_frequency_shift,
            channel_to_averaging_window,
            acquisition_config,
        )

        result = execute(job, assignment_quel)

        # plot result
        if acquisition_config.flag_average_shots:
            if acquisition_config.flag_average_waveform:
                plot_both_average(result, job_idx)
            else:
                plot_average_shot(result, job_idx)
        else:
            if acquisition_config.flag_average_waveform:
                plot_average_waveform(result, job_idx)
            else:
                plot_no_average(result, job_idx)

    plt.tight_layout()
    plt.show()


def example3():
    # config
    target_qubit_list = [0, 1, 2, 3]
    num_qubit = 16
    num_shot = 100
    flag_average_shots = True
    flag_average_waveform = False
    enable_CR = False

    # create template
    num_averageing_window_sample = get_available_averaging_window_sample(CONST_QuEL1SE_LOW_FREQ)
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
    assignment_quel = assign_to_quel(
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency_reference,
        wiring_dict_16Q,
        CONST_QuEL1SE_LOW_FREQ,
    )

    # set frequency
    for i, q in enumerate(target_qubit_list):
        channel_to_frequency[f"Q{q}_qubit"] = 64.0 * tunits.units.GHz
        channel_to_frequency[f"Q{q}_resonator"] = 6.0 * tunits.units.GHz

    # create seqeunce
    sequence.add_blank_command([f"Q{target_qubit_list[0]}_resonator"], 100)
    sequence.add_synchronize_all_command()
    sequence.add_capture_command([f"Q{q}_resonator" for q in target_qubit_list])
    for q in target_qubit_list:
        sequence.add_pulse("FLATTOP", {"channel": f"Q{q}_qubit"})
    sequence.add_synchronize_all_command()

    # create seqeunce config
    sequence_config = sequence.get_config()
    for q in target_qubit_list:
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_width"] = 500
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_amplitude"] = 0.9
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.1)

    # create acquisition config
    acquisition_config = AcquisitionConfig()
    acquisition_config.flag_average_shots = flag_average_shots
    acquisition_config.flag_average_waveform = flag_average_waveform
    acquisition_config.num_shot = num_shot
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1000 * tunits.units.ns


    plt.figure(figsize=(20, 10))
    num_job = 1
    for job_idx in range(1):

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

        result = execute(job, assignment_quel)

        # plot result
        if acquisition_config.flag_average_shots:
            if acquisition_config.flag_average_waveform:
                plot_both_average(result, job_idx)
            else:
                plot_average_shot(result, job_idx)
        else:
            if acquisition_config.flag_average_waveform:
                plot_average_waveform(result, job_idx)
            else:
                plot_no_average(result, job_idx)

    plt.tight_layout()
    plt.show()


def example4():
    # config
    enable_CR = True
    num_averageing_window_sample = get_available_averaging_window_sample(CONST_QuEL1SE_LOW_FREQ)
    num_qubit = 16

    target_qubit_list = [0]
    # create template
    (
        sequence,
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_frequency_reference,
        channel_to_averaging_window,
    ) = generate_template(num_qubit, target_qubit_list, num_averageing_window_sample, enable_CR)

    # config center frequency
    channel_to_frequency["Q0_qubit"] = 4 * tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6 * tunits.units.GHz
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence_config = sequence.get_config()
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_width"] = 500
    acquisition_config = AcquisitionConfig()
    acquisition_config.num_shot = 100

    # create job
    job = Job(
        sequence,
        sequence_config,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_averaging_window,
        acquisition_config,
    )

    # create translator
    assignment_quel = assign_to_quel(
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency_reference,
        wiring_dict_16Q,
        CONST_QuEL1SE_LOW_FREQ,
    )

    sweep_parameter = [
        {"frequency_shift.Q0_qubit": np.linspace(-10, 10, 10) * tunits.units.MHz},
    ]


    logging.getLogger("mt_quel_meas").setLevel(logging.WARN)
    result = execute_sweep(job, assignment_quel, sweep_parameter)

    for key, matrix in result.items():
        print(key, matrix.shape)


def example5():
    # config
    enable_CR = True
    num_averageing_window_sample = get_available_averaging_window_sample(CONST_QuEL1SE_LOW_FREQ)
    num_qubit = 16

    target_qubit_list = [0]
    # create template
    (
        sequence,
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_frequency_reference,
        channel_to_averaging_window,
    ) = generate_template(num_qubit, target_qubit_list, num_averageing_window_sample, enable_CR)

    # config center frequency
    channel_to_frequency["Q0_qubit"] = 4 * tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6 * tunits.units.GHz
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence_config = sequence.get_config()
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_width"] = 500
    acquisition_config = AcquisitionConfig()
    acquisition_config.num_shot = 100

    # create job
    job = Job(
        sequence,
        sequence_config,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_averaging_window,
        acquisition_config,
    )

    # create translator
    assignment_quel = assign_to_quel(
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency_reference,
        wiring_dict_16Q,
        CONST_QuEL1SE_LOW_FREQ,
    )

    sweep_parameter = [
        {"frequency_shift.Q0_qubit": np.linspace(-10, 10, 3) * tunits.units.MHz},
        {"sequencer.Q0.FLATTOP.flattop_width": np.linspace(10, 100, 2)},
    ]


    logging.getLogger("mt_quel_meas").setLevel(logging.WARN)
    result = execute_sweep(job, assignment_quel, sweep_parameter)

    for key, matrix in result.items():
        print(key, matrix.shape)


def example6():
    # config
    enable_CR = True
    num_averageing_window_sample = get_available_averaging_window_sample(CONST_QuEL1SE_LOW_FREQ)
    num_qubit = 16

    target_qubit_list = [0]
    # create template
    (
        sequence,
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_frequency_reference,
        channel_to_averaging_window,
    ) = generate_template(num_qubit, target_qubit_list, num_averageing_window_sample, enable_CR)

    # config center frequency
    channel_to_frequency["Q0_qubit"] = 4 * tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6 * tunits.units.GHz
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence_config = sequence.get_config()
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_width"] = 500
    acquisition_config = AcquisitionConfig()
    acquisition_config.num_shot = 100

    # create job
    job = Job(
        sequence,
        sequence_config,
        channel_to_frequency,
        channel_to_frequency_shift,
        channel_to_averaging_window,
        acquisition_config,
    )

    # create translator
    assignment_quel = assign_to_quel(
        channel_to_role,
        channel_to_qubit_index_list,
        channel_to_frequency_reference,
        wiring_dict_16Q,
        CONST_QuEL1SE_LOW_FREQ,
    )

    sweep_parameter = [
        {"frequency_shift.Q0_qubit": np.linspace(-10, 10, 3) * tunits.units.MHz,
         "sequencer.Q0.FLATTOP.flattop_width": np.linspace(10, 100, 3)}
    ]


    logging.getLogger("mt_quel_meas").setLevel(logging.WARN)
    result = execute_sweep(job, assignment_quel, sweep_parameter)

    for key, matrix in result.items():
        print(key, matrix.shape)

# example1()
# example2()
# example3()
# example4()
# example5()
example6()
