from __future__ import annotations
from typing import Any
from dataclasses import field, dataclass, asdict
import numpy as np
from mt_pulse.pulse_library import PulseLibrary

_SYNC_COMMAND_ = "__SYNC__"
_CAPT_COMMAND_ = "__CAPT__"

@dataclass(frozen=True, slots=True)
class SequenceCommand:
    name: str
    pulse_channel_to_sequence_channel: dict[str, str] = field(default_factory=dict)
    channel_list: list[str] = field(default_factory=list)
    blank_time: float = 0.

@dataclass(frozen=True, slots=True)
class SequenceConfig:
    _raw_config_list: list[dict[str, Any]]
    _group_to_index: dict[tuple[str,...], int] = field(default_factory=dict)
    def __post_init__(self):
        for idx, item in enumerate(self._raw_config_list):
            key = tuple(sorted(item["group"]))
            self._group_to_index[key] = idx

    def to_json_dict(self) -> list[dict[str, Any]]:
        return self._raw_config_list
    
    @staticmethod
    def from_json_dict(raw_config_list: list[dict[str, Any]]) -> SequenceConfig:
        sequence = SequenceConfig(raw_config_list)
        return sequence

    def get_parameter_group_list(self) -> list[tuple[str,...]]:
        return list(self._group_to_index.keys())

    def get_parameter(self, group_key: tuple[str, ...]) -> Any:
        key = tuple(sorted(group_key))
        idx = self._group_to_index[key]
        return self._raw_config_list[idx]["parameter"]

