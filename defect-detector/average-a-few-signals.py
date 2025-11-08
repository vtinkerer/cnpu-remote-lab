import json
from random import random
from .simulation import BuckConverter
import numpy as np

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

# Load all measurements
measurements_data = load_ndjson_file('defect-detector/raw-measurements.json')

# Number of signals to average
num_signals = 10  # Change this to 5 or any other number

# Select the first num_signals measurements
selected_measurements = measurements_data[:num_signals]

# Extract time array (assuming all measurements have the same time points)
time = np.array(selected_measurements[0]['measurements']['time'])

# Collect all current signals
current_signals = []
for measurement in selected_measurements:
    current_signals.append(np.array(measurement['measurements']['current']))

# Average the current signals
averaged_current = np.mean(current_signals, axis=0)

# Use the circuit parameters from the first measurement for simulation
circuit_params = CircuitParams(selected_measurements[0]['circuit_params'])

# SIMULATE THE CIRCUIT WITH THE GIVEN PARAMETERS
simulator = BuckConverter(circuit_params)
simulation_result = simulator.run_simulation(time)

# PLOT CURRENT SIGNAL AND HARMONICS
import matplotlib.pyplot as plt
from scipy import signal

# Use the averaged current signal
value = averaged_current

# Calculate FFT for averaged measured signal
fft_values = np.fft.fft(value)
fft_freq = np.fft.fftfreq(len(value), d=(time[1] - time[0]))

# Filter: Keep only frequencies below a cutoff (e.g., 2 MHz)
cutoff_frequency = 0.4  # MHz - adjust this value as needed
fft_filtered = fft_values.copy()
fft_filtered[np.abs(fft_freq) > cutoff_frequency] = 0

# Reconstruct signal using inverse FFT
reconstructed_signal = np.fft.ifft(fft_filtered).real

# Apply IIR Butterworth low-pass filter
# Calculate sampling frequency
sampling_period = time[1] - time[0]  # in microseconds
fs = 1.0 / sampling_period  # Sampling frequency in MHz

# Design Butterworth filter (4th order)
# Normalize cutoff frequency (cutoff / Nyquist frequency)
nyquist_freq = fs / 2
normalized_cutoff = cutoff_frequency / nyquist_freq

print(f"Averaged {num_signals} signals")
print(f"Normalized cutoff: {normalized_cutoff}")
print(f"Cutoff frequency: {cutoff_frequency}")

# Design the filter
order = 4  # Filter order
b, a = signal.butter(order, normalized_cutoff, btype='low', analog=False)

# Apply the filter (using filtfilt for zero-phase filtering)
iir_filtered_signal = signal.filtfilt(b, a, value)

# Calculate FFT for simulated signal
sim_time = np.array(simulation_result['sim_time_full'])
sim_current = np.array(simulation_result['sim_current_full'])
fft_sim = np.fft.fft(sim_current)
fft_freq_sim = np.fft.fftfreq(len(sim_current), d=(sim_time[-5] - sim_time[-4]))

# Create figure with 3 subplots
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 14))

# Plot 1: Averaged time domain signal
ax1.plot(time, value, label=f'Averaged ({num_signals} signals)', alpha=0.6)
ax1.plot(sim_time, sim_current, label='Simulated', linestyle='--', alpha=0.8)
ax1.set_xlabel('Time (µs)')
ax1.set_ylabel('Current (A)')
ax1.set_title('Current Signal (Averaged)')
ax1.legend()
ax1.grid()

# Plot 2: Averaged signal frequency spectrum
positive_freq_idx = fft_freq > 0
frequencies = fft_freq[positive_freq_idx]
magnitudes = np.abs(fft_values[positive_freq_idx])

ax2.plot(frequencies, magnitudes)
ax2.set_xlabel('Frequency (MHz)')
ax2.set_ylabel('Magnitude')
ax2.set_title('Averaged Signal Frequency Spectrum')
ax2.legend()
ax2.grid()

# Plot 3: Simulated signal frequency spectrum
positive_freq_idx_sim = fft_freq_sim > 0
frequencies_sim = fft_freq_sim[positive_freq_idx_sim]
magnitudes_sim = np.abs(fft_sim[positive_freq_idx_sim])

ax3.plot(frequencies_sim, magnitudes_sim, color='green')
ax3.set_xlabel('Frequency (MHz)')
ax3.set_ylabel('Magnitude')
ax3.set_title('Simulated Signal Frequency Spectrum')
ax3.grid()

plt.tight_layout()
plt.show()