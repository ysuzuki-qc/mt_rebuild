from logging import DEBUG, basicConfig, getLogger
format_str = "%(levelname)-7s : %(asctime)s : %(message)s"
basicConfig(format=format_str)
getLogger("mt_quel_meas").setLevel(DEBUG)

wiring_dict_16Q = {
    "qubit": {
        "Q0": {"device_name": "quel1se-2-01","port_index": 7},
        "Q1": {"device_name": "quel1se-2-01","port_index": 6},
        "Q2": {"device_name": "quel1se-2-01","port_index": 9},
        "Q3": {"device_name": "quel1se-2-01","port_index": 8},
        "Q4": {"device_name": "quel1se-2-02","port_index": 7},
        "Q5": {"device_name": "quel1se-2-02","port_index": 6},
        "Q6": {"device_name": "quel1se-2-02","port_index": 9},
        "Q7": {"device_name": "quel1se-2-02","port_index": 8},
        "Q8": {"device_name": "quel1se-2-03","port_index": 7},
        "Q9": {"device_name": "quel1se-2-03","port_index": 6},
        "Q10": {"device_name": "quel1se-2-03","port_index": 9},
        "Q11": {"device_name": "quel1se-2-03","port_index": 8},
        "Q12": {"device_name": "quel1se-2-04","port_index": 7},
        "Q13": {"device_name": "quel1se-2-04","port_index": 6},
        "Q14": {"device_name": "quel1se-2-04","port_index": 9},
        "Q15": {"device_name": "quel1se-2-04","port_index": 8},
    },
    "resonator": {
        "M0": {"device_name": "quel1se-2-01","port_index": 1},
        "M1": {"device_name": "quel1se-2-02","port_index": 1},
        "M2": {"device_name": "quel1se-2-03","port_index": 1},
        "M3": {"device_name": "quel1se-2-04","port_index": 1},
    },
    "jpa": {
        "M0": {"device_name": "quel1se-2-01","port_index": 1},
        "M1": {"device_name": "quel1se-2-02","port_index": 1},
        "M2": {"device_name": "quel1se-2-03","port_index": 1},
        "M3": {"device_name": "quel1se-2-04","port_index": 1},
    },
}

def example1():
    # Create a job that is independent of executor and multiplexing details
    import pprint
    from mt_quel_meas.meas_1Q import create_1Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    target_qubit_list = [0,1]
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_1Q_objects(target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)

    sequence.add_blank_command(["Q0_qubit"], 100)
    sequence.add_pulse("FLATTOP", {"channel": "Q0_qubit"})
    sequence.add_synchronize_all_command()
    sequence.add_capture_command(["Q0_resonator", "Q1_resonator"])
    sequence.add_pulse("MEAS", {"resonator": "Q0_resonator"})
    sequence.add_pulse("MEAS", {"resonator": "Q1_resonator"})
    sequence_config = sequence.get_config()
    acquisition_config = AcquisitionConfig()
    job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)

    # convert job to qube_server form, execute it, and convert results
    job_qube_server = translate_job_qube_server(job, translate)
    pprint.pprint(job_qube_server.acquisition_config)
    pprint.pprint(job_qube_server.awg_channel_to_dac_unit)
    pprint.pprint(job_qube_server.awg_channel_to_waveform.keys())
    pprint.pprint(job_qube_server.awg_channel_to_FNCO_frequency)
    pprint.pprint(job_qube_server.boxport_to_CNCO_frequency)
    pprint.pprint(job_qube_server.capture_channel_to_adc_unit)
    pprint.pprint(job_qube_server.capture_channel_to_capture_point)
    pprint.pprint(job_qube_server.capture_channel_to_preceding_time)
    pprint.pprint(job_qube_server.capture_channel_to_FIR_coefficients)
    pprint.pprint(job_qube_server.capture_channel_to_averaging_window_coefficients.keys())


