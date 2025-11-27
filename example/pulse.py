import sys

path_list = ["./mt_circuit/", "./mt_note/", "./mt_pulse/", "./mt_util/", "./mt_quel_util/", "./mt_quel_meas/"]
for path in path_list:
    sys.path.append(path)
    sys.path.append("../" + path)


def func1():
    # Create preset shape
    import json
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_pulse.shape import Shape
    from mt_pulse.shape_preset import gaussian_drag

    shape = gaussian_drag()

    # create time slots
    cursor = 400
    time_slots = np.arange(0, 1000, 8)

    # instantiate waveform
    param = {"width": 200, "amplitude": 0.5, "drag": 40, "phase": np.pi / 10}
    shape_func = shape.get_function(param)
    shape_waveform = shape_func(time_slots - cursor)

    # plot waveform
    plt.plot(time_slots, np.real(shape_waveform), ".-", label="I")
    plt.plot(time_slots, np.imag(shape_waveform), ".-", label="Q")
    plt.xlim(np.min(time_slots), np.max(time_slots))
    plt.ylim(-1, 1)
    plt.xlabel("Time [ns]")
    plt.ylabel("Amplitude [a.u.]")
    plt.legend()
    plt.show()

    # show equations and variables
    print("expression\n", shape.shape_expr, "\n")
    print("symbols\n", shape.get_symbol_name_set(), "\n")

    # JSON serializable
    json_str = json.dumps(shape.to_json_dict())
    shape_load = Shape.from_json_dict(json.loads(json_str))
    print("json\n", json_str, "\n")
    assert json_str == json.dumps(shape_load.to_json_dict())


def func2():
    # Create original shape
    import numpy as np
    import json
    import matplotlib.pyplot as plt
    import sympy as sp
    from mt_pulse.shape import Shape

    # add user's custom shape
    t, width, amplitude = sp.symbols(["t", "width", "amplitude"])
    shape = sp.Piecewise(
        (amplitude * (1 - sp.Abs(t) / width), sp.And(-width < t, t < width)),
        (0, True),
    )
    shape = Shape(
        name="triangle",
        shape_expr=shape,
        progress_time_ns=sp.Float(0),
    )

    # show equations and variables
    print("expression\n", shape.shape_expr, "\n")
    print("symbols\n", shape.get_symbol_name_set(), "\n")

    # create time slots
    cursor = 400
    time_slots = np.arange(0, 1000, 8)

    # instantiate waveform
    param = {"width": 200, "amplitude": 0.5}
    shape_func = shape.get_function(param)
    shape_waveform = shape_func(time_slots - cursor)

    # plot waveform
    plt.plot(time_slots, np.real(shape_waveform), ".-", label="I")
    plt.plot(time_slots, np.imag(shape_waveform), ".-", label="Q")
    plt.xlim(np.min(time_slots), np.max(time_slots))
    plt.ylim(-1, 1)
    plt.xlabel("Time [ns]")
    plt.ylabel("Amplitude [a.u.]")
    plt.legend()
    plt.show()

    # JSON serializable
    json_str = json.dumps(shape.to_json_dict())
    shape_load = Shape.from_json_dict(json.loads(json_str))
    print("json\n", json_str, "\n")
    assert json_str == json.dumps(shape_load.to_json_dict())


def func3():
    # List of shapes are managed by shape library
    import json
    import sympy as sp
    from mt_pulse.shape import Shape
    from mt_pulse.shape_library import ShapeLibrary
    from mt_pulse.shape_preset import gaussian

    # add preset shape
    shape_lib = ShapeLibrary()
    shape_lib.add_shape(gaussian())

    # add user's custom shape
    t, width, amplitude = sp.symbols(["t", "width", "amplitude"])
    shape = sp.Piecewise(
        (amplitude * (1 - sp.Abs(t) / width), sp.And(-width < t, t < width)),
        (0, True),
    )
    shape = Shape(
        name="triangle",
        shape_expr=shape,
        progress_time_ns=sp.Float(0),
    )
    shape_lib.add_shape(shape)

    # JSON serializable
    json_str = json.dumps(shape_lib.to_json_dict())
    shape_lib_load = ShapeLibrary.from_json_dict(json.loads(json_str))
    print("json\n", json_str, "\n")
    assert json_str == json.dumps(shape_lib_load.to_json_dict())


