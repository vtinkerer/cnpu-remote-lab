import json
import matplotlib.pyplot as plt
import numpy as np
from .utils import filter_signal

# Read the file
with open('defect-detector/raw-measurements-with-ok.json', 'r') as f:
    content = f.read()

# Parse JSON objects (each line is a separate JSON object)
data = []
for line in content.strip().split('\n'):
    if line:
        data.append(json.loads(line))

# Extract statistics from each measurement
stats_list = []
for idx, measurement in enumerate(data):
    voltage = measurement['measurements']['voltage']
    current = filter_signal(measurement['measurements']['current'], 'current')
    measurement['measurements']['current'] = list(current)

    rippleV = max(voltage) - min(voltage)
    rippleI = max(current) - min(current)

    meanV = np.mean(voltage)
    meanI = np.mean(current)

    stats_list.append({
        'index': idx,
        'rippleV': rippleV,
        'meanV': meanV,
        'rippleI': rippleI,
        'meanI': meanI,
        'original_data': measurement
    })

# Extract ripple values
rippleV_values = np.array([s['rippleV'] for s in stats_list])
rippleI_values = np.array([s['rippleI'] for s in stats_list])

# Calculate midpoints (min + max) / 2
midpoint_rippleV = (np.min(rippleV_values) + np.max(rippleV_values)) / 2
midpoint_rippleI = (np.min(rippleI_values) + np.max(rippleI_values)) / 2

# Normalize the values (z-score normalization)
# This accounts for different scales between voltage and current ripples
rippleV_normalized = (rippleV_values - np.mean(rippleV_values)) / np.std(rippleV_values)
rippleI_normalized = (rippleI_values - np.mean(rippleI_values)) / np.std(rippleI_values)

# Calculate normalized midpoints
midpoint_rippleV_norm = (np.min(rippleV_normalized) + np.max(rippleV_normalized)) / 2
midpoint_rippleI_norm = (np.min(rippleI_normalized) + np.max(rippleI_normalized)) / 2

# Since voltage ripples are smaller in magnitude, give them higher weight
# This ensures they contribute equally to the distance calculation
weight_V = 1.0  # Give voltage ripple 2x importance
weight_I = 1.0

# Calculate weighted distance from midpoint for each measurement
distances = []
for i, stats in enumerate(stats_list):
    # Use the actual midpoint values, not normalized midpoints
    dist_V = weight_V * ((rippleV_values[i] - midpoint_rippleV) / np.std(rippleV_values)) ** 2
    dist_I = weight_I * ((rippleI_values[i] - midpoint_rippleI) / np.std(rippleI_values)) ** 2
    total_distance = np.sqrt(dist_V + dist_I)
    distances.append(total_distance)
    stats['distance_from_midpoint'] = total_distance

# Find the measurement closest to the midpoint
midpoint_measurement_idx = np.argmin(distances)
midpoint_measurement = stats_list[midpoint_measurement_idx]

# Sort by each metric for plotting
sorted_by_rippleV = sorted(stats_list, key=lambda x: x['rippleV'])
sorted_by_meanV = sorted(stats_list, key=lambda x: x['meanV'])
sorted_by_rippleI = sorted(stats_list, key=lambda x: x['rippleI'])
sorted_by_meanI = sorted(stats_list, key=lambda x: x['meanI'])

# Set global font sizes for better readability
plt.rcParams.update({
    'font.size': 20,
    'axes.labelsize': 20,
    'axes.titlesize': 20,
    'xtick.labelsize': 20,
    'ytick.labelsize': 20,
    'legend.fontsize': 20,
    'figure.titlesize': 20
})

# Create figure with subplots - increased height for taller charts
fig, axes = plt.subplots(2, 1, figsize=(12, 22))
# fig.suptitle('Circuit Measurements Distribution Analysis', fontsize=22, fontweight='bold')

# # Plot 1: Ripple Voltage
# ax1 = axes[0, 0]
# rippleV_sorted = [s['rippleV'] for s in sorted_by_rippleV]
# ax1.plot(rippleV_sorted, 'o-', color='#2E86AB', linewidth=2, markersize=8)
# ax1.set_title('Voltage Ripple (sorted)', fontweight='bold')
# ax1.set_xlabel('Measurement Index')
# ax1.set_ylabel('Ripple Voltage (V)')
# ax1.grid(True, alpha=0.3)
# ax1.axhline(midpoint_rippleV, color='red', linestyle='--', 
#             label=f'Midpoint: {midpoint_rippleV:.4f}V')
# ax1.axhline(midpoint_measurement['rippleV'], color='green', linestyle=':', linewidth=2,
#             label=f'Closest to Midpoint: {midpoint_measurement["rippleV"]:.4f}V')
# ax1.legend()

# # Plot 2: Mean Voltage
# ax2 = axes[0, 1]
# meanV_values = [s['meanV'] for s in sorted_by_meanV]
# ax2.plot(meanV_values, 'o-', color='#A23B72', linewidth=2, markersize=8)
# ax2.set_title('Mean Voltage (sorted)', fontweight='bold')
# ax2.set_xlabel('Measurement Index')
# ax2.set_ylabel('Mean Voltage (V)')
# ax2.grid(True, alpha=0.3)
# ax2.axhline(np.mean(meanV_values), color='red', linestyle='--', 
#             label=f'Mean: {np.mean(meanV_values):.4f}V')
# ax2.legend()