def example2():
    # Create a job that is independent of executor and multiplexing details
    import pprint
    from tunits.units import GHz
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0]
    num_qubit = 16
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)

    channel_to_frequency["Q0_qubit"] = 4.0*GHz
    channel_to_frequency["Q0_resonator"] = 6.1*GHz
    sequence.add_blank_command(["Q0_qubit"], 100)
    sequence.add_pulse("FLATTOP", {"channel": "Q0_qubit"})
    sequence.add_synchronize_all_command()
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("MEAS", {"resonator": "Q0_resonator"})
    sequence_config = sequence.get_config()
    acquisition_config = AcquisitionConfig()
    acquisition_config.flag_average_shots = False
    acquisition_config.flag_average_waveform = True
    job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)

    # convert job to qube_server form, execute it, and convert results
    job_qube_server = translate_job_qube_server(job, translate)
    executor = JobExecutorQubeServer()
    result_qube_server = executor.do_measurement(job_qube_server)
    # result = extract_dataset(job, job_qube_server, translate, result_qube_server)

def example3():
    # Create a job that is independent of executor and multiplexing details
    import pprint
    from tunits.units import GHz
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,1]
    num_qubit = 16
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)

    channel_to_frequency["Q0_qubit"] = 4.0*GHz
    channel_to_frequency["Q0_resonator"] = 6.1*GHz
    channel_to_frequency["Q1_qubit"] = 4.2*GHz
    channel_to_frequency["Q1_resonator"] = 6.3*GHz
    sequence.add_blank_command(["Q0_qubit"], 100)
    sequence.add_pulse("FLATTOP", {"channel": "Q0_qubit"})
    # sequence.add_pulse("FLATTOP", {"channel": "Q1_qubit"})
    sequence.add_synchronize_all_command()
    sequence.add_capture_command(["Q0_resonator", "Q1_resonator"])
    sequence.add_pulse("MEAS", {"resonator": "Q0_resonator"})
    # sequence.add_pulse("MEAS", {"resonator": "Q1_resonator"})

    sequence_config = sequence.get_config()
    acquisition_config = AcquisitionConfig()
    acquisition_config.flag_average_shots = False
    acquisition_config.flag_average_waveform = True
    job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)

    # convert job to qube_server form, execute it, and convert results
    job_qube_server = translate_job_qube_server(job, translate)
    executor = JobExecutorQubeServer()
    result_qube_server = executor.do_measurement(job_qube_server)
    # result = extract_dataset(job, job_qube_server, translate, result_qube_server)

def example4():
    # Create a job that is independent of executor and multiplexing details
    import pprint
    from tunits.units import GHz
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,1,4]
    num_qubit = 16
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)

    channel_to_frequency["Q0_qubit"] = 4.0*GHz
    channel_to_frequency["Q0_resonator"] = 6.1*GHz
    channel_to_frequency["Q1_qubit"] = 4.2*GHz
    channel_to_frequency["Q1_resonator"] = 6.3*GHz
    channel_to_frequency["Q4_qubit"] = 4.3*GHz
    channel_to_frequency["Q4_resonator"] = 6.4*GHz
    sequence.add_blank_command(["Q0_qubit"], 100)
    sequence.add_pulse("FLATTOP", {"channel": "Q0_qubit"})
    # sequence.add_pulse("FLATTOP", {"channel": "Q1_qubit"})
    sequence.add_synchronize_all_command()
    sequence.add_capture_command(["Q0_resonator", "Q1_resonator", "Q4_resonator"])
    sequence.add_pulse("MEAS", {"resonator": "Q0_resonator"})
    # sequence.add_pulse("MEAS", {"resonator": "Q1_resonator"})

    sequence_config = sequence.get_config()
    acquisition_config = AcquisitionConfig()
    acquisition_config.flag_average_shots = False
    acquisition_config.flag_average_waveform = True
    job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)

    # convert job to qube_server form, execute it, and convert results
    job_qube_server = translate_job_qube_server(job, translate)
    executor = JobExecutorQubeServer()
    result_qube_server = executor.do_measurement(job_qube_server)
    # result = extract_dataset(job, job_qube_server, translate, result_qube_server)


def example5():
    # Create a job that is independent of executor and multiplexing details
    import pprint
    from tunits.units import GHz
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,]
    num_qubit = 16
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)

    channel_to_frequency["Q0_qubit"] = 4.0*GHz
    channel_to_frequency["Q0_resonator"] = 6.1*GHz
    sequence.add_blank_command(["Q0_qubit"], 100)
    sequence.add_pulse("FLATTOP", {"channel": "Q0_qubit"})
    sequence.add_synchronize_all_command()
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_blank_command(["Q0_qubit"], 2048 + 8)
    sequence.add_synchronize_all_command()
    sequence.add_capture_command(["Q0_resonator"])

    sequence_config = sequence.get_config()
    acquisition_config = AcquisitionConfig()
    acquisition_config.flag_average_shots = False
    acquisition_config.flag_average_waveform = True
    job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)

    # convert job to qube_server form, execute it, and convert results
    job_qube_server = translate_job_qube_server(job, translate)
    executor = JobExecutorQubeServer()
    result_qube_server = executor.do_measurement(job_qube_server)
    # result = extract_dataset(job, job_qube_server, translate, result_qube_server)

