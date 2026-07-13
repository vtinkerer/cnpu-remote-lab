import json
import os
from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
from .simulation import BuckConverter
from .state_space_model import StateSpaceBuckConverter, StateSpaceBuckConverterNative
from .utils import filter_signal
from . import simulation_cache

plt.rcParams.update({
    'font.size': 20,
    'axes.labelsize': 20,
    'axes.titlesize': 20,
    'xtick.labelsize': 20,
    'ytick.labelsize': 20,
    'legend.fontsize': 20,
    'figure.titlesize': 20
})

def load_json_file(filepath):
    """Load JSON data from file"""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_ndjson_file(filepath):
    """Load newline-delimited JSON data from file"""
    measurements = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                measurements.append(json.loads(line))
    return measurements

# Percentile range used for "ripple" (instead of max-min). Picks the spread
# of the central RIPPLE_PCT_HIGH-RIPPLE_PCT_LOW % of samples — robust to
# impulsive spikes (each spike is too rare to push the high percentile up).
# A symmetric percentile range is applied to *both* simulation and measurement
# so any small residual bias cancels in the diff.
# RIPPLE_PCT_LOW = 1.0
# RIPPLE_PCT_HIGH = 99.0

# RIPPLE_PCT_LOW=1
# RIPPLE_PCT_HIGH=99


# def _ripple(samples):
#     return np.percentile(samples, RIPPLE_PCT_HIGH) - np.percentile(samples, RIPPLE_PCT_LOW)

def _ripple(samples): 
    return np.max(samples) - np.mean(samples)


def calculate_statistics(voltage, current):
    """Calculate mean and ripple for voltage and current."""
    return {
        'voltage_mean': np.mean(voltage),
        'voltage_ripple': _ripple(voltage),
        'current_mean': np.mean(current),
        'current_ripple': _ripple(current)
    }

# Simulation models compared against each other on every test case
MODEL_KEYS = ['spice', 'state_space']
MODEL_LABELS = {'spice': 'SPICE', 'state_space': 'State-space'}
MODEL_CLASSES = {'spice': BuckConverter, 'state_space': StateSpaceBuckConverterNative}


def run_simulation_with_optimized_params(circuit_params, optimization_params, time_points,
                                         model_key='spice'):
    """Run simulation with optimized parameters, cached on disk for 1h."""
    cache_key = simulation_cache.make_key(
        {**circuit_params.to_dict(), '_model': model_key},
        optimization_params,
        np.asarray(time_points),
    )
    cached = simulation_cache.get(cache_key)
    if cached is not None:
        return cached

    buck = MODEL_CLASSES[model_key](circuit_params, optimization_params)
    simulation_result = buck.run_simulation(time_points)

    sim_voltage = simulation_result['sim_voltage_full']
    sim_current = simulation_result['sim_current_full']

    simulation_cache.set(cache_key, (sim_voltage, sim_current))
    return sim_voltage, sim_current

def process_simulation_result(sim_voltage, sim_current):
    return calculate_statistics(sim_voltage, sim_current)

def process_measurement(measurement_data):
    """Process measurement data - no filtering, just calculate statistics"""
    voltage = np.asarray(measurement_data['measurements']['voltage'])
    current = filter_signal(np.asarray(measurement_data['measurements']['current']), 'current')
    
    return calculate_statistics(voltage, current)

def calculate_percentage_differences(sim_stats, meas_stats):
    """Calculate percentage differences between simulation and measurement"""
    return {
        'voltage_mean_diff': ((meas_stats['voltage_mean'] - sim_stats['voltage_mean']) / 
                              sim_stats['voltage_mean']) * 100,
        'voltage_ripple_diff': ((meas_stats['voltage_ripple'] - sim_stats['voltage_ripple']) / 
                                sim_stats['voltage_ripple']) * 100,
        'current_mean_diff': ((meas_stats['current_mean'] - sim_stats['current_mean']) / 
                              sim_stats['current_mean']) * 100,
        'current_ripple_diff': ((meas_stats['current_ripple'] - sim_stats['current_ripple']) / 
                                sim_stats['current_ripple']) * 100
    }

class CircuitParams:
    """Simple class to hold circuit parameters"""
    def __init__(self, params_dict):
        self.vin = params_dict['vin']
        self.c_value = params_dict['c_value']
        self.pwm_percentage = params_dict['pwm_percentage']
        self.r_load = params_dict['r_load']
    
    def to_dict(self):
        """Convert to dictionary for comparison"""
        return {
            'vin': self.vin,
            'c_value': self.c_value,
            'pwm_percentage': self.pwm_percentage,
            'r_load': self.r_load
        }
    
    def __eq__(self, other):
        """Check if two CircuitParams are equal"""
        if not isinstance(other, CircuitParams):
            return False
        return self.to_dict() == other.to_dict()

