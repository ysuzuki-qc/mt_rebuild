import sys
path_list = ["./mt_circuit/", "./mt_note/", "./mt_pulse/" , "./mt_util/", "./mt_quel_util/", "./mt_quel_meas/"]
for path in path_list:
    sys.path.append(path)
    sys.path.append("../"+path)


import numpy as np
from tunits.units import MHz, GHz
from mt_quel_util.mux_assignment import get_multiplex_config
from mt_quel_util.constant import CONST_QuEL1SE_LOW_FREQ
from mt_util.tunits_util import JSON_TypedUnitsEncoder
from mt_quel_util.mux_print import print_mux_config

def pos_to_index_16Q(x: int, y: int) -> int:
    qubit_per_mux = 4
    mux_width = 2
    mx, my = x//2, y//2,
    mq = x%2 + (y%2)*2
    return qubit_per_mux * (mux_width * my + mx) + mq

def index_to_pos_16Q(index: int) -> tuple[int, int]:
    mux = index//4
    mq = index%4
    mx, my = mux%2, mux//2
    x = mx*2 + mq%2
    y = my*2 + mq//2
    return x,y

def create_channel_to_frequency_16Q(freq_Q: list, freq_R: list) -> dict:
    channel_to_frequency = {}
    for index in range(16):
        channel_to_frequency[f"{index}_resonator"] = freq_R[index]
        channel_to_frequency[f"{index}_qubit"] = freq_Q[index]
        if index%4 in [1,2]:
            x,y = index_to_pos_16Q(index)
            if x > 0:
                tgt = pos_to_index_16Q(x-1, y)
                channel_to_frequency[f"{index}_CR_L"] = freq_Q[tgt]
            if x < 3:
                tgt = pos_to_index_16Q(x+1, y)
                channel_to_frequency[f"{index}_CR_R"] = freq_Q[tgt]
            if y > 0:
                tgt = pos_to_index_16Q(x, y-1)
                channel_to_frequency[f"{index}_CR_U"] = freq_Q[tgt]
            if y < 3:
                tgt = pos_to_index_16Q(x, y+1)
                channel_to_frequency[f"{index}_CR_D"] = freq_Q[tgt]
    return channel_to_frequency

def create_channel_to_device_16Q(channel_list: list[str]) -> dict[str, str]:
    channel_to_device = {}
    for channel in channel_list:
        qubit_index = int(channel.split("_")[0])
        channel_to_device[channel] = f"quel_{qubit_index//4}"
    return channel_to_device

def create_channel_to_port_index_16Q(channel_list: list[str]) -> dict[str, int]:
    channel_to_port = {}
    for channel in channel_list:
        qubit_index = int(channel.split("_")[0])
        channel_name = channel.split("_")[1]
        if channel_name == "resonator":
            channel_to_port[channel] = 1
        else:
            channel_to_port[channel] = 6 + qubit_index%4
    return channel_to_port


def example2():
    freq_Q = [3.87, 4.40, 4.46, 3.68,
            3.89, 4.47, 4.50, 3.83,
            3.82, 4.37, 4.24, 3.76,
            3.88, 4.54, 4.80, 4.01]
    freq_R = [6.16, 6.43, 6.32, 6.03,
            6.22, 6.49, 6.36, 6.08,
            6.15, 6.43, 6.30, 6.03,
            6.20, 6.48, 6.36, 6.09]
    freq_Q = np.array(freq_Q) * GHz
    freq_R = np.array(freq_R) * GHz

    channel_to_frequency = create_channel_to_frequency_16Q(freq_Q, freq_R)
    channel_to_device = create_channel_to_device_16Q(channel_to_frequency.keys())
    channel_to_port_index = create_channel_to_port_index_16Q(channel_to_frequency.keys())

    result = get_multiplex_config(channel_to_frequency, channel_to_device, channel_to_port_index, CONST_QuEL1SE_LOW_FREQ)
    print_mux_config(channel_to_frequency, channel_to_device, channel_to_port_index, CONST_QuEL1SE_LOW_FREQ, result)


def example1():
    channel_to_frequency = {
        "0_qubit": 4*GHz,
        "0_resonator": 6.1*GHz,
        "1_qubit": 4.2*GHz,
        "1_resonator": 6.2*GHz,
        "1_CR1": 4.0*GHz,
        "1_CR2": 4.4*GHz,
        "2_qubit": 4.4*GHz,
        "2_resonator": 6.3*GHz,
    }
    channel_to_device = {
        "0_qubit": "dev",
        "0_resonator": "dev",
        "1_qubit": "dev",
        "1_resonator": "dev",
        "1_CR1": "dev",
        "1_CR2": "dev",
        "2_qubit": "dev",
        "2_resonator": "dev",
    }
    channel_to_port_index = {
        "0_qubit": 6,
        "0_resonator": 1,
        "1_qubit": 7,
        "1_resonator": 1,
        "1_CR1": 7,
        "1_CR2": 7,
        "2_qubit": 8,
        "2_resonator": 1,
    }
    result = get_multiplex_config(channel_to_frequency, channel_to_device, channel_to_port_index, CONST_QuEL1SE_LOW_FREQ)
    print_mux_config(channel_to_frequency, channel_to_device, channel_to_port_index, CONST_QuEL1SE_LOW_FREQ, result)

# example1()
example2()