def func4():
    # Create pulse by combining shape
    import json
    from mt_pulse.pulse import Pulse

    # create new pulse
    # Pulse assumes shapes used in pulse will be provided at instantiation stage
    pulse = Pulse(name="HPI", channel_list=["qubit"])
    w = pulse.add_variable("hpi_width", default_value=20, description="width of half-pi shape")
    a = pulse.add_variable("hpi_amplitude", default_value=0.1, description="amplitude of HPI shape")
    m = pulse.add_variable(
        "hpi_margin_coef", default_value=1.0, description="product of sigma and this value is padded to gaussian center"
    )
    p = pulse.add_variable("hpi_phase", default_value=0, description="phase of this shape")
    pulse.add_shape(channel_name="qubit", shape_name="blank", shape_param={"width": m * w})
    pulse.add_shape(channel_name="qubit", shape_name="gaussian", shape_param={"width": w, "amplitude": a, "phase": p})
    pulse.add_shape(channel_name="qubit", shape_name="blank", shape_param={"width": m * w})

    # pulse is JSON serializable
    dump = json.dumps(pulse.to_json_dict())
    pulse = Pulse.from_json_dict(json.loads(dump))
    dump2 = json.dumps(pulse.to_json_dict())
    assert dump == dump2

    # show description
    print("description", pulse.get_description())
    print("config dict", pulse.get_config())


def func5():
    # Instantiate 1 Qubit pulse
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_pulse.pulse_library import PulseLibrary
    from mt_pulse.pulse_preset import HPI
    from mt_pulse.shape_preset import get_preset_shape_library

    # get pulse-shape libs
    shape_lib = get_preset_shape_library()

    # create sequence library and add sequence
    pulse_lib = PulseLibrary(shape_lib)
    pulse_lib.add_pulse(HPI())

    # get parameter config of sequence, which contains correspondence between key and default values
    config = pulse_lib.get_config("HPI")

    # create cursor and timeslots
    time_slots = np.arange(0, 1000, 8)
    waveform = np.zeros_like(time_slots, dtype=complex)
    cursor = initial_cursor = 100

    # generate waveform of pulse with different config
    # short pulse with large padding
    config["hpi_width"] = 50
    config["hpi_amplitude"] = 0.5
    config["hpi_margin_coef"] = 1.5
    config["hpi_phase"] = np.pi / 3
    pulse_waveform, duration = pulse_lib.get_waveform("HPI", time_slots, cursor, config)
    waveform += pulse_waveform["qubit"]
    cursor += duration
    # long pulse with small padding
    config["hpi_width"] = 100
    config["hpi_amplitude"] = 0.3
    config["hpi_margin_coef"] = 0.8
    config["hpi_phase"] = -np.pi / 4
    pulse_waveform, duration = pulse_lib.get_waveform("HPI", time_slots, cursor, config)
    waveform += pulse_waveform["qubit"]
    cursor += duration

    # plot waveform
    plt.plot(time_slots, np.real(waveform), ".-", label="I")
    plt.plot(time_slots, np.imag(waveform), ".-", label="Q")
    plt.plot([initial_cursor, initial_cursor], [-1, 1], "--", c="black", label="start")
    plt.plot([cursor, cursor], [-1, 1], ":", c="black", label="end")
    plt.legend()
    plt.show()


def func6():
    # Instantiate 2 Qubit pulse
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_pulse.pulse_preset import get_preset_pulse_library

    pulse_lib = get_preset_pulse_library()

    # get parameter config of sequence, which contains correspondence between key and default values
    config = pulse_lib.get_config("TPCX")

    # create cursor and timeslots
    time_slots = np.arange(0, 1000, 8)
    cursor = initial_cursor = 50

    # generate waveform of pulse with different config
    pulse_waveform, duration = pulse_lib.get_waveform("TPCX", time_slots, cursor, config)
    cursor += duration

    # plot waveform
    plt.plot(time_slots, np.real(pulse_waveform["control"]), ".-", label="control-I")
    plt.plot(time_slots, np.imag(pulse_waveform["control"]), ".-", label="control-Q")
    plt.plot(time_slots, np.real(pulse_waveform["target"]), ".-", label="target-I")
    plt.plot(time_slots, np.imag(pulse_waveform["target"]), ".-", label="target-Q")
    plt.plot([initial_cursor, initial_cursor], [-1, 1], "--", c="black", label="start")
    plt.plot([cursor, cursor], [-1, 1], ":", c="black", label="end")
    plt.legend()
    plt.show()


