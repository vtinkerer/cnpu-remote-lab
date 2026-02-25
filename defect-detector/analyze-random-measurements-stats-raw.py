import json
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Read the file
with open('defect-detector/raw-measurements.json', 'r') as f:
    content = f.read()

# Parse JSON objects (each line is a separate JSON object)
data = []
for line in content.strip().split('\n'):
    if line:
        data.append(json.loads(line))

# Extract statistics from each measurement
all_voltages = []
all_currents = []
ripple_voltages = []
ripple_currents = []
mean_voltages = []
mean_currents = []

for line in data:
    measurements = line['measurements']
    voltage = measurements['voltage']
    current = measurements['current']
    
    all_voltages.extend(voltage)
    all_currents.extend(current)
    
    rippleV = max(voltage) - min(voltage)
    meanV = sum(voltage) / len(voltage)
    rippleI = max(current) - min(current)
    meanI = sum(current) / len(current)
    
    ripple_voltages.append(rippleV)
    mean_voltages.append(meanV)
    ripple_currents.append(rippleI)
    mean_currents.append(meanI)

# Convert to numpy arrays
ripple_voltages = np.array(ripple_voltages)
mean_voltages = np.array(mean_voltages)
ripple_currents = np.array(ripple_currents)
mean_currents = np.array(mean_currents)

def plot_distribution_with_iqr(ax, data, title, color='#FF6B6B'):
    """
    Plot distribution with IQR box similar to the reference image
    """
    # Calculate statistics
    q1 = np.percentile(data, 25)
    median = np.median(data)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1
    
    # Calculate bounds for outliers
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    
    # Create histogram and KDE using actual values
    hist, bins = np.histogram(data, bins=50, density=True)
    bin_centers = (bins[:-1] + bins[1:]) / 2
    
    # KDE for smooth distribution
    kde = stats.gaussian_kde(data)
    x_range = np.linspace(data.min() - (data.max() - data.min()) * 0.1, 
                          data.max() + (data.max() - data.min()) * 0.1, 1000)
    kde_values = kde(x_range)
    
    # Plot the distribution curve
    ax.plot(x_range, kde_values, 'k-', linewidth=2)
    ax.fill_between(x_range, kde_values, alpha=0.3, color='lightblue')
    
    # Fill IQR region
    iqr_mask = (x_range >= q1) & (x_range <= q3)
    ax.fill_between(x_range[iqr_mask], kde_values[iqr_mask], alpha=0.6, color=color)
    
    # Calculate percentages
    total = len(data)
    iqr_count = np.sum((data >= q1) & (data <= q3))
    lower_count = np.sum(data < q1)
    upper_count = np.sum(data > q3)
    
    iqr_percent = 100 * iqr_count / total
    lower_percent = 100 * lower_count / total
    upper_percent = 100 * upper_count / total
    
    # Add vertical lines at quartiles
    ax.axvline(q1, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.axvline(median, color='black', linestyle='-', linewidth=2)
    ax.axvline(q3, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
    
    # Add box plot at the top
    y_max = kde_values.max()
    box_bottom = y_max * 1.20
    box_top = y_max * 1.35
    box_center = (box_bottom + box_top) / 2
    
    # Calculate whisker positions (1.5 * IQR from quartiles)
    lower_whisker = q1 - 1.5 * iqr
    upper_whisker = q3 + 1.5 * iqr
    
    # Draw the box (Q1 to Q3)
    box_width = q3 - q1
    rect = plt.Rectangle((q1, box_bottom), box_width, box_top - box_bottom,
                          linewidth=2, edgecolor='black', facecolor='white', zorder=10)
    ax.add_patch(rect)
    
    # Draw median line inside the box
    ax.plot([median, median], [box_bottom, box_top], 'k-', linewidth=3, zorder=11)
    
    # Draw whiskers (lines from box to whisker ends)
    # Left whisker
    ax.plot([lower_whisker, q1], [box_center, box_center], 'k-', linewidth=2, zorder=10)
    # Right whisker
    ax.plot([q3, upper_whisker], [box_center, box_center], 'k-', linewidth=2, zorder=10)
    
    # Draw whisker caps
    cap_height = (box_top - box_bottom) * 0.6
    ax.plot([lower_whisker, lower_whisker], 
            [box_center - cap_height/2, box_center + cap_height/2], 'k-', linewidth=2, zorder=10)
    ax.plot([upper_whisker, upper_whisker], 
            [box_center - cap_height/2, box_center + cap_height/2], 'k-', linewidth=2, zorder=10)
    
    # Add percentage annotations
    data_range = data.max() - data.min()
    ax.text(q1 - data_range * 0.15, y_max * 0.5, f'{lower_percent:.2f}%', ha='center', va='center', 
            fontsize=16, weight='bold')
    ax.text((q1 + q3) / 2, y_max * 0.5, f'{iqr_percent:.2f}%', ha='center', va='center',
            fontsize=16, weight='bold', color='darkred')
    ax.text(q3 + data_range * 0.15, y_max * 0.5, f'{upper_percent:.2f}%', ha='center', va='center',
            fontsize=16, weight='bold')
    
    
    # Labels
    title_offset_pixels = 20  # Vertical offset for title in pixels
    ax.set_xlabel('')  # Remove x-axis label
    ax.set_ylabel('Probability Density', fontsize=16, weight='bold')
    ax.set_title(title, fontsize=14, weight='bold')
    ax.tick_params(axis='both', which='major', labelsize=14)  # Increase tick label font size
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, y_max * 1.5)
    
    # Print statistics
    print(f"\n{title}:")
    print(f"  Q1: {q1:.6f}")
    print(f"  Median: {median:.6f}")
    print(f"  Q3: {q3:.6f}")
    print(f"  IQR: {iqr:.6f}")
    print(f"  Percentage in IQR: {iqr_percent:.2f}%")
    print(f"  Percentage below Q1: {lower_percent:.2f}%")
    print(f"  Percentage above Q3: {upper_percent:.2f}%")

# Create figure with subplots (2x2 layout)
fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# Plot distributions
plot_distribution_with_iqr(axes[0, 0], ripple_voltages, 
                           'Voltage Ripple Distribution (V)', 
                           '#FF6B6B')

plot_distribution_with_iqr(axes[0, 1], mean_voltages, 
                           'Mean Voltage Distribution (V)', 
                           '#4ECDC4')

plot_distribution_with_iqr(axes[1, 0], ripple_currents, 
                           'Current Ripple Distribution (A)', 
                           '#FFE66D')

plot_distribution_with_iqr(axes[1, 1], mean_currents, 
                           'Mean Current Distribution (A)', 
                           '#95E1D3')

# Adjust layout
plt.tight_layout(h_pad=4.0, w_pad=3.0)  # Add more horizontal and vertical spacing
plt.savefig('circuit_measurements_distribution.svg', bbox_inches='tight', dpi=300)
plt.savefig('circuit_measurements_distribution.png', bbox_inches='tight', dpi=300)
plt.show()

print("\n" + "="*60)
print("DISTRIBUTION ANALYSIS COMPLETE")
print("="*60)