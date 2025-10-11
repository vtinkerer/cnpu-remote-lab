import json
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

# Read the file
with open('defect-detector/filtered-random-measurements.json', 'r') as f:
    content = f.read()

# Parse JSON objects (each line is a separate JSON object)
data = []
for line in content.strip().split('\n'):
    if line:
        data.append(json.loads(line))

# Extract statistics from each measurement
rippleV_values = []
rippleI_values = []
meanV_values = []
meanI_values = []

for measurement in data:
    stats_data = measurement['stats']
    rippleV_values.append(stats_data['rippleV'])
    rippleI_values.append(stats_data['rippleI'])
    meanV_values.append(stats_data['meanV'])
    meanI_values.append(stats_data['meanI'])

# Calculate correlation
correlation = np.corrcoef(rippleV_values, rippleI_values)[0, 1]
slope, intercept, r_value, p_value, std_err = stats.linregress(rippleV_values, rippleI_values)

# Create figure with subplots
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Main scatter plot with trend line
ax1 = fig.add_subplot(gs[0:2, :])
ax1.scatter(rippleV_values, rippleI_values, alpha=0.7, s=100, 
            c=range(len(rippleV_values)), cmap='viridis', edgecolors='black', linewidth=0.5)
ax1.plot(rippleV_values, np.array(rippleV_values) * slope + intercept, 
         'r--', linewidth=2, label=f'Linear fit: y = {slope:.2f}x + {intercept:.2f}')
ax1.set_xlabel('Voltage Ripple (V)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Current Ripple (A)', fontsize=12, fontweight='bold')
ax1.set_title(f'Voltage Ripple vs Current Ripple Correlation\nPearson r = {correlation:.4f} (R² = {r_value**2:.4f})', 
              fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=11)

# Add colorbar
cbar = plt.colorbar(ax1.collections[0], ax=ax1)
cbar.set_label('Measurement Index', rotation=270, labelpad=20)

# Histogram of voltage ripple
ax2 = fig.add_subplot(gs[2, 0])
ax2.hist(rippleV_values, bins=15, color='#2E86AB', alpha=0.7, edgecolor='black')
ax2.set_xlabel('Voltage Ripple (V)', fontweight='bold')
ax2.set_ylabel('Frequency', fontweight='bold')
ax2.set_title('Voltage Ripple Distribution', fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')
ax2.axvline(np.mean(rippleV_values), color='red', linestyle='--', linewidth=2, 
            label=f'Mean: {np.mean(rippleV_values):.4f}V')
ax2.legend()

# Histogram of current ripple
ax3 = fig.add_subplot(gs[2, 1])
ax3.hist(rippleI_values, bins=15, color='#F18F01', alpha=0.7, edgecolor='black')
ax3.set_xlabel('Current Ripple (A)', fontweight='bold')
ax3.set_ylabel('Frequency', fontweight='bold')
ax3.set_title('Current Ripple Distribution', fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')
ax3.axvline(np.mean(rippleI_values), color='red', linestyle='--', linewidth=2, 
            label=f'Mean: {np.mean(rippleI_values):.4f}A')
ax3.legend()

plt.suptitle('Ripple Analysis: Voltage vs Current Correlation', 
             fontsize=16, fontweight='bold', y=0.995)
plt.show()

# Print detailed analysis
print("\n" + "="*70)
print("RIPPLE CORRELATION ANALYSIS")
print("="*70)

print("\n📊 CORRELATION STATISTICS:")
print(f"  Pearson Correlation Coefficient: {correlation:.6f}")
print(f"  R-squared (R²):                  {r_value**2:.6f}")
print(f"  P-value:                         {p_value:.6e}")

# Interpret correlation strength
if abs(correlation) > 0.9:
    strength = "Very Strong"
elif abs(correlation) > 0.7:
    strength = "Strong"
elif abs(correlation) > 0.5:
    strength = "Moderate"
elif abs(correlation) > 0.3:
    strength = "Weak"
else:
    strength = "Very Weak"

direction = "Positive" if correlation > 0 else "Negative"
print(f"  Correlation Strength:            {strength} {direction}")

print("\n📈 LINEAR REGRESSION:")
print(f"  Equation: I_ripple = {slope:.4f} × V_ripple + {intercept:.4f}")
print(f"  Slope:                           {slope:.6f}")
print(f"  Intercept:                       {intercept:.6f}")
print(f"  Standard Error:                  {std_err:.6f}")

print("\n📉 VOLTAGE RIPPLE STATISTICS:")
print(f"  Min:    {min(rippleV_values):.6f} V")
print(f"  Max:    {max(rippleV_values):.6f} V")
print(f"  Mean:   {np.mean(rippleV_values):.6f} V")
print(f"  Median: {np.median(rippleV_values):.6f} V")
print(f"  Std:    {np.std(rippleV_values):.6f} V")

print("\n⚡ CURRENT RIPPLE STATISTICS:")
print(f"  Min:    {min(rippleI_values):.6f} A")
print(f"  Max:    {max(rippleI_values):.6f} A")
print(f"  Mean:   {np.mean(rippleI_values):.6f} A")
print(f"  Median: {np.median(rippleI_values):.6f} A")
print(f"  Std:    {np.std(rippleI_values):.6f} A")

print("\n💡 INTERPRETATION:")
if p_value < 0.05:
    print(f"  ✓ The correlation is statistically significant (p < 0.05)")
    if abs(correlation) > 0.7:
        print(f"  ✓ Higher voltage ripples ARE strongly connected to higher current ripples")
        print(f"  ✓ About {(r_value**2)*100:.1f}% of current ripple variation can be explained")
        print(f"    by voltage ripple variation")
    elif abs(correlation) > 0.5:
        print(f"  ⚠ There is a moderate connection between voltage and current ripples")
        print(f"  ⚠ About {(r_value**2)*100:.1f}% of current ripple variation can be explained")
        print(f"    by voltage ripple variation")
    else:
        print(f"  ⚠ The correlation is weak, suggesting other factors influence the ripples")
else:
    print(f"  ✗ The correlation is NOT statistically significant (p >= 0.05)")
    print(f"  ✗ Cannot conclude a meaningful relationship between the ripples")

print("="*70)