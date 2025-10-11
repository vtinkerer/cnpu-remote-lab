import json
import matplotlib.pyplot as plt
import numpy as np

# Read the file
with open('defect-detector/filtered-random-measurements.json', 'r') as f:
    content = f.read()

# Parse JSON objects (each line is a separate JSON object)
data = []
for line in content.strip().split('\n'):
    if line:
        data.append(json.loads(line))

# Extract statistics from each measurement
stats_list = []
for idx, measurement in enumerate(data):
    stats = measurement['stats']
    stats_list.append({
        'index': idx,
        'rippleV': stats['rippleV'],
        'meanV': stats['meanV'],
        'rippleI': stats['rippleI'],
        'meanI': stats['meanI'],
        'original_data': measurement
    })

# Extract ripple values
rippleV_values = np.array([s['rippleV'] for s in stats_list])
rippleI_values = np.array([s['rippleI'] for s in stats_list])

# Calculate means (changed from medians)
mean_rippleV = np.mean(rippleV_values)
mean_rippleI = np.mean(rippleI_values)

# Normalize the values (z-score normalization)
# This accounts for different scales between voltage and current ripples
rippleV_normalized = (rippleV_values - np.mean(rippleV_values)) / np.std(rippleV_values)
rippleI_normalized = (rippleI_values - np.mean(rippleI_values)) / np.std(rippleI_values)

# Calculate normalized means (changed from medians)
mean_rippleV_norm = np.mean(rippleV_normalized)
mean_rippleI_norm = np.mean(rippleI_normalized)

# Since voltage ripples are smaller in magnitude, give them higher weight
# This ensures they contribute equally to the distance calculation
weight_V = 2.0  # Give voltage ripple 2x importance
weight_I = 1.0

# Calculate weighted distance from mean point for each measurement (changed from median)
distances = []
for i, stats in enumerate(stats_list):
    # Use the actual mean values, not normalized means
    dist_V = weight_V * ((rippleV_values[i] - mean_rippleV) / np.std(rippleV_values)) ** 2
    dist_I = weight_I * ((rippleI_values[i] - mean_rippleI) / np.std(rippleI_values)) ** 2
    total_distance = np.sqrt(dist_V + dist_I)
    distances.append(total_distance)
    stats['distance_from_mean'] = total_distance

# Find the measurement closest to the mean (changed from median)
mean_measurement_idx = np.argmin(distances)
mean_measurement = stats_list[mean_measurement_idx]

# Sort by each metric for plotting
sorted_by_rippleV = sorted(stats_list, key=lambda x: x['rippleV'])
sorted_by_meanV = sorted(stats_list, key=lambda x: x['meanV'])
sorted_by_rippleI = sorted(stats_list, key=lambda x: x['rippleI'])
sorted_by_meanI = sorted(stats_list, key=lambda x: x['meanI'])

# Create figure with subplots
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Circuit Measurements Distribution Analysis', fontsize=16, fontweight='bold')

# Plot 1: Ripple Voltage
ax1 = axes[0, 0]
rippleV_sorted = [s['rippleV'] for s in sorted_by_rippleV]
ax1.plot(rippleV_sorted, 'o-', color='#2E86AB', linewidth=2, markersize=8)
ax1.set_title('Voltage Ripple (sorted)', fontweight='bold')
ax1.set_xlabel('Measurement Index')
ax1.set_ylabel('Ripple Voltage (V)')
ax1.grid(True, alpha=0.3)
ax1.axhline(mean_rippleV, color='red', linestyle='--', 
            label=f'Mean: {mean_rippleV:.4f}V')
ax1.axhline(mean_measurement['rippleV'], color='green', linestyle=':', linewidth=2,
            label=f'Closest to Mean: {mean_measurement["rippleV"]:.4f}V')
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
rippleI_sorted = [s['rippleI'] for s in sorted_by_rippleI]
ax3.plot(rippleI_sorted, 'o-', color='#F18F01', linewidth=2, markersize=8)
ax3.set_title('Current Ripple (sorted)', fontweight='bold')
ax3.set_xlabel('Measurement Index')
ax3.set_ylabel('Ripple Current (A)')
ax3.grid(True, alpha=0.3)
ax3.axhline(mean_rippleI, color='red', linestyle='--', 
            label=f'Mean: {mean_rippleI:.4f}A')
ax3.axhline(mean_measurement['rippleI'], color='green', linestyle=':', linewidth=2,
            label=f'Closest to Mean: {mean_measurement["rippleI"]:.4f}A')
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

# Plot 5: Scatter plot showing relationship between ripples
ax5 = axes[0, 2]
ax5.scatter(rippleV_values, rippleI_values, alpha=0.6, s=50, color='#2E86AB')
ax5.scatter(mean_rippleV, mean_rippleI, color='red', s=200, marker='*', 
            label='Mean Point', edgecolors='black', linewidth=2)
ax5.scatter(mean_measurement['rippleV'], mean_measurement['rippleI'], 
            color='green', s=200, marker='D', label='Closest to Mean Measurement', 
            edgecolors='black', linewidth=2)
ax5.set_xlabel('Voltage Ripple (V)')
ax5.set_ylabel('Current Ripple (A)')
ax5.set_title('Ripple Relationship', fontweight='bold')
ax5.grid(True, alpha=0.3)
ax5.legend()

# Plot 6: Distance distribution
ax6 = axes[1, 2]
sorted_distances = sorted(distances)
ax6.plot(sorted_distances, 'o-', color='#6A4C93', linewidth=2, markersize=6)
ax6.axhline(mean_measurement['distance_from_mean'], color='green', 
            linestyle=':', linewidth=2, label=f'Min Distance: {mean_measurement["distance_from_mean"]:.4f}')
ax6.set_xlabel('Measurement Index (sorted by distance)')
ax6.set_ylabel('Normalized Distance from Mean')
ax6.set_title('Distance from Mean Point', fontweight='bold')
ax6.grid(True, alpha=0.3)
ax6.legend()

plt.tight_layout()
plt.show()

# Print summary statistics
print("\n" + "="*60)
print("SUMMARY STATISTICS")
print("="*60)

print("\nVoltage Ripple:")
print(f"  Min:    {min(rippleV_values):.6f} V")
print(f"  Max:    {max(rippleV_values):.6f} V")
print(f"  Mean:   {mean_rippleV:.6f} V")
print(f"  Std:    {np.std(rippleV_values):.6f} V")

print("\nCurrent Ripple:")
print(f"  Min:    {min(rippleI_values):.6f} A")
print(f"  Max:    {max(rippleI_values):.6f} A")
print(f"  Mean:   {mean_rippleI:.6f} A")
print(f"  Std:    {np.std(rippleI_values):.6f} A")

print("\n" + "="*60)
print("MEASUREMENT CLOSEST TO MEAN")
print("="*60)
print(f"\nOriginal Index: {mean_measurement['index']}")
print(f"Voltage Ripple: {mean_measurement['rippleV']:.6f} V")
print(f"Current Ripple: {mean_measurement['rippleI']:.6f} A")
print(f"Mean Voltage:   {mean_measurement['meanV']:.6f} V")
print(f"Mean Current:   {mean_measurement['meanI']:.6f} A")
print(f"Distance from mean point: {mean_measurement['distance_from_mean']:.6f}")
print(f"\nWeights used: Voltage={weight_V}, Current={weight_I}")
print("="*60)

# Optionally save the mean measurement to a file
with open('defect-detector/mean-measurement.json', 'w') as f:
    json.dump(mean_measurement['original_data'], f, indent=2)
    print(f"\nMean measurement saved to 'defect-detector/mean-measurement.json'")