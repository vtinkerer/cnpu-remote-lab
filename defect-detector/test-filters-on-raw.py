# Read the file
import json
from .utils import filter_signal, fix_signal_spike
from .simulation import BuckConverter

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

def load_ndjson_file(filepath):
    """Load newline-delimited JSON data from file"""
    measurements = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                measurements.append(json.loads(line))
    return measurements

def load_json_file(filepath):
    """Load JSON data from file"""
    with open(filepath, 'r') as f:
        return json.load(f)

with open('defect-detector/raw-measurements.json', 'r') as f:
    content = f.read()

# Parse JSON objects (each line is a separate JSON object)
data = []
for line in content.strip().split('\n'):
    if line:
        data.append(json.loads(line))

index = 5062
sample = data[index]

rippleV = max(sample['measurements']['voltage']) - min(sample['measurements']['voltage'])
meanV = sum(sample['measurements']['voltage']) / len(sample['measurements']['voltage'])

rippleI = max(sample['measurements']['current']) - min(sample['measurements']['current'])
meanI = sum(sample['measurements']['current']) / len(sample['measurements']['current'])
                                                                            
print(f"Sample Index: {index}")
print(f"Ripple Voltage: {rippleV}")
print(f"Mean Voltage: {meanV}")
print(f"Ripple Current: {rippleI}")
print(f"Mean Current: {meanI}")

def run_simulation_with_optimized_params(circuit_params, optimization_params, time_points):
    """Run simulation with optimized parameters"""
    buck = BuckConverter(circuit_params, optimization_params)
    simulation_result = buck.run_simulation(time_points)
    
    # Get full simulation data
    sim_voltage = simulation_result['sim_voltage_full']
    sim_current = simulation_result['sim_current_full']
    
    return sim_voltage, sim_current

measurements_data = load_ndjson_file('defect-detector/filtered-current-raw-measurements.json')

print(f"Found {len(measurements_data)} measurements to process\n")

# Extract first circuit parameters and time points
print("Extracting reference circuit parameters from first measurement...")
first_measurement = measurements_data[0]
reference_circuit_params_dict = first_measurement['circuit_params']
reference_circuit_params = CircuitParams(reference_circuit_params_dict)
time_points = first_measurement['measurements']['time']
opt_params_data = load_json_file('defect-detector/optimized_parameters.json')
optimization_params = opt_params_data['best_parameters']

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

# Draw diagrams
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(2, 3, figsize=(14, 10))
fig.suptitle('Raw vs Filtered Signal Comparison', fontsize=16, fontweight='bold')
# Plot 1: Raw Voltage
ax1 = axes[0, 0]
ax1.plot(sample['measurements']['voltage'], label='Raw Voltage', color='blue')
ax1.set_title('Raw Voltage Signal', fontweight='bold')
ax1.set_xlabel('Sample Index')
ax1.set_ylabel('Voltage (V)')
ax1.grid(True, alpha=0.3)
ax1.legend()
# Plot 2: Filtered Voltage
ax2 = axes[0, 1]
ax2.plot(filter_signal(sample['measurements']['voltage'], 'voltage'), label='Filtered Voltage', color='orange')
ax2.set_title('Filtered Voltage Signal', fontweight='bold')
ax2.set_xlabel('Sample Index')
ax2.set_ylabel('Voltage (V)')
ax2.grid(True, alpha=0.3)
ax2.legend()
# Plot 3: Simulated Voltage
ax3 = axes[0, 2]
ax3.plot(sim_voltage, label='Simulated Voltage', color='green')
ax3.set_title('Simulated Voltage Signal', fontweight='bold')
ax3.set_xlabel('Sample Index')
ax3.set_ylabel('Voltage (V)')
ax3.grid(True, alpha=0.3)
ax3.legend()

# Plot 4: Raw Current
ax4 = axes[1, 0]
ax4.plot(sample['measurements']['current'], label='Raw Current', color='blue')
ax4.set_title('Raw Current Signal', fontweight='bold')
ax4.set_xlabel('Sample Index')
ax4.set_ylabel('Current (A)')
ax4.grid(True, alpha=0.3)
ax4.legend()
# Plot 5: Filtered Current
ax5 = axes[1, 1]
ax5.plot(filter_signal(sample['measurements']['current'], 'current'), label='Filtered Current', color='orange')
ax5.set_title('Filtered Current Signal', fontweight='bold')
ax5.set_xlabel('Sample Index')
ax5.set_ylabel('Current (A)')
ax5.grid(True, alpha=0.3)
ax5.legend()
# Plot 6: Simulated Current
ax6 = axes[1, 2]
ax6.plot(sim_current, label='Simulated Current', color='green')
ax6.set_title('Simulated Current Signal', fontweight='bold')
ax6.set_xlabel('Sample Index')
ax6.set_ylabel('Current (A)')
ax6.grid(True, alpha=0.3)
ax6.legend()

plt.show()