@dataclass(frozen=True, slots=True)
class Sequence:
    pulse_library: PulseLibrary
    _channel_list: list[str] = field(default_factory=list)
    _channel_to_group: dict[str, str] = field(default_factory=dict)
    _command_list: list[SequenceCommand] = field(default_factory=list)

    def __post_init__(self) -> None:
        special_command_list = [_SYNC_COMMAND_, _CAPT_COMMAND_]
        for special_command in special_command_list:
            if special_command in self.pulse_library._pulse_dict:
                raise ValueError(f"pulse name {special_command} is registered and cannot be used")

    def to_json_dict(self) -> dict:
        data: dict = {}
        data["pulse_library"] = self.pulse_library.to_json_dict()
        data["_channel_list"] = self._channel_list
        data["_channel_to_group"] = self._channel_to_group
        data["_command_list"] = [asdict(d) for d in self._command_list]
        return data
    
    @staticmethod
    def from_json_dict(data: dict) -> Sequence:
        pulse_lib = PulseLibrary.from_json_dict(data["pulse_library"])
        command_list = [SequenceCommand(**s) for s in data["_command_list"]]
        sequence = Sequence(pulse_lib, _channel_list=data["_channel_list"], _channel_to_group=data["_channel_to_group"], _command_list=command_list)
        return sequence

    def add_channel(self, channel: str, channel_group: str = "_default_") -> None:
        if channel in self._channel_list:
            raise ValueError(f"channel {channel} already exists")
        self._channel_list.append(channel)
        self._channel_to_group[channel] = channel_group

    def _validate_channel_exists(self, channel_list: list[str]) -> None:
        for channel in channel_list:
            if channel not in self._channel_list:
                raise ValueError(f"channel {channel} not found in channel list {self._channel_list}")

    def _validate_pulse_channel_match(self, pulse_name: str, pulse_channel_list: list[str]) -> None:
        pulse_channel_set_required = set(self.pulse_library.get_channel_list(pulse_name))
        pulse_channel_set_provided = set(pulse_channel_list)
        if len(pulse_channel_set_required - pulse_channel_set_provided) > 0:
            raise ValueError(f"pulse channel {pulse_channel_set_required - pulse_channel_set_provided} is required but not provided")
        if len(pulse_channel_set_provided - pulse_channel_set_required) > 0:
            raise ValueError(f"pulse channel {pulse_channel_set_provided - pulse_channel_set_required} not found in list")

    def add_pulse(self, pulse_name: str, pulse_channel_to_sequence_channel: dict[str, str]) -> None:
        # check sequence in list
        if pulse_name not in self.pulse_library.get_pulse_name_list():
            raise ValueError(f"sequence {pulse_name} not found in sequence library list {self.pulse_library.get_pulse_name_list()}")
        
        # check sequence channels are mapped to qubit channels
        self._validate_pulse_channel_match(pulse_name, list(pulse_channel_to_sequence_channel.keys()))

        # check mapped channel exists
        self._validate_channel_exists(list(pulse_channel_to_sequence_channel.values()))
            
        # create and regist command
        command = SequenceCommand(pulse_name, pulse_channel_to_sequence_channel=pulse_channel_to_sequence_channel)
        self._command_list.append(command)

    def add_synchronize_command(self, channel_list: list[str]) -> None:
        self.add_blank_command(channel_list, blank_time_ns = 0)

    def add_synchronize_all_command(self) -> None:
        self.add_blank_command(self._channel_list, blank_time_ns = 0)

    def add_capture_command(self, channel_list: list[str]) -> None:
        self._validate_channel_exists(channel_list)
        seq_command = SequenceCommand(_CAPT_COMMAND_, channel_list=channel_list)
        self._command_list.append(seq_command)

    def add_blank_command(self, channel_list: list[str], blank_time_ns: float) -> None:
        self._validate_channel_exists(channel_list)
        seq_command = SequenceCommand(_SYNC_COMMAND_, channel_list=channel_list, blank_time=blank_time_ns)
        self._command_list.append(seq_command)

    def _get_group_key_from_command(self, command: SequenceCommand) -> tuple[str,...]:
        if command.name in [_SYNC_COMMAND_, _CAPT_COMMAND_]:
            channel_list: list[str] = command.channel_list
        else:
            channel_list: list[str] = list(command.pulse_channel_to_sequence_channel.values())
        group_list = [self._channel_to_group[channel] for channel in channel_list]
        group_key = tuple(sorted(list(set(group_list))))
        return group_key

    def get_config(self) -> SequenceConfig:
        config_dict: dict[tuple[str,...], dict[str, float]] = {}
        for command in self._command_list:
            if command.name in [_SYNC_COMMAND_, _CAPT_COMMAND_]:
                continue
            # get relevant channel list
            group_key = self._get_group_key_from_command(command)
            if group_key not in config_dict:
                config_dict[group_key] = {}
            sequence_config = self.pulse_library.get_config(command.name)
            config_dict[group_key].update({command.name: sequence_config})
        
        raw_config: list[dict[str, Any]] = []
        for key, value in config_dict.items():
            raw_config.append({
                "group": key,
                "parameter": value,
            })
        config = SequenceConfig(raw_config)
        return config

    def _get_latest_cursor(self, cursor: dict[str, float], channel_list: list[str]) -> float:
        latest_cursor = 0.
        for channel in channel_list:
            latest_cursor = max(latest_cursor, cursor[channel])
        return latest_cursor

    def _synchronize_cursor(self, cursor: dict[str, float], channel_list: list[str], point: float) -> None:
        for channel in channel_list:
            cursor[channel] = point

    def get_duration(self, config: SequenceConfig, capture_duration: float) -> float:
        duration: float = 0.

        cursor: dict[str, float] = {}
        for channel in self._channel_list:
            cursor[channel] = 0.

        for command in self._command_list:
            if command.name == _CAPT_COMMAND_:
                latest_cursor = self._get_latest_cursor(cursor, command.channel_list)
                self._synchronize_cursor(cursor, command.channel_list, latest_cursor)
                duration = max(duration, latest_cursor+capture_duration)
            elif command.name == _SYNC_COMMAND_:
                latest_cursor = self._get_latest_cursor(cursor, command.channel_list)
                latest_cursor += command.blank_time
                self._synchronize_cursor(cursor, command.channel_list, latest_cursor)
                duration = max(duration, latest_cursor)
            else:
                sequence_channel_list = list(command.pulse_channel_to_sequence_channel.values())
                latest_cursor = self._get_latest_cursor(cursor, sequence_channel_list)
                pulse_config = config.get_parameter(self._get_group_key_from_command(command))[command.name]
                pulse_duration = self.pulse_library.get_duration(command.name, pulse_config)
                self._synchronize_cursor(cursor, sequence_channel_list, latest_cursor+pulse_duration)
                duration = max(duration, latest_cursor+pulse_duration)
        return duration


    def get_waveform(self, time_slots: np.ndarray, config: SequenceConfig) -> tuple[dict[str, np.ndarray], dict[str, list[float]]]:
        # intialize
        cursor: dict[str, float] = {}
        waveform: dict[str, np.ndarray] = {}
        capture_point: dict[str, list[float]] = {}
        for channel in self._channel_list:
            cursor[channel] = 0.
            waveform[channel] = np.zeros_like(time_slots, dtype=complex)
            capture_point[channel] = []

        for command in self._command_list:
            if command.name == _CAPT_COMMAND_:
                latest_cursor = self._get_latest_cursor(cursor, command.channel_list)
                for channel in command.channel_list:
                    capture_point[channel].append(latest_cursor)
                self._synchronize_cursor(cursor, command.channel_list, latest_cursor)
            elif command.name == _SYNC_COMMAND_:
                latest_cursor = self._get_latest_cursor(cursor, command.channel_list)
                latest_cursor += command.blank_time
                self._synchronize_cursor(cursor, command.channel_list, latest_cursor)
            else:
                sequence_channel_list = list(command.pulse_channel_to_sequence_channel.values())
                latest_cursor = self._get_latest_cursor(cursor, sequence_channel_list)
                pulse_config = config.get_parameter(self._get_group_key_from_command(command))[command.name]
                pulse_waveform, pulse_duration = self.pulse_library.get_waveform(command.name, time_slots, latest_cursor, pulse_config)
                for pulse_channel, channel_waveform in pulse_waveform.items():
                    channel = command.pulse_channel_to_sequence_channel[pulse_channel]
                    waveform[channel] += channel_waveform
                self._synchronize_cursor(cursor, sequence_channel_list, latest_cursor+pulse_duration)
        return waveform, capture_point