# THRESHOLDS = {
#     'voltage_mean': 5.34,
#     'voltage_ripple': 50.03,
#     'current_mean': 13.96,
#     'current_ripple': 50.7
# }

THRESHOLDS = {
    'voltage_mean':   5.0,   # was 5.34;  
    'voltage_ripple': 56.5,  # was 50.03; 
    'current_mean':   8.5,   # was 13.96; 
    'current_ripple': 38.0,  # was 50.7;  
}

METRIC_KEYS = ['voltage_mean', 'voltage_ripple', 'current_mean', 'current_ripple']
METRIC_TITLES = ['Voltage Mean', 'Voltage Ripple', 'Current Mean', 'Current Ripple']


def classify_vector(differences):
    """Build a 4-char +/0/- vector from a differences dict using THRESHOLDS."""
    vector = ''
    for key in METRIC_KEYS:
        diff = differences[f'{key}_diff']
        threshold = THRESHOLDS[key]
        if diff < -threshold:
            vector += '-'
        elif diff > threshold:
            vector += '+'
        else:
            vector += '0'
    return vector


def plot_comparison(all_comparisons, output_path):
    """Plot the four difference metrics for a single test case, one bar
    series per simulation model."""
    indices = np.array([c['index'] for c in all_comparisons])

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axis_positions = {
        'voltage_mean': axes[0, 0],
        'voltage_ripple': axes[0, 1],
        'current_mean': axes[1, 0],
        'current_ripple': axes[1, 1],
    }
    model_colors = {'spice': 'steelblue', 'state_space': 'darkorange'}
    width = 0.8 / len(MODEL_KEYS)

    for key, title in zip(METRIC_KEYS, METRIC_TITLES):
        ax = axis_positions[key]
        threshold = THRESHOLDS[key]
        for m_idx, model_key in enumerate(MODEL_KEYS):
            data = [c['models'][model_key]['differences'][f'{key}_diff']
                    for c in all_comparisons]
            offset = (m_idx - (len(MODEL_KEYS) - 1) / 2) * width
            ax.bar(indices + offset, data, width=width,
                   color=model_colors[model_key], alpha=0.7,
                   label=MODEL_LABELS[model_key])
        ax.axhline(y=0, color='red', linestyle='--', linewidth=1)
        ax.axhline(y=threshold, color='gray', linestyle=':', linewidth=1.5)
        ax.axhline(y=-threshold, color='gray', linestyle=':', linewidth=1.5)
        ax.set_xlabel('Measurement Index')
        ax.set_ylabel(f'% Difference of {title}')
        ax.tick_params(axis='both', which='major')
        ax.grid(axis='y', alpha=0.3)

    axes[1, 0].legend(fontsize=14)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)


