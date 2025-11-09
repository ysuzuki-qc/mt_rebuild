
from dataclasses import dataclass
from tunits.units import us, ms
import numpy as np
from mt_util.tunits_util import FrequencyType, TimeType
from mt_quel_meas.quelware.job import JobQuelware, ChannelIdentifier


try:
    from e7awghal import AwgParam, CapParam, CapSection, WaveChunk # pyright: ignore[reportMissingImports]
    from quel_ic_config import Quel1Box, Quel1BoxType, Quel1PortType # pyright: ignore[reportMissingImports]
    __import_success = True
except Exception:
    __import_success = False


if __import_success:
    class QuEL1ManagerQuelware:
        def __init__(self, name_to_ip: dict[str, str]) -> None:
            self.box_dict: dict[str, Quel1Box] = {}
            for name, ip in name_to_ip.items():
                box = Quel1Box.create(ipaddr_wss=ip, boxtype=Quel1BoxType.QuEL1SE_RIKEN8)
                box.reconnect()
                self.box_dict[name] = box

        def _update_waveform(self, ID_to_box_port_dac: dict[str, ChannelIdentifier], ID_to_waveform: dict[str, np.ndarray]):
            waveform_name = "waveform"
            for ID, waveform in ID_to_waveform.items():
                channel = ID_to_box_port_dac[ID]
                box = self.box_dict[channel.box]
                box.register_wavedata(channel.port, channel.dac, waveform_name, waveform)
                awg_param = AwgParam(num_wait_word=0, num_repeat=1)
                awg_param.chunks.append(WaveChunk(name_of_wavedata=waveform_name, num_blank_word=0, num_repeat=1))
                box.config_channel(channel.port, channel.dac, awg_param=awg_param)

        def _update_NCO_frequency(self, ID_to_box_port_dac: dict[str, ChannelIdentifier], ID_to_NCO_frequency: dict[str, tuple[FrequencyType, list[FrequencyType]]]):
            for ID, frequency in ID_to_NCO_frequency.items():
                CNCO_freq = frequency[0]
                FNCO_list = frequency[1]
                FNCO_channels = {}
                for index in range(len(FNCO_list)):
                    FNCO_channels[index] = {"fnco_freq": FNCO_list[index]["Hz"]}

                channel = ID_to_box_port_dac[ID]
                box = self.box_dict[channel.box]
                box.config_port(port = channel.port,cnco_freq=CNCO_freq["Hz"],channels=FNCO_channels)

        def _update_capture_point(self, ID_to_box_port_dac: dict[str, ChannelIdentifier], ID_to_capture_point: dict[str, list[TimeType]]):
            for ID, capture_point_list in ID_to_capture_point.items():
                channel = ID_to_box_port_dac[ID]
                capture_param = CapParam(num_repeat=1)
                for index, capture_point in enumerate(capture_point_list):
                    name = f"{channel.box}__{channel.port}__{channel.dac}__{index}"
                    capture_point["ns"]
                    capture_param.sections.append(CapSection(name=name, num_capture_word=(2048 + 512) // 4, num_blank_word=4 // 4))
                box = self.box_dict[channel.box]
                box.config_runit(channel.port, channel.dac, capture_param=capture_param)

        def _get_relevant_box_list(self, ID_to_box_port_dac: dict[str, ChannelIdentifier]) -> list[tuple[str, Quel1Box, list, list]]:
            # gather unique box name list
            box_name_list = []
            for channel in ID_to_box_port_dac.values():
                box_name_list.append(self.box_dict[channel.box])
            box_name_list = sorted(set(box_name_list))

            # gather relevant awg/capture units
            capture_units: dict[str, list] = {}
            awg_units: dict[str, list] = {}
            for box_name in box_name_list:
                capture_units[box_name] = []
                awg_units[box_name] = []
            for unit in ID_to_box_port_dac.values():
                if unit.port == 0:
                    capture_units[unit.box].append((unit.port, unit.dac))
                else:
                    awg_units[unit.box].append((unit.port, unit.dac))

            # create return objects
            result = []
            for unit in ID_to_box_port_dac.values():
                box_name = unit.box
                result.append( (box_name, self.box_dict[box_name], capture_units[box_name], awg_units[box_name]))
            return result

        def do_measurement(self, job: JobQuelware) -> dict[str, np.ndarray]:
            if job.ID_to_waveform is not None:
                self._update_waveform(job.ID_to_box_port_dac, job.ID_to_waveform)
            if job.ID_to_NCO_frequency is not None:
                self._update_NCO_frequency(job.ID_to_box_port_dac, job.ID_to_NCO_frequency)

            box_list: list[tuple[str, Quel1Box, list, list]] = self._get_relevant_box_list(job.ID_to_box_port_dac)
            

            # determine synchronize time
            synchronization_delay = job.acquisition_config.acquisition_synchronization_delay["ns"]
            current_time = box_list[0][1].get_current_timecounter()
            synchronization_time = current_time + synchronization_delay

            # trigger all box
            capture_task_list = []
            awg_task_list = []
            for _, box, capture_units, awg_units in box_list:
                capture_task, awg_task = box.start_capture_by_awg_trigger(capture_units, awg_units, synchronization_time)
                capture_task_list.append(capture_task)
                awg_task_list.append(awg_task)

            # wait for finish awg tasks
            for awg_task in awg_task_list:
                awg_task.result(timeout=job.acquisition_config.acquisition_timeout["ns"])

            # wait for finish capture tasks and obtain waveforms
            result_data: dict[str, np.ndarray] = {}
            for box_info, capture_task in zip(box_list, capture_task_list):
                box_name, _, box_capture_units,_ = box_info
                result_dict = capture_task.result()
                for capture_unit in box_capture_units:
                    wavedata = result_dict[capture_unit].as_wave_dict()
                    result_data[box_name] = wavedata
            return wavedata



