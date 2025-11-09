

from logging import getLogger
from typing import Literal
import numpy as np
import labrad
from mt_util.tunits_util import FrequencyType, TimeType
from mt_quel_meas.labrad.labrad_job import JobLabrad, PhysicalUnitIdentifier, AcquisitionConfigLabrad

logger = getLogger(__name__)

class JobExecutorLabrad:
    def __init__(self) -> None:
        # Assume hostname and password are provided by environment value LABRADHOST and LABRADPASSWORD for safety.
        self._connection = labrad.connect()
        if "qube_server" not in self._connection.servers:
            raise ValueError("Qube server is not running")
        self._qube = self._connection.qube_server

    def _update_common_config(self, acquisition_config: AcquisitionConfigLabrad) -> None:
        self._qube.daq_timeout(acquisition_config.acquisition_timeout["ns"] * labrad.units.ns)
        logger.info(f"set daq_timeout | v: {acquisition_config.acquisition_timeout}")
        self._qube.daq_synchronization_delay(acquisition_config.acquisition_synchronization_delay["ns"] * labrad.units.ns)
        logger.info(f"set daq_synchronizatoin_delay | v: {acquisition_config.acquisition_synchronization_delay}")

    def _update_waveform(self, awg_channel_to_dac_unit: dict[str, PhysicalUnitIdentifier], awg_channel_to_waveform: dict[str, np.ndarray], acquisition_config: AcquisitionConfigLabrad) -> None:
        for channel, waveform in awg_channel_to_waveform.items():
            physical_unit = awg_channel_to_dac_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            self._qube.daq_length(acquisition_config.waveform_length["ns"] * labrad.units.ns)
            self._qube.repetition_time(acquisition_config.repetition_time["ns"] * labrad.units.ns)
            self._qube.upload_waveform([waveform], [physical_unit.unit_index])
            logger.info(f"set waveform | ch: {channel}, len: {len(waveform)}")

    def _update_shot(self, awg_channel_to_dac_unit: dict[str, PhysicalUnitIdentifier], acquisition_config: AcquisitionConfigLabrad) -> None:
        for channel, physical_unit in awg_channel_to_dac_unit.items():
            self._qube.select_device(physical_unit.box_port)
            self._qube.shots(acquisition_config.num_shot)
            logger.info(f"set num_shot | ch: {channel}, v: {acquisition_config.num_shot}")

    def _update_FNCO_frequency(self, awg_channel_to_dac_unit: dict[str, PhysicalUnitIdentifier], awg_channel_to_FNCO_frequency: dict[str, FrequencyType]) -> None:
        for channel, frequency in awg_channel_to_FNCO_frequency.items():
            physical_unit = awg_channel_to_dac_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            self._qube.frequency_tx_fine_nco(physical_unit.unit_index, frequency["MHz"] * labrad.units.MHz)
            logger.info(f"set FNCO frequency | ch: {channel}, v: {frequency}")

    def _update_CNCO_frequency(self, boxport_to_CNCO_frequency: dict[str, FrequencyType]) -> None:
        for box_port, frequency in boxport_to_CNCO_frequency.items():
            self._qube.select_device(box_port)
            self._qube.frequency_tx_nco(frequency["MHz"] * labrad.units.MHz)
            logger.info(f"set CNCO-tx frequency | ch: {box_port}, v: {frequency}")
            # TODO: check with port index
            if "readout" in box_port:
                self._qube.frequency_rx_nco(frequency["MHz"] * labrad.units.MHz)
                logger.info(f"set CNCO-rx frequency | ch: {box_port}, v: {frequency}")

    def _check_LO_frequency_and_sideband(self, boxport_to_LO_frequency: dict[str, FrequencyType], boxport_to_LO_sideband: dict[str, Literal["USB", "LSB", "Direct"]]) -> None:
        assert(set(boxport_to_LO_frequency.keys()) == set(boxport_to_LO_sideband.keys()))
        for box_port, sideband_expected in boxport_to_LO_sideband.items():

            if sideband_expected == "Direct":
                logger.info(f"check LO | ch: {box_port} skip No LO")
                continue

            self._qube.select_device(box_port)
            sideband_obtained: str = self._qube.frequency_sideband()
            if sideband_expected != sideband_obtained.upper():
                raise ValueError(f"Wrong LO sideband: ch: {box_port}, obtained {sideband_obtained}, expected {sideband_expected}")
            
            freq_expected = boxport_to_LO_frequency[box_port]["MHz"] * labrad.units.MHz
            freq_obtained = self._qube.frequency_local()
            if not (abs((freq_expected-freq_obtained)["Hz"]) < 1):
                raise ValueError(f"Wrong LO frequency: ch: {box_port}, obtained {freq_obtained}, expected {freq_expected}")
            logger.info(f"check LO | ch: {box_port}, v: {freq_expected} sb: {sideband_expected}")


    def _update_capture_point(self, capture_channel_to_adc_unit: dict[str, PhysicalUnitIdentifier], capture_channel_to_capture_point: dict[str, list[TimeType]], readout_length: TimeType) -> None:
        labrad_ns = labrad.units.ns
        readout_length_ns = readout_length["ns"]
        for channel, capture_point_list in capture_channel_to_capture_point.items():
            physical_unit = capture_channel_to_adc_unit[channel]
            window_list: list = []
            #TODO: upload all the relevant mux channels simultaneously
            for capture_point in capture_point_list:
                capture_point_ns = capture_point["ns"]
                window = (capture_point_ns*labrad_ns, capture_point_ns*labrad_ns + readout_length_ns*labrad_ns)
                window_list.append(window)
            self._qube.select_device(physical_unit.box_port)
            self._qube.acquisition_window(physical_unit.unit_index, window_list)
            logger.info(f"set capture windows | ch: {channel}, window: {window_list}")

    def _update_FIR_coefficients(self, capture_channel_to_adc_unit: dict[str, PhysicalUnitIdentifier], capture_channel_to_FIR_coefficients: dict[str, np.ndarray]) -> None:
        for channel, FIR_coefficients in capture_channel_to_FIR_coefficients.items():
            physical_unit = capture_channel_to_adc_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            self._qube.acquisition_fir_coefficients(physical_unit.unit_index, FIR_coefficients)
            logger.info(f"set FIR coefs | ch: {channel}, len: {len(FIR_coefficients)}")

    def _update_averaging_window_coefficients(self, capture_channel_to_adc_unit: dict[str, PhysicalUnitIdentifier], capture_channel_to_averaging_window_coefficients: dict[str, np.ndarray]) -> None:
        for channel, window_coefficients in capture_channel_to_averaging_window_coefficients.items():
            physical_unit = capture_channel_to_adc_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            self._qube.acquisition_window_coefficients(physical_unit.unit_index, window_coefficients)
            logger.info(f"set averaging window coefs | ch: {channel}, len: {len(window_coefficients)}")

    def _get_acquisition_mode(self, acquisition_config: AcquisitionConfigLabrad) -> str:
        averaging_waveform = acquisition_config.flag_average_waveform
        averaging_shots = acquisition_config.flag_average_shots
        if averaging_waveform and averaging_shots:
            # Average waveform and shots. Obtained shape will be [#capture_points]
            acquisition_mode = "B"
        elif (not averaging_waveform) and averaging_shots:
            # Average shots. Obtained shape will be [#time_slot, #capture_points]
            acquisition_mode = "3"
        elif averaging_waveform and (not averaging_shots):
            # Average waveform. Obtained shape will be [#shot, #capture_points]
            acquisition_mode = "A"
        else:
            # Average nothing. Obtained shape will be [#shot, #time_slots, #capture_points]
            acquisition_mode = "2"
        return acquisition_mode

    def _upload_parameters(self, awg_channel_to_dac_unit: dict[str, PhysicalUnitIdentifier], acquisition_config: AcquisitionConfigLabrad) -> None:
        acquisition_mode = self._get_acquisition_mode(acquisition_config)
        for channel, physical_unit in awg_channel_to_dac_unit.items():
            self._qube.select_device(physical_unit.box_port)
            #TODO check with port index
            if "readout" in physical_unit.box_port:
                self._qube.acquisition_mode(physical_unit.unit_index, acquisition_mode)
                logger.info(f"set acq mode | ch: {physical_unit.box_port}, mode: {acquisition_mode} (shot_avg={acquisition_config.flag_average_shots}, time_avg={acquisition_config.flag_average_waveform})")
                self._qube.upload_parameters([0,])
                logger.info(f"upload parameters | box: {physical_unit.box_port} ch: 0")
                self._qube.upload_readout_parameters([physical_unit.unit_index,])
                logger.info(f"upload readout parameters | box: {physical_unit.box_port} ch: {physical_unit.unit_index}")
            else:
                self._qube.upload_parameters([physical_unit.unit_index,])
                logger.info(f"upload parameters | box: {physical_unit.box_port} ch: {physical_unit.unit_index}")

    def _do_measurement(self) -> None:
        logger.info(f"daq start")
        self._qube.daq_start()
        logger.info(f"daq trigger")
        self._qube.daq_trigger()
        logger.info(f"daq stop | start waiting...")
        self._qube.daq_stop()
        logger.info(f"daq stop | returned")
        logger.info(f"daq clear")
        self._qube.daq_clear()

    def _download_waveform(self, capture_channel_to_adc_unit: dict[str, PhysicalUnitIdentifier], capture_channel_to_capture_point: dict[str, list[TimeType]]) -> dict[str, np.ndarray]:
        result: dict[str, np.ndarray] = {}
        # TODO: get mux simultaneously
        for channel, capture_points in capture_channel_to_capture_point.items():
            physical_unit = capture_channel_to_adc_unit[channel]
            self._qube.select_device(physical_unit.box_port)
            waveform = self._qube.download_waveform(physical_unit.unit_index)
            result[channel] = waveform
            logger.info(f"download waveform | ch: {channel} num_window: {len(capture_points)} waveform_shape: {waveform.shape}")
        return result

    def do_measurement(self, job: JobLabrad) -> dict[str, np.ndarray]:
        # config general values
        self._update_common_config(job.acquisition_config)
        self._update_shot(job.awg_channel_to_dac_unit ,job.acquisition_config)

        # update AWG
        self._update_waveform(job.awg_channel_to_dac_unit, job.awg_channel_to_waveform, job.acquisition_config)
        self._update_FNCO_frequency(job.awg_channel_to_dac_unit, job.awg_channel_to_FNCO_frequency)

        # update box
        self._update_CNCO_frequency(job.boxport_to_CNCO_frequency)
        self._check_LO_frequency_and_sideband(job.boxport_to_LO_frequency, job.boxport_to_LO_sideband)

        # update Capture
        self._update_capture_point(job.capture_channel_to_adc_unit, job.capture_channel_to_capture_point, job.acquisition_config.acquisition_duration)
        self._update_FIR_coefficients(job.capture_channel_to_adc_unit, job.capture_channel_to_FIR_coefficients)
        self._update_averaging_window_coefficients(job.capture_channel_to_adc_unit, job.capture_channel_to_averaging_window_coefficients)

        # measurement
        self._upload_parameters(job.awg_channel_to_dac_unit, job.acquisition_config)
        self._do_measurement()
        dataset = self._download_waveform(job.capture_channel_to_adc_unit, job.capture_channel_to_capture_point)
        return dataset