def run_test_case(test_case, optimization_params, show_plot=False):
    """Run a single test case and return its results dict."""
    name = test_case['name']
    measurements_path = test_case['measurements_file']
    overrides = test_case.get('overrides', {})
    expected_vectors = set(test_case.get('expected_vectors', []))
    reference_index = test_case.get('reference_measurement_index', 0)

    print("\n" + "#" * 70)
    print(f"# TEST CASE: {name}")
    print(f"# File: {measurements_path}")
    print("#" * 70)

    measurements_data = load_ndjson_file(measurements_path)
    print(f"Loaded {len(measurements_data)} measurements")

    reference_measurement = measurements_data[reference_index]
    reference_circuit_params_dict = dict(reference_measurement['circuit_params'])
    print(f"Original reference circuit params: {reference_measurement['circuit_params']}")
    if overrides:
        reference_circuit_params_dict.update(overrides)
        print(f"Applied overrides: {overrides}")
    print(f"Effective reference circuit params: {reference_circuit_params_dict}")

    reference_circuit_params = CircuitParams(reference_circuit_params_dict)
    time_points = reference_measurement['measurements']['time']

    # Reference simulation with each model
    sim_stats_by_model = {}
    for model_key in MODEL_KEYS:
        sim_voltage, sim_current = run_simulation_with_optimized_params(
            reference_circuit_params,
            optimization_params,
            time_points,
            model_key=model_key,
        )
        sim_stats = process_simulation_result(sim_voltage, sim_current)
        sim_stats_by_model[model_key] = sim_stats
        print(
            f"Sim stats [{MODEL_LABELS[model_key]:<11}] — "
            f"V_mean={sim_stats['voltage_mean']:.4f}, "
            f"V_ripple={sim_stats['voltage_ripple']:.4f}, "
            f"I_mean={sim_stats['current_mean']:.4f}, "
            f"I_ripple={sim_stats['current_ripple']:.4f}"
        )

    all_comparisons = []
    all_vectors = {model_key: [] for model_key in MODEL_KEYS}
    for idx, measurement_entry in enumerate(measurements_data):
        meas_stats = process_measurement(measurement_entry)
        models = {}
        for model_key in MODEL_KEYS:
            differences = calculate_percentage_differences(
                sim_stats_by_model[model_key], meas_stats)
            vector = classify_vector(differences)
            all_vectors[model_key].append(vector)
            models[model_key] = {'differences': differences, 'vector': vector}
        all_comparisons.append({
            'index': idx,
            'meas_stats': meas_stats,
            'models': models,
        })

    n_meas = len(all_comparisons)

    # Per-metric diff distribution — useful for calibrating THRESHOLDS,
    # especially on the no-deviation (OK) baseline run.
    print("\nDiff distribution (% of sim) — helpful for threshold calibration:")
    print(f"  {'metric':<16} {'model':<12} {'min':>9} {'p1':>9} {'p50':>9} {'p99':>9} {'max':>9} {'p99(|d|)':>10}  threshold")
    for key in METRIC_KEYS:
        for model_key in MODEL_KEYS:
            diffs = np.array([c['models'][model_key]['differences'][f'{key}_diff']
                              for c in all_comparisons])
            abs_p99 = np.percentile(np.abs(diffs), 99)
            print(
                f"  {key:<16} {MODEL_LABELS[model_key]:<12} "
                f"{np.min(diffs):>9.2f} "
                f"{np.percentile(diffs, 1):>9.2f} "
                f"{np.percentile(diffs, 50):>9.2f} "
                f"{np.percentile(diffs, 99):>9.2f} "
                f"{np.max(diffs):>9.2f} "
                f"{abs_p99:>10.2f}  ±{THRESHOLDS[key]}"
            )

    # Vector distributions of both models side by side
    vector_counts = {m: Counter(all_vectors[m]) for m in MODEL_KEYS}
    all_seen_vectors = sorted(
        set().union(*[vector_counts[m].keys() for m in MODEL_KEYS]),
        key=lambda v: (-max(vector_counts[m][v] for m in MODEL_KEYS), v),
    )
    print(f"\nVector distribution ({n_meas} measurements):")
    header = f"  {'vector':<8}" + ''.join(f"{MODEL_LABELS[m]:>20}" for m in MODEL_KEYS)
    print(header)
    for vector in all_seen_vectors:
        in_expected = ' (expected)' if vector in expected_vectors else ''
        cells = ''.join(
            f"{vector_counts[m][vector]:>12} ({vector_counts[m][vector] / n_meas * 100:5.1f}%)"
            for m in MODEL_KEYS
        )
        print(f"  {vector:<8}{cells}{in_expected}")

    # Per-measurement correct-reason detection: a model detects the correct
    # fault reason when its vector is one of the expected vectors.
    correct_breakdown = None
    if expected_vectors and n_meas:
        correct = {
            m: np.array([v in expected_vectors for v in all_vectors[m]])
            for m in MODEL_KEYS
        }
        spice_ok = correct['spice']
        ss_ok = correct['state_space']
        correct_breakdown = {
            'both_correct': int(np.sum(spice_ok & ss_ok)),
            'spice_only': int(np.sum(spice_ok & ~ss_ok)),
            'state_space_only': int(np.sum(~spice_ok & ss_ok)),
            'both_wrong': int(np.sum(~spice_ok & ~ss_ok)),
        }
        print("\nCorrect fault-reason detection (vector in expected set):")
        for m in MODEL_KEYS:
            n_ok = int(np.sum(correct[m]))
            print(f"  {MODEL_LABELS[m]:<11}: {n_ok}/{n_meas} ({n_ok / n_meas * 100:.1f}%)")
        delta_pp = (np.sum(ss_ok) - np.sum(spice_ok)) / n_meas * 100
        print(f"  delta (State-space - SPICE): {delta_pp:+.2f} pp")
        print(f"  both correct: {correct_breakdown['both_correct']} | "
              f"only SPICE: {correct_breakdown['spice_only']} | "
              f"only State-space: {correct_breakdown['state_space_only']} | "
              f"both wrong: {correct_breakdown['both_wrong']}")

    # Pass/fail per model
    model_results = {}
    for model_key in MODEL_KEYS:
        counts = vector_counts[model_key]
        sorted_vectors = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        dominant_vector = sorted_vectors[0][0] if sorted_vectors else None
        matched = sum(count for vec, count in counts.items() if vec in expected_vectors)
        matched_pct = matched / n_meas * 100 if n_meas else 0.0
        passed = bool(expected_vectors) and dominant_vector in expected_vectors
        model_results[model_key] = {
            'dominant_vector': dominant_vector,
            'matched_count': matched,
            'matched_pct': matched_pct,
            'passed': passed,
            'vector_counts': dict(counts),
        }

    if expected_vectors:
        print(f"\nExpected vectors: {sorted(expected_vectors)}")
        for model_key in MODEL_KEYS:
            mr = model_results[model_key]
            print(
                f"  [{MODEL_LABELS[model_key]:<11}] dominant={mr['dominant_vector']} "
                f"-> {'PASS' if mr['passed'] else 'FAIL'} | "
                f"matching expected: {mr['matched_count']}/{n_meas} ({mr['matched_pct']:.1f}%)"
            )
    else:
        print("\nNo expected vectors specified — reporting only.")

    plot_filename = f"comparison_{os.path.splitext(os.path.basename(measurements_path))[0]}.png"
    plot_comparison(all_comparisons, plot_filename)
    print(f"Plot saved as '{plot_filename}'")
    if show_plot:
        plt.show()

    return {
        'name': name,
        'measurements_file': measurements_path,
        'expected_vectors': sorted(expected_vectors),
        'total': n_meas,
        'correct_breakdown': correct_breakdown,
        'models': model_results,
    }


