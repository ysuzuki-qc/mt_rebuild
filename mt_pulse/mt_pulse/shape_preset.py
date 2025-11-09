import sympy as sp
from mt_pulse.shape import Shape
from mt_pulse.shape_library import ShapeLibrary


def blank() -> Shape:
    zero = sp.Float(0)
    width = sp.Symbol("width")

    name = "blank"
    shape = Shape(
        name=name,
        shape_expr=zero,
        progress_time_ns=width,
    )
    return shape


def gaussian() -> Shape:
    zero = sp.Float(0)
    t = sp.Symbol("t")
    width = sp.Symbol("width")
    amplitude = sp.Symbol("amplitude")
    phase = sp.Symbol("phase")

    name = "gaussian"
    inv_var = 4.0 * sp.log(2.0) / width**2
    shape_gaussian: sp.Expr = sp.exp(-inv_var * t**2)
    coef_phase: sp.Expr = sp.exp(1.0j * phase)
    shape = amplitude * shape_gaussian * coef_phase
    shape = Shape(
        name=name,
        shape_expr=shape,
        progress_time_ns=zero,
    )
    return shape


def gaussian_drag() -> Shape:
    zero = sp.Float(0)
    t = sp.Symbol("t")
    width = sp.Symbol("width")
    amplitude = sp.Symbol("amplitude")
    phase = sp.Symbol("phase")
    drag = sp.Symbol("drag")

    name = "gaussian_drag"
    inv_var = 4.0 * sp.log(2.0) / width**2
    shape_gaussian: sp.Expr = sp.exp(-inv_var * t**2)
    shape_drag: sp.Expr = -1.0j * drag * sp.diff(shape_gaussian, t)
    coef_phase: sp.Expr = sp.exp(1.0j * phase)
    shape = amplitude * (shape_gaussian + shape_drag) * coef_phase
    shape = Shape(
        name=name,
        shape_expr=shape,
        progress_time_ns=zero,
    )
    return shape


def flattop() -> Shape:
    t = sp.Symbol("t")
    width = sp.Symbol("width")
    amplitude = sp.Symbol("amplitude")
    phase = sp.Symbol("phase")

    name = "flattop"
    coef_phase: sp.Expr = sp.exp(1.0j * phase)
    shape = sp.Piecewise(
        (amplitude * coef_phase, sp.And(0 < t, t < width)),
        (0, True),
    )
    shape = Shape(
        name=name,
        shape_expr=shape,
        progress_time_ns=width,
    )
    return shape


def flattop_cosrise() -> Shape:
    t = sp.Symbol("t")
    width = sp.Symbol("width")
    amplitude = sp.Symbol("amplitude")
    risetime = sp.Symbol("risetime")
    phase = sp.Symbol("phase")

    name = "flattop_cosrise"
    coef_phase: sp.Expr = sp.exp(1.0j * phase)
    shape = coef_phase * sp.Piecewise(
        (
            (1.0 - sp.cos((t + risetime / 2) / risetime * sp.pi)) / 2 * amplitude,
            sp.And(-risetime / 2 < t, t < sp.Min(risetime / 2, width / 2)),
        ),
        (
            (1.0 - sp.cos((width + risetime / 2 - t) / risetime * sp.pi)) / 2 * amplitude,
            sp.And(sp.Max(width - risetime / 2, width / 2) < t, t < width + risetime / 2),
        ),
        (amplitude, sp.And(0 < t, t < width)),
        (0, True),
    )
    shape = Shape(
        name=name,
        shape_expr=shape,
        progress_time_ns=width,
    )
    return shape


def get_preset_shape_library() -> ShapeLibrary:
    shape_lib = ShapeLibrary()
    shape_list = [blank(), gaussian(), gaussian_drag(), flattop(), flattop_cosrise()]
    for shape in shape_list:
        shape_lib.add_shape(shape)
    return shape_lib
