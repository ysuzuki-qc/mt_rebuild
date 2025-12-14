from typing import Iterable, Any
import numpy as np
import tqdm
import tunits
from mt_quel_meas.job import Job, AssignmentQuel
from mt_quel_meas.qubeserver.translate import translate_job_qube_server
from mt_quel_meas.qubeserver.extract import extract_dataset
from mt_quel_meas.qubeserver.execute import JobExecutorQubeServer


def execute(job: Job, assignment_quel: AssignmentQuel) -> dict[str, np.ndarray]:
    # start executor
    executor = JobExecutorQubeServer()

    # bind job to qube server
    job_qube_server = translate_job_qube_server(job, assignment_quel)

    # do measurement
    result_qube_server = executor.do_measurement(job_qube_server)

    # extract data by binding information
    result = extract_dataset(job, job_qube_server, assignment_quel, result_qube_server)

    return result


def extract_sweep_dims(sweep_parameter: list[dict[str, Iterable]]):
    num_axis = len(sweep_parameter)
    axis_dims: list[int] = [
        -1,
    ] * num_axis
    for axis_index, axis_dict in enumerate(sweep_parameter):
        if len(axis_dict) == 0:
            raise ValueError(f"Sweep axis {axis_dict} has empty parameter. Each axis must have at least one parameter")
        for axis_param in axis_dict.values():
            if axis_dims[axis_index] == -1:
                axis_dims[axis_index] = len(axis_param)
            else:
                if axis_dims[axis_index] != len(axis_param):
                    raise ValueError(
                        f"Sweep axis {axis_index}: {axis_dict} has different dimensions."
                        "Iterable parameter must have the same dimension."
                    )
    return axis_dims


def get_sweep_state(index: int, sweep_dims: list[int]) -> list[int]:
    result: list[int] = []
    for dim in sweep_dims:
        result.append(index % dim)
        index //= dim
    return result


def get_update_parameter_list(
    sweep_parameter: list[dict[str, Iterable]], sweep_state: list[int], last_sweep_state: list[int]
) -> dict[str, Any]:
    assert len(sweep_state) == len(last_sweep_state)
    result: dict[str, Any] = {}
    for axis_index in range(len(sweep_state)):
        index = sweep_state[axis_index]
        last_index = last_sweep_state[axis_index]
        if index == last_index:
            continue
        for name, values in sweep_parameter[axis_index].items():
            result[name] = values[index]
    return result


def process_update(name: str, value: Any, job: Job) -> None:
    elements = name.split(".")
    assert len(elements) >= 2
    category = elements[0]
    handle = elements[1:]
    if category == "frequency_shift":
        assert len(handle) == 1
        channel = handle[0]
        if channel not in job.sequence_channel_to_frequency_shift:
            raise ValueError(f"Channel for {channel} in parameter {name} not found")
        job.sequence_channel_to_frequency_shift[handle[0]] = value
    elif category == "sequencer":
        assert len(handle) == 3
        group, pulse, param_name = handle
        group_tuple = tuple(group.split("_"))
        job.sequence_config.get_parameter(group_tuple)[pulse][param_name] = value
    else:
        raise ValueError(f"Unknown parameter category {category}")


def execute_sweep(
    job: Job, assignment_quel: AssignmentQuel, sweep_parameter: list[dict[str, Iterable]], verbose: bool = True
) -> dict[str, np.ndarray]:
    # start executor
    executor = JobExecutorQubeServer()

    # get sweep dims
    sweep_dims = extract_sweep_dims(sweep_parameter)
    total_iteration = 1
    for dim in sweep_dims:
        total_iteration *= dim

    last_sweep_state = [
        -1,
    ] * len(sweep_dims)
    result_dict_list: dict[str, list[np.ndarray]] = {}
    with tqdm.tqdm(range(total_iteration), disable=(not verbose)) as progress_bar:
        for index in progress_bar:
            # update sweep state and get parameters to update
            sweep_state = get_sweep_state(index, sweep_dims)
            update_parameter_dict = get_update_parameter_list(sweep_parameter, sweep_state, last_sweep_state)
            last_sweep_state = sweep_state

            # update progress bar
            if len(sweep_dims) == 1:
                message: str = ""
                for value in update_parameter_dict.values():
                    if isinstance(value, tunits.Value):
                        message += f"{value.value} {value.units} "
                    else:
                        message += f"{value} "
                message = message.strip()
                progress_bar.set_postfix_str(message)
            else:
                message = ""
                for val, dim in zip(sweep_state, sweep_dims):
                    message += f"{val+1}/{dim} "
                message = message.strip()
                progress_bar.set_postfix_str(message)

            # update parameters in job
            for name, value in update_parameter_dict.items():
                process_update(name, value, job)

            # bind job to qube server
            job_qube_server = translate_job_qube_server(job, assignment_quel)

            # do measurement
            result_qube_server = executor.do_measurement(job_qube_server)

            # extract data by binding information
            result = extract_dataset(job, job_qube_server, assignment_quel, result_qube_server)
            for key, matrix in result.items():
                if key not in result_dict_list:
                    result_dict_list[key] = []
                result_dict_list[key].append(matrix)

    result_dict: dict[str, np.ndarray] = {}
    for key, matrix_list in result_dict_list.items():
        shape = sweep_dims + list(matrix_list[0].shape)
        result_dict[key] = np.reshape(matrix_list, shape=shape)

    return result_dict
