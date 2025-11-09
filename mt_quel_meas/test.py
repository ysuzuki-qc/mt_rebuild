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

# example1()
# example2()
# example3()
# example4()
example5()





