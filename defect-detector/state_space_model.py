"""Piecewise-affine state-space model of the buck converter.

Mirrors the SPICE netlist in simulation.py with the same structure and
parasitic parameters:

    Vin --[switch ron]-- sw --[L 10uH]-- out --[R_L 19.5mOhm]-- out_c
    gnd --[diode is/rs]-- sw
    out_c --[L_c cap_inductance]--[R_esr cap_esr]--[C]-- gnd
    out_c --[R_load]-- gnd

State vector x = [i_L, i_C, v_C]:
    i_L — main inductor current
    i_C — capacitor branch current (through the parasitic cap inductance)
    v_C — ideal capacitor voltage

Three affine topologies dx/dt = A x + b:
    ON  — switch closed (v_sw = Vin - ron*i_L), diode blocking
    OFF — switch open, diode conducting (v_sw = -(V_f + rs*i_L), V_f from
          the Shockley equation linearized at the average inductor current)
    DCM — switch open, diode blocking (i_L clamped to 0)

Gate rise/fall times are folded into an effective on-time: the SPICE switch
(vt=1V, 10V gate pulse) conducts from 10% of the rise ramp until 90% of the
fall ramp, so ton_eff = ton + 0.9*(t_rise + t_fall). The ramps themselves are
not modeled as separate intervals.

Integration is exact per interval: each topology is discretized with the
matrix exponential of the augmented system, so the only approximations are
the diode linearization and the DCM clamp resolution (one substep).
"""

import ctypes
import os
import subprocess
import time

import numpy as np
from scipy.linalg import expm

# Thermal voltage kT/q at 25 degC (matches SPICE temperature=25)
_VT_25C = 1.380649e-23 * 298.15 / 1.602176634e-19


