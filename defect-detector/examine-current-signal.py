import json
from random import random
from .simulation import BuckConverter
from .utils import filter_signal

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

measurements_data = load_ndjson_file('defect-detector/raw-measurements.json')
random_measurement = measurements_data[0]

raw_signal = random_measurement['measurements']
circuit_params = CircuitParams(random_measurement['circuit_params'])
time = random_measurement['measurements']['time']

# SIMULATE THE CIRCUIT WITH THE GIVEN PARAMETERS
simulator = BuckConverter(circuit_params)
simulation_result = simulator.run_simulation(
    time
)

# PLOT CURRENT SIGNAL AND HARMONICS
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

time = np.array(raw_signal['time'])
value = np.array(raw_signal['current'])

# Calculate FFT for measured signal
fft_values = np.fft.fft(value)
fft_freq = np.fft.fftfreq(len(value), d=(time[1] - time[0]))

sampling_step = 0.01e-6 # 0.01 microseconds
sampling_frequency = 1.0 / sampling_step  # in MHz
fundamental_frequency = 312e03  # 312 kHz
smoothing_factor = 6

window_size = (sampling_frequency / fundamental_frequency) / smoothing_factor
print(f"Window size for moving average: {window_size}")



# Filter: Keep only frequencies below a cutoff (e.g., 2 MHz)
cutoff_frequency = 0.4  # MHz - adjust this value as needed
fft_filtered = fft_values.copy()
fft_filtered[np.abs(fft_freq) > cutoff_frequency] = 0
# Filter: Remove frequencies above 0.01 MHz and below 0.3 MHz
fft_filtered[(np.abs(fft_freq) > 0.01) & (np.abs(fft_freq) < 0.3)] = 0


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


print(normalized_cutoff)
print(cutoff_frequency)
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

filtered_moving_average_signal = filter_signal(np.array(raw_signal['current']), signal_type='current')

# Create figure with 4 subplots
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 14))

# Plot 1: Original time domain signal
ax1.plot(time, value, label='Original', alpha=0.6)
ax1.plot(time, reconstructed_signal, label='FFT Reconstructed (filtered)', alpha=0.7)
# ax1.plot(time, iir_filtered_signal, label='IIR Filtered (Butterworth)', linewidth=2)
ax1.plot(time, filtered_moving_average_signal, label='Moving Average Filtered', linewidth=2)
ax1.plot(sim_time, sim_current, label='Simulated', linestyle='--', alpha=0.8)
ax1.set_xlabel('Time (µs)')
ax1.set_ylabel('Current (A)')
ax1.set_title('Current Signal - Original vs Filtered vs Simulated')
ax1.legend()
ax1.grid()

# Plot 2: Original frequency spectrum
positive_freq_idx = fft_freq > 0
frequencies = fft_freq[positive_freq_idx]
magnitudes = np.abs(fft_values[positive_freq_idx])

ax2.plot(frequencies, magnitudes)
ax2.axvline(x=cutoff_frequency, color='r', linestyle='--', label=f'Cutoff: {cutoff_frequency} MHz')
ax2.set_xlabel('Frequency (MHz)')
ax2.set_ylabel('Magnitude')
ax2.set_title('Original Frequency Spectrum')
ax2.legend()
ax2.grid()

# Plot 3: Filtered frequency spectrum
magnitudes_filtered = np.abs(fft_filtered[positive_freq_idx])
ax3.plot(frequencies, magnitudes_filtered)
ax3.axvline(x=cutoff_frequency, color='r', linestyle='--', label=f'Cutoff: {cutoff_frequency} MHz')
ax3.set_xlabel('Frequency (MHz)')
ax3.set_ylabel('Magnitude')
ax3.set_title('Filtered Frequency Spectrum')
ax3.legend()
ax3.grid()

# Plot 4: Simulated signal frequency spectrum
positive_freq_idx_sim = fft_freq_sim > 0
frequencies_sim = fft_freq_sim[positive_freq_idx_sim]
magnitudes_sim = np.abs(fft_sim[positive_freq_idx_sim])

ax4.plot(frequencies_sim, magnitudes_sim, color='green')
ax4.set_xlabel('Frequency (MHz)')
ax4.set_ylabel('Magnitude')
ax4.set_title('Simulated Signal Frequency Spectrum')
ax4.grid()

plt.tight_layout()
plt.show()