# Test cases: (measurements file) + (overrides applied to the reference circuit
# params extracted from that file) + (expected vectors that the analysis should
# produce). The "dominant vector must be in expected_vectors" rule decides
# pass/fail; matching count/percentage is reported regardless.
TEST_CASES = [
    {
        'name': 'D=5 instead of 50 (PWM extremely low)',
        'measurements_file': 'defect-detector/raw-measurements-with-v-12-pwm-5-c-44-r-4.jsonl',
        'overrides': {'pwm_percentage': 50},
        'expected_vectors': ['-0-0', '----'],
    },
    {
        'name': 'D 40 instead of 50',
        'measurements_file': 'defect-detector/raw-measurements-with-40-pwm-instead-of-50.json',
        'overrides': {'pwm_percentage': 50},
        'expected_vectors': ['-0-0', '----'],
    },
    {
        'name': 'D 45 instead of 50',
        'measurements_file': 'defect-detector/raw-measurements-with-45-pwm-instead-of-50.json',
        'overrides': {'pwm_percentage': 50},
        'expected_vectors': ['-0-0', '----'],
    },
    # --- PWM (duty cycle) deviation tests from notes ---
    {
        'name': 'D=1 instead of 50 (PWM extremely low)',
        'measurements_file': 'defect-detector/raw-measurements-with-1-pwm-instead-of-50.json',
        # File's circuit_params has r_load=0.4 (abnormal) 
        'overrides': {'pwm_percentage': 50 },
        'expected_vectors': ['-0-0', '----'],
    },
    {
        'name': 'D=60 instead of 50 (PWM slightly high)',
        'measurements_file': 'defect-detector/raw-measurements-with-60-pwm-instead-of-50.json',
        'overrides': {'pwm_percentage': 50},
        'expected_vectors': ['+0+0', '+-+-', '+0+-'],
    },
    # --- Input voltage deviation tests from notes ---
    {
        'name': 'Vin=10V instead of 12V',
        'measurements_file': 'defect-detector/raw-measurements-with-10-volts-instead-of-12.json',
        'overrides': {'vin': 12},
        'expected_vectors': ['-0-0', '-0--'],
    },
    {
        'name': 'Vin=6V instead of 12V',
        'measurements_file': 'defect-detector/raw-measurements-with-v-6-pwm-50-c-44-r-4.jsonl',
        'overrides': {'vin': 12},
        'expected_vectors': ['-0-0', '-0--'],
    },
    {
        'name': 'Vin=14V instead of 12V',
        'measurements_file': 'defect-detector/raw-measurements-with-14-volts-instead-of-12.json',
        'overrides': {'vin': 12},
        'expected_vectors': ['++++', '+0++', '+0+0'],
    },
    {
        'name': 'Vin=18V instead of 12V',
        'measurements_file': 'defect-detector/raw-measurements-with-18-volts-instead-of-12.json',
        'overrides': {'vin': 12},
        'expected_vectors': ['++++', '+0++', '+0+0'],
    },
    # --- Load resistance deviation tests from notes ---
    {
        'name': 'R_load=2Ω instead of 4Ω',
        'measurements_file': 'defect-detector/raw-measurements-with-2-ohm-instead-of-4.json',
        'overrides': {'r_load': 4},
        'expected_vectors': ['00+0', '--+0'],
    },
    {
        'name': 'R_load=5Ω instead of 4Ω',
        'measurements_file': 'defect-detector/raw-measurements-with-5-ohm-instead-of-4.json',
        'overrides': {'r_load': 4},
        'expected_vectors': ['00-0', '+---', '+0-0'],
    },
        {
        'name': 'R_load=15Ω instead of 4Ω',
        'measurements_file': 'defect-detector/raw-measurements-with-v-12-pwm-50-c-44-r-15.jsonl',
        'overrides': {'r_load': 4},
        'expected_vectors': ['00-0', '+---', '+0-0'],
    },
    # --- Baseline: no deviation (algorithm must NOT raise a false positive) ---
    {
        'name': 'No deviation (nominal setup)',
        'measurements_file': 'defect-detector/raw-measurements-with-ok.json',
        'overrides': {},
        'expected_vectors': ['0000'],
    },
]


