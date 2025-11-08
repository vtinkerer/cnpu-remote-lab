import json
import numpy as np
import matplotlib.pyplot as plt
from .utils import filter_signal

def load_ndjson_file(filepath):
    """Load newline-delimited JSON data from file"""
    measurements = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():  # Skip empty lines
                measurements.append(json.loads(line))
    return measurements

def moving_median(signal, window_width):
    """Your current approach - MEDIAN filter"""
    pad_width = window_width // 2
    signal_padded = np.pad(signal, pad_width, mode='reflect')
    filtered = np.median(
        np.lib.stride_tricks.sliding_window_view(signal_padded, window_width),
        axis=1
    )
    return filtered

def moving_average(signal, window_width):
    """Alternative approach - MEAN filter"""
    pad_width = window_width // 2
    signal_padded = np.pad(signal, pad_width, mode='reflect')
    kernel = np.ones(window_width) / window_width
    filtered = np.convolve(signal_padded, kernel, mode='valid')
    return filtered

def hybrid_filter(signal, window_width):
    """Best of both worlds: median for spikes, then mean for smoothing"""
    # Step 1: Remove spikes with small median window
    spike_window = 5
    despiked = moving_median(signal, spike_window)
    
    # Step 2: Smooth spectrum with larger mean window
    smoothed = moving_average(despiked, window_width)
    
    return smoothed

# Load data
measurements_data = load_ndjson_file('defect-detector/raw-measurements.json')
random_measurement = measurements_data[0]
raw_signal = random_measurement['measurements']['current']

# Apply different filters
window = 17  # Your window size
filtered_median = moving_median(raw_signal, window)
filtered_mean = moving_average(raw_signal, window)
filtered_hybrid = hybrid_filter(raw_signal, window)
filtered_old = filter_signal(raw_signal, 'current')

# Plot the signals
plt.figure(figsize=(14, 10))

# Plot 1: Raw signal
plt.subplot(5, 1, 1)
plt.plot(raw_signal, label='Raw Signal', color='black', alpha=0.7)
plt.title('Raw Signal')
plt.ylabel('Current')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 2: Median filtered
plt.subplot(5, 1, 2)
plt.plot(raw_signal, label='Raw Signal', color='gray', alpha=0.3)
plt.plot(filtered_median, label='Median Filter', color='blue', linewidth=2)
plt.title('Median Filter (Window=23)')
plt.ylabel('Current')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 3: Mean filtered
plt.subplot(5, 1, 3)
plt.plot(raw_signal, label='Raw Signal', color='gray', alpha=0.3)
plt.plot(filtered_mean, label='Mean Filter', color='green', linewidth=2)
plt.title('Mean Filter (Window=23)')
plt.ylabel('Current')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 4: Hybrid filtered
plt.subplot(5, 1, 4)
plt.plot(raw_signal, label='Raw Signal', color='gray', alpha=0.3)
plt.plot(filtered_hybrid, label='Hybrid Filter', color='red', linewidth=2)
plt.title('Hybrid Filter (Median→Mean)')
plt.ylabel('Current')
plt.xlabel('Sample Index')
plt.legend()
plt.grid(True, alpha=0.3)

# Plot 5: Old filter for comparison
plt.subplot(5, 1, 5)
plt.plot(raw_signal, label='Raw Signal', color='gray', alpha=0.3)
plt.plot(filtered_old, label='Old Filter', color='purple', linewidth=2)
plt.title('Old Filter Implementation')
plt.ylabel('Current')
plt.xlabel('Sample Index')
plt.legend()
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# Optional: Comparison plot with all filters together
plt.figure(figsize=(14, 6))
plt.plot(raw_signal, label='Raw Signal', color='black', alpha=0.4, linewidth=1)
plt.plot(filtered_median, label='Median Filter', color='blue', linewidth=2, alpha=0.8)
plt.plot(filtered_mean, label='Mean Filter', color='green', linewidth=2, alpha=0.8)
plt.plot(filtered_hybrid, label='Hybrid Filter', color='red', linewidth=2, alpha=0.8)
plt.plot(filtered_old, label='Old Filter', color='purple', linewidth=2, alpha=0.8)
plt.title('Comparison of All Filtering Approaches')
plt.xlabel('Sample Index')
plt.ylabel('Current')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()