def func7():
    # Instantiate 2 Qubit pulse
    import json
    from pprint import pprint
    import numpy as np
    import matplotlib.pyplot as plt
    from mt_pulse.pulse_preset import get_preset_pulse_library
    from mt_pulse.sequence import Sequence, SequenceConfig

    pulse_lib = get_preset_pulse_library()

    # show description of registered sequence
    config_desc = pulse_lib.get_description()
    pprint(config_desc)

    # qubit sequence
    seq = Sequence(pulse_lib)
    seq.add_channel("Q0_qubit", channel_group="Q0")
    seq.add_channel("Q1_qubit", channel_group="Q1")
    seq.add_channel("Q2_qubit", channel_group="Q2")
    seq.add_channel("Q0_resonator", channel_group="Q0")
    seq.add_channel("Q1_resonator", channel_group="Q1")
    seq.add_channel("Q2_resonator", channel_group="Q2")
    seq.add_channel("Q0_cr", channel_group="Q0")
    seq.add_channel("Q2_cr", channel_group="Q2")

    seq.add_blank_command(["Q0_qubit"], 200)
    seq.add_synchronize_all_command()
    seq.add_pulse("HPI", {"qubit": "Q0_qubit"})
    seq.add_pulse("HPI", {"qubit": "Q1_qubit"})
    seq.add_pulse("HPI", {"qubit": "Q2_qubit"})
    seq.add_synchronize_command(["Q0_qubit", "Q1_qubit", "Q2_qubit"])
    seq.add_pulse("TPCX", {"control": "Q0_cr", "target": "Q1_qubit"})
    seq.add_pulse("TPCX", {"control": "Q2_cr", "target": "Q1_qubit"})
    seq.add_synchronize_command(["Q1_qubit", "Q1_resonator"])
    seq.add_capture_command(
        [
            "Q1_resonator",
        ]
    )
    seq.add_pulse("MEAS", {"resonator": "Q1_resonator"})
    seq.add_synchronize_all_command()
    seq.add_blank_command(["Q1_resonator"], 200)
    seq.add_synchronize_all_command()

    # sequence is json serializable
    dump_str = json.dumps(seq.to_json_dict())
    seq = Sequence.from_json_dict(json.loads(dump_str))
    dump_str2 = json.dumps(seq.to_json_dict())
    assert dump_str == dump_str2

    # get variables of Sequence
    config = seq.get_config()
    pprint(config)

    # sequence config is json serializable
    dump_str = json.dumps(config.to_json_dict())
    config = SequenceConfig.from_json_dict(json.loads(dump_str))
    dump_str2 = json.dumps(config.to_json_dict())
    assert dump_str == dump_str2

    # get sequence length
    capture_duration = 200
    length = seq.get_duration(config, capture_duration)
    delta_time = 2
    time_slots = np.arange(0, length, delta_time)

    # get waveform
    waveform_dict, capture_point = seq.get_waveform(time_slots, config)
    idx = 0
    for channel in waveform_dict:
        waveform = waveform_dict[channel]
        plt.plot(time_slots, -2 * idx + np.real(waveform), ".-", color="r", markersize=2, linewidth=1)
        plt.plot(time_slots, -2 * idx + np.imag(waveform), ".-", color="b", markersize=2, linewidth=1)
        if idx != 0:
            plt.plot(
                [min(time_slots), max(time_slots)], [-2 * idx + 1, -2 * idx + 1], "-", c="black", alpha=1.0, linewidth=1
            )

        point_list = capture_point[channel]
        for point in point_list:
            plt.fill_between(
                [point, point + capture_duration],
                [-2 * idx + 1, -2 * idx + 1],
                y2=[-2 * idx - 1, -2 * idx - 1],
                color="black",
                alpha=0.1,
            )
        idx += 1
    plt.xlim(min(time_slots), max(time_slots))
    plt.ylim(-2 * idx + 1, 1)
    plt.yticks(-np.arange(len(waveform_dict.keys())) * 2, waveform_dict.keys())
    plt.grid(which="major", color="black", linestyle="-", alpha=0.2)
    plt.grid(which="minor", color="black", linestyle="-", alpha=0.2)
    plt.xlabel("Time [ns]")
    plt.tight_layout()
    plt.show()


func1()
func2()
func3()
func4()
func5()
func6()
func7()
