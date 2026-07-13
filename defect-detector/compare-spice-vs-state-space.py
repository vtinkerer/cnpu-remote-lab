"""Compare the SPICE model (simulation.BuckConverter) against the
state-space model (state_space_model.StateSpaceBuckConverter): accuracy of
the four detector metrics and wall-clock speed.

Run from the repo root:
    python3 -m defect-detector.compare-spice-vs-state-space
"""

import json
import time

import numpy as np
import matplotlib.pyplot as plt

from .simulation import BuckConverter
from .state_space_model import StateSpaceBuckConverter, StateSpaceBuckConverterNative


class CircuitParams:
    def __init__(self, vin, c_value, pwm_percentage, r_load):
        self.vin = vin
        self.c_value = c_value
        self.pwm_percentage = pwm_percentage
        self.r_load = r_load


def _ripple(samples):
    return np.max(samples) - np.mean(samples)


def stats(result):
    v = result['sim_voltage_full']
    i = result['sim_current_full']
    return {
        'voltage_mean': np.mean(v),
        'voltage_ripple': _ripple(v),
        'current_mean': np.mean(i),
        'current_ripple': _ripple(i),
    }


def timed_run(model_cls, params, opt_params, time_points, repeats):
    """Build + run `repeats` times; return (best_s, best_core_s, last_result).

    best_core_s is the raw in-process time inside the native C core
    (None for models without one).
    """
    best = np.inf
    best_core = np.inf
    result = None
    for _ in range(repeats):
        t0 = time.perf_counter()
        model = model_cls(params, opt_params)
        result = model.run_simulation(time_points)
        best = min(best, time.perf_counter() - t0)
        core = getattr(model, 'last_core_time_s', None)
        if core is not None:
            best_core = min(best_core, core)
    return best, (best_core if np.isfinite(best_core) else None), result


CASES = [
    ('Nominal (Vin=12, D=50%, R=4.1)', CircuitParams(12, 44, 50, 4.1)),
    ('Low Vin (Vin=6)', CircuitParams(6, 44, 50, 4.1)),
    ('High duty (D=60%)', CircuitParams(12, 44, 60, 4.1)),
    ('Light load (R=15)', CircuitParams(12, 44, 50, 15)),
    ('DCM (D=5%)', CircuitParams(12, 44, 5, 4.1)),
]


def main():
    with open('defect-detector/optimized_parameters.json') as f:
        opt_params = json.load(f)['best_parameters']

    # Standard measurement grid: 600 points, 0 .. 5.99 us
    time_points = np.arange(600) * 0.01

    fig, axes = plt.subplots(len(CASES), 2, figsize=(16, 4 * len(CASES)))
    rows = []

    for row_idx, (name, params) in enumerate(CASES):
        print(f'\n=== {name} ===')
        t_spice, _, res_spice = timed_run(BuckConverter, params, opt_params,
                                          time_points, repeats=3)
        t_ss, _, res_ss = timed_run(StateSpaceBuckConverter, params, opt_params,
                                    time_points, repeats=10)
        t_nat, t_core, res_nat = timed_run(StateSpaceBuckConverterNative, params,
                                           opt_params, time_points, repeats=100)

        # Native must reproduce the Python state-space model bit-for-bit
        # (same math, same order of operations up to expm implementation)
        nat_dev = max(
            np.max(np.abs(res_nat['sim_voltage_full'] - res_ss['sim_voltage_full'])),
            np.max(np.abs(res_nat['sim_current_full'] - res_ss['sim_current_full'])),
        )

        s_spice, s_ss = stats(res_spice), stats(res_ss)
        print(f"  {'metric':<16} {'SPICE':>10} {'state-space':>12} {'diff %':>8}")
        diffs = {}
        for key in ('voltage_mean', 'voltage_ripple', 'current_mean', 'current_ripple'):
            ref = s_spice[key]
            diff = (s_ss[key] - ref) / ref * 100 if ref != 0 else np.nan
            diffs[key] = diff
            print(f"  {key:<16} {ref:>10.4f} {s_ss[key]:>12.4f} {diff:>8.2f}")
        speedup = t_spice / t_nat
        print(f"  native vs python max waveform deviation: {nat_dev:.2e}")
        print(f"  time: SPICE {t_spice*1e3:.1f} ms | SS python {t_ss*1e3:.2f} ms "
              f"| SS native {t_nat*1e3:.3f} ms (core {t_core*1e6:.0f} us) "
              f"| native speedup vs SPICE x{speedup:.0f}")
        rows.append((name, t_spice, t_ss, t_nat, t_core, diffs))

        for col, (key, label) in enumerate((('sim_voltage_full', 'Voltage [V]'),
                                            ('sim_current_full', 'Current [A]'))):
            ax = axes[row_idx, col]
            ax.plot(res_spice['sim_time_full'], res_spice[key],
                    label='SPICE', lw=1.2)
            ax.plot(res_ss['sim_time_full'], res_ss[key],
                    label='state-space', lw=1.2, ls='--')
            ax.set_title(f'{name}', fontsize=11)
            ax.set_xlabel('t [us]')
            ax.set_ylabel(label)
            ax.grid(alpha=0.3)
            if row_idx == 0 and col == 0:
                ax.legend()

    plt.tight_layout()
    out = 'spice_vs_state_space.png'
    plt.savefig(out, dpi=150, bbox_inches='tight')
    print(f"\nWaveform overlay saved to '{out}'")

    print('\n' + '=' * 100)
    print('SUMMARY')
    print('=' * 100)
    print(f"{'case':<32} {'SPICE ms':>9} {'SS-py ms':>9} {'SS-nat ms':>10} "
          f"{'core us':>8} {'nat spdup':>10} {'max |diff| %':>13}")
    for name, t_spice, t_ss, t_nat, t_core, diffs in rows:
        worst = max(abs(d) for d in diffs.values())
        print(f"{name:<32} {t_spice*1e3:>9.1f} {t_ss*1e3:>9.2f} {t_nat*1e3:>10.3f} "
              f"{t_core*1e6:>8.0f} {'x%.0f' % (t_spice/t_nat):>10} {worst:>13.2f}")


if __name__ == '__main__':
    main()