class StateSpaceBuckConverter:
    """Drop-in analogue of simulation.BuckConverter based on state-space ODEs."""

    def __init__(self, params, optimization_params=None):
        self.vin = params.vin
        self.freq = 312500
        self.l_value = 10e-6
        self.c_value = params.c_value * 1e-6  # Convert to Farads
        self.duty_cycle = params.pwm_percentage / 100.0
        self.l_resistance = 19.5e-3  # from datasheet (fixed, not optimized)
        self.r_load = params.r_load
        self.period = 1 / self.freq

        opt = optimization_params or {}
        self.gate_rise_time = opt.get('gate_rise_time', 1.0072085534880547e-10)
        self.gate_fall_time = opt.get('gate_fall_time', 8.265072857706626e-08)
        self.switch_ron = opt.get('switch_ron', 3.3157359136705763e-12)
        self.diode_rs = opt.get('diode_rs', 1e-06)
        self.diode_is = opt.get('diode_is', 2.423465389750961e-15)
        self.cap_esr = opt.get('cap_esr', 0.08779711061951505)
        self.cap_inductance = opt.get('cap_inductance', 3.215742370055204e-10)

    def calculate_steady_state_values(self):
        """Same analytic steady-state estimate as the SPICE model."""
        vout_ideal = self.vin * self.duty_cycle
        il_avg = vout_ideal / self.r_load
        vout_with_loss = vout_ideal - il_avg * self.l_resistance
        il_avg = vout_with_loss / self.r_load
        vout_with_loss = vout_ideal - il_avg * self.l_resistance
        delta_il = (self.vin - vout_with_loss) * self.duty_cycle * self.period / self.l_value
        return {
            'vout': vout_with_loss,
            'il_avg': il_avg,
            'il_initial': il_avg - delta_il / 2,
            'delta_il': delta_il,
        }

    # ------------------------------------------------------------------
    # Model construction
    # ------------------------------------------------------------------

    def _diode_drop(self, il_avg):
        """Forward drop of the diode at the operating current (Shockley)."""
        i = max(il_avg, 1e-6)
        return _VT_25C * np.log(i / self.diode_is + 1.0)

    def _system_matrices(self, v_f):
        """Return {mode: (A, b)} for the three topologies."""
        L, Lc, C = self.l_value, self.cap_inductance, self.c_value
        Rl, Resr, Rload = self.l_resistance, self.cap_esr, self.r_load
        ron, rs = self.switch_ron, self.diode_rs

        # Rows shared by all topologies (capacitor branch and capacitor):
        #   di_C/dt = (R_load*(i_L - i_C) - R_esr*i_C - v_C) / L_c
        #   dv_C/dt = i_C / C
        row_ic = [Rload / Lc, -(Rload + Resr) / Lc, -1.0 / Lc]
        row_vc = [0.0, 1.0 / C, 0.0]

        # di_L/dt = (v_sw - R_load*(i_L - i_C) - R_L*i_L) / L
        a_on = np.array([
            [-(ron + Rload + Rl) / L, Rload / L, 0.0],
            row_ic,
            row_vc,
        ])
        b_on = np.array([self.vin / L, 0.0, 0.0])

        a_off = np.array([
            [-(rs + Rload + Rl) / L, Rload / L, 0.0],
            row_ic,
            row_vc,
        ])
        b_off = np.array([-v_f / L, 0.0, 0.0])

        # DCM: i_L frozen at zero, cap discharges into the load
        a_dcm = np.array([
            [0.0, 0.0, 0.0],
            row_ic,
            row_vc,
        ])
        b_dcm = np.zeros(3)

        return {'on': (a_on, b_on), 'off': (a_off, b_off), 'dcm': (a_dcm, b_dcm)}

    @staticmethod
    def _discretize(A, b, dt):
        """Exact discretization of dx/dt = A x + b over a step dt."""
        aug = np.zeros((4, 4))
        aug[:3, :3] = A
        aug[:3, 3] = b
        M = expm(aug * dt)
        return M[:3, :3], M[:3, 3]

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    @staticmethod
    def _step_period(x, n_on, on_mats, n_off, off_mats, dcm_mats,
                     record=None, frozen_k=-1):
        """Advance one PWM period with DCM clamping.

        record, if given, is a (state_list, gate_list) tuple filled with
        one sample per substep boundary.

        frozen_k >= 0 forces the DCM clamp at off-substep index frozen_k
        instead of detecting the i_L zero crossing, which makes the period
        map affine in x. Returns (x, clamp_index) where clamp_index is the
        off-substep at which the clamp engaged (None if it never did).
        """
        ad_on, bd_on = on_mats
        ad_off, bd_off = off_mats
        ad_dcm, bd_dcm = dcm_mats

        for _ in range(n_on):
            x = ad_on @ x + bd_on
            if record is not None:
                record[0].append(x)
                record[1].append(10.0)
        clamp_idx = None
        for j in range(n_off):
            if clamp_idx is not None and j > clamp_idx:
                x = ad_dcm @ x + bd_dcm
            else:
                x = ad_off @ x + bd_off
                if (j == frozen_k) if frozen_k >= 0 else (x[0] <= 0.0):
                    x[0] = 0.0
                    clamp_idx = j
            if record is not None:
                record[0].append(x)
                record[1].append(0.0)
        return x, clamp_idx

    def _prepare_grid(self, measurement_time_points):
        """Common setup: time grid, switching intervals, system matrices."""
        time_points = np.asarray(measurement_time_points, dtype=np.float64) * 1e-6
        t_end = time_points[-1]
        dt_target = (time_points[1] - time_points[0]) * 0.5

        T = self.period
        # Effective conduction time: the SPICE PULSE source holds the gate
        # above the switch threshold (1V of a 10V swing) for 90% of both ramps
        ton = self.duty_cycle * T + 0.9 * (self.gate_rise_time + self.gate_fall_time)
        ton = min(max(ton, 0.0), T)
        toff = T - ton

        n_on = max(1, int(round(ton / dt_target))) if ton > 0 else 0
        n_off = max(1, int(round(toff / dt_target))) if toff > 0 else 0
        dt_on = ton / n_on if n_on else 0.0
        dt_off = toff / n_off if n_off else 0.0

        ss = self.calculate_steady_state_values()
        v_f = self._diode_drop(ss['il_avg'])
        mats = self._system_matrices(v_f)
        n_periods = int(np.ceil(t_end / T)) + 1
        return (t_end, ton, toff, n_on, n_off, dt_on, dt_off, ss, mats,
                n_periods)

    def _package_result(self, states, n_on, dt_on, ton, n_off, dt_off,
                        n_periods, t_end, measurement_time_points):
        """Build the SPICE-compatible result dict from recorded states."""
        gate_tile = np.concatenate([np.full(n_on, 10.0), np.zeros(n_off)])
        gates = np.concatenate([[10.0 if n_on else 0.0],
                                np.tile(gate_tile, n_periods)])

        # Substep-boundary time grid (seconds), one period tile repeated
        tile = np.concatenate([
            dt_on * np.arange(1, n_on + 1),
            ton + dt_off * np.arange(1, n_off + 1),
        ])
        T = self.period
        times = np.concatenate([[0.0]] + [k * T + tile for k in range(n_periods)])

        sim_voltage_full = self.r_load * (states[:, 0] - states[:, 1])
        sim_current_full = states[:, 0]
        sim_time_full = times * 1e6

        keep = sim_time_full <= t_end * 1e6 + 1e-9
        return {
            'sim_voltage_full': sim_voltage_full[keep],
            'sim_current_full': sim_current_full[keep],
            'sim_time_full': sim_time_full[keep],
            'sim_gate_full': gates[keep],
            'measurement_time_points': measurement_time_points,
        }

    def run_simulation(self, measurement_time_points):
        (t_end, ton, toff, n_on, n_off, dt_on, dt_off, ss, mats,
         n_periods) = self._prepare_grid(measurement_time_points)

        on_mats = self._discretize(*mats['on'], dt_on) if n_on else None
        off_mats = self._discretize(*mats['off'], dt_off) if n_off else None
        dcm_mats = self._discretize(*mats['dcm'], dt_off) if n_off else None

        x0 = self._find_periodic_state(mats, ss, n_on, on_mats, dt_on * n_on,
                                       n_off, off_mats, dcm_mats, dt_off * n_off)

        # --- Record the output window (same phase convention as SPICE:
        # recording starts at an ON edge after warmup) ---
        states = [x0.copy()]
        record = (states, [])
        x = x0.copy()
        for _ in range(n_periods):
            x, _ = self._step_period(x, n_on, on_mats, n_off, off_mats,
                                     dcm_mats, record)

        return self._package_result(np.array(states), n_on, dt_on, ton,
                                    n_off, dt_off, n_periods, t_end,
                                    measurement_time_points)

    def run_simulation_stats(self, measurement_time_points):
        """Simulate and reduce to the four detector metrics.

        Returns {'voltage_mean', 'voltage_ripple', 'current_mean',
        'current_ripple'} with ripple = max - mean, matching
        calculate_statistics() in the analysis scripts.
        """
        result = self.run_simulation(measurement_time_points)
        v = result['sim_voltage_full']
        i = result['sim_current_full']
        return {
            'voltage_mean': float(np.mean(v)),
            'voltage_ripple': float(np.max(v) - np.mean(v)),
            'current_mean': float(np.mean(i)),
            'current_ripple': float(np.max(i) - np.mean(i)),
        }

    def _find_periodic_state(self, mats, ss, n_on, on_mats, ton, n_off,
                             off_mats, dcm_mats, toff):
        """Find the state at the start of the ON interval in steady state."""
        if n_on == 0 or n_off == 0:
            # Degenerate 0%/100% duty: pure LTI, steady state is the DC fixed point
            A, b = mats['on'] if n_off == 0 else mats['dcm' if n_on == 0 else 'off']
            return np.linalg.solve(-A, b) if n_off == 0 else np.zeros(3)

        # CCM candidate: exact periodic fixed point of the two-interval map
        phi_on, gam_on = self._discretize(*mats['on'], ton)
        phi_off, gam_off = self._discretize(*mats['off'], toff)
        lhs = np.eye(3) - phi_off @ phi_on
        rhs = phi_off @ gam_on + gam_off
        try:
            x_ccm = np.linalg.solve(lhs, rhs)
        except np.linalg.LinAlgError:
            x_ccm = None

        if x_ccm is not None:
            # Validate: inductor current must stay non-negative over a period
            valid = x_ccm[0] >= 0.0
            if valid:
                _, clamp_idx = self._step_period(x_ccm.copy(), n_on, on_mats,
                                                 n_off, off_mats, dcm_mats)
                valid = clamp_idx is None
            if valid:
                return x_ccm

        # DCM: with the clamp substep fixed, the period map is affine
        # (x -> P x + q), so its fixed point can be solved directly.
        # Iterate on the clamp index until it is self-consistent.
        def frozen_map(x, k):
            return self._step_period(x, n_on, on_mats, n_off, off_mats,
                                     dcm_mats, frozen_k=k)[0]

        x = np.array([0.0, 0.0, ss['vout']])
        _, k = self._step_period(x.copy(), n_on, on_mats, n_off, off_mats,
                                 dcm_mats)
        for _ in range(10):
            if k is None:
                k = n_off - 1
            q = frozen_map(np.zeros(3), k)
            P = np.column_stack([frozen_map(e, k) - q for e in np.eye(3)])
            x = np.linalg.solve(np.eye(3) - P, q)
            x[0] = max(x[0], 0.0)
            x_next, k_next = self._step_period(x.copy(), n_on, on_mats,
                                               n_off, off_mats, dcm_mats)
            if k_next == k and np.max(np.abs(x_next - x)) < 1e-7:
                break
            k = k_next
        return x

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def get_visualization_data(self, simulation_result):
        """Same nearest-sample matching as the SPICE model."""
        sim_time_full = simulation_result['sim_time_full']
        measurement_time = np.asarray(simulation_result['measurement_time_points'])
        indices = np.searchsorted(sim_time_full, measurement_time)
        indices = np.clip(indices, 0, len(sim_time_full) - 1)
        mask = indices > 0
        prev_diff = np.abs(sim_time_full[indices[mask] - 1] - measurement_time[mask])
        curr_diff = np.abs(sim_time_full[indices[mask]] - measurement_time[mask])
        indices[mask][prev_diff < curr_diff] -= 1
        return {
            'sim_voltage_matched': simulation_result['sim_voltage_full'][indices],
            'sim_current_matched': simulation_result['sim_current_full'][indices],
            'sim_pwm_matched': simulation_result['sim_gate_full'][indices],
            'matched_time': measurement_time,
        }


