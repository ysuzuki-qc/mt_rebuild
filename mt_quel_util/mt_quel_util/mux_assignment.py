from typing import Literal, Any
import numpy as np
from tunits.units import GHz
import pydantic
from mt_util.tunits_util import FrequencyType
from mt_quel_util.constant import InstrumentConstantQuEL
from mt_quel_util.mux_frequency_grouping import get_frequency_group

class MultiplexingResult(pydantic.BaseModel):
    channel_to_dac_index: dict[str, int]
    channel_to_residual_frequency: dict[str, FrequencyType] 
    channel_to_pulse_bandwidth: dict[str, FrequencyType] 
    CNCO_setting: dict[str, dict[int, FrequencyType]]
    FNCO_setting: dict[str, dict[int, dict[int, FrequencyType]]]
    def to_json_dict(self) -> dict[str, Any]:
        return self.model_dump()

class PortMultiplexing(pydantic.BaseModel):
    channel_to_dac: dict[str, int]
    channel_to_residual_frequency: dict[str, FrequencyType] 
    channel_to_pulse_bandwidth: dict[str, FrequencyType]
    CNCO_frequency: FrequencyType
    FNCO_frequency_dict: dict[int, FrequencyType]


@pydantic.validate_call
def get_multiplex_config(channel_to_frequency: dict[str, FrequencyType], channel_to_quel_name: dict[str, str], channel_to_port_index: dict[str, int], constant: InstrumentConstantQuEL) -> MultiplexingResult:
    channel_list = list(channel_to_frequency)
    port_channel_list: dict[tuple[str, int], list[str]] = {}
    for channel in channel_list:
        quel_name = channel_to_quel_name[channel]
        port_index = channel_to_port_index[channel]
        key = (quel_name, port_index)
        if key not in port_channel_list:
            port_channel_list[key] = [channel]
        else:
            port_channel_list[key].append(channel)

    channel_to_dac_index: dict[str, int] = {}
    channel_to_residual_frequency: dict[str, FrequencyType] = {}
    channel_to_pulse_bandwidth: dict[str, FrequencyType] = {}
    CNCO_setting: dict[str, dict[int, FrequencyType]] = {}
    FNCO_setting: dict[str, dict[int, dict[int, FrequencyType]]] = {}

    for port_key, channel_list in port_channel_list.items():
        quel_name, port_index = port_key
        # gather channels multiplexed to a single physical port
        port_channel_to_frequency: dict[str, FrequencyType] = {}
        for channel in channel_list:
            port_channel_to_frequency[channel] = channel_to_frequency[channel]

        # pick values for multiplexing
        port_type = constant.port_type[port_index]
        NCO_step_freq = constant.NCO_step_freq
        num_dac_channel = constant.num_dac_channel[port_index]
        if port_type == "ReadOut":
            LO_freq = constant.LO_freq_resonator
            LO_sideband = constant.LO_sideband_resonator
        elif port_type == "Control":
            LO_freq = constant.LO_freq_qubit
            LO_sideband = constant.LO_sideband_qubit
        elif port_type == "Pump":
            LO_freq = constant.LO_freq_jpa
            LO_sideband = constant.LO_sideband_jpa
        else:
            raise ValueError(f"port type {port_type} is not supported")
        if LO_sideband == "Direct" and (LO_freq != 0*GHz):
            raise ValueError(f"{port_key} use no LO but LO frequency is set as non-zero value {LO_freq}")
        port_mux_info = multiplex_port(port_channel_to_frequency, LO_freq, NCO_step_freq, num_dac_channel, LO_sideband, constant)

        # extract values
        for channel, residual_frequency in port_mux_info.channel_to_residual_frequency.items():
            channel_to_residual_frequency[channel] = residual_frequency

        for channel, dac_index in port_mux_info.channel_to_dac.items():
            channel_to_dac_index[channel] = dac_index

        for channel, bandwidth in port_mux_info.channel_to_pulse_bandwidth.items():
            channel_to_pulse_bandwidth[channel] = bandwidth

        if quel_name not in CNCO_setting:
            CNCO_setting[quel_name] = {}
        CNCO_setting[quel_name][port_index] = port_mux_info.CNCO_frequency

        if quel_name not in FNCO_setting:
            FNCO_setting[quel_name] = {}
        FNCO_setting[quel_name][port_index] = port_mux_info.FNCO_frequency_dict
        
    return MultiplexingResult(channel_to_dac_index=channel_to_dac_index, channel_to_residual_frequency=channel_to_residual_frequency,channel_to_pulse_bandwidth=channel_to_pulse_bandwidth,  CNCO_setting=CNCO_setting, FNCO_setting=FNCO_setting)

