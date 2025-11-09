from typing import Literal

_separator_device_port_index_readout = "-readout_"
_separator_device_port_index_control = "-control_"
_separator_device_port_index_pump = "-pump_"

def _boxport_name(device_name: str, port_index: int, port_type: Literal["Unused", "ReadIn", "ReadOut", "Pump", "Control"]) -> str:
    if port_type in ["ReadOut", "ReadIn"]:
        return f"{device_name}{_separator_device_port_index_readout}{port_index}"
    elif port_type in ["Pump"]:
        return f"{device_name}{_separator_device_port_index_pump}{port_index}"
    elif port_type in ["Control"]:
        return f"{device_name}{_separator_device_port_index_control}{port_index}"
    else:
        raise ValueError(f"Unexpected qube device specified: {device_name, port_index}")

def _boxport_to_device_and_port_index(boxport: str) -> tuple[str, int]:
    separator_list = [_separator_device_port_index_readout, _separator_device_port_index_pump, _separator_device_port_index_pump]
    for separator in separator_list:
        if separator in boxport:
            device_name, port_index_str = boxport.split(_separator_device_port_index_control)
            port_index = int(port_index_str)
            return device_name, port_index
    raise ValueError(f"cannot convert {boxport} to device and str")


_separator_boxport_awg = "-AWG_"
_separator_boxport_capture = "-Capture_"

def _awg_channel_name(device_name: str, port_index: int, port_type: Literal["Unused", "ReadIn", "ReadOut", "Pump", "Control"], awg_channel: int) -> str:
    return f"{_boxport_name(device_name, port_index, port_type)}{_separator_boxport_awg}{awg_channel}"

def _capture_channel_name(device_name: str, port_index: int, port_type: Literal["Unused", "ReadIn", "ReadOut", "Pump", "Control"], capture_channel: int) -> str:
    return f"{_boxport_name(device_name, port_index, port_type)}{_separator_boxport_capture}{capture_channel}"

def _awg_channel_to_boxport(awg_channel: str) -> str:
    assert(_separator_boxport_awg in awg_channel)
    return awg_channel.split(_separator_boxport_awg)[0]

def _capture_channel_to_boxport(capture_channel: str) -> str:
    assert(_separator_boxport_capture in capture_channel)
    return capture_channel.split(_separator_boxport_capture)[0]