# ----------------------------------------------------------------------
# Native (C) backend
# ----------------------------------------------------------------------

_NATIVE_LIB = None


def _load_native():
    """Compile (if needed) and load the C core, cached per process."""
    global _NATIVE_LIB
    if _NATIVE_LIB is not None:
        return _NATIVE_LIB
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, '_state_space_core.c')
    lib_path = os.path.join(here, '_state_space_core.so')
    if (not os.path.exists(lib_path)
            or os.path.getmtime(lib_path) < os.path.getmtime(src)):
        subprocess.check_call(
            ['cc', '-O3', '-shared', '-fPIC', src, '-o', lib_path, '-lm'])
    lib = ctypes.CDLL(lib_path)
    dp = ctypes.POINTER(ctypes.c_double)
    lib.ss_simulate.restype = ctypes.c_int
    lib.ss_simulate.argtypes = (
        [dp] * 6                                   # A_on,b_on,A_off,b_off,A_dcm,b_dcm
        + [ctypes.c_double] * 2                    # ton, toff
        + [ctypes.c_int] * 3                       # n_on, n_off, n_periods
        + [ctypes.c_double, dp]                    # vout_guess, out_states
    )
    lib.ss_simulate_stats.restype = ctypes.c_int
    lib.ss_simulate_stats.argtypes = (
        [dp] * 6                                   # A_on,b_on,A_off,b_off,A_dcm,b_dcm
        + [ctypes.c_double] * 2                    # ton, toff
        + [ctypes.c_int] * 3                       # n_on, n_off, n_periods
        + [ctypes.c_double] * 3                    # vout_guess, r_load, t_end
        + [dp, dp]                                 # out_states (may be NULL), out_stats
    )
    _NATIVE_LIB = lib
    return lib