def example6():
    # test Average shots
    import pprint
    import tunits
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,]
    num_qubit = 16
    executor = JobExecutorQubeServer()
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)
    acquisition_config = AcquisitionConfig()

    # set frequency
    channel_to_frequency["Q0_qubit"] = 4.0*tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6.1*tunits.units.GHz

    # create seqeunce
    sequence.add_blank_command(["Q0_resonator"], 100)
    sequence.add_synchronize_all_command()
    sequence.add_pulse("BLANK", {"channel": "Q0_resonator"})
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    sequence.add_blank_command(["Q0_resonator"], 2500)
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    sequence.add_blank_command(["Q0_resonator"], 2600)
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    sequence.add_blank_command(["Q0_resonator"], 2555)
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    # create seqeunce config
    sequence_config = sequence.get_config()
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_width"] = 500
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.25)

    acquisition_config.flag_average_shots = True
    acquisition_config.flag_average_waveform = False
    acquisition_config.num_shot = 100
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1030 * tunits.units.ns

    plt.figure(figsize=(16,8))
    for job_idx in range(1):
        sequence_config.get_parameter(("Q0",))["BLANK"]["blank_width"] = 300 * job_idx
        job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)
        job_qube_server = translate_job_qube_server(job, translate)

        plt.subplot(1,2,1)
        duration = sequence.get_duration(sequence_config, capture_duration=acquisition_config.acquisition_duration["ns"])
        time_slots = np.arange(0, duration, 2)
        waveform, _ = sequence.get_waveform(time_slots, sequence_config)
        for ch, data in waveform.items():
            plt.plot(time_slots, data, ".-", label=ch)

        result_qube_server = executor.do_measurement(job_qube_server)
        result = extract_dataset(job, job_qube_server, translate, result_qube_server)

        plt.subplot(1,2,2)
        for ch, data in result.items():
            assert(data.ndim==2)
            time_slots = np.arange(data.shape[-1]) * 8
            for capture_point_index, waveform in enumerate(data):
                plt.plot(time_slots, np.real(waveform), ".-", label=ch+f"_{capture_point_index}_I")
                plt.plot(time_slots, np.imag(waveform), ".-", label=ch+f"_{capture_point_index}_Q")
    plt.subplot(1,2,1)
    plt.legend()
    plt.subplot(1,2,2)
    plt.legend()
    plt.tight_layout()
    plt.show()

def example7():
    # test No averaging
    import pprint
    import tunits
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,]
    num_qubit = 16
    executor = JobExecutorQubeServer()
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)
    acquisition_config = AcquisitionConfig()

    # set frequency
    channel_to_frequency["Q0_qubit"] = 4.0*tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6.1*tunits.units.GHz

    # create seqeunce
    sequence.add_blank_command(["Q0_resonator"], 100)
    sequence.add_synchronize_all_command()
    sequence.add_pulse("BLANK", {"channel": "Q0_resonator"})
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    sequence.add_blank_command(["Q0_resonator"], 2500)
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    sequence.add_blank_command(["Q0_resonator"], 2500)
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    sequence.add_blank_command(["Q0_resonator"], 2500)
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    # create seqeunce config
    sequence_config = sequence.get_config()
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_width"] = 500
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.1)

    acquisition_config.flag_average_shots = False
    acquisition_config.flag_average_waveform = False
    acquisition_config.num_shot = 4
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1030 * tunits.units.ns

    plt.figure(figsize=(16,8))
    for job_idx in range(1):
        sequence_config.get_parameter(("Q0",))["BLANK"]["blank_width"] = 300
        job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)
        job_qube_server = translate_job_qube_server(job, translate)

        plt.subplot(1,2,1)
        duration = sequence.get_duration(sequence_config, capture_duration=acquisition_config.acquisition_duration["ns"])
        time_slots = np.arange(0, duration, 2)
        waveform, _ = sequence.get_waveform(time_slots, sequence_config)
        for ch, data in waveform.items():
            plt.plot(time_slots, data, ".-", label=ch)

        result_qube_server = executor.do_measurement(job_qube_server)
        result = extract_dataset(job, job_qube_server, translate, result_qube_server)

        plt.subplot(1,2,2)
        for ch, data in result.items():
            assert(data.ndim==3)
            time_slots = np.arange(data.shape[-1]) * 8
            for capture_point_index, shots_waveform in enumerate(data):
                for shot_index, waveform in enumerate(shots_waveform):
                    plt.plot(time_slots, np.real(waveform), ".-", label=ch+f"_{capture_point_index}_{shot_index}_I")
                    plt.plot(time_slots, np.imag(waveform), ".-", label=ch+f"_{capture_point_index}_{shot_index}_Q")
    plt.legend()
    plt.tight_layout()
    plt.show()


