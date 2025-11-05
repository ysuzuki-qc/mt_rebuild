# NOTE on frequency setting

## Typical values in RIKEN's chip

Resonator frequency: 6.0 GHz - 6.5 GHz 
Qubit Freuqency: 3.6 GHz - 4.8 GHz

## QuEL Spec and Control conventions

## Manual
- See the following URL for low-freqeuncy models (QuEL1 SE 2-8GHz Model)
- https://github.com/quel-inc/quelware/blob/main/reference_manuals/Quel1seRiken8ReferenceManual.md

## Resonator / JPA-pump AWG

### QuEL port and output band
- QuEL Port means physical connector in the front of QuEL electronics.
- QuEL Port #0, #1 ports are assigned to read-in and read-out.
- QuEL Port #2 is used for control JPA pump.
- These ports can output frequencies in range (5.8 GHz, 8.0 GHz).

### AWG
- Each QuEL port has one arbitrary-waveform-generator (AWG).
- Each AWG is 500 MSample/sec.
  - This means, we can synthesize IQ waveform in the range (-250 MHz, +250 MHz).
  - The band is effectively limited by (-200 MHz, +200 MHz) due to limit.
  - We denote `AWG_bandwidth = 400 MHz`

### NCO
- Each port has a pair of two-types of numerically-controlled-oscillator (NCO).
  - NCO can generate digital high-frequency siginals in digital manner.
- One is fine-NCO (FNCO) and the other is coarse NCO (CNCO).
  - The frequency of FNCO can be chosen from (-1 GHz, +1 GHz), but recommended range is (-850 MHz, +850 MHz).
    - This restriciton is typically satisfied and not checked
  - The frequency of CNCO can be chosen from (0 GHz, 6 GHz), but recommended range is (500 MHz, 6000 MHz).
    - This restriction is typically satisfied and not checked
  - The freuqency of Both NCO must be an integer-mutiple of 12GHz/(2^9) = 23.4375 MHz.
    - We denote `NCO_freq_step = 12 GHz / (2^9)`
- The output of AWG is digitally combined with FNCO and CNCO.
  - Suppose we upload sine-wave functions with frequency `f_AWG` to AWG.
    - We must satisfy `-AWG_bandwidth/2 < f_AWG < AWG_bandwidth/2`
  - The output frequency after combine of `f_digital = f_AWG + f_FNCO + f_CNCO`

### LO
- Each QuEL port has a single local-oscillator (LO).
- The output of AWG-NCO is combined with LO with analog mixers.
  - Suppose the frequency of LO is `f_LO`.
  - Then, a mixed signal has two components.
    - upper-side-band (USB): `f_LO + f_digital`
    - lower-side-band (LSB): `f_LO - f_digital`
  - We choose one of them, and the other is filtered out.

### Mutiplexing for resonators
- RIKEN's chip assumes a single set of (AWG-CNCO-FNCO-LO) will manage four readout resonators.
- Suppose frequencies of four resonators are  `f_R0, f_R1, f_R2, f_R3`.
  - To this mutiplexing, `max(f_Ri) - min(f_Ri)` must be smaller than the `AWG_bandwidth`.
- Thus, we choose four AWG frequencies `f_AWG0, f_AWG1, f_AWG2, f_AWG3`, and each of them are targeted to `f_R0, f_R1, f_R2, f_R3`, respectively.
  - Suppose we perform time-domain measurement
    - We need to modulate upload waveform by `f_AWGi` and download waveform by `-f_AWGi`.
  - Suppose we perform averaging on the download waveform `[s0, s1, ...]` with window `[w0, w1, ...]` as `V = \sum_i wi si`.
    - We need to modulate upload averaging window by `-f_AWgi`

### Variables and conventions
- resonators `f_Ri`
- LO `f_LO`: 8.5 GHz is used as a fixed value. We use LSB for controls.
- CNCO `f_CNCO`: chosen according to resonators.
- FNCO `f_FNCO`: 0 GHz is used as a fixed value, i.e., FNCO is not used.
- AWG: `f_AWGi`: is used for synthesizing waveform according to the i-th resonators f_Ri

### Equations and restrictions

- `f_LO - (f_AWGi + f_FNCO + f_CNCO) = f_Ri`
- `f_FNCO, f_CNCO` must be mutiple of `NCO_freq_step`
- `-AWG_bandwidth/2 <= f_AWGi <= AWG_bandwidth/2`

### How to determine frequencies
- `f_LO = 8.5 GHz`
- `f_FNCO = 0 GHz`
- `f_CNCO = appriximate_with_integer_mutiple(f_LO - mean([f_R0, f_R1, f_R2, f_R3]), step = NCO_freq_step)`
- `f_AWGi = f_LO - f_FNCO - f_Ri`
- `assert(-AWG_bandwidth/2 <= f_AWGi <= AWG_bandwidth/2)`

- NOTE: Since typical readout only emits a long flattop pulse (longer than at least 100 ns), the bandwidth of awg signal is a few tens of MHz.

## Qubit control AWG

### QuEL port and output band
- QuEL Port means physical connector in the front of QuEL electronics.
- QuEL Port #6,#7,#8,#9 are assigned to control qubits.
- These ports can output frequencies in range (2.0 GHz, 5.8 GHz).
- The number of AWGs is denoted with `num_dac_channel`.

