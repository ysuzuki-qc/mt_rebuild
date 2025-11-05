# mt_quel_util

Utility functions to handle quel devices so that there is loose restrictions.

## Overview

This library provides utilities to determine how to multiplex virtual channels to physical channels under the restriction of DAC channels and electronics bandwidth.

- Cope with discrete NCO frequencies
  - assign qubit/resnator/jpa channels to DACs according to specified LO and sidebands so that the available pulse bandwidth becomes maximum
  - modulate upload waveforms and averaging window coefficients according to modulation frequency
  - demodulate download waveforms and samples according to demodulation frequency
  - choose FIR filter coefficients for readout demultiplex

- Cope with discrete time window positions
  - adjust capture window position and averaging window coefficients so that discritized position will be concealed
  - restore original position for readout waveform 