def example8():
    # test No averaging
    import pprint
    import tunits
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,]
    num_qubit = 16
    executor = JobExecutorQubeServer()
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)
    acquisition_config = AcquisitionConfig()

    # set frequency
    channel_to_frequency["Q0_qubit"] = 4.0*tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6.0*tunits.units.GHz # + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq

    # create seqeunce
    sequence.add_blank_command(["Q0_resonator"], 100)
    sequence.add_synchronize_all_command()
    sequence.add_pulse("BLANK", {"channel": "Q0_resonator"})
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    num_window = 3

    for _ in range(num_window-1):
        sequence.add_blank_command(["Q0_resonator"], 2500)
        sequence.add_capture_command(["Q0_resonator"])
        sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
        sequence.add_synchronize_all_command()


    # create seqeunce config
    sequence_config = sequence.get_config()
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_width"] = 500
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.1)

    acquisition_config.flag_average_shots = False
    acquisition_config.flag_average_waveform = True
    acquisition_config.num_shot = 100
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1030 * tunits.units.ns

    plt.figure(figsize=(16,8))
    num_job = 6
    for job_idx in range(num_job):
        sequence_config.get_parameter(("Q0",))["BLANK"]["blank_width"] = 300
        sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01) + (2*np.pi/num_job) * job_idx
        job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)
        job_qube_server = translate_job_qube_server(job, translate)

        result_qube_server = executor.do_measurement(job_qube_server)
        result = extract_dataset(job, job_qube_server, translate, result_qube_server)
        for ch, data in result.items():
            assert(data.ndim==2)
            for capture_point_index, shots in enumerate(data):
                # plt.subplot(num_window,num_job,job_idx+capture_point_index*num_job+1)
                plt.subplot(num_window,1,capture_point_index+1)
                plt.xlim(-1e11, 1e11)
                plt.ylim(-1e11, 1e11)
                plt.grid()
                plt.scatter(np.real(shots), np.imag(shots), label=f"job{job_idx}"+ch+f"_{capture_point_index}")
    plt.tight_layout()
    plt.show()



def example9():
    # test No averaging
    import pprint
    import tunits
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,]
    num_qubit = 16
    executor = JobExecutorQubeServer()
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)
    acquisition_config = AcquisitionConfig()

    # set frequency
    channel_to_frequency["Q0_qubit"] = 4.0*tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.2*tunits.units.GHz

    # create seqeunce
    sequence.add_blank_command(["Q0_resonator"], 100)
    sequence.add_synchronize_all_command()
    sequence.add_pulse("BLANK", {"channel": "Q0_resonator"})
    sequence.add_capture_command(["Q0_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_synchronize_all_command()

    num_window = 3

    for _ in range(num_window-1):
        sequence.add_blank_command(["Q0_resonator"], 2500)
        sequence.add_capture_command(["Q0_resonator"])
        sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
        sequence.add_synchronize_all_command()


    # create seqeunce config
    sequence_config = sequence.get_config()
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_width"] = 500
    sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.1)

    acquisition_config.flag_average_shots = True
    acquisition_config.flag_average_waveform = True
    acquisition_config.num_shot = 100
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1030 * tunits.units.ns

    plt.figure(figsize=(4,9))
    num_job = 5
    for job_idx in range(num_job):
        sequence_config.get_parameter(("Q0",))["BLANK"]["blank_width"] = 300
        # channel_to_frequency_shift["Q0_resonator"] = 0.001*tunits.units.GHz/num_job * job_idx
        # channel_to_frequency_shift["Q0_resonator"] = 0.0001*tunits.units.GHz/num_job
        sequence_config.get_parameter(("Q0",))["FLATTOP"]["flattop_phase"] = np.pi * (0.44) + (2*np.pi/num_job) * job_idx
        job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)
        job_qube_server = translate_job_qube_server(job, translate)

        result_qube_server = executor.do_measurement(job_qube_server)
        result = extract_dataset(job, job_qube_server, translate, result_qube_server)
        for ch, data in result.items():
            assert(data.ndim==1)
            for capture_point_index, value in enumerate(data):
                # plt.subplot(num_window,num_job,job_idx+capture_point_index*num_job+1)
                plt.subplot(num_window,1,capture_point_index+1)
                plt.xlim(-1e11, 1e11)
                plt.ylim(-1e11, 1e11)
                plt.grid()
                plt.scatter(np.real(value), np.imag(value), label=f"job{job_idx}"+ch+f"_{capture_point_index}")
    plt.tight_layout()
    plt.show()



