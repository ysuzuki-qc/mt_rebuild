import numpy as np
from mt_util.tunits_util import FrequencyType
from mt_quel_util.mux_assignment import MultiplexingResult
from mt_quel_util.constant import InstrumentConstantQuEL
import pydantic


@pydantic.validate_call
def print_mux_config(
    channel_to_frequency: dict[str, FrequencyType],
    channel_to_device: dict[str, str],
    channel_to_port_index: dict[str, int],
    constant: InstrumentConstantQuEL,
    result: MultiplexingResult,
):
    for channel in channel_to_frequency:
        devname = channel_to_device[channel]
        port_index = channel_to_port_index[channel]
        dac_index = result.channel_to_dac_index[channel]
        port_type = constant.port_type[port_index]
        LO_freq = constant.LO_freq_resonator if port_type == "ReadOut" else constant.LO_freq_qubit
        LO_sideband = constant.LO_sideband_resonator if port_type == "ReadOut" else constant.LO_sideband_qubit
        CNCO_freq = result.CNCO_setting[devname][port_index]
        FNCO_freq = result.FNCO_setting[devname][port_index][dac_index]
        RES_freq = result.channel_to_residual_frequency[channel]
        channel_freq = channel_to_frequency[channel]
        print(f"{channel:15}")
        print(f"assignment:  dev: {devname:5} port:{port_index:3} dac:{dac_index:3} sideband: {LO_sideband:8}")
        if LO_sideband == "LSB":
            print(
                f"frequency:  LO:{LO_freq['MHz']:8.2f} - CNCO:{CNCO_freq['MHz']:8.2f} - "
                f"FNCO:{FNCO_freq['MHz']:8.2f} - RES:{RES_freq['MHz']:8.2f} = "
                f"{(LO_freq-CNCO_freq-FNCO_freq-RES_freq)['MHz']:8.2f} MHz (target={channel_freq['MHz']:8.2f} MHz)"
            )
            assert np.allclose((LO_freq - CNCO_freq - FNCO_freq - RES_freq)["MHz"], channel_freq["MHz"])
        else:
            print(
                f"frequency:  LO:{LO_freq['MHz']:8.2f} + CNCO:{CNCO_freq['MHz']:8.2f} + "
                f"FNCO:{FNCO_freq['MHz']:8.2f} + RES:{RES_freq['MHz']:8.2f} = "
                f"{(LO_freq+CNCO_freq+FNCO_freq+RES_freq)['MHz']:8.2f} MHz (target={channel_freq['MHz']:8.2f} MHz)"
            )
            assert np.allclose((LO_freq + CNCO_freq + FNCO_freq + RES_freq)["MHz"], channel_freq["MHz"])
        print("bandwidth:", result.channel_to_pulse_bandwidth[channel]["MHz"], "MHz")
        print()