def main():
    print("Loading optimized parameters...")
    opt_params_data = load_json_file('defect-detector/optimized_parameters.json')
    optimization_params = opt_params_data['best_parameters']
    print(f"Optimized Parameters: {optimization_params}")

    results = []
    for test_case in TEST_CASES:
        try:
            results.append(run_test_case(test_case, optimization_params))
        except FileNotFoundError as e:
            print(f"\n[SKIP] {test_case['name']}: {e}")
            results.append({
                'name': test_case['name'],
                'measurements_file': test_case['measurements_file'],
                'expected_vectors': test_case.get('expected_vectors', []),
                'total': 0,
                'correct_breakdown': None,
                'models': {},
                'error': str(e),
            })

    print("\n" + "=" * 100)
    print("TEST CASE SUMMARY (SPICE vs State-space, % = correct fault-reason detection)")
    print("=" * 100)
    for result in results:
        if 'error' in result:
            print(f"  [SKIP] {result['name']}: {result['error']}")
            continue
        deltas = (result['models']['state_space']['matched_pct']
                  - result['models']['spice']['matched_pct'])
        print(f"  {result['name']}  (expected={result['expected_vectors']}, "
              f"delta {deltas:+.2f} pp)")
        for model_key in MODEL_KEYS:
            mr = result['models'][model_key]
            status = 'PASS' if mr['passed'] else 'FAIL'
            print(
                f"      [{status}] {MODEL_LABELS[model_key]:<11} "
                f"dominant={mr['dominant_vector']} "
                f"correct={mr['matched_count']}/{result['total']} "
                f"({mr['matched_pct']:.1f}%)"
            )

    print()
    valid = [r for r in results if 'error' not in r]
    for model_key in MODEL_KEYS:
        passed = sum(1 for r in valid if r['models'][model_key]['passed'])
        total_meas = sum(r['total'] for r in valid)
        total_correct = sum(r['models'][model_key]['matched_count'] for r in valid)
        print(f"  {MODEL_LABELS[model_key]:<11}: {passed}/{len(results)} cases passed | "
              f"correct reason on {total_correct}/{total_meas} measurements "
              f"({total_correct / total_meas * 100:.2f}%)"
              f"{'' if len(valid) == len(results) else f' ({len(results) - len(valid)} skipped)'}")
    if valid:
        total_meas = sum(r['total'] for r in valid)
        both_wrong = sum(r['correct_breakdown']['both_wrong']
                         for r in valid if r['correct_breakdown'])
        spice_only = sum(r['correct_breakdown']['spice_only']
                         for r in valid if r['correct_breakdown'])
        ss_only = sum(r['correct_breakdown']['state_space_only']
                      for r in valid if r['correct_breakdown'])
        print(f"  Disagreements: only SPICE correct on {spice_only}, "
              f"only State-space correct on {ss_only}, "
              f"both wrong on {both_wrong} of {total_meas} measurements")


if __name__ == "__main__":
    main()