@pydantic.validate_call
def approximate_frequency_by_step(freq: FrequencyType, step: FrequencyType) -> tuple[FrequencyType, FrequencyType]:
    step_div: float = (freq/step)[""]
    freq_approx = np.round(step_div) * step
    freq_residual = freq - freq_approx
    return freq_approx, freq_residual

@pydantic.validate_call
def get_residual_frequency(freq_LO: FrequencyType, freq_CNCO: FrequencyType, freq_FNCO: FrequencyType, freq_target: FrequencyType, sideband: Literal["USB", "LSB", "Direct"]) -> FrequencyType:
    if sideband == "USB" or sideband=="Direct":
        # f_LO + (f_RES + f_FNCO + f_CNCO) = f_target
        return freq_target - freq_LO - freq_CNCO - freq_FNCO
    elif sideband == "LSB":
        # f_LO - (f_RES + f_FNCO + f_CNCO) = f_target
        return freq_LO - freq_CNCO - freq_FNCO - freq_target

@pydantic.validate_call
def multiplex_port(channel_to_freq: dict[str, FrequencyType], freq_LO: FrequencyType, freq_NCO_step: FrequencyType, num_dac_channel: int, sideband: Literal["USB", "LSB", "Direct"], constant: InstrumentConstantQuEL) -> PortMultiplexing:
    freq_mean: FrequencyType = np.mean(list(channel_to_freq.values())) # type: ignore
    freq_CNCO, _ = approximate_frequency_by_step(get_residual_frequency(freq_LO, 0*GHz, 0*GHz, freq_mean, sideband), freq_NCO_step)
    channel_to_dac = get_frequency_group(channel_to_freq, freq_NCO_step/4, num_dac_channel)
    freq_FNCO_dict: dict[int, FrequencyType] = {}
    channel_to_residual_freq: dict[str, FrequencyType] = {}
    channel_to_pulse_bandwidth: dict[str, FrequencyType] = {}
    for dac_index in range(num_dac_channel):
        target_channel_list = [channel for channel, dac in channel_to_dac.items() if dac==dac_index]
        if len(target_channel_list) == 0:
            continue
        target_frequency_list = [channel_to_freq[channel] for channel in target_channel_list]
        freq_dac_mean: FrequencyType = np.mean(target_frequency_list) # type: ignore
        freq_FNCO, _ = approximate_frequency_by_step(get_residual_frequency(freq_LO, freq_CNCO, 0*GHz, freq_dac_mean, sideband), freq_NCO_step)
        freq_FNCO_dict[dac_index] = freq_FNCO
        for channel in target_channel_list:
            freq_RES = get_residual_frequency(freq_LO, freq_CNCO, freq_FNCO, channel_to_freq[channel], sideband)
            channel_to_residual_freq[channel] = freq_RES

            DAC_BW = constant.DAC_bandwidth_effective
            NCO_BW = constant.NCO_bandwidth_effective
            pulse_BW_DAC = (DAC_BW/2 - abs(freq_RES))*2
            pulse_BW_NCO = (NCO_BW/2 - np.abs(freq_FNCO + freq_RES))*2
            pulse_BW = np.min([pulse_BW_DAC, pulse_BW_NCO])
            channel_to_pulse_bandwidth[channel] = pulse_BW

    return PortMultiplexing(channel_to_dac=channel_to_dac, channel_to_residual_frequency=channel_to_residual_freq, channel_to_pulse_bandwidth=channel_to_pulse_bandwidth, CNCO_frequency=freq_CNCO, FNCO_frequency_dict=freq_FNCO_dict)