### AWG
- QuEL port #6,#9 has one AWG, and #7,#8 has three AWGs.
- The properties of AWG is the same as resonator/JPA

### NCO
- QuEL Port #6,#9 have one FNCO and one CNCO.
- QuEL Port #7,#8 have three FNCOs and one CNCO.
  - Each FNCO is assigned to corresponding AWG, i.e., there are three pairs of AWG,FNCO with shared CNCO
  - FNCO frequencies must be within 1200 MHz, i.e, `max([f_FNCO0, f_FNCO1, f_FNCO2]) - min([f_FNCO0, f_FNCO1, f_FNCO2]) < 1200 MHz`
  - We denote this value `FNCO_range_limit = 1200 MHz`
- The properties of AWG is the same as resonator/JPA except for the number of FNCOs.

### LO
- Qubit control port does not have LO.
- The output frequency after combine `f_digital = f_AWG + f_FNCO + f_CNCO` is directly emitted.

### Mutiplexing for cross resonance
- #6,#9: these ports are intended to manage the resonant frequency of a single qubit `f_Q`.
  - We should choose `f_AWG + f_FNCO + f_CNCO = f_Q`
- #7,#8: these ports are intended to manage five qubit requencies with three AWG and FNCO. 
  - The three AWGs need to control these five frequencies
    - the resonant frequency of a directly connected qubit: `f_Q`
    - the resonant frequency of a neighboring qubits `f_CR0, f_CR1, f_CR2, f_CR3`
  - These ports need to cover these five frequencies with three AWG-FNCO and one CNCO.
    - Thus, we need to map five frequencies to three DACs. This procedure is called freuqnecy grouping.
      - ch0: `fg0 = [f_Q]`
      - ch1: `fg1 = [f_Q0, f_Q1]`
      - ch2: `fg2 = [f_Q2, f_Q3]`
    - Suppose a full-bandwidth of control pulse is `control_bandwidth_margin`.
      - If we use `10 ns` Gaussian pulse, the `control_bandwidth_margine` would be about two-sigma of `1/(10ns) * 2 = 200 MHz`
    - Then, each channel group must satisfy the following conditions for each AWG/FNCO index `i`.
      - `max(fgi) + control_bandwidth_margin/2 < f_CNCO + f_FNCOi + AWG_bandwidth/2`
      - `min(fgi) - control_bandwidth_margin/2 > f_CNCO + f_FNCOi - AWG_bandwidth/2`

### Variables and conventions
- For #6, #9
  - Qubits `f_Q`:qubit frequency
  - CNCO `f_CNCO`: chosen according to resonators.
  - FNCO `f_FNCO`: typically not used
  - AWG: `f_AWG`: modulation of qubit control waveform
- For #7, #8
  - Qubits `f_Qi`: `i=0,1,2,3,4` for #6 and #8
  - Freuqency grouping `gr: [0,1,2,3,4] -> [0,1,2]`: `i`-th qubit frequency is managed by `gr(i)`-th AWG.
  - CNCO `f_CNCO`: chosen according to resonators.
  - FNCO `f_FNCOi`: chosen according to frequency group (`i=0` for #6 and #9, and `i=0,1,2` for #6 and #8)
  - AWG: `f_AWGi`: modulation of -th qubit control waveform, including CRs `i=0,1,2,3,4`

### Equations and restrictions
- For #6, #9
  - `f_AWG + f_FNCO + f_CNCO= f_Q`
  - `f_FNCO, f_CNCO` must be mutiple of `NCO_freq_step`
  - `-AWG_bandwidth/2 <= f_AWG <= AWG_bandwidth/2`
- For #7, #8
  - `f_AWGi + f_FNCO_gr(i) + f_CNCO = f_Qi`
  - `f_FNCOi, f_CNCO` must be mutiple of `NCO_freq_step`
  - `-AWG_bandwidth/2 <= f_AWGi <= AWG_bandwidth/2`
  - `max(f_FNCOi) - min(f_FNCOi) < FNCO_range_limit`

### How to determine frequencies
- For #6, #9 (if `num_dac_channel=1` and the number of managing frequency is 1)
  - `f_FNCO = 0 GHz`
  - `f_CNCO = appriximate_with_integer_mutiple(f_Q, step = NCO_freq_step)`
  - `f_AWG = f_Q - f_FNCO`
- For #7, #9 (if `num_dac_channel>1` and the number of managinc frequency is NO MORE THAN `num_dac_channel`)
  - Determing grouping `gr'
    - If `num_dac_channel >= num_waveform`, we use `gr(i)=i` (one-to-one correspondence)
    - If `num_dac_channel < num_waveform`, we find channel grouping with bisectional search so that the available channel bandwidth becomes largest.
  - `f_CNCO = appriximate_with_integer_mutiple(mean(f_Qi), step = NCO_freq_step)`
  - `f_FNCOi = appriximate_with_integer_mutiple(mean(fgi) - f_CNCO, step = NCO_freq_step)`
  - `f_AWGi = f_Qi - f_CNCO - f_FNCO_gr(i)`
  - `assert(max(f_FNCOi) - min(f_FNCOi) < FNCO_range_limit)`
- NOTE: Since typical readout only emits a long flattop pulse (longer than at least 100 ns), the bandwidth of awg signal is a few tens of MHz.

