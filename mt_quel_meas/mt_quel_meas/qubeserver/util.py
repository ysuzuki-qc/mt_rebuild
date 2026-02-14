from typing import Literal

_separator_device_port_index_readout = "-readout_"
_separator_device_port_index_control = "-control_"
_separator_device_port_index_pump = "-pump_"


def _boxport_name(
    box_name: str, port_index: int, wiring_dict: dict
) -> str:
    for type in wiring_dict:
        for component in wiring_dict[type]:
            if box_name == wiring_dict[type][component]["box_name"] and port_index == wiring_dict[type][component]["port_index"]:
                return wiring_dict[type][component]["boxport_name"]
    raise ValueError(f"Unexpected qube device specified: {device_name, port_index}")


def _boxport_to_device_and_port_index(boxport: str) -> tuple[str, int]:
    separator_list = [
        _separator_device_port_index_readout,
        _separator_device_port_index_pump,
        _separator_device_port_index_pump,
    ]
    for separator in separator_list:
        if separator in boxport:
            device_name, port_index_str = boxport.split(_separator_device_port_index_control)
            port_index = int(port_index_str)
            return device_name, port_index
    raise ValueError(f"cannot convert {boxport} to device and str")


def _boxport_to_port_type(boxport: str) -> Literal["Unused", "ReadIn", "ReadOut", "Pump", "Control"]:
    if _separator_device_port_index_readout in boxport:
        return "ReadOut"
    elif _separator_device_port_index_control in boxport:
        return "Control"
    elif _separator_device_port_index_pump in boxport:
        return "Pump"
    raise ValueError(f"cannot convert {boxport} to port type")


_separator_boxport_awg = "-AWG_"
_separator_boxport_capture = "-Capture_"


def _awg_channel_name(
    device_name: str,
    port_index: int,
    port_type: Literal["Unused", "ReadIn", "ReadOut", "Pump", "Control"],
    awg_channel: int,
) -> str:
    return f"Name_{device_name}__Type_{port_type}__Port_{port_index}__AWG_{awg_channel}"


def _capture_channel_name(
    device_name: str,
    port_index: int,
    port_type: Literal["Unused", "ReadIn", "ReadOut", "Pump", "Control"],
    capture_channel: int,
) -> str:
    return f"Name_{device_name}__Type_{port_type}__Port_{port_index}__CAP_{capture_channel}"
