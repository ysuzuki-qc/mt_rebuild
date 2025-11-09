import numpy as np
from mt_pulse.pulse import Pulse
from mt_pulse.pulse_library import PulseLibrary
from mt_pulse.shape_preset import get_preset_shape_library

def BLANK() -> Pulse:
    pulse = Pulse(name="BLANK", channel_list=["channel"])
    w = pulse.add_variable("blank_width", default_value=100, description="margine before and after sequence")
    pulse.add_shape(channel_name="channel", shape_name="blank", shape_param={"width": w})
    return pulse

def FLATTOP() -> Pulse:
    pulse = Pulse(name="FLATTOP", channel_list=["channel"])
    w = pulse.add_variable("flattop_width", default_value=100, description="width of flattop pulse")
    a = pulse.add_variable("flattop_amplitude", default_value=0.9, description="amplitude of flattop pulse")
    p = pulse.add_variable("flattop_phase", default_value=0, description="phase of flattop pulse")
    pulse.add_shape(channel_name="channel", shape_name="flattop", shape_param={"width": w, "amplitude": a, "phase": p})
    return pulse

def HPI() -> Pulse:
    pulse = Pulse(name="HPI", channel_list=["qubit"])
    w = pulse.add_variable("hpi_width", default_value=20, description="width of half-pi pulse")
    a = pulse.add_variable("hpi_amplitude", default_value=0.9, description="amplitude of HPI pulse")
    m = pulse.add_variable("hpi_margin_coef", default_value=2.0, description="product of sigma and this value is padded to gaussian center")
    p = pulse.add_variable("hpi_phase", default_value=0, description="phase of this pulse")
    pulse.add_shape(channel_name="qubit", shape_name="blank", shape_param={"width": m*w})
    pulse.add_shape(channel_name="qubit", shape_name="gaussian", shape_param={"width": w, "amplitude": a, "phase": p})
    pulse.add_shape(channel_name="qubit", shape_name="blank", shape_param={"width": m*w})
    return pulse

def TPCX() -> Pulse:
    pulse = Pulse(name="TPCX", channel_list=["control", "target"])
    tpcx_w = pulse.add_variable("tpcx_width", default_value=200, description="width of TPCX main and counter pulse")
    tpcx_r = pulse.add_variable("tpcx_risetime", default_value=20, description="risetime of TPCX main and counter pulse")
    tpcx_ma = pulse.add_variable("tpcx_main_amplitude", default_value=0.9, description="amplitude of TPCX main pulse")
    tpcx_mp = pulse.add_variable("tpcx_main_phase", default_value=0, description="phase of TPCX main pulse")
    tpcx_ca = pulse.add_variable("tpcx_counter_amplitude", default_value=0.9, description="amplitude of TPCX counter pulse")
    tpcx_cp = pulse.add_variable("tpcx_counter_phase", default_value=0, description="phase of TPCX counter pulse")
    hpi_w = pulse.add_variable("tpcx_hpi_width", default_value=20, description="width of HPI gaussian pulse on control qubits")
    hpi_a = pulse.add_variable("tpcx_hpi_amplitude", default_value=0.9, description="amplitude of HPI gaussian pulse on control qubits")
    hpi_p = pulse.add_variable("tpcx_hpi_phase", default_value=0, description="phase of HPI gaussian pulse on control qubits")
    hpi_c = pulse.add_variable("tpcx_hpi_margin_coef", default_value=2.0, description="product of sigma and this value is padded to HPI gaussian pulse on control")
    pulse.add_shape(channel_name="control", shape_name="flattop_cosrise", shape_param={"width": tpcx_w, "risetime": tpcx_r, "amplitude": tpcx_ma, "phase": tpcx_mp})
    pulse.add_shape(channel_name="target",  shape_name="flattop_cosrise", shape_param={"width": tpcx_w, "risetime": tpcx_r, "amplitude": tpcx_ca, "phase": tpcx_cp})
    pulse.add_shape(channel_name="control", shape_name="blank", shape_param={"width": hpi_c*hpi_w})
    pulse.add_shape(channel_name="control", shape_name="gaussian", shape_param={"width": hpi_w, "amplitude": hpi_a, "phase": hpi_p})
    pulse.add_shape(channel_name="control", shape_name="blank", shape_param={"width": hpi_c*hpi_w})
    pulse.add_shape(channel_name="target",  shape_name="blank", shape_param={"width": hpi_c*hpi_w*2})
    pulse.add_shape(channel_name="control", shape_name="flattop_cosrise", shape_param={"width": tpcx_w, "risetime": tpcx_r, "amplitude": tpcx_ma, "phase": tpcx_mp + np.pi})
    pulse.add_shape(channel_name="target",  shape_name="flattop_cosrise", shape_param={"width": tpcx_w, "risetime": tpcx_r, "amplitude": tpcx_ca, "phase": tpcx_cp + np.pi})
    return pulse

def CR() -> Pulse:
    pulse = Pulse(name="CR", channel_list=["control", "target"])
    cr_w = pulse.add_variable("cr_width", default_value=400, description="width of CR main and counter pulse")
    cr_r = pulse.add_variable("cr_risetime", default_value=20, description="risetime of CR main and counter pulse")
    cr_ma = pulse.add_variable("cr_main_amplitude", default_value=0.9, description="amplitude of CR main pulse")
    cr_mp = pulse.add_variable("cr_main_phase", default_value=0, description="phase of CR main pulse")
    cr_ca = pulse.add_variable("cr_counter_amplitude", default_value=0.9, description="amplitude of CR counter pulse")
    cr_cp = pulse.add_variable("cr_counter_phase", default_value=0, description="phase of CR counter pulse")
    pulse.add_shape(channel_name="control", shape_name="flattop_cosrise", shape_param={"width": cr_w, "risetime": cr_r, "amplitude": cr_ma, "phase": cr_mp})
    pulse.add_shape(channel_name="target",  shape_name="flattop_cosrise", shape_param={"width": cr_w, "risetime": cr_r, "amplitude": cr_ca, "phase": cr_cp})
    return pulse

def MEAS() -> Pulse:
    pulse = Pulse(name="MEAS", channel_list=["resonator"])
    m_w = pulse.add_variable("meas_width", default_value=400, description="width of measurement pulse")
    m_r = pulse.add_variable("meas_risetime", default_value=20, description="risetime of measuerment pulse")
    m_a = pulse.add_variable("meas_amplitude", default_value=0.9, description="amplitude of measurement pulse")
    m_p = pulse.add_variable("meas_phase", default_value=0, description="phase of measuerment pulse")
    pulse.add_shape(channel_name="resonator", shape_name="flattop_cosrise", shape_param={"width": m_w, "risetime": m_r, "amplitude": m_a, "phase": m_p})
    return pulse


def get_preset_pulse_library() -> PulseLibrary:
    shape_lib = get_preset_shape_library()
    pulse_lib = PulseLibrary(shape_lib)
    pulse_list = [BLANK(), FLATTOP(), HPI(), CR(), MEAS(), TPCX()]
    for pulse in pulse_list:
        pulse_lib.add_pulse(pulse)
    return pulse_lib
