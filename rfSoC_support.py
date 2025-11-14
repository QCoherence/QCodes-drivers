import sys

import numpy as np

sys.path.append("C:/QCodes drivers and scripts/Drivers")


# qcodes.config.subscription.default_subscribers = ["Plottr"]
import sys

import numpy as np

sys.path.append("C:/QCodes drivers and scripts/Scripts/Arpit/Modules")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from general_functions import find_nearest
from progress_barV2 import bar


def optimize_IQ_balance(
    rfsoc_device,
    nu,
    nu_det_offset,
    display_plots=False,
    pump_sig_ch=[1, 2],
    amp=0.05,
    dc_offset_I=8,
    dc_offset_Q=6,
    active_mode="lower",
    acq_length=10,
    adc_start=1.0,
):
    mem_seq_display = rfsoc_device.display_sequence
    rfsoc_device.display_sequence = False

    phase_vec = np.arange(0, 360, 10)
    data_down = np.array([])
    data_up = np.array([])
    num_repetitions = 10_000

    [ch_1, ch_2] = pump_sig_ch

    for phase_offset in phase_vec:
        param_sin_I = {
            "amp": amp,
            "freq": nu,
            "dc_offset": dc_offset_I * 1e-3,
            "phase_offset": 0,
        }

        param_sin_Q = {
            "amp": amp,
            "freq": nu,
            "dc_offset": dc_offset_Q * 1e-3,
            "phase_offset": np.pi * phase_offset / 180,
        }

        pulse_sin = dict(
            label="signal+pump",
            module="DAC",
            channel=ch_1,
            mode="sin",
            start=0,
            length=acq_length + 2,
            param=param_sin_I,
            parent=None,
        )

        record_sin = dict(
            label="record_both",
            module="ADC",
            channel=1,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        pulse_sin2 = dict(
            label="signal+pump2",
            module="DAC",
            channel=ch_2,
            mode="sin",
            start=0,
            length=acq_length + 2,
            param=param_sin_Q,
            parent=None,
        )

        record_sin2 = dict(
            label="record_both2",
            module="ADC",
            channel=2,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        pulses = pd.DataFrame()
        pulses = pulses.append(pulse_sin, ignore_index=True)
        pulses = pulses.append(record_sin, ignore_index=True)
        pulses = pulses.append(pulse_sin2, ignore_index=True)
        pulses = pulses.append(record_sin2, ignore_index=True)

        rfsoc_device.pulses = pulses

        rfsoc_device.acquisition_mode("IQ")
        rfsoc_device.ADC1.fmixer(nu - nu_det_offset)  # MHz
        rfsoc_device.ADC2.fmixer(nu + nu_det_offset)  # MHz
        rfsoc_device.freq_sync(1e6)
        rfsoc_device.ADC1.status("ON")
        rfsoc_device.ADC2.status("ON")
        rfsoc_device.output_format("BIN")
        rfsoc_device.n_rep(num_repetitions)

        rfsoc_device.process_sequencing()

        data_raw = rfsoc_device.ADC_power_dBm()[:2]

        data_down = np.append(data_down, data_raw[0])
        data_up = np.append(data_up, data_raw[1])

    if display_plots:
        fig = plt.figure(figsize=(16, 12))
        ax3 = fig.add_subplot(221)
        ax3.plot(phase_vec, data_down, label="ch1", marker=".", color="orange")
        ax3.plot(phase_vec, data_up, label="ch2", marker=".", color="blue")
        plt.legend()
        plt.xlabel("Phase [degree]", fontsize=14)
        plt.ylabel("PSD (dBm)", fontsize=14)
        plt.grid()
        plt.show()

        # plt.figure(figsize=(14, 10), dpi= 80) #facecolor='w', edgecolor='k'
        # x_label='Phase [degree]'
        # y_label='PSD [dBm]'

        # plt.rc('axes', labelsize=10)    # fontsize of the x and y labels
        # plt.rc('xtick', labelsize=12)    # fontsize of the tick labels
        # plt.rc('ytick', labelsize=12)    # fontsize of the tick labels
        # plt.rc('grid', linestyle="--")
        # plt.grid(True)

        # plt.plot(phase_vec,data_down,label='data_ch1')
        # plt.plot(phase_vec,data_up,label='data_ch2')

        # plt.xlabel(x_label, size=14)
        # plt.ylabel(y_label, size=14)

        # plt.legend(fontsize = 12)
        # plt.show()

    optimal_phase_1 = phase_vec[find_nearest(data_up, np.min(data_up))]

    phase_vec = np.arange(optimal_phase_1 - 5, optimal_phase_1 + 5, 1)
    data_down = np.array([])
    data_up = np.array([])

    for phase_offset in phase_vec:
        param_sin_I = {
            "amp": amp,
            "freq": nu,
            "dc_offset": dc_offset_I * 1e-3,
            "phase_offset": 0,
        }

        param_sin_Q = {
            "amp": amp,
            "freq": nu,
            "dc_offset": dc_offset_Q * 1e-3,
            "phase_offset": np.pi * phase_offset / 180,
        }

        pulse_sin = dict(
            label="signal+pump",
            module="DAC",
            channel=1,
            mode="sin",
            start=0,
            length=acq_length + 2,
            param=param_sin_I,
            parent=None,
        )

        record_sin = dict(
            label="record_both",
            module="ADC",
            channel=1,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        pulse_sin2 = dict(
            label="signal+pump2",
            module="DAC",
            channel=2,
            mode="sin",
            start=0,
            length=acq_length + 2,
            param=param_sin_Q,
            parent=None,
        )

        record_sin2 = dict(
            label="record_both2",
            module="ADC",
            channel=2,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        pulses = pd.DataFrame()
        pulses = pulses.append(pulse_sin, ignore_index=True)
        pulses = pulses.append(record_sin, ignore_index=True)
        pulses = pulses.append(pulse_sin2, ignore_index=True)
        pulses = pulses.append(record_sin2, ignore_index=True)

        rfsoc_device.pulses = pulses

        rfsoc_device.acquisition_mode("IQ")
        rfsoc_device.ADC1.fmixer(nu - nu_det_offset)  # MHz
        rfsoc_device.ADC2.fmixer(nu + nu_det_offset)  # MHz
        rfsoc_device.freq_sync(1e6)
        rfsoc_device.ADC1.status("ON")
        rfsoc_device.ADC2.status("ON")
        rfsoc_device.output_format("BIN")
        rfsoc_device.n_rep(num_repetitions)

        rfsoc_device.process_sequencing()

        data_raw = rfsoc_device.ADC_power_dBm()[:2]

        data_down = np.append(data_down, data_raw[0])
        data_up = np.append(data_up, data_raw[1])

    if display_plots:
        fig = plt.figure(figsize=(16, 12))
        ax3 = fig.add_subplot(221)
        ax3.plot(phase_vec, data_down, label="ch1", marker=".", color="orange")
        ax3.plot(phase_vec, data_up, label="ch2", marker=".", color="blue")
        plt.legend()
        plt.xlabel("Phase [degree]", fontsize=14)
        plt.ylabel("PSD (dBm)", fontsize=14)
        plt.grid()
        plt.show()

        # plt.figure(figsize=(14, 10), dpi= 80) #facecolor='w', edgecolor='k'
        # x_label='Phase [degree]'
        # y_label='PSD [dBm]'

        # plt.rc('axes', labelsize=10)    # fontsize of the x and y labels
        # plt.rc('xtick', labelsize=12)    # fontsize of the tick labels
        # plt.rc('ytick', labelsize=12)    # fontsize of the tick labels
        # plt.rc('grid', linestyle="--")
        # plt.grid(True)

        # plt.plot(phase_vec,data_down,label='data_ch1')
        # plt.plot(phase_vec,data_up,label='data_ch2')

        # plt.xlabel(x_label, size=14)
        # plt.ylabel(y_label, size=14)

        # plt.legend(fontsize = 12)
        # plt.show()

    rfsoc_device.display_sequence = mem_seq_display

    return phase_vec[find_nearest(data_up, np.min(data_up))]


class gain_signal_idler_cls:
    def __init__(self, rfsoc_device, MW_source_gen_sig, MW_source_det):
        self.rfsoc_device = rfsoc_device
        self.amp_if = 0.15
        self.nu_if = 271
        self.delta = 220

        self.MW_source_det = MW_source_det
        self.MW_source_gen_sig = MW_source_gen_sig
        self.nu_det_offset_idl = 20
        self.nu_det_offset_sig = 36
        self.nu_p = 4

        self.phase_offset_if = 0  # degrees
        self.phase_offset_sig = 0  # degrees
        self.phase_offset_idl = 0  # degrees
        self.dc_offset_I_pump = None
        self.dc_offset_Q_pump = None
        self.dc_offset_I_weak = None
        self.dc_offset_Q_weak = None

        self.amp_sig = 0.01 * self.amp_if / 0.15
        self.acq_length = 29.0
        self.wait_time = 1.0
        self.wait_between_pulses = 0
        self.num_rep = 10_000

        self.ch_out_weak_I = None
        self.ch_out_weak_Q = None
        self.ch_out_pump_I = None
        self.ch_out_pump_Q = None

        self.ch_pump_cancel = None
        self.optimal_amp_if_cancel = 0.5
        self.optimal_phase = 92

    def g(self):
        ch_out_weak_I = self.ch_out_weak_I
        ch_out_weak_Q = self.ch_out_weak_Q
        ch_out_pump_I = self.ch_out_pump_I
        ch_out_pump_Q = self.ch_out_pump_Q
        ch_pump_cancel = self.ch_pump_cancel

        nu_if = self.nu_if
        delta = self.delta
        dc_offset_I_pump = self.dc_offset_I_pump
        dc_offset_Q_pump = self.dc_offset_Q_pump
        dc_offset_I_weak = self.dc_offset_I_weak
        dc_offset_Q_weak = self.dc_offset_Q_weak
        phase_offset_if = self.phase_offset_if
        phase_offset_sig = self.phase_offset_sig
        phase_offset_idl = self.phase_offset_idl
        acq_length = self.acq_length
        wait_time = self.wait_time
        wait_between_pulses = self.wait_between_pulses
        num_rep = self.num_rep

        nu_sig = nu_if + delta
        nu_idl = nu_if - delta

        amp_weak = self.amp_sig
        amp_if = self.amp_if
        amp_cancel = self.optimal_amp_if_cancel
        phase_cancel = self.optimal_phase
        rfsoc_device = self.rfsoc_device

        mem_display_sequence = rfsoc_device.display_sequence
        rfsoc_device.display_sequence = False

        adc_start = wait_time / 2

        for gain_mode in ["idl", "sig"]:
            if gain_mode == "idl":
                nu_weak = nu_idl
                phase_offset_weak = phase_offset_idl

            else:
                nu_weak = nu_sig
                phase_offset_weak = phase_offset_sig

            param_sin_I_pump = {
                "amp": amp_if,
                "freq": nu_if,
                "dc_offset": dc_offset_I_pump * 1e-3,
                "phase_offset": 0,
            }

            param_sin_Q_pump = {
                "amp": amp_if,
                "freq": nu_if,
                "dc_offset": dc_offset_Q_pump * 1e-3,
                "phase_offset": np.pi * phase_offset_if / 180,
            }

            param_sin_I_pump_null = {
                "amp": 0,
                "freq": nu_if,
                "dc_offset": dc_offset_I_pump * 1e-3,
                "phase_offset": 0,
            }

            param_sin_Q_pump_null = {
                "amp": 0,
                "freq": nu_if,
                "dc_offset": dc_offset_Q_pump * 1e-3,
                "phase_offset": np.pi * phase_offset_if / 180,
            }

            param_sin_I_weak = {
                "amp": amp_weak,
                "freq": nu_weak,
                "dc_offset": dc_offset_I_weak * 1e-3,
                "phase_offset": 0,
            }

            param_sin_Q_weak = {
                "amp": amp_weak,
                "freq": nu_weak,
                "dc_offset": dc_offset_Q_weak * 1e-3,
                "phase_offset": np.pi * phase_offset_weak / 180,
            }

            pulse_pump_I = dict(
                label="pumpI",
                module="DAC",
                channel=ch_out_pump_I,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_I_pump,
                parent=None,
            )

            pulse_pump_Q = dict(
                label="pumpQ",
                module="DAC",
                channel=ch_out_pump_Q,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_Q_pump,
                parent=None,
            )

            pulse_weak_I = dict(
                label="weakI",
                module="DAC",
                channel=ch_out_weak_I,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_I_weak,
                parent=None,
            )

            pulse_weak_Q = dict(
                label="weakQ",
                module="DAC",
                channel=ch_out_weak_Q,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_Q_weak,
                parent=None,
            )

            record_both = dict(
                label="record_both",
                module="ADC",
                channel=1,
                mode="raw",
                start=adc_start,
                length=acq_length,
                param=None,
                parent=None,
            )

            record_both2 = dict(
                label="record_both2",
                module="ADC",
                channel=2,
                mode="raw",
                start=adc_start,
                length=acq_length,
                param=None,
                parent=None,
            )

            pulse_pump_I2 = dict(
                label="pumpI2",
                module="DAC",
                channel=ch_out_pump_I,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_I_pump_null,
                parent="pumpI",
            )

            pulse_pump_Q2 = dict(
                label="pumpQ2",
                module="DAC",
                channel=ch_out_pump_Q,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_Q_pump_null,
                parent="pumpI",
            )

            pulse_weak_I2 = dict(
                label="weakI2",
                module="DAC",
                channel=ch_out_weak_I,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_I_weak,
                parent="pumpI",
            )

            pulse_weak_Q2 = dict(
                label="weakQ2",
                module="DAC",
                channel=ch_out_weak_Q,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_Q_weak,
                parent="pumpI",
            )

            record_weak = dict(
                label="record_signal",
                module="ADC",
                channel=1,
                mode="raw",
                start=adc_start,
                length=acq_length,
                param=None,
                parent="pumpI",
            )

            record_weak2 = dict(
                label="record_signal2",
                module="ADC",
                channel=2,
                mode="raw",
                start=adc_start,
                length=acq_length,
                param=None,
                parent="pumpI",
            )

            pulses = pd.DataFrame()
            pulses = pulses.append(pulse_pump_I, ignore_index=True)
            pulses = pulses.append(pulse_pump_Q, ignore_index=True)
            pulses = pulses.append(pulse_weak_I, ignore_index=True)
            pulses = pulses.append(pulse_weak_Q, ignore_index=True)
            pulses = pulses.append(record_both, ignore_index=True)
            pulses = pulses.append(record_both2, ignore_index=True)
            pulses = pulses.append(pulse_pump_I2, ignore_index=True)
            pulses = pulses.append(pulse_pump_Q2, ignore_index=True)
            pulses = pulses.append(pulse_weak_I2, ignore_index=True)
            pulses = pulses.append(pulse_weak_Q2, ignore_index=True)
            pulses = pulses.append(record_weak, ignore_index=True)
            pulses = pulses.append(record_weak2, ignore_index=True)

            rfsoc_device.pulses = pulses

            rfsoc_device.acquisition_mode("IQ")
            rfsoc_device.ADC1.decfact(1)
            rfsoc_device.ADC2.decfact(1)
            rfsoc_device.freq_sync(1e6)
            rfsoc_device.ADC1.fmixer(nu_sig)
            rfsoc_device.ADC2.fmixer(nu_idl)
            rfsoc_device.ADC1.status("ON")
            rfsoc_device.ADC2.status("ON")
            rfsoc_device.output_format("BIN")
            rfsoc_device.n_rep(num_rep)
            rfsoc_device.process_sequencing()

            if gain_mode == "idl":
                data_idl = np.array(rfsoc_device.ADC_power_dBm()[0:2])

            else:
                data_sig = np.array(rfsoc_device.ADC_power_dBm()[0:2])

        gain_sig = data_sig[0, 0] - data_sig[0, 1]
        gain_idl = data_idl[1, 0] - data_idl[1, 1]

        gain_sig_with_idler_input = data_idl[0, 0] - data_idl[0, 1]
        gain_idl_with_sig_input = data_sig[1, 0] - data_sig[1, 1]

        data_save = np.array(
            [
                np.array([gain_sig, gain_idl]),
                np.array([gain_sig_with_idler_input, gain_idl_with_sig_input]),
                np.array([data_sig[0, 0], data_sig[0, 1]]),
                np.array([data_sig[1, 0], data_sig[1, 1]]),
                np.array([data_idl[0, 0], data_idl[0, 1]]),
                np.array([data_idl[1, 0], data_idl[1, 1]]),
            ]
        )

        rfsoc_device.display_sequence = mem_display_sequence

        return data_save

    def g_v2_lo_freq_sweep(self):
        ch_out_weak_I = self.ch_out_weak_I
        ch_out_weak_Q = self.ch_out_weak_Q
        ch_out_pump_I = self.ch_out_pump_I
        ch_out_pump_Q = self.ch_out_pump_Q
        ch_pump_cancel = self.ch_pump_cancel

        nu_p = self.nu_p
        nu_det_offset_idl = self.nu_det_offset_idl
        nu_det_offset_sig = self.nu_det_offset_sig
        MW_source_det = self.MW_source_det
        MW_source_gen_sig = self.MW_source_gen_sig

        nu_if = self.nu_if
        delta = self.delta
        dc_offset_I_pump = self.dc_offset_I_pump
        dc_offset_Q_pump = self.dc_offset_Q_pump
        dc_offset_I_weak = self.dc_offset_I_weak
        dc_offset_Q_weak = self.dc_offset_Q_weak
        phase_offset_if = self.phase_offset_if
        phase_offset_sig = self.phase_offset_sig
        phase_offset_idl = self.phase_offset_idl
        acq_length = self.acq_length
        wait_time = self.wait_time
        wait_between_pulses = self.wait_between_pulses
        num_rep = self.num_rep

        nu_sig = nu_if + delta
        nu_idl = nu_if - delta

        amp_weak = self.amp_sig
        amp_if = self.amp_if
        amp_cancel = self.optimal_amp_if_cancel
        phase_cancel = self.optimal_phase
        rfsoc_device = self.rfsoc_device

        mem_display_sequence = rfsoc_device.display_sequence
        rfsoc_device.display_sequence = False

        adc_start = wait_time / 2

        for gain_mode in ["idl", "sig"]:
            if gain_mode == "idl":
                nu_weak = nu_if
                phase_offset_weak = phase_offset_idl
                MW_source_gen_sig.frequency(nu_p * 1e9 + nu_if * 1e6 - delta * 1e6)
                MW_source_det.frequency(
                    nu_p * 1e9 + nu_if * 1e6 - nu_det_offset_idl * 1e6 - delta * 1e6
                )

            else:
                nu_weak = nu_if
                phase_offset_weak = phase_offset_sig
                MW_source_gen_sig.frequency(nu_p * 1e9 + nu_if * 1e6 + delta * 1e6)
                MW_source_det.frequency(
                    nu_p * 1e9 + nu_if * 1e6 - nu_det_offset_sig * 1e6 + delta * 1e6
                )

            param_sin_I_pump = {
                "amp": amp_if,
                "freq": nu_if,
                "dc_offset": dc_offset_I_pump * 1e-3,
                "phase_offset": 0,
            }

            param_sin_Q_pump = {
                "amp": amp_if,
                "freq": nu_if,
                "dc_offset": dc_offset_Q_pump * 1e-3,
                "phase_offset": np.pi * phase_offset_if / 180,
            }

            # param_sin_cancel = {'amp':amp_cancel,
            #                  'freq':nu_if,
            #                  'dc_offset':0,
            #                   'phase_offset':np.pi*phase_cancel/180}

            param_sin_I_pump_null = {
                "amp": 0,
                "freq": nu_if,
                "dc_offset": dc_offset_I_pump * 1e-3,
                "phase_offset": 0,
            }

            param_sin_Q_pump_null = {
                "amp": 0,
                "freq": nu_if,
                "dc_offset": dc_offset_Q_pump * 1e-3,
                "phase_offset": np.pi * phase_offset_if / 180,
            }

            # param_sin_cancel_null = {'amp':0,
            #                  	'freq':nu_if,
            #                  	'dc_offset':0,
            #                   	'phase_offset':np.pi*phase_cancel/180}

            param_sin_I_weak = {
                "amp": amp_weak,
                "freq": nu_weak,
                "dc_offset": dc_offset_I_weak * 1e-3,
                "phase_offset": 0,
            }

            param_sin_Q_weak = {
                "amp": amp_weak,
                "freq": nu_weak,
                "dc_offset": dc_offset_Q_weak * 1e-3,
                "phase_offset": np.pi * phase_offset_weak / 180,
            }

            pulse_pump_I = dict(
                label="pumpI",
                module="DAC",
                channel=ch_out_pump_I,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_I_pump,
                parent=None,
            )

            pulse_pump_Q = dict(
                label="pumpQ",
                module="DAC",
                channel=ch_out_pump_Q,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_Q_pump,
                parent=None,
            )

            # pulse_cancel_pump = dict(label='cancel_pump',
            #                              module='DAC',
            #                              channel=ch_pump_cancel,
            #                              mode='sin',
            #                              start=0,
            #                              length=acq_length+wait_time,
            #                              param=param_sin_cancel,
            #                              parent=None)

            pulse_weak_I = dict(
                label="weakI",
                module="DAC",
                channel=ch_out_weak_I,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_I_weak,
                parent=None,
            )

            pulse_weak_Q = dict(
                label="weakQ",
                module="DAC",
                channel=ch_out_weak_Q,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_Q_weak,
                parent=None,
            )

            record_both = dict(
                label="record_both",
                module="ADC",
                channel=1,
                mode="raw",
                start=adc_start,
                length=acq_length,
                param=None,
                parent=None,
            )

            record_both2 = dict(
                label="record_both2",
                module="ADC",
                channel=2,
                mode="raw",
                start=adc_start,
                length=acq_length,
                param=None,
                parent=None,
            )

            pulse_pump_I2 = dict(
                label="pumpI2",
                module="DAC",
                channel=ch_out_pump_I,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_I_pump_null,
                parent="pumpI",
            )

            pulse_pump_Q2 = dict(
                label="pumpQ2",
                module="DAC",
                channel=ch_out_pump_Q,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_Q_pump_null,
                parent="pumpI",
            )

            # pulse_cancel_pump2 = dict(label='cancel_pump2',
            #                              module='DAC',
            #                              channel=ch_pump_cancel,
            #                              mode='sin',
            #                              start=0,
            #                              length=acq_length+wait_time,
            #                              param=param_sin_cancel_null,
            #                              parent='cancel_pump')

            pulse_weak_I2 = dict(
                label="weakI2",
                module="DAC",
                channel=ch_out_weak_I,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_I_weak,
                parent="pumpI",
            )

            pulse_weak_Q2 = dict(
                label="weakQ2",
                module="DAC",
                channel=ch_out_weak_Q,
                mode="sin",
                start=0,
                length=acq_length + wait_time,
                param=param_sin_Q_weak,
                parent="pumpI",
            )

            record_weak = dict(
                label="record_signal",
                module="ADC",
                channel=1,
                mode="raw",
                start=adc_start,
                length=acq_length,
                param=None,
                parent="pumpI",
            )

            record_weak2 = dict(
                label="record_signal2",
                module="ADC",
                channel=2,
                mode="raw",
                start=adc_start,
                length=acq_length,
                param=None,
                parent="pumpI",
            )

            pulses = pd.DataFrame()
            pulses = pulses.append(pulse_pump_I, ignore_index=True)
            pulses = pulses.append(pulse_pump_Q, ignore_index=True)
            # pulses = pulses.append(pulse_cancel_pump, ignore_index=True)
            pulses = pulses.append(pulse_weak_I, ignore_index=True)
            pulses = pulses.append(pulse_weak_Q, ignore_index=True)
            pulses = pulses.append(record_both, ignore_index=True)
            pulses = pulses.append(record_both2, ignore_index=True)
            pulses = pulses.append(pulse_pump_I2, ignore_index=True)
            pulses = pulses.append(pulse_pump_Q2, ignore_index=True)
            # pulses = pulses.append(pulse_cancel_pump2, ignore_index=True)
            pulses = pulses.append(pulse_weak_I2, ignore_index=True)
            pulses = pulses.append(pulse_weak_Q2, ignore_index=True)
            pulses = pulses.append(record_weak, ignore_index=True)
            pulses = pulses.append(record_weak2, ignore_index=True)

            rfsoc_device.pulses = pulses

            rfsoc_device.acquisition_mode("IQ")
            rfsoc_device.ADC1.decfact(1)
            rfsoc_device.ADC2.decfact(1)
            rfsoc_device.freq_sync(1e6)
            rfsoc_device.ADC1.fmixer(nu_if - nu_det_offset_sig)
            rfsoc_device.ADC2.fmixer(nu_if - nu_det_offset_idl)
            rfsoc_device.ADC1.status("ON")
            rfsoc_device.ADC2.status("ON")
            rfsoc_device.output_format("BIN")
            rfsoc_device.n_rep(num_rep)
            rfsoc_device.process_sequencing()

            if gain_mode == "idl":
                data_idl = np.array(rfsoc_device.ADC_power_dBm()[0:2])

            else:
                data_sig = np.array(rfsoc_device.ADC_power_dBm()[0:2])

        gain_sig = data_sig[0, 0] - data_sig[0, 1]
        gain_idl = data_idl[1, 0] - data_idl[1, 1]

        gain_sig_with_idler_input = data_idl[0, 0] - data_idl[0, 1]
        gain_idl_with_sig_input = data_sig[1, 0] - data_sig[1, 1]

        data_save = np.array(
            [
                np.array([gain_sig, gain_idl]),
                np.array([gain_sig_with_idler_input, gain_idl_with_sig_input]),
                np.array([data_sig[0, 0], data_sig[0, 1]]),
                np.array([data_sig[1, 0], data_sig[1, 1]]),
                np.array([data_idl[0, 0], data_idl[0, 1]]),
                np.array([data_idl[1, 0], data_idl[1, 1]]),
            ]
        )

        rfsoc_device.display_sequence = mem_display_sequence

        return data_save


class pump_cancellation_cls:
    def __init__(self, rfsoc_device, Vaunix_Att_device, Vaunix_FS_device):
        self.rfsoc_device = rfsoc_device
        self.Vaunix_Att_device = Vaunix_Att_device
        self.Vaunix_FS_device = Vaunix_FS_device

        self.display_plots = True

        self.amp_if = 0
        self.nu_if = 271
        self.delta = 220

        self.iter_depth = 2

        self.phase_range = (0, 360)
        self.phase_window_narrowing = 20  # percent of previous range
        self.phase_points = 21

        self.attn_range = (0, 50)
        self.attn_window_narrowing = 20  # percent of previous range
        self.attn_points = 21

        self.amp_if_cancel_range = (0.1, 1)
        self.amp_if_cancel_window_narrowing = 40
        self.amp_if_cancel_points = 21

        self.phase_offset_if = 0  # degrees
        self.angle_amp_if = 45  # degrees
        self.dc_offset_I_pump = 8
        self.dc_offset_Q_pump = 6
        self.dc_offset_I_weak = 0
        self.dc_offset_Q_weak = 0

        self.acq_length = 10.0
        self.wait_time = 2.0
        self.num_rep = 20

        self.dac_pump_I = 1
        self.dac_pump_Q = 2
        self.dac_weak_I = 3
        self.dac_weak_Q = 4
        self.dac_pump_cancel = 5

    def get_optimal_attn_phase(self):
        rfsoc_device = self.rfsoc_device
        Vaunix_Att_device = self.Vaunix_Att_device
        Vaunix_FS_device = self.Vaunix_FS_device

        display_plots = self.display_plots

        amp_if = self.amp_if
        nu_if = self.nu_if
        delta = self.delta

        iter_depth = self.iter_depth

        phase_range = self.phase_range
        phase_window_narrowing = self.phase_window_narrowing
        phase_points = self.phase_points

        attn_range = self.attn_range
        attn_window_narrowing = self.attn_window_narrowing
        attn_points = self.attn_points

        phase_offset_if = self.phase_offset_if
        angle_amp_if = self.angle_amp_if
        dc_offset_I_pump = self.dc_offset_I_pump
        dc_offset_Q_pump = self.dc_offset_Q_pump
        dc_offset_I_weak = self.dc_offset_I_weak
        dc_offset_Q_weak = self.dc_offset_Q_weak

        acq_length = self.acq_length
        wait_time = self.wait_time
        num_rep = self.num_rep

        mem_display_sequence = rfsoc_device.display_sequence
        mem_display_IQ_progress = rfsoc_device.display_IQ_progress
        rfsoc_device.display_sequence = False
        rfsoc_device.display_IQ_progress = False

        adc_start = wait_time / 2

        param_sin_I_pump = {
            "amp": (1 / np.sqrt(2)) * amp_if * np.cos(np.pi * angle_amp_if / 180),
            "freq": nu_if,
            "dc_offset": self.dc_offset_I_pump * 1e-3,
            "phase_offset": 0,
        }

        param_sin_Q_pump = {
            "amp": (1 / np.sqrt(2)) * amp_if * np.sin(np.pi * angle_amp_if / 180),
            "freq": nu_if,
            "dc_offset": self.dc_offset_Q_pump * 1e-3,
            "phase_offset": np.pi * phase_offset_if / 180,
        }

        param_sin_I_weak = {
            "amp": 0,
            "freq": 0,
            "dc_offset": self.dc_offset_I_weak * 1e-3,
            "phase_offset": 0,
        }

        param_sin_Q_weak = {
            "amp": 0,
            "freq": 0,
            "dc_offset": self.dc_offset_Q_weak * 1e-3,
            "phase_offset": np.pi * 0 / 180,
        }

        pulse_pump_I = dict(
            label="pumpI",
            module="DAC",
            channel=self.dac_pump_I,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_I_pump,
            parent=None,
        )

        pulse_pump_Q = dict(
            label="pumpQ",
            module="DAC",
            channel=self.dac_pump_Q,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_Q_pump,
            parent=None,
        )

        pulse_weak_I = dict(
            label="weakI",
            module="DAC",
            channel=self.dac_weak_I,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_I_weak,
            parent=None,
        )

        pulse_weak_Q = dict(
            label="weakQ",
            module="DAC",
            channel=self.dac_weak_Q,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_Q_weak,
            parent=None,
        )

        record_both = dict(
            label="record_both",
            module="ADC",
            channel=1,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        record_both2 = dict(
            label="record_both2",
            module="ADC",
            channel=2,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        pulses = pd.DataFrame()
        pulses = pulses.append(pulse_pump_I, ignore_index=True)
        pulses = pulses.append(pulse_pump_Q, ignore_index=True)
        pulses = pulses.append(pulse_weak_I, ignore_index=True)
        pulses = pulses.append(pulse_weak_Q, ignore_index=True)
        pulses = pulses.append(record_both, ignore_index=True)
        pulses = pulses.append(record_both2, ignore_index=True)

        rfsoc_device.pulses = pulses

        rfsoc_device.acquisition_mode("IQ")

        rfsoc_device.ADC1.fmixer(nu_if)
        rfsoc_device.ADC2.fmixer(nu_if)
        rfsoc_device.ADC1.decfact(1)
        rfsoc_device.ADC2.decfact(1)
        rfsoc_device.freq_sync(1e6)
        rfsoc_device.ADC1.status("ON")
        rfsoc_device.ADC2.status("ON")
        rfsoc_device.output_format("BIN")
        rfsoc_device.n_rep(num_rep)

        rfsoc_device.process_sequencing()

        for iter_n in range(iter_depth):
            # optimize phase

            phase_vec_org = np.linspace(phase_range[0], phase_range[1], phase_points)
            phase_vec = self.process_phase(phase_vec_org)
            pow_vec_0 = np.array([])
            pow_vec_1 = np.array([])
            for phase in phase_vec:
                Vaunix_FS_device.phase_shift(phase)
                pow_tmp = rfsoc_device.ADC_power_dBm()
                pow_vec_0 = np.append(pow_vec_0, pow_tmp[0][0])
                pow_vec_1 = np.append(pow_vec_1, pow_tmp[1][0])

                # IQ_data = []
                # data_out_I,data_out_Q = rfsoc_device.IQINT_AVG()
                # data_out1 = np.zeros((2, 8, 2))
                # data_out1[0][0] = data_out_I[0]
                # data_out1[1][0] = data_out_Q[0]
                # IQ_data.append(list(data_out1))
                # IQ_data = np.array(IQ_data)
                # I_ch1_on = IQ_data[:, 0, 0, 0]
                # I_ch2_on = IQ_data[:, 0, 1, 0]
                # Q_ch1_on = IQ_data[:, 1, 0, 0]
                # Q_ch2_on = IQ_data[:, 1, 1, 0]
                # Mag_ch2_on = (I_ch2_on**2 + Q_ch2_on**2)/50 ## W
                # Mag_ch2_on_dBm = 10 * np.log10(Mag_ch2_on*1e3)
                # Mag_ch1_on = (I_ch1_on**2 + Q_ch1_on**2)/50 ## W
                # Mag_ch1_on_dBm = 10 * np.log10(Mag_ch1_on*1e3)
                # pow_vec_0 = np.append(pow_vec_0,Mag_ch1_on_dBm)
                # pow_vec_1 = np.append(pow_vec_1,Mag_ch2_on_dBm)

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(
                    phase_vec_org, pow_vec_0, label="ch1", marker=".", color="orange"
                )
                ax3.plot(
                    phase_vec_org, pow_vec_1, label="ch2", marker=".", color="blue"
                )
                plt.legend()
                plt.xlabel("Phase [degree]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            phase_min = phase_vec[np.argmin(pow_vec_0)]
            Vaunix_FS_device.phase_shift(phase_min)
            phase_sweep_mag = (
                (phase_range[1] - phase_range[0]) * phase_window_narrowing / 100
            )
            if phase_sweep_mag < phase_points:
                phase_sweep_mag = phase_points
            phase_range = (
                phase_min - 0.5 * phase_sweep_mag,
                phase_min + 0.5 * phase_sweep_mag,
            )

            # optimize attn

            attn_vec = np.linspace(attn_range[0], attn_range[1], attn_points)
            pow_vec_0 = np.array([])
            pow_vec_1 = np.array([])
            for attn in attn_vec:
                if attn < 0.0:
                    attn = 0.0
                    print("attn cannot be < 0, set to be = 0")
                Vaunix_Att_device.attn(attn)
                pow_tmp = rfsoc_device.ADC_power_dBm()
                pow_vec_0 = np.append(pow_vec_0, pow_tmp[0][0])
                pow_vec_1 = np.append(pow_vec_1, pow_tmp[1][0])

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(attn_vec, pow_vec_0, label="ch1", marker=".", color="orange")
                ax3.plot(attn_vec, pow_vec_1, label="ch2", marker=".", color="blue")
                plt.legend()
                plt.xlabel("Attenuation [dB]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            attn_min = int(attn_vec[np.argmin(pow_vec_0)])
            if attn_min < 0:
                attn_min = 0
                print("attn_min cannot be < 0, set to be = 0")

            Vaunix_Att_device.attn(attn_min)
            attn_sweep_mag = (
                (attn_range[1] - attn_range[0]) * attn_window_narrowing / 100
            )
            if attn_sweep_mag < attn_points * 0.1:
                attn_sweep_mag = attn_points * 0.1
            if (attn_min + 0.5 * attn_sweep_mag) > 50:
                attn_range = (attn_min - 0.5 * attn_sweep_mag, 50)
            elif (attn_min - 0.5 * attn_sweep_mag) < 0:
                attn_range = (0, attn_min + 0.5 * attn_sweep_mag)
            else:
                attn_range = (
                    attn_min - 0.5 * attn_sweep_mag,
                    attn_min + 0.5 * attn_sweep_mag,
                )

        pow_min = pow_vec_0[np.argmin(pow_vec_0)]

        rfsoc_device.display_sequence = mem_display_sequence
        rfsoc_device.display_IQ_progress = mem_display_IQ_progress

        return (phase_min, attn_min)

    def get_optimal_attn_phase_test_Giulio_Gwenael(self):
        rfsoc_device = self.rfsoc_device
        Vaunix_Att_device = self.Vaunix_Att_device
        Vaunix_FS_device = self.Vaunix_FS_device

        display_plots = self.display_plots

        amp_if = self.amp_if
        nu_if = self.nu_if
        delta = self.delta

        iter_depth = self.iter_depth

        phase_range = self.phase_range
        phase_window_narrowing = self.phase_window_narrowing
        phase_points = self.phase_points

        attn_range = self.attn_range
        attn_window_narrowing = self.attn_window_narrowing
        attn_points = self.attn_points

        phase_offset_if = self.phase_offset_if
        dc_offset_I_pump = self.dc_offset_I_pump
        dc_offset_Q_pump = self.dc_offset_Q_pump
        dc_offset_I_weak = self.dc_offset_I_weak
        dc_offset_Q_weak = self.dc_offset_Q_weak

        acq_length = self.acq_length
        wait_time = self.wait_time
        num_rep = self.num_rep

        mem_display_sequence = rfsoc_device.display_sequence
        mem_display_IQ_progress = rfsoc_device.display_IQ_progress
        rfsoc_device.display_sequence = False
        rfsoc_device.display_IQ_progress = False

        adc_start = wait_time / 2

        param_sin_I_pump = {
            "amp": amp_if,
            "freq": nu_if,
            "dc_offset": self.dc_offset_I_pump * 1e-3,
            "phase_offset": 0,
        }

        param_sin_Q_pump = {
            "amp": amp_if,
            "freq": nu_if,
            "dc_offset": self.dc_offset_Q_pump * 1e-3,
            "phase_offset": np.pi * phase_offset_if / 180,
        }

        param_sin_I_weak = {
            "amp": 0,
            "freq": 0,
            "dc_offset": self.dc_offset_I_weak * 1e-3,
            "phase_offset": 0,
        }

        param_sin_Q_weak = {
            "amp": 0,
            "freq": 0,
            "dc_offset": self.dc_offset_Q_weak * 1e-3,
            "phase_offset": np.pi * 0 / 180,
        }

        pulse_pump_I = dict(
            label="pumpI",
            module="DAC",
            channel=self.dac_pump_I,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_I_pump,
            parent=None,
        )

        pulse_pump_Q = dict(
            label="pumpQ",
            module="DAC",
            channel=self.dac_pump_Q,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_Q_pump,
            parent=None,
        )

        pulse_weak_I = dict(
            label="weakI",
            module="DAC",
            channel=self.dac_weak_I,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_I_weak,
            parent=None,
        )

        pulse_weak_Q = dict(
            label="weakQ",
            module="DAC",
            channel=self.dac_weak_Q,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_Q_weak,
            parent=None,
        )

        record_both = dict(
            label="record_both",
            module="ADC",
            channel=1,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        record_both2 = dict(
            label="record_both2",
            module="ADC",
            channel=2,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        pulses = pd.DataFrame()
        pulses = pulses.append(pulse_pump_I, ignore_index=True)
        pulses = pulses.append(pulse_pump_Q, ignore_index=True)
        pulses = pulses.append(pulse_weak_I, ignore_index=True)
        pulses = pulses.append(pulse_weak_Q, ignore_index=True)
        pulses = pulses.append(record_both, ignore_index=True)
        pulses = pulses.append(record_both2, ignore_index=True)

        rfsoc_device.pulses = pulses

        rfsoc_device.acquisition_mode("IQ")

        rfsoc_device.ADC1.fmixer(nu_if)
        rfsoc_device.ADC2.fmixer(nu_if)
        rfsoc_device.ADC1.decfact(1)
        rfsoc_device.ADC2.decfact(1)
        rfsoc_device.freq_sync(1e6)
        rfsoc_device.ADC1.status("ON")
        rfsoc_device.ADC2.status("ON")
        rfsoc_device.output_format("BIN")
        rfsoc_device.n_rep(num_rep)

        rfsoc_device.process_sequencing()

        for iter_n in range(iter_depth):
            # optimize phase

            phase_vec_org = np.linspace(phase_range[0], phase_range[1], phase_points)
            phase_vec = self.process_phase(phase_vec_org)
            pow_vec_0 = np.array([])
            pow_vec_1 = np.array([])
            for phase in phase_vec:
                Vaunix_FS_device.phase_shift(phase)
                pow_tmp = rfsoc_device.ADC_power_dBm()
                pow_vec_0 = np.append(pow_vec_0, pow_tmp[0][0])
                pow_vec_1 = np.append(pow_vec_1, pow_tmp[1][0])

                # IQ_data = []
                # data_out_I,data_out_Q = rfsoc_device.IQINT_AVG()
                # data_out1 = np.zeros((2, 8, 2))
                # data_out1[0][0] = data_out_I[0]
                # data_out1[1][0] = data_out_Q[0]
                # IQ_data.append(list(data_out1))
                # IQ_data = np.array(IQ_data)
                # I_ch1_on = IQ_data[:, 0, 0, 0]
                # I_ch2_on = IQ_data[:, 0, 1, 0]
                # Q_ch1_on = IQ_data[:, 1, 0, 0]
                # Q_ch2_on = IQ_data[:, 1, 1, 0]
                # Mag_ch2_on = (I_ch2_on**2 + Q_ch2_on**2)/50 ## W
                # Mag_ch2_on_dBm = 10 * np.log10(Mag_ch2_on*1e3)
                # Mag_ch1_on = (I_ch1_on**2 + Q_ch1_on**2)/50 ## W
                # Mag_ch1_on_dBm = 10 * np.log10(Mag_ch1_on*1e3)
                # pow_vec_0 = np.append(pow_vec_0,Mag_ch1_on_dBm)
                # pow_vec_1 = np.append(pow_vec_1,Mag_ch2_on_dBm)

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(
                    phase_vec_org, pow_vec_0, label="ch1", marker=".", color="orange"
                )
                ax3.plot(
                    phase_vec_org, pow_vec_1, label="ch2", marker=".", color="blue"
                )
                plt.legend()
                plt.xlabel("Phase [degree]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            phase_min = phase_vec[np.argmin(pow_vec_0)]
            Vaunix_FS_device.phase_shift(phase_min)
            phase_sweep_mag = (
                (phase_range[1] - phase_range[0]) * phase_window_narrowing / 100
            )
            if phase_sweep_mag < phase_points:
                phase_sweep_mag = phase_points
            phase_range = (
                phase_min - 0.5 * phase_sweep_mag,
                phase_min + 0.5 * phase_sweep_mag,
            )

            # optimize attn

            attn_vec = np.linspace(attn_range[0], attn_range[1], attn_points)
            pow_vec_0 = np.array([])
            pow_vec_1 = np.array([])
            for attn in attn_vec:
                if attn < 0.0:
                    attn = 0.0
                    print("attn cannot be < 0, set to be = 0")
                Vaunix_Att_device.attn(attn)
                pow_tmp = rfsoc_device.ADC_power_dBm()
                pow_vec_0 = np.append(pow_vec_0, pow_tmp[0][0])
                pow_vec_1 = np.append(pow_vec_1, pow_tmp[1][0])

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(attn_vec, pow_vec_0, label="ch1", marker=".", color="orange")
                ax3.plot(attn_vec, pow_vec_1, label="ch2", marker=".", color="blue")
                plt.legend()
                plt.xlabel("Attenuation [dB]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            attn_min = attn_vec[np.argmin(pow_vec_0)]
            if attn_min < 0:
                attn_min = 0
                print("attn_min cannot be < 0, set to be = 0")

            Vaunix_Att_device.attn(attn_min)
            attn_sweep_mag = (
                (attn_range[1] - attn_range[0]) * attn_window_narrowing / 100
            )
            if attn_sweep_mag < attn_points * 0.1:
                attn_sweep_mag = attn_points * 0.1
            attn_range = (
                attn_min - 0.5 * attn_sweep_mag,
                attn_min + 0.5 * attn_sweep_mag,
            )

        pow_min = pow_vec_0[np.argmin(pow_vec_0)]

        rfsoc_device.display_sequence = mem_display_sequence
        rfsoc_device.display_IQ_progress = mem_display_IQ_progress

        return (phase_min, attn_min, pow_min)

    def get_pump_cancel_rfsoc(self):
        rfsoc_device = self.rfsoc_device

        display_plots = self.display_plots

        amp_if = self.amp_if
        nu_if = self.nu_if
        delta = self.delta

        iter_depth = self.iter_depth

        phase_range = self.phase_range
        phase_window_narrowing = self.phase_window_narrowing
        phase_points = self.phase_points

        amp_if_cancel_range = self.amp_if_cancel_range
        amp_if_cancel_window_narrowing = self.amp_if_cancel_window_narrowing
        amp_if_cancel_points = self.amp_if_cancel_points

        phase_offset_if = self.phase_offset_if
        angle_amp_if = self.angle_amp_if
        dc_offset_I_pump = self.dc_offset_I_pump
        dc_offset_Q_pump = self.dc_offset_Q_pump
        dc_offset_I_weak = self.dc_offset_I_weak
        dc_offset_Q_weak = self.dc_offset_Q_weak

        acq_length = self.acq_length
        wait_time = self.wait_time
        num_rep = self.num_rep

        mem_display_sequence = rfsoc_device.display_sequence
        mem_display_IQ_progress = rfsoc_device.display_IQ_progress
        rfsoc_device.display_sequence = False
        rfsoc_device.display_IQ_progress = False

        adc_start = wait_time / 2

        # param_sin_I_pump = {'amp':(1/np.sqrt(2))*amp_if*np.cos(np.pi*angle_amp_if/180),
        # 			 'freq':nu_if,
        # 			 'dc_offset':self.dc_offset_I_pump*1e-3,
        # 			 'phase_offset':0}

        # param_sin_Q_pump = {'amp':(1/np.sqrt(2))*amp_if*np.sin(np.pi*angle_amp_if/180),
        # 			 'freq':nu_if,
        # 			 'dc_offset':self.dc_offset_Q_pump*1e-3,
        # 			 'phase_offset':np.pi*phase_offset_if/180}

        amp_min = amp_if_cancel_range[0]

        for iter_n in range(iter_depth):
            # optimize phase

            phase_vec_org = np.linspace(phase_range[0], phase_range[1], phase_points)
            phase_vec = self.process_phase(phase_vec_org)
            pow_vec_0 = np.array([])
            pow_vec_1 = np.array([])

            print("Optimal DAC voltage = " + str(amp_min))

            for phase in bar(phase_vec):
                param_sin_I_pump = {
                    "amp": amp_if,
                    "freq": nu_if,
                    "dc_offset": self.dc_offset_I_pump * 1e-3,
                    "phase_offset": 0,
                }

                param_sin_Q_pump = {
                    "amp": amp_if,
                    "freq": nu_if,
                    "dc_offset": self.dc_offset_Q_pump * 1e-3,
                    "phase_offset": np.pi * phase_offset_if / 180,
                }

                param_sin_cancel = {
                    "amp": amp_min,
                    "freq": nu_if,
                    "dc_offset": 0,
                    "phase_offset": np.pi * phase / 180,
                }

                pulse_pump_I = dict(
                    label="pumpI",
                    module="DAC",
                    channel=self.dac_pump_I,
                    mode="sin",
                    start=0,
                    length=acq_length + wait_time,
                    param=param_sin_I_pump,
                    parent=None,
                )

                pulse_pump_Q = dict(
                    label="pumpQ",
                    module="DAC",
                    channel=self.dac_pump_Q,
                    mode="sin",
                    start=0,
                    length=acq_length + wait_time,
                    param=param_sin_Q_pump,
                    parent=None,
                )

                pulse_cancel_pump = dict(
                    label="cancel_pump",
                    module="DAC",
                    channel=self.dac_pump_cancel,
                    mode="sin",
                    start=0,
                    length=acq_length + wait_time,
                    param=param_sin_cancel,
                    parent=None,
                )

                record_both = dict(
                    label="record_both",
                    module="ADC",
                    channel=1,
                    mode="raw",
                    start=adc_start,
                    length=acq_length,
                    param=None,
                    parent=None,
                )

                record_both2 = dict(
                    label="record_both2",
                    module="ADC",
                    channel=2,
                    mode="raw",
                    start=adc_start,
                    length=acq_length,
                    param=None,
                    parent=None,
                )

                pulses = pd.DataFrame()
                pulses = pulses.append(pulse_pump_I, ignore_index=True)
                pulses = pulses.append(pulse_pump_Q, ignore_index=True)
                pulses = pulses.append(pulse_cancel_pump, ignore_index=True)
                pulses = pulses.append(record_both, ignore_index=True)
                pulses = pulses.append(record_both2, ignore_index=True)

                rfsoc_device.pulses = pulses

                rfsoc_device.acquisition_mode("IQ")

                rfsoc_device.ADC1.fmixer(nu_if)
                rfsoc_device.ADC2.fmixer(nu_if)
                rfsoc_device.ADC1.decfact(1)
                rfsoc_device.ADC2.decfact(1)
                rfsoc_device.freq_sync(1e6)
                rfsoc_device.ADC1.status("ON")
                rfsoc_device.ADC2.status("ON")
                rfsoc_device.output_format("BIN")
                rfsoc_device.n_rep(num_rep)

                rfsoc_device.process_sequencing()

                pow_tmp = rfsoc_device.ADC_power_dBm()
                pow_vec_0 = np.append(pow_vec_0, pow_tmp[0][0])
                pow_vec_1 = np.append(pow_vec_1, pow_tmp[1][0])

                # IQ_data = []
                # data_out_I,data_out_Q = rfsoc_device.IQINT_AVG()
                # data_out1 = np.zeros((2, 8, 2))
                # data_out1[0][0] = data_out_I[0]
                # data_out1[1][0] = data_out_Q[0]
                # IQ_data.append(list(data_out1))
                # IQ_data = np.array(IQ_data)
                # I_ch1_on = IQ_data[:, 0, 0, 0]
                # I_ch2_on = IQ_data[:, 0, 1, 0]
                # Q_ch1_on = IQ_data[:, 1, 0, 0]
                # Q_ch2_on = IQ_data[:, 1, 1, 0]
                # Mag_ch2_on = (I_ch2_on**2 + Q_ch2_on**2)/50 ## W
                # Mag_ch2_on_dBm = 10 * np.log10(Mag_ch2_on*1e3)
                # Mag_ch1_on = (I_ch1_on**2 + Q_ch1_on**2)/50 ## W
                # Mag_ch1_on_dBm = 10 * np.log10(Mag_ch1_on*1e3)
                # pow_vec_0 = np.append(pow_vec_0,Mag_ch1_on_dBm)
                # pow_vec_1 = np.append(pow_vec_1,Mag_ch2_on_dBm)

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(
                    phase_vec_org, pow_vec_0, label="ch1", marker=".", color="orange"
                )
                ax3.plot(
                    phase_vec_org, pow_vec_1, label="ch2", marker=".", color="blue"
                )
                plt.legend()
                plt.xlabel("Phase [degree]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            phase_min = phase_vec[np.argmin(pow_vec_0)]

            phase_sweep_mag = (
                (phase_range[1] - phase_range[0]) * phase_window_narrowing / 100
            )
            if phase_sweep_mag < phase_points:
                phase_sweep_mag = phase_points
            phase_range = (
                phase_min - 0.5 * phase_sweep_mag,
                phase_min + 0.5 * phase_sweep_mag,
            )

            # optimize DAc voltage

            dac_v_vec = np.linspace(
                amp_if_cancel_range[0], amp_if_cancel_range[1], amp_if_cancel_points
            )
            pow_vec_0 = np.array([])
            pow_vec_1 = np.array([])

            print("Optimal phase = " + str(phase_min))

            for amp in bar(dac_v_vec):
                param_sin_I_pump = {
                    "amp": amp_if,
                    "freq": nu_if,
                    "dc_offset": self.dc_offset_I_pump * 1e-3,
                    "phase_offset": 0,
                }

                param_sin_Q_pump = {
                    "amp": amp_if,
                    "freq": nu_if,
                    "dc_offset": self.dc_offset_Q_pump * 1e-3,
                    "phase_offset": np.pi * phase_offset_if / 180,
                }

                param_sin_cancel = {
                    "amp": amp,
                    "freq": nu_if,
                    "dc_offset": 0,
                    "phase_offset": np.pi * phase_min / 180,
                }

                pulse_pump_I = dict(
                    label="pumpI",
                    module="DAC",
                    channel=self.dac_pump_I,
                    mode="sin",
                    start=0,
                    length=acq_length + wait_time,
                    param=param_sin_I_pump,
                    parent=None,
                )

                pulse_pump_Q = dict(
                    label="pumpQ",
                    module="DAC",
                    channel=self.dac_pump_Q,
                    mode="sin",
                    start=0,
                    length=acq_length + wait_time,
                    param=param_sin_Q_pump,
                    parent=None,
                )

                pulse_cancel_pump = dict(
                    label="cancel_pump",
                    module="DAC",
                    channel=self.dac_pump_cancel,
                    mode="sin",
                    start=0,
                    length=acq_length + wait_time,
                    param=param_sin_cancel,
                    parent=None,
                )

                record_both = dict(
                    label="record_both",
                    module="ADC",
                    channel=1,
                    mode="raw",
                    start=adc_start,
                    length=acq_length,
                    param=None,
                    parent=None,
                )

                record_both2 = dict(
                    label="record_both2",
                    module="ADC",
                    channel=2,
                    mode="raw",
                    start=adc_start,
                    length=acq_length,
                    param=None,
                    parent=None,
                )

                pulses = pd.DataFrame()
                pulses = pulses.append(pulse_pump_I, ignore_index=True)
                pulses = pulses.append(pulse_pump_Q, ignore_index=True)
                pulses = pulses.append(pulse_cancel_pump, ignore_index=True)
                pulses = pulses.append(record_both, ignore_index=True)
                pulses = pulses.append(record_both2, ignore_index=True)

                rfsoc_device.pulses = pulses

                rfsoc_device.acquisition_mode("IQ")

                rfsoc_device.ADC1.fmixer(nu_if)
                rfsoc_device.ADC2.fmixer(nu_if)
                rfsoc_device.ADC1.decfact(1)
                rfsoc_device.ADC2.decfact(1)
                rfsoc_device.freq_sync(1e6)
                rfsoc_device.ADC1.status("ON")
                rfsoc_device.ADC2.status("ON")
                rfsoc_device.output_format("BIN")
                rfsoc_device.n_rep(num_rep)

                rfsoc_device.process_sequencing()

                pow_tmp = rfsoc_device.ADC_power_dBm()
                pow_vec_0 = np.append(pow_vec_0, pow_tmp[0][0])
                pow_vec_1 = np.append(pow_vec_1, pow_tmp[1][0])

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(dac_v_vec, pow_vec_0, label="ch1", marker=".", color="orange")
                ax3.plot(dac_v_vec, pow_vec_1, label="ch2", marker=".", color="blue")
                plt.legend()
                plt.xlabel("Dac voltage [V]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            amp_min = dac_v_vec[np.argmin(pow_vec_0)]

            amp_if_cancel_sweep_mag = (
                (amp_if_cancel_range[1] - amp_if_cancel_range[0])
                * amp_if_cancel_window_narrowing
                / 100
            )
            amp_if_cancel_range = (
                amp_min - 0.5 * amp_if_cancel_sweep_mag,
                amp_min + 0.5 * amp_if_cancel_sweep_mag,
            )

        pow_min = pow_vec_0[np.argmin(pow_vec_0)]

        rfsoc_device.display_sequence = mem_display_sequence
        rfsoc_device.display_IQ_progress = mem_display_IQ_progress

        return (phase_min, amp_min)

    def get_pump_pow_max(self):
        rfsoc_device = self.rfsoc_device
        Vaunix_Att_device = self.Vaunix_Att_device
        Vaunix_FS_device = self.Vaunix_FS_device

        display_plots = self.display_plots

        amp_if = self.amp_if
        nu_if = self.nu_if
        delta = self.delta

        iter_depth = self.iter_depth

        phase_range = self.phase_range
        phase_window_narrowing = self.phase_window_narrowing
        phase_points = self.phase_points

        attn_range = self.attn_range
        attn_window_narrowing = self.attn_window_narrowing
        attn_points = self.attn_points

        phase_offset_if = self.phase_offset_if
        dc_offset_I_pump = self.dc_offset_I_pump
        dc_offset_Q_pump = self.dc_offset_Q_pump
        dc_offset_I_weak = self.dc_offset_I_weak
        dc_offset_Q_weak = self.dc_offset_Q_weak

        acq_length = self.acq_length
        wait_time = self.wait_time
        num_rep = self.num_rep

        mem_display_sequence = rfsoc_device.display_sequence
        mem_display_IQ_progress = rfsoc_device.display_IQ_progress
        rfsoc_device.display_sequence = False
        rfsoc_device.display_IQ_progress = False

        adc_start = wait_time / 2

        param_sin_I_pump = {
            "amp": amp_if,
            "freq": nu_if,
            "dc_offset": self.dc_offset_I_pump * 1e-3,
            "phase_offset": 0,
        }

        param_sin_Q_pump = {
            "amp": amp_if,
            "freq": nu_if,
            "dc_offset": self.dc_offset_Q_pump * 1e-3,
            "phase_offset": np.pi * phase_offset_if / 180,
        }

        param_sin_I_weak = {
            "amp": 0,
            "freq": 0,
            "dc_offset": self.dc_offset_I_weak * 1e-3,
            "phase_offset": 0,
        }

        param_sin_Q_weak = {
            "amp": 0,
            "freq": 0,
            "dc_offset": self.dc_offset_Q_weak * 1e-3,
            "phase_offset": np.pi * 0 / 180,
        }

        pulse_pump_I = dict(
            label="pumpI",
            module="DAC",
            channel=self.dac_pump_I,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_I_pump,
            parent=None,
        )

        pulse_pump_Q = dict(
            label="pumpQ",
            module="DAC",
            channel=self.dac_pump_Q,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_Q_pump,
            parent=None,
        )

        pulse_weak_I = dict(
            label="weakI",
            module="DAC",
            channel=self.dac_weak_I,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_I_weak,
            parent=None,
        )

        pulse_weak_Q = dict(
            label="weakQ",
            module="DAC",
            channel=self.dac_weak_Q,
            mode="sin",
            start=0,
            length=acq_length + wait_time,
            param=param_sin_Q_weak,
            parent=None,
        )

        record_both = dict(
            label="record_both",
            module="ADC",
            channel=1,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        record_both2 = dict(
            label="record_both2",
            module="ADC",
            channel=2,
            mode="raw",
            start=adc_start,
            length=acq_length,
            param=None,
            parent=None,
        )

        pulses = pd.DataFrame()
        pulses = pulses.append(pulse_pump_I, ignore_index=True)
        pulses = pulses.append(pulse_pump_Q, ignore_index=True)
        pulses = pulses.append(pulse_weak_I, ignore_index=True)
        pulses = pulses.append(pulse_weak_Q, ignore_index=True)
        pulses = pulses.append(record_both, ignore_index=True)
        pulses = pulses.append(record_both2, ignore_index=True)

        rfsoc_device.pulses = pulses

        rfsoc_device.acquisition_mode("IQ")

        rfsoc_device.ADC1.fmixer(nu_if)
        rfsoc_device.ADC2.fmixer(nu_if)
        rfsoc_device.ADC1.decfact(1)
        rfsoc_device.ADC2.decfact(1)
        rfsoc_device.freq_sync(1e6)
        rfsoc_device.ADC1.status("ON")
        rfsoc_device.ADC2.status("ON")
        rfsoc_device.output_format("BIN")
        rfsoc_device.n_rep(num_rep)

        rfsoc_device.process_sequencing()

        for iter_n in range(iter_depth):
            # optimize phase

            phase_vec_org = np.linspace(phase_range[0], phase_range[1], phase_points)
            phase_vec = self.process_phase(phase_vec_org)
            pow_vec_0 = np.array([])
            pow_vec_1 = np.array([])
            for phase in phase_vec:
                Vaunix_FS_device.phase_shift(phase)
                pow_tmp = rfsoc_device.ADC_power_dBm()
                pow_vec_0 = np.append(pow_vec_0, pow_tmp[0][0])
                pow_vec_1 = np.append(pow_vec_1, pow_tmp[1][0])

                # IQ_data = []
                # data_out_I,data_out_Q = rfsoc_device.IQINT_AVG()
                # data_out1 = np.zeros((2, 8, 2))
                # data_out1[0][0] = data_out_I[0]
                # data_out1[1][0] = data_out_Q[0]
                # IQ_data.append(list(data_out1))
                # IQ_data = np.array(IQ_data)
                # I_ch1_on = IQ_data[:, 0, 0, 0]
                # I_ch2_on = IQ_data[:, 0, 1, 0]
                # Q_ch1_on = IQ_data[:, 1, 0, 0]
                # Q_ch2_on = IQ_data[:, 1, 1, 0]
                # Mag_ch2_on = (I_ch2_on**2 + Q_ch2_on**2)/50 ## W
                # Mag_ch2_on_dBm = 10 * np.log10(Mag_ch2_on*1e3)
                # Mag_ch1_on = (I_ch1_on**2 + Q_ch1_on**2)/50 ## W
                # Mag_ch1_on_dBm = 10 * np.log10(Mag_ch1_on*1e3)
                # pow_vec_0 = np.append(pow_vec_0,Mag_ch1_on_dBm)
                # pow_vec_1 = np.append(pow_vec_1,Mag_ch2_on_dBm)

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(
                    phase_vec_org, pow_vec_0, label="ch1", marker=".", color="orange"
                )
                ax3.plot(
                    phase_vec_org, pow_vec_1, label="ch2", marker=".", color="blue"
                )
                plt.legend()
                plt.xlabel("Phase [degree]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            pow_phase_max = pow_vec_0[np.argmax(pow_vec_0)]
            phase_max = phase_vec[np.argmax(pow_vec_0)]
            Vaunix_FS_device.phase_shift(phase_max)
            # phase_sweep_mag = (phase_range[1]-phase_range[0])*phase_window_narrowing/100
            # if phase_sweep_mag<phase_points:
            # 	phase_sweep_mag = phase_points
            # phase_range = (phase_min-0.5*phase_sweep_mag,phase_min+0.5*phase_sweep_mag)

            # optimize attn

            attn_vec = np.linspace(attn_range[0], attn_range[1], attn_points)
            pow_vec_0 = np.array([])
            pow_vec_1 = np.array([])
            for attn in attn_vec:
                if attn < 0.0:
                    attn = 0.0
                    print("attn cannot be < 0, set to be = 0")
                Vaunix_Att_device.attn(attn)
                pow_tmp = rfsoc_device.ADC_power_dBm()
                pow_vec_0 = np.append(pow_vec_0, pow_tmp[0][0])
                pow_vec_1 = np.append(pow_vec_1, pow_tmp[1][0])

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(attn_vec, pow_vec_0, label="ch1", marker=".", color="orange")
                ax3.plot(attn_vec, pow_vec_1, label="ch2", marker=".", color="blue")
                plt.legend()
                plt.xlabel("Attenuation [dB]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            pow_att_max = pow_vec_0[np.argmax(pow_vec_0)]
            attn_max = attn_vec[np.argmax(pow_vec_0)]
            if attn_max < 0:
                attn_max = 0
                print("attn_min cannot be < 0, set to be = 0")

            # Vaunix_Att_device.attn(attn_min)
            # attn_sweep_mag = (attn_range[1]-attn_range[0])*attn_window_narrowing/100
            # if attn_sweep_mag<attn_points*0.1:
            # 	attn_sweep_mag = attn_points*0.1
            # attn_range = (attn_min-0.5*attn_sweep_mag,attn_min+0.5*attn_sweep_mag)

        rfsoc_device.display_sequence = mem_display_sequence
        rfsoc_device.display_IQ_progress = mem_display_IQ_progress

        return (phase_max, pow_phase_max)

    def process_phase(self, phase_arr):
        phase_arr_out = np.array([])

        for angle in phase_arr:
            while angle < 0:
                angle += 360
            while angle > 360:
                angle -= 360
            phase_arr_out = np.append(phase_arr_out, int(angle))

        return phase_arr_out


class check_ADC_meas_freq_cls:
    def __init__(self, rfsoc_device):
        self.rfsoc_device = rfsoc_device

        self.display_plots = True

        self.amp_if = 0.1

        self.iter_num = 5
        self.tolerance = 10  # percent

        self.phase_offset_if = 0  # degrees
        self.dc_offset_I = 8  # mV
        self.dc_offset_Q = 6  # mV

        self.acq_length = 10.0
        self.wait_time = 2.0
        self.num_rep = 100

    def check_freq(self, freq_list):
        rfsoc_device = self.rfsoc_device

        display_plots = self.display_plots

        amp_if = self.amp_if

        iter_num = self.iter_num
        tolerance = self.tolerance

        phase_offset_if = self.phase_offset_if
        dc_offset_I = self.dc_offset_I
        dc_offset_Q = self.dc_offset_Q

        acq_length = self.acq_length
        wait_time = self.wait_time
        num_rep = self.num_rep

        mem_display_sequence = rfsoc_device.display_sequence
        mem_display_IQ_progress = rfsoc_device.display_IQ_progress
        rfsoc_device.display_sequence = False
        rfsoc_device.display_IQ_progress = False

        adc_start = wait_time / 2

        sweep_mem_ch1 = {}
        sweep_mem_ch2 = {}
        corrupted_bins_ch1 = {}
        corrupted_bins_ch2 = {}

        for iter_n in bar(range(iter_num)):
            sweep_mem_ch1[iter_n] = []
            sweep_mem_ch2[iter_n] = []
            corrupted_bins_ch1[iter_n] = []
            corrupted_bins_ch2[iter_n] = []

            for nu_if in bar(freq_list):
                param_sin_I = {
                    "amp": amp_if,
                    "freq": nu_if,
                    "dc_offset": dc_offset_I * 1e-3,
                    "phase_offset": 0,
                }

                param_sin_Q = {
                    "amp": amp_if,
                    "freq": nu_if,
                    "dc_offset": dc_offset_Q * 1e-3,
                    "phase_offset": np.pi * phase_offset_if / 180,
                }

                pulse_sin = dict(
                    label="pump",
                    module="DAC",
                    channel=1,
                    mode="sin",
                    start=0,
                    length=acq_length + wait_time,
                    param=param_sin_I,
                    parent=None,
                )

                record_sin = dict(
                    label="record_signal",
                    module="ADC",
                    channel=1,
                    mode="IQ",
                    start=adc_start,
                    length=acq_length,
                    param=None,
                    parent=None,
                )

                pulse_sin2 = dict(
                    label="pump2",
                    module="DAC",
                    channel=2,
                    mode="sin",
                    start=0,
                    length=acq_length + wait_time,
                    param=param_sin_Q,
                    parent=None,
                )

                record_sin2 = dict(
                    label="record_signal2",
                    module="ADC",
                    channel=2,
                    mode="IQ",
                    start=adc_start,
                    length=acq_length,
                    param=None,
                    parent=None,
                )

                pulses = pd.DataFrame()
                pulses = pulses.append(pulse_sin, ignore_index=True)
                pulses = pulses.append(record_sin, ignore_index=True)
                pulses = pulses.append(pulse_sin2, ignore_index=True)
                pulses = pulses.append(record_sin2, ignore_index=True)

                rfsoc_device.pulses = pulses

                rfsoc_device.acquisition_mode("IQ")

                rfsoc_device.ADC1.fmixer(nu_if)
                rfsoc_device.ADC2.fmixer(nu_if)
                rfsoc_device.ADC1.decfact(1)
                rfsoc_device.ADC2.decfact(1)
                rfsoc_device.freq_sync(1e6)
                rfsoc_device.ADC1.status("ON")
                rfsoc_device.ADC2.status("ON")
                rfsoc_device.output_format("BIN")
                rfsoc_device.n_rep(num_rep)

                rfsoc_device.process_sequencing()

                pow_tmp = rfsoc_device.ADC_power_dBm()

                sweep_mem_ch1[iter_n].append(pow_tmp[0][0])
                sweep_mem_ch2[iter_n].append(pow_tmp[1][0])

            if display_plots:
                fig = plt.figure(figsize=(16, 12))
                ax3 = fig.add_subplot(221)
                ax3.plot(
                    freq_list,
                    sweep_mem_ch1[iter_n],
                    label="ch1",
                    marker=".",
                    color="orange",
                )
                ax3.plot(
                    freq_list,
                    sweep_mem_ch2[iter_n],
                    label="ch2",
                    marker=".",
                    color="blue",
                )
                plt.legend()
                plt.xlabel("Frequency [MHz]", fontsize=14)
                plt.ylabel("Power (dBm)", fontsize=14)
                plt.grid()
                plt.show()

            corrupted_bins_ch1[iter_n].append(
                freq_list[np.where(np.asarray(sweep_mem_ch1[iter_n]) < (-60))[0]]
            )
            corrupted_bins_ch2[iter_n].append(
                freq_list[np.where(np.asarray(sweep_mem_ch2[iter_n]) < (-60))[0]]
            )

            print(
                "Channel 1 corrupted bins : " + str(corrupted_bins_ch1[iter_n]) + "MHz"
            )
            print(
                "Channel 2 corrupted bins : " + str(corrupted_bins_ch2[iter_n]) + "MHz"
            )

        if display_plots:
            fig = plt.figure(figsize=(16, 12))
            ax3 = fig.add_subplot(221)
            for iter_n in range(iter_num):
                ax3.plot(
                    freq_list,
                    sweep_mem_ch1[iter_n],
                    label="ch1",
                    marker=".",
                    color="orange",
                )
                ax3.plot(
                    freq_list,
                    sweep_mem_ch2[iter_n],
                    label="ch2",
                    marker=".",
                    color="blue",
                )
            plt.legend()
            plt.xlabel("Frequency [MHz]", fontsize=14)
            plt.ylabel("Power (dBm)", fontsize=14)
            plt.grid()
            plt.show()
        # To be modified this histogram doesn't work (Gwen)
        corrupted_bins_ch1_tot = corrupted_bins_ch1.flatten()
        corrupted_bins_ch2_tot = corrupted_bins_ch2.flatten()

        print("Channel 1 corrupted bins total: " + str(corrupted_bins_ch1_tot) + "MHz")
        print("Channel 2 corrupted bins total: " + str(corrupted_bins_ch2_tot) + "MHz")

        if display_plots:
            fig = plt.figure(figsize=(16, 12))

            plt.hist(corrupted_bins_ch1_tot, len(freq_list), color="orange")

            plt.rc("axes", labelsize=20)  # fontsize of the x and y labels
            plt.rc("xtick", labelsize=20)  # fontsize of the tick labels
            plt.rc("ytick", labelsize=20)  # fontsize of the tick labels
            plt.rc("grid", linestyle="--")
            plt.grid(True)
            plt.xlabel("ADC frequency [MHz]", fontsize=20)
            plt.ylabel("Counts over 5 measurements", fontsize=20)
            plt.title(
                "Corrupted bins ADC 1 counts over 5 independant measurements",
                fontsize=20,
            )
            plt.show()

            fig = plt.figure(figsize=(16, 12))

            plt.hist(corrupted_bins_ch2_tot, len(freq_list), color="blue")

            plt.rc("axes", labelsize=20)  # fontsize of the x and y labels
            plt.rc("xtick", labelsize=20)  # fontsize of the tick labels
            plt.rc("ytick", labelsize=20)  # fontsize of the tick labels
            plt.rc("grid", linestyle="--")
            plt.grid(True)
            plt.xlabel("ADC frequency [MHz]", fontsize=20)
            plt.ylabel("Counts over 5 measurements", fontsize=20)
            plt.title(
                "Corrupted bins ADC 2 counts over 5 independant measurements",
                fontsize=20,
            )
            plt.show()