# # Plot 3: Ripple Current
# ax3 = axes[1, 0]
# rippleI_sorted = [s['rippleI'] for s in sorted_by_rippleI]
# ax3.plot(rippleI_sorted, 'o-', color='#F18F01', linewidth=2, markersize=8)
# ax3.set_title('Current Ripple (sorted)', fontweight='bold')
# ax3.set_xlabel('Measurement Index')
# ax3.set_ylabel('Ripple Current (A)')
# ax3.grid(True, alpha=0.3)
# ax3.axhline(midpoint_rippleI, color='red', linestyle='--', 
#             label=f'Midpoint: {midpoint_rippleI:.4f}A')
# ax3.axhline(midpoint_measurement['rippleI'], color='green', linestyle=':', linewidth=2,
#             label=f'Closest to Midpoint: {midpoint_measurement["rippleI"]:.4f}A')
# ax3.legend()

# # Plot 4: Mean Current
# ax4 = axes[1, 1]
# meanI_values = [s['meanI'] for s in sorted_by_meanI]
# ax4.plot(meanI_values, 'o-', color='#6A994E', linewidth=2, markersize=8)
# ax4.set_title('Mean Current (sorted)', fontweight='bold')
# ax4.set_xlabel('Measurement Index')
# ax4.set_ylabel('Mean Current (A)')
# ax4.grid(True, alpha=0.3)
# ax4.axhline(np.mean(meanI_values), color='red', linestyle='--', 
#             label=f'Mean: {np.mean(meanI_values):.4f}A')
# ax4.legend()

# Plot 5: Scatter plot showing relationship between ripples
ax5 = axes[0]
ax5.scatter(rippleV_values, rippleI_values, alpha=0.6, s=80, color='#2E86AB')
ax5.scatter(midpoint_measurement['rippleV'], midpoint_measurement['rippleI'], 
            color='green', s=300, marker='D', label='Closest to Midpoint Measurement', 
            edgecolors='black', linewidth=2)
ax5.set_xlabel('Voltage Ripple (V)')
ax5.set_ylabel('Current Ripple (A)')
# ax5.set_title('Ripple Relationship', fontweight='bold', fontsize=20)
# Add annotation pointing to the midpoint
ax5.annotate(f'Min: {midpoint_measurement["distance_from_midpoint"]:.4f}',
             xy=(midpoint_measurement['rippleV'], midpoint_measurement['rippleI']),
             xytext=(midpoint_measurement['rippleV'] + 0.02, midpoint_measurement['rippleI'] + 0.3),
             arrowprops=dict(arrowstyle='->', color='green', lw=2),
              fontweight='bold', color='darkgreen',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.7))
ax5.grid(True, alpha=0.3)
ax5.tick_params(axis='both', which='major')

# Plot 6: Distance distribution
ax6 = axes[1]
sorted_distances = sorted(distances)
ax6.plot(sorted_distances, 'o-', color='#6A4C93', linewidth=2, markersize=8)
ax6.axhline(midpoint_measurement['distance_from_midpoint'], color='green', 
            linestyle=':', linewidth=2, label=f'Min Distance: {midpoint_measurement["distance_from_midpoint"]:.4f}')
ax6.set_xlabel('Measurement Index (sorted by distance)')
ax6.set_ylabel('Normalized Distance from Midpoint')
# ax6.set_title('Distance from Midpoint (sorted)', fontweight='bold', fontsize=20)
ax6.grid(True, alpha=0.3)
ax6.tick_params(axis='both', which='major')

plt.tight_layout(pad=2.0)
plt.savefig('best-candidate.svg', bbox_inches='tight')
plt.show()

# Print summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

print("\nVoltage Ripple:")
print(f"  Min:      {min(rippleV_values):.6f} V")
print(f"  Max:      {max(rippleV_values):.6f} V")
print(f"  Midpoint: {midpoint_rippleV:.6f} V")
print(f"  Mean:     {np.mean(rippleV_values):.6f} V")
print(f"  Std:      {np.std(rippleV_values):.6f} V")

print("\nCurrent Ripple:")
print(f"  Min:      {min(rippleI_values):.6f} A")
print(f"  Max:      {max(rippleI_values):.6f} A")
print(f"  Midpoint: {midpoint_rippleI:.6f} A")
print(f"  Mean:     {np.mean(rippleI_values):.6f} A")
print(f"  Std:      {np.std(rippleI_values):.6f} A")

print("\n" + "="*60)
print("MEASUREMENT CLOSEST TO MIDPOINT")
print("="*60)
print(f"\nOriginal Index: {midpoint_measurement['index']}")
print(f"Voltage Ripple: {midpoint_measurement['rippleV']:.6f} V")
print(f"Current Ripple: {midpoint_measurement['rippleI']:.6f} A")
print(f"Mean Voltage:   {midpoint_measurement['meanV']:.6f} V")
print(f"Mean Current:   {midpoint_measurement['meanI']:.6f} A")
print(f"Distance from midpoint: {midpoint_measurement['distance_from_midpoint']:.6f}")
print(f"\nWeights used: Voltage={weight_V}, Current={weight_I}")
print("="*60)

# Optionally save the midpoint measurement to a file
with open('defect-detector/midpoint-measurement.json', 'w') as f:
    json.dump(midpoint_measurement['original_data'], f, indent=2)
    print(f"\nMidpoint measurement saved to 'defect-detector/midpoint-measurement.json'")