def example10():
    # test No averaging
    import pprint
    import tunits
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,1,2,3]
    num_qubit = 16
    executor = JobExecutorQubeServer()
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)
    acquisition_config = AcquisitionConfig()

    # set frequency
    channel_to_frequency["Q0_qubit"] = 4.0*tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.2*tunits.units.GHz
    channel_to_frequency["Q1_qubit"] = 4.1*tunits.units.GHz
    channel_to_frequency["Q1_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.3*tunits.units.GHz
    channel_to_frequency["Q2_qubit"] = 4.2*tunits.units.GHz
    channel_to_frequency["Q2_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.4*tunits.units.GHz
    channel_to_frequency["Q3_qubit"] = 4.3*tunits.units.GHz
    channel_to_frequency["Q3_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.35*tunits.units.GHz

    # create seqeunce
    sequence.add_blank_command(["Q0_resonator"], 100)
    sequence.add_synchronize_all_command()
    sequence.add_pulse("BLANK", {"channel": "Q0_resonator"})
    sequence.add_capture_command(["Q0_resonator", "Q1_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_pulse("FLATTOP", {"channel": "Q1_resonator"})
    sequence.add_synchronize_all_command()

    num_window = 3

    for _ in range(num_window-1):
        sequence.add_blank_command(["Q0_resonator"], 2500)
        sequence.add_capture_command(["Q0_resonator", "Q1_resonator", "Q2_resonator", "Q3_resonator"])
        sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
        sequence.add_pulse("FLATTOP", {"channel": "Q1_resonator"})
        sequence.add_pulse("FLATTOP", {"channel": "Q2_resonator"})
        sequence.add_pulse("FLATTOP", {"channel": "Q3_resonator"})
        sequence.add_synchronize_all_command()


    # create seqeunce config
    sequence_config = sequence.get_config()
    for q in range(4):
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_width"] = 500
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_amplitude"] = 0.24
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.1)

    acquisition_config.flag_average_shots = True
    acquisition_config.flag_average_waveform = True
    acquisition_config.num_shot = 100
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1030 * tunits.units.ns

    plt.figure(figsize=(4,9))
    num_job = 2
    for job_idx in range(num_job):
        for q in range(4):
            sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_phase"] = np.pi * (0.44) + (2*np.pi/num_job) * job_idx
        job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)
        job_qube_server = translate_job_qube_server(job, translate)

        result_qube_server = executor.do_measurement(job_qube_server)
        result = extract_dataset(job, job_qube_server, translate, result_qube_server)
        for ch, data in result.items():
            assert(data.ndim==1)
            for capture_point_index, value in enumerate(data):
                # plt.subplot(num_window,num_job,job_idx+capture_point_index*num_job+1)
                plt.subplot(num_window,1,capture_point_index+1)
                plt.xlim(-1e10, 1e10)
                plt.ylim(-1e10, 1e10)
                plt.grid()
                plt.scatter(np.real(value), np.imag(value), label=f"job{job_idx}_"+ch+f"_w{capture_point_index}")
                plt.legend()
    plt.tight_layout()
    plt.show()

def example11():
    # test No averaging
    import pprint
    import tunits
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_quel_meas.meas_2Q import create_2Q_objects
    from mt_quel_meas.job import Job, AcquisitionConfig
    from mt_quel_meas.qubeserver.translate import translate_job_qube_server
    from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer
    from mt_quel_meas.qubeserver.extract import extract_dataset
    from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
    
    target_qubit_list = [0,1,4,5]
    num_qubit = 16
    executor = JobExecutorQubeServer()
    sequence,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, translate = create_2Q_objects(num_qubit, target_qubit_list, wiring_dict_16Q, CONST_QuEL1SE_LOW_FREQ)
    acquisition_config = AcquisitionConfig()

    # set frequency
    channel_to_frequency["Q0_qubit"] = 4.0*tunits.units.GHz
    channel_to_frequency["Q0_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.2*tunits.units.GHz
    channel_to_frequency["Q1_qubit"] = 4.1*tunits.units.GHz
    channel_to_frequency["Q1_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.3*tunits.units.GHz
    channel_to_frequency["Q4_qubit"] = 4.2*tunits.units.GHz
    channel_to_frequency["Q4_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.4*tunits.units.GHz
    channel_to_frequency["Q5_qubit"] = 4.3*tunits.units.GHz
    channel_to_frequency["Q5_resonator"] = 6.0*tunits.units.GHz + CONST_QuEL1SE_LOW_FREQ.NCO_step_freq + 0.35*tunits.units.GHz

    # create seqeunce
    sequence.add_blank_command(["Q0_resonator"], 100)
    sequence.add_synchronize_all_command()
    sequence.add_pulse("BLANK", {"channel": "Q0_resonator"})
    sequence.add_capture_command(["Q0_resonator", "Q1_resonator"])
    sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
    sequence.add_pulse("FLATTOP", {"channel": "Q1_resonator"})
    sequence.add_synchronize_all_command()

    num_window = 3

    for _ in range(num_window-1):
        sequence.add_blank_command(["Q0_resonator"], 2500)
        sequence.add_capture_command(["Q0_resonator", "Q1_resonator", "Q4_resonator", "Q5_resonator"])
        sequence.add_pulse("FLATTOP", {"channel": "Q0_resonator"})
        sequence.add_pulse("FLATTOP", {"channel": "Q1_resonator"})
        sequence.add_pulse("FLATTOP", {"channel": "Q4_resonator"})
        sequence.add_pulse("FLATTOP", {"channel": "Q5_resonator"})
        sequence.add_synchronize_all_command()


    # create seqeunce config
    sequence_config = sequence.get_config()
    for q in target_qubit_list:
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_width"] = 500
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_amplitude"] = 0.24
        sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_phase"] = np.pi * (1.01 + 0.1)

    acquisition_config.flag_average_shots = True
    acquisition_config.flag_average_waveform = True
    acquisition_config.num_shot = 100
    acquisition_config.acquisition_timeout = 3 * tunits.units.s
    acquisition_config.acquisition_delay = 1030 * tunits.units.ns

    plt.figure(figsize=(4,9))
    num_job = 2
    for job_idx in range(num_job):
        for q in target_qubit_list:
            sequence_config.get_parameter((f"Q{q}",))["FLATTOP"]["flattop_phase"] = np.pi * (0.44) + (2*np.pi/num_job) * job_idx
        job = Job(sequence, sequence_config,  channel_to_frequency, channel_to_frequency_shift, channel_to_averaging_window, acquisition_config)
        job_qube_server = translate_job_qube_server(job, translate)

        result_qube_server = executor.do_measurement(job_qube_server)
        result = extract_dataset(job, job_qube_server, translate, result_qube_server)
        for ch, data in result.items():
            assert(data.ndim==1)
            for capture_point_index, value in enumerate(data):
                plt.subplot(num_window,1,capture_point_index+1)
                plt.xlim(-1e10, 1e10)
                plt.ylim(-1e10, 1e10)
                plt.grid()
                plt.scatter(np.real(value), np.imag(value), label=f"job{job_idx}_"+ch+f"_w{capture_point_index}")
                plt.legend()
    plt.tight_layout()
    plt.show()


# example1()
# example2()
# example3()
# example4()
# example5()
# example6() # average shots
# example7() # no average
# example8() # average waveform
# example9() # both average
# example10() # mux
example11() # mux with dif unit










