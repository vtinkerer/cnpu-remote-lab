import json
import numpy as np
import matplotlib.pyplot as plt
from .simulation import BuckConverter

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

def calculate_statistics(voltage, current):
    """Calculate mean and ripple for voltage and current"""
    return {
        'voltage_mean': np.mean(voltage),
        'voltage_ripple': np.max(voltage) - np.min(voltage),
        'current_mean': np.mean(current),
        'current_ripple': np.max(current) - np.min(current)
    }

def run_simulation_with_optimized_params(circuit_params, optimization_params, time_points):
    """Run simulation with optimized parameters"""
    buck = BuckConverter(circuit_params, optimization_params)
    simulation_result = buck.run_simulation(time_points)
    
    # Get full simulation data
    sim_voltage = simulation_result['sim_voltage_full']
    sim_current = simulation_result['sim_current_full']
    
    return sim_voltage, sim_current

def process_simulation_result(sim_voltage, sim_current):
    return calculate_statistics(sim_voltage, sim_current)

def process_measurement(measurement_data):
    """Process measurement data - no filtering, just calculate statistics"""
    voltage = np.asarray(measurement_data['measurements']['measurements']['voltage'])
    current = np.asarray(measurement_data['measurements']['measurements']['current'])
    
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

def main():
    # Load optimized parameters
    print("Loading optimized parameters...")
    opt_params_data = load_json_file('defect-detector/optimized_parameters.json')
    optimization_params = opt_params_data['best_parameters']
    
    print(f"Optimized Parameters: {optimization_params}\n")

    # Load random measurements
    print("Loading random measurements...")
    measurements_data = load_ndjson_file('defect-detector/filtered-random-measurements.json')
    
    print(f"Found {len(measurements_data)} measurements to process\n")
    
    # Extract first circuit parameters and time points
    print("Extracting reference circuit parameters from first measurement...")
    first_measurement = measurements_data[0]
    reference_circuit_params_dict = first_measurement['measurements']['circuit_params']
    reference_circuit_params = CircuitParams(reference_circuit_params_dict)
    time_points = first_measurement['measurements']['measurements']['time']
    
    print(f"Reference circuit parameters:")
    print(f"  Vin: {reference_circuit_params.vin}")
    print(f"  C_value: {reference_circuit_params.c_value}")
    print(f"  PWM percentage: {reference_circuit_params.pwm_percentage}")
    print(f"  R_load: {reference_circuit_params.r_load}\n")
    
    # Run simulation ONCE with reference parameters
    print("Running simulation with reference circuit parameters and optimized params...")
    sim_voltage, sim_current = run_simulation_with_optimized_params(
        reference_circuit_params,
        optimization_params,
        time_points
    )
    
    # Process simulation result ONCE
    print("Processing simulation result with filtering and spike removal...")
    sim_stats = process_simulation_result(sim_voltage, sim_current)
    print(f"Simulation statistics calculated:\n")
    print(f"  Voltage Mean: {sim_stats['voltage_mean']:.4f}")
    print(f"  Voltage Ripple: {sim_stats['voltage_ripple']:.4f}")
    print(f"  Current Mean: {sim_stats['current_mean']:.4f}")
    print(f"  Current Ripple: {sim_stats['current_ripple']:.4f}\n")
    
    # Store all results
    all_comparisons = []
    
    # Process each measurement
    for idx, measurement_entry in enumerate(measurements_data):
        # print(f"Processing measurement {idx + 1}/{len(measurements_data)}...")
        
        # Extract circuit parameters from this measurement
        circuit_params_dict = measurement_entry['measurements']['circuit_params']
        circuit_params = CircuitParams(circuit_params_dict)
        
        # Verify that circuit parameters match the reference
        if circuit_params != reference_circuit_params:
            print(f"  WARNING: Circuit parameters differ from reference!")
            print(f"  Expected: {reference_circuit_params.to_dict()}")
            print(f"  Got: {circuit_params.to_dict()}")
            print(f"  Skipping this measurement...\n")
            continue
        
        # Process measurement (no filtering, just raw statistics)
        meas_stats = process_measurement(measurement_entry)
        
        # Calculate differences
        differences = calculate_percentage_differences(sim_stats, meas_stats)
        
        # Store results
        comparison = {
            'index': idx,
            'sim_stats': sim_stats,
            'meas_stats': meas_stats,
            'differences': differences
        }
        all_comparisons.append(comparison)
        
        # print(f"  Voltage Mean Diff: {differences['voltage_mean_diff']:.2f}%")
        # print(f"  Voltage Ripple Diff: {differences['voltage_ripple_diff']:.2f}%")
        # print(f"  Current Mean Diff: {differences['current_mean_diff']:.2f}%")
        # print(f"  Current Ripple Diff: {differences['current_ripple_diff']:.2f}%\n")
    
    # Check if we have valid comparisons
    if not all_comparisons:
        print("ERROR: No valid comparisons were made. All measurements had different circuit parameters.")
        return
    
    # Extract data for plotting
    indices = [c['index'] for c in all_comparisons]
    voltage_mean_diffs = [c['differences']['voltage_mean_diff'] for c in all_comparisons]
    voltage_ripple_diffs = [c['differences']['voltage_ripple_diff'] for c in all_comparisons]
    current_mean_diffs = [c['differences']['current_mean_diff'] for c in all_comparisons]
    current_ripple_diffs = [c['differences']['current_ripple_diff'] for c in all_comparisons]
    
    # Create comprehensive comparison plot
    print("Generating comprehensive comparison plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Percentage Differences: All Measurements vs Optimized Simulation', 
                 fontsize=16, fontweight='bold')
    
    # Plot 1: Voltage Mean Differences
    ax1 = axes[0, 0]
    bars1 = ax1.bar(indices, voltage_mean_diffs, color='steelblue', alpha=0.7, edgecolor='black')
    ax1.axhline(y=0, color='red', linestyle='--', linewidth=1, label='Zero Difference')
    ax1.set_xlabel('Measurement Index')
    ax1.set_ylabel('Percentage Difference (%)')
    ax1.set_title('Voltage Mean Difference')
    ax1.grid(axis='y', alpha=0.3)
    ax1.legend()
    
    # Color bars based on magnitude
    for bar, diff in zip(bars1, voltage_mean_diffs):
        if abs(diff) < 5:
            bar.set_color('green')
        elif abs(diff) < 10:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    # Plot 2: Voltage Ripple Differences
    ax2 = axes[0, 1]
    bars2 = ax2.bar(indices, voltage_ripple_diffs, color='steelblue', alpha=0.7, edgecolor='black')
    ax2.axhline(y=0, color='red', linestyle='--', linewidth=1, label='Zero Difference')
    ax2.set_xlabel('Measurement Index')
    ax2.set_ylabel('Percentage Difference (%)')
    ax2.set_title('Voltage Ripple Difference')
    ax2.grid(axis='y', alpha=0.3)
    ax2.legend()
    
    for bar, diff in zip(bars2, voltage_ripple_diffs):
        if abs(diff) < 5:
            bar.set_color('green')
        elif abs(diff) < 10:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    # Plot 3: Current Mean Differences
    ax3 = axes[1, 0]
    bars3 = ax3.bar(indices, current_mean_diffs, color='steelblue', alpha=0.7, edgecolor='black')
    ax3.axhline(y=0, color='red', linestyle='--', linewidth=1, label='Zero Difference')
    ax3.set_xlabel('Measurement Index')
    ax3.set_ylabel('Percentage Difference (%)')
    ax3.set_title('Current Mean Difference')
    ax3.grid(axis='y', alpha=0.3)
    ax3.legend()
    
    for bar, diff in zip(bars3, current_mean_diffs):
        if abs(diff) < 5:
            bar.set_color('green')
        elif abs(diff) < 10:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    # Plot 4: Current Ripple Differences
    ax4 = axes[1, 1]
    bars4 = ax4.bar(indices, current_ripple_diffs, color='steelblue', alpha=0.7, edgecolor='black')
    ax4.axhline(y=0, color='red', linestyle='--', linewidth=1, label='Zero Difference')
    ax4.set_xlabel('Measurement Index')
    ax4.set_ylabel('Percentage Difference (%)')
    ax4.set_title('Current Ripple Difference')
    ax4.grid(axis='y', alpha=0.3)
    ax4.legend()
    
    for bar, diff in zip(bars4, current_ripple_diffs):
        if abs(diff) < 5:
            bar.set_color('green')
        elif abs(diff) < 10:
            bar.set_color('orange')
        else:
            bar.set_color('red')
    
    plt.tight_layout()
    plt.savefig('all_measurements_comparison.png', dpi=300, bbox_inches='tight')
    print("Plot saved as 'all_measurements_comparison.png'")
    plt.show()
    
    # Create summary statistics plot
    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
    fig2.suptitle('Summary Statistics: Percentage Differences Distribution', 
                  fontsize=16, fontweight='bold')
    
    metrics = [voltage_mean_diffs, voltage_ripple_diffs, current_mean_diffs, current_ripple_diffs]
    titles = ['Voltage Mean', 'Voltage Ripple', 'Current Mean', 'Current Ripple']
    
    for ax, data, title in zip(axes2.flat, metrics, titles):
        ax.hist(data, bins=15, color='steelblue', alpha=0.7, edgecolor='black')
        ax.axvline(x=0, color='red', linestyle='--', linewidth=2, label='Zero Difference')
        ax.axvline(x=np.mean(data), color='green', linestyle='--', linewidth=2, label=f'Mean: {np.mean(data):.2f}%')
        ax.set_xlabel('Percentage Difference (%)')
        ax.set_ylabel('Frequency')
        ax.set_title(f'{title} Distribution')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('difference_distributions.png', dpi=300, bbox_inches='tight')
    print("Plot saved as 'difference_distributions.png'")
    plt.show()
    
    # Create box plot for all metrics
    fig3, ax = plt.subplots(figsize=(12, 8))
    box_data = [voltage_mean_diffs, voltage_ripple_diffs, current_mean_diffs, current_ripple_diffs]
    box_labels = ['Voltage\nMean', 'Voltage\nRipple', 'Current\nMean', 'Current\nRipple']
    
    bp = ax.boxplot(box_data, labels=box_labels, patch_artist=True, 
                    notch=True, showmeans=True)
    
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    
    ax.axhline(y=0, color='red', linestyle='--', linewidth=1, label='Zero Difference')
    ax.set_ylabel('Percentage Difference (%)')
    ax.set_title('Box Plot: Percentage Differences Across All Measurements')
    ax.grid(axis='y', alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('boxplot_comparison.png', dpi=300, bbox_inches='tight')
    print("Plot saved as 'boxplot_comparison.png'")
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    for metric_name, data in zip(titles, metrics):
        print(f"\n{metric_name}:")
        print(f"  Mean: {np.mean(data):.2f}%")
        print(f"  Median: {np.median(data):.2f}%")
        print(f"  Std Dev: {np.std(data):.2f}%")
        print(f"  Min: {np.min(data):.2f}%")
        print(f"  Max: {np.max(data):.2f}%")
        print(f"  Range: {np.max(data) - np.min(data):.2f}%")
        
        # Count how many are within acceptable ranges
        within_5 = sum(1 for d in data if abs(d) < 5)
        within_10 = sum(1 for d in data if abs(d) < 10)
        total = len(data)
        
        print(f"  Within ±5%: {within_5}/{total} ({within_5/total*100:.1f}%)")
        print(f"  Within ±10%: {within_10}/{total} ({within_10/total*100:.1f}%)")

if __name__ == "__main__":
    main()