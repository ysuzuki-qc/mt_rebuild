

from typing import Literal
import numpy as np
import labrad
from mt_util.tunits_util import FrequencyType, TimeType
from mt_quel_meas.job import AcquisitionConfig
from mt_quel_meas.labrad.labrad_job import JobLabrad, PhysicalUnitIdentifier

class JobExecutorLabrad:
    def __init__(self, labrad_host: str, port: int) -> None:
        self._connection = labrad.connect(labrad_host, port=port)
        if "qube_server" not in self._connection:
            raise ValueError("Qube server is not running")
        self._qube = self._connection.qube_server

    def _update_waveform(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], channel_to_waveform: dict[str, np.ndarray]) -> None:
        for channel, waveform in channel_to_waveform.items():
            physical_unit = channel_to_physical_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            self._qube.upload_waveform([waveform], [physical_unit.unit_index])

    def _check_LO_frequency(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], channel_to_LO_frequency: dict[str, FrequencyType]) -> None:
        for channel, frequency in channel_to_LO_frequency.items():
            physical_unit = channel_to_physical_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            LO_freq: FrequencyType = self._qube.frequency_LO()
            freq_dif = LO_freq - frequency
            if not (freq_dif["Hz"] < 1):
                raise ValueError(f"Wrong LO setting: obtained {LO_freq}, expected {frequency}")

    def _check_LO_sideband(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], channel_to_LO_sideband: dict[str, Literal["USB", "LSB"]]) -> None:
        for channel, sideband in channel_to_LO_sideband.items():
            physical_unit = channel_to_physical_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            _sideband: str = self._qube.sideband()
            if _sideband.upper() != sideband:
                raise ValueError(f"Wrong sideband setting: obtained {_sideband.upper()}, expected {sideband}")


    def _update_NCO_frequency(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], channel_to_NCO_frequency: dict[str, tuple[FrequencyType, dict[int, FrequencyType]]]) -> None:
        for channel, frequency in channel_to_NCO_frequency.items():
            physical_unit = channel_to_physical_unit[channel]
            CNCO_freq = frequency[0]
            FNCO_freq_dict = frequency[1]
            self._qube.select_device(physical_unit.box_port)
            self._qube.frequency_tx_NCO(CNCO_freq["MHz"] * labrad.units.MHz)
            if "readout" in physical_unit.box_port:
                self._qube.frequency_rx_NCO(CNCO_freq["MHz"] * labrad.units.MHz)
            for index, freq in FNCO_freq_dict.items():
                self._qube.frequency_tx_fine_nco(index, freq["MHz"] * labrad.units.MHz)

    def _update_capture_point(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], channel_to_capture_point: dict[str, list[TimeType]], readout_length: TimeType) -> None:
        for channel, capture_point_list in channel_to_capture_point.items():
            physical_unit = channel_to_physical_unit[channel]
            for capture_point in capture_point_list:
                self._qube.select_device(physical_unit.box_port)
                self._qube.acquisition_window(physical_unit.unit_index, (capture_point, capture_point + readout_length))

    def _update_FIR_coefficients(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], channel_to_FIR_coefficients: dict[str, list[np.ndarray]]) -> None:
        for channel, FIR_coefficients in channel_to_FIR_coefficients.items():
            physical_unit = channel_to_physical_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            self._qube.acquisition_fir_coefficients(physical_unit.unit_index, FIR_coefficients)

    def _update_averaging_window_coefficients(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], channel_to_averaging_window_coefficients: dict[str, np.ndarray]) -> None:
        for channel, window_coefficients in channel_to_averaging_window_coefficients.items():
            physical_unit = channel_to_physical_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            self._qube.acquisition_window_coefficients(physical_unit.unit_index, window_coefficients)

    def _get_acquisition_mode(self, acquisition_config: AcquisitionConfig) -> str:
        averaging_waveform = acquisition_config.flag_average_waveform
        averaging_shots = acquisition_config.flag_average_shots
        if averaging_waveform and averaging_shots:
            # average wave and shots, obtain points [#measurement_windows]
            acquisition_mode = "B"
        elif (not averaging_waveform) and averaging_shots:
            # average for shots, obtain single waveform [#time_array, #measurement_windows]
            acquisition_mode = "3"
        elif averaging_waveform and (not averaging_shots):
            # average for waveform, obtain many shots with [#shots, #measurement_windows]
            acquisition_mode = "A"
        else:
            # no average, obtain [#shots, #time_array, #measurement_windows]
            acquisition_mode = "2"
        return acquisition_mode

    def _update_acquisition_config(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], acquisition_config: AcquisitionConfig) -> None:
        self._qube.daq_timeout(acquisition_config.acquisition_timeout)
        self._qube.daq_synchronization_delay(acquisition_config.acquisition_synchronization_delay)
        self._qube.daq_length(acquisition_config.waveform_length)
        self._qube.repetition_time(acquisition_config.waveform_length + acquisition_config.repetition_margin)
        self._qube.shots(acquisition_config.num_shot)

        acquisition_mode = self._get_acquisition_mode(acquisition_config)
        for _, physical_unit in channel_to_physical_unit.items():
            self._qube.select_device(physical_unit.box_port)
            if "readout" in physical_unit.box_port:
                self._qube.upload_parameters([0,])
                self._qube.upload_readout_parameters([physical_unit.unit_index,])
                self._qube.acquisition_mode(physical_unit.unit_index, acquisition_mode)
            else:
                self._qube.upload_parameters([physical_unit.unit_index,])

    def _do_measurement(self) -> None:
        self._qube.daq_start()
        self._qube.daq_trigger()
        self._qube.daq_stop()
        self._qube.daq_clear()

    def _download_waveform(self, channel_to_physical_unit: dict[str, PhysicalUnitIdentifier], channel_to_capture_point: dict[str, list[TimeType]]) -> dict[str, dict[int, np.ndarray]]:
        result: dict[str, dict[int, np.ndarray]] = {}
        for channel, _ in channel_to_capture_point.items():
            physical_unit = channel_to_physical_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            waveform = self._qube.download_waveform(physical_unit.unit_index)
            if physical_unit.box_port not in result:
                result[physical_unit.box_port] = {}
            result[physical_unit.box_port][physical_unit.unit_index] = waveform
        return result

    def do_measurement(self, job: JobLabrad) -> dict[str, dict[int, np.ndarray]]:
        self._update_waveform(job.channel_to_physical_unit, job.channel_to_waveform)
        self._check_LO_frequency(job.channel_to_physical_unit, job.channel_to_LO_frequency)
        self._check_LO_sideband(job.channel_to_physical_unit, job.channel_to_LO_sideband)
        self._update_NCO_frequency(job.channel_to_physical_unit, job.channel_to_NCO_frequency)
        self._update_capture_point(job.channel_to_physical_unit, job.channel_to_capture_point, job.acquisition_config.acquisition_duration)
        self._update_FIR_coefficients(job.channel_to_physical_unit, job.channel_to_FIR_coefficients)
        self._update_averaging_window_coefficients(job.channel_to_physical_unit, job.channel_to_averaging_window_coefficients)
        self._update_acquisition_config(job.channel_to_physical_unit, job.acquisition_config)
        self._do_measurement()
        dataset = self._download_waveform(job.channel_to_physical_unit, job.channel_to_capture_point)
        return dataset