class StateSpaceBuckConverterNative(StateSpaceBuckConverter):
    """Same model with the whole simulation core (discretization,
    steady-state solve, stepping) in C. Python only builds the continuous
    A/b matrices and packages the output arrays.

    After run_simulation()/run_simulation_stats(), `last_core_time_s`
    holds the raw in-process time spent inside the C core (excluding
    Python setup/packaging).
    """

    last_core_time_s = None

    @staticmethod
    def _marshal(mats):
        """Keep-alive contiguous arrays + ctypes pointers for the A/b sets."""
        keep = []
        ptrs = []
        for mode in ('on', 'off', 'dcm'):
            for arr in mats[mode]:
                a = np.ascontiguousarray(arr, dtype=np.float64)
                keep.append(a)
                ptrs.append(a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)))
        return keep, ptrs

    def run_simulation(self, measurement_time_points):
        (t_end, ton, toff, n_on, n_off, dt_on, dt_off, ss, mats,
         n_periods) = self._prepare_grid(measurement_time_points)

        if n_on == 0 or n_off == 0:
            # Degenerate 0%/100% duty — rare; use the Python path
            return super().run_simulation(measurement_time_points)

        lib = _load_native()
        keep, ptrs = self._marshal(mats)

        n_samples = 1 + n_periods * (n_on + n_off)
        states = np.empty((n_samples, 3), dtype=np.float64)
        p_states = states.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

        t0 = time.perf_counter()
        status = lib.ss_simulate(
            *ptrs,
            ctypes.c_double(ton), ctypes.c_double(toff),
            n_on, n_off, n_periods,
            ctypes.c_double(ss['vout']), p_states,
        )
        self.last_core_time_s = time.perf_counter() - t0
        if status != 0:
            raise RuntimeError('native state-space core failed (singular solve)')

        return self._package_result(states, n_on, dt_on, ton, n_off, dt_off,
                                    n_periods, t_end, measurement_time_points)

    def run_simulation_stats(self, measurement_time_points):
        """Simulate and reduce to the four detector metrics entirely in C
        (waveform never crosses the C/Python boundary)."""
        (t_end, ton, toff, n_on, n_off, dt_on, dt_off, ss, mats,
         n_periods) = self._prepare_grid(measurement_time_points)

        if n_on == 0 or n_off == 0:
            return super().run_simulation_stats(measurement_time_points)

        lib = _load_native()
        keep, ptrs = self._marshal(mats)

        stats = np.empty(4, dtype=np.float64)
        p_stats = stats.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        null_states = ctypes.POINTER(ctypes.c_double)()

        t0 = time.perf_counter()
        status = lib.ss_simulate_stats(
            *ptrs,
            ctypes.c_double(ton), ctypes.c_double(toff),
            n_on, n_off, n_periods,
            ctypes.c_double(ss['vout']),
            ctypes.c_double(self.r_load), ctypes.c_double(t_end),
            null_states, p_stats,
        )
        self.last_core_time_s = time.perf_counter() - t0
        if status != 0:
            raise RuntimeError('native state-space core failed (singular solve)')

        return {
            'voltage_mean': stats[0],
            'voltage_ripple': stats[1],
            'current_mean': stats[2],
            'current_ripple': stats[3],
        }
