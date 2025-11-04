import json
import matplotlib.pyplot as plt
import numpy as np
import random

# Read the file
with open('defect-detector/raw-measurements.json', 'r') as f:
    content = f.read()

# Parse JSON objects (each line is a separate JSON object)
data = []
for line in content.strip().split('\n'):
    if line:
        data.append(json.loads(line))

# Randomly select 4 samples (or all if less than 4)
num_samples = min(4, len(data))
random_indices = random.sample(range(len(data)), num_samples)

# Create figure with subplots - increased figure size for better readability
fig, axes = plt.subplots(num_samples, 2, figsize=(16, 3.5*num_samples))

# If only one sample, axes needs to be wrapped in a list
if num_samples == 1:
    axes = [axes]

for i, idx in enumerate(random_indices):
    measurement = data[idx]['measurements']

    rippleV = max(measurement['voltage']) - min(measurement['voltage'])
    meanV = sum(measurement['voltage']) / len(measurement['voltage'])

    rippleI = max(measurement['current']) - min(measurement['current'])
    meanI = sum(measurement['current']) / len(measurement['current'])
    
    voltage = measurement['voltage']
    current = measurement['current']
    time = measurement['time']

    stats = {
        'rippleV': rippleV,
        'meanV': meanV,
        'rippleI': rippleI,
        'meanI': meanI
    }
    data[idx]['stats'] = stats  # Store stats for later summary

    # Plot voltage
    ax_v = axes[i][0]
    ax_v.plot(time, voltage, color='#2E86AB', linewidth=2)
    ax_v.set_ylabel('Voltage (V)', fontweight='bold', fontsize=14)
    ax_v.set_title(f'Sample {idx+1} - Voltage (Mean: {stats["meanV"]:.3f}V, Ripple: {stats["rippleV"]:.3f}V)', 
                   fontsize=13, fontweight='bold')
    ax_v.grid(True, alpha=0.3)
    ax_v.axhline(stats['meanV'], color='red', linestyle='--', alpha=0.7, linewidth=1.5)
    ax_v.tick_params(axis='both', which='major', labelsize=12)
    
    # Plot current
    ax_i = axes[i][1]
    ax_i.plot(time, current, color='#F18F01', linewidth=2)
    ax_i.set_ylabel('Current (A)', fontweight='bold', fontsize=14)
    ax_i.set_title(f'Sample {idx+1} - Current (Mean: {stats["meanI"]:.3f}A, Ripple: {stats["rippleI"]:.3f}A)', 
                   fontsize=13, fontweight='bold')
    ax_i.grid(True, alpha=0.3)
    ax_i.axhline(stats['meanI'], color='red', linestyle='--', alpha=0.7, linewidth=1.5)
    ax_i.tick_params(axis='both', which='major', labelsize=12)
    
    # Add x-label only to bottom plots
    if i == num_samples - 1:
        ax_v.set_xlabel('Time (s)', fontweight='bold', fontsize=14)
        ax_i.set_xlabel('Time (s)', fontweight='bold', fontsize=14)

plt.tight_layout()
plt.show()

# Print summary
print("\n" + "="*70)
print("RANDOM SAMPLES SUMMARY")
print("="*70)
for i, idx in enumerate(random_indices):
    stats = data[idx]['stats']
    print(f"\nSample {idx+1}:")
    print(f"  Voltage - Mean: {stats['meanV']:.6f}V, Ripple: {stats['rippleV']:.6f}V")
    print(f"  Current - Mean: {stats['meanI']:.6f}A, Ripple: {stats['rippleI']:.6f}A")
print("="*70)