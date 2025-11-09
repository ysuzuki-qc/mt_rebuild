import numpy as np
from tunits.units import ns
from mt_util.tunits_util import FrequencyType, TimeType
from mt_quel_util.constant import InstrumentConstantQuEL


def get_gaussian_FIR_coefficients(
    frequency: FrequencyType, constant: InstrumentConstantQuEL, sigma: TimeType = 6 * ns
) -> np.ndarray:
    ADC_BB = constant.ADCBB_sampling_freq
    num_band = constant.ACQ_max_fir_coeff
    if -0.5 * ADC_BB >= frequency or 0.5 * ADC_BB <= frequency:
        raise ValueError(f"Baseband frequency too large, ADCBB_sampling_freq: {ADC_BB} bb_frequency: {frequency}")

    band_step = ADC_BB / num_band
    band_idx = np.rint(frequency / band_step).astype(int)
    band_center = band_step * band_idx

    x = (np.arange(num_band) - (num_band - 1) / 2) / ADC_BB["GHz"]
    gaussian = np.exp(-0.5 * x**2 / (sigma["ns"] ** 2))
    phase_factor = 2 * np.pi * band_center["GHz"] * x
    coeffs = gaussian * np.exp(-1j * phase_factor) * (1 - 1e-3)
    return coeffs
