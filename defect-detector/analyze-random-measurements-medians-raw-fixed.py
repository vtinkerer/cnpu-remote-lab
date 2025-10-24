import json
import matplotlib.pyplot as plt
import numpy as np
from .utils import fix_signal_spike

# Read the file
with open('defect-detector/raw-measurements.json', 'r') as f:
    content = f.read()

# Parse JSON objects (each line is a separate JSON object)
data = []
for line in content.strip().split('\n'):
    if line:
        data.append(json.loads(line))

# Extract statistics from each measurement
stats_list = []
for line in data:
    measurements = line['measurements']
    voltage = fix_signal_spike(measurements['voltage'])
    current = fix_signal_spike(measurements['current'])

    rippleV = max(voltage) - min(voltage)
    meanV = sum(voltage) / len(voltage)

    rippleI = max(current) - min(current)
    meanI = sum(current) / len(current)

    stats_list.append({
        'rippleV': rippleV,
        'meanV': meanV,
        'rippleI': rippleI,
        'meanI': meanI
    })

# Sort by each metric
sorted_by_rippleV = sorted(stats_list, key=lambda x: x['rippleV'])
sorted_by_meanV = sorted(stats_list, key=lambda x: x['meanV'])
sorted_by_rippleI = sorted(stats_list, key=lambda x: x['rippleI'])
sorted_by_meanI = sorted(stats_list, key=lambda x: x['meanI'])

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Circuit Measurements Distribution Analysis', fontsize=16, fontweight='bold')

# Plot 1: Ripple Voltage
ax1 = axes[0, 0]
rippleV_values = [s['rippleV'] for s in sorted_by_rippleV]
ax1.plot(rippleV_values, 'o-', color='#2E86AB', linewidth=2, markersize=8)
ax1.set_title('Voltage Ripple (sorted)', fontweight='bold')
ax1.set_xlabel('Measurement Index')
ax1.set_ylabel('Ripple Voltage (V)')
ax1.grid(True, alpha=0.3)
ax1.axhline(np.mean(rippleV_values), color='red', linestyle='--', 
            label=f'Mean: {np.mean(rippleV_values):.4f}V')
ax1.legend()

# Plot 2: Mean Voltage
ax2 = axes[0, 1]
meanV_values = [s['meanV'] for s in sorted_by_meanV]
ax2.plot(meanV_values, 'o-', color='#A23B72', linewidth=2, markersize=8)
ax2.set_title('Mean Voltage (sorted)', fontweight='bold')
ax2.set_xlabel('Measurement Index')
ax2.set_ylabel('Mean Voltage (V)')
ax2.grid(True, alpha=0.3)
ax2.axhline(np.mean(meanV_values), color='red', linestyle='--', 
            label=f'Mean: {np.mean(meanV_values):.4f}V')
ax2.legend()

# Plot 3: Ripple Current
ax3 = axes[1, 0]
rippleI_values = [s['rippleI'] for s in sorted_by_rippleI]
ax3.plot(rippleI_values, 'o-', color='#F18F01', linewidth=2, markersize=8)
ax3.set_title('Current Ripple (sorted)', fontweight='bold')
ax3.set_xlabel('Measurement Index')
ax3.set_ylabel('Ripple Current (A)')
ax3.grid(True, alpha=0.3)
ax3.axhline(np.mean(rippleI_values), color='red', linestyle='--', 
            label=f'Mean: {np.mean(rippleI_values):.4f}A')
ax3.legend()

# Plot 4: Mean Current
ax4 = axes[1, 1]
meanI_values = [s['meanI'] for s in sorted_by_meanI]
ax4.plot(meanI_values, 'o-', color='#6A994E', linewidth=2, markersize=8)
ax4.set_title('Mean Current (sorted)', fontweight='bold')
ax4.set_xlabel('Measurement Index')
ax4.set_ylabel('Mean Current (A)')
ax4.grid(True, alpha=0.3)
ax4.axhline(np.mean(meanI_values), color='red', linestyle='--', 
            label=f'Mean: {np.mean(meanI_values):.4f}A')
ax4.legend()

plt.tight_layout()
plt.show()

# Print summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

print("\nVoltage Ripple:")
print(f"  Min:  {min(rippleV_values):.6f} V")
print(f"  Max:  {max(rippleV_values):.6f} V")
print(f"  Mean: {np.mean(rippleV_values):.6f} V")
print(f"  Std:  {np.std(rippleV_values):.6f} V")
print(f" Median: {np.median(rippleV_values):.6f} V")
print(f"  Symmetric percentage difference between Min and Max: {100 * (max(rippleV_values) - min(rippleV_values)) / ((min(rippleV_values) + max(rippleV_values)) / 2 ):.2f}%")

print("\nMean Voltage:")
print(f"  Min:  {min(meanV_values):.6f} V")
print(f"  Max:  {max(meanV_values):.6f} V")
print(f"  Mean: {np.mean(meanV_values):.6f} V")
print(f"  Std:  {np.std(meanV_values):.6f} V")
print(f" Median: {np.median(meanV_values):.6f} V")
print(f"  Symmetric percentage difference between Min and Max: {100 * (max(meanV_values) - min(meanV_values)) / ((min(meanV_values) + max(meanV_values)) / 2 ):.2f}%")

print("\nCurrent Ripple:")
print(f"  Min:  {min(rippleI_values):.6f} A")
print(f"  Max:  {max(rippleI_values):.6f} A")
print(f"  Mean: {np.mean(rippleI_values):.6f} A")
print(f"  Std:  {np.std(rippleI_values):.6f} A")
print(f" Median: {np.median(rippleI_values):.6f} A")
print(f"  Symmetric percentage difference between Min and Max: {100 * (max(rippleI_values) - min(rippleI_values)) / ((min(rippleI_values) + max(rippleI_values)) / 2 ):.2f}%")

print("\nMean Current:")
print(f"  Min:  {min(meanI_values):.6f} A")
print(f"  Max:  {max(meanI_values):.6f} A")
print(f"  Mean: {np.mean(meanI_values):.6f} A")
print(f"  Std:  {np.std(meanI_values):.6f} A")
print(f" Median: {np.median(meanI_values):.6f} A")
print(f"  Symmetric percentage difference between Min and Max: {100 * (max(meanI_values) - min(meanI_values)) / ((min(meanI_values) + max(meanI_values)) / 2 ):.2f}%")
print("="*60)