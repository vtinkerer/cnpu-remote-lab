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
meanV_values = []

for measurement in data:
    stats_data = measurement['stats']
    rippleV_values.append(stats_data['rippleV'])
    meanV_values.append(stats_data['meanV'])

# Calculate correlation
correlation = np.corrcoef(meanV_values, rippleV_values)[0, 1]
slope, intercept, r_value, p_value, std_err = stats.linregress(meanV_values, rippleV_values)

# Create figure with subplots
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# Main scatter plot with trend line
ax1 = fig.add_subplot(gs[0:2, :])
ax1.scatter(meanV_values, rippleV_values, alpha=0.7, s=100, 
            c=range(len(meanV_values)), cmap='coolwarm', edgecolors='black', linewidth=0.5)
ax1.plot(meanV_values, np.array(meanV_values) * slope + intercept, 
         'r--', linewidth=2, label=f'Linear fit: y = {slope:.2f}x + {intercept:.2f}')
ax1.set_xlabel('Mean Voltage (V)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Voltage Ripple (V)', fontsize=12, fontweight='bold')
ax1.set_title(f'Mean Voltage vs Voltage Ripple Correlation\nPearson r = {correlation:.4f} (R² = {r_value**2:.4f})', 
              fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=11)

# Add colorbar
cbar = plt.colorbar(ax1.collections[0], ax=ax1)
cbar.set_label('Measurement Index', rotation=270, labelpad=20)

# Histogram of mean voltage
ax2 = fig.add_subplot(gs[2, 0])
ax2.hist(meanV_values, bins=15, color='#A23B72', alpha=0.7, edgecolor='black')
ax2.set_xlabel('Mean Voltage (V)', fontweight='bold')
ax2.set_ylabel('Frequency', fontweight='bold')
ax2.set_title('Mean Voltage Distribution', fontweight='bold')
ax2.grid(True, alpha=0.3, axis='y')
ax2.axvline(np.mean(meanV_values), color='red', linestyle='--', linewidth=2, 
            label=f'Mean: {np.mean(meanV_values):.4f}V')
ax2.legend()

# Histogram of voltage ripple
ax3 = fig.add_subplot(gs[2, 1])
ax3.hist(rippleV_values, bins=15, color='#2E86AB', alpha=0.7, edgecolor='black')
ax3.set_xlabel('Voltage Ripple (V)', fontweight='bold')
ax3.set_ylabel('Frequency', fontweight='bold')
ax3.set_title('Voltage Ripple Distribution', fontweight='bold')
ax3.grid(True, alpha=0.3, axis='y')
ax3.axvline(np.mean(rippleV_values), color='red', linestyle='--', linewidth=2, 
            label=f'Mean: {np.mean(rippleV_values):.4f}V')
ax3.legend()

plt.suptitle('Voltage Analysis: Mean vs Ripple Correlation', 
             fontsize=16, fontweight='bold', y=0.995)
plt.show()

# Print detailed analysis
print("\n" + "="*70)
print("VOLTAGE RIPPLE vs MEAN VOLTAGE CORRELATION ANALYSIS")
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
print(f"  Equation: V_ripple = {slope:.4f} × V_mean + {intercept:.4f}")
print(f"  Slope:                           {slope:.6f}")
print(f"  Intercept:                       {intercept:.6f}")
print(f"  Standard Error:                  {std_err:.6f}")

print("\n⚡ MEAN VOLTAGE STATISTICS:")
print(f"  Min:    {min(meanV_values):.6f} V")
print(f"  Max:    {max(meanV_values):.6f} V")
print(f"  Mean:   {np.mean(meanV_values):.6f} V")
print(f"  Median: {np.median(meanV_values):.6f} V")
print(f"  Std:    {np.std(meanV_values):.6f} V")
print(f"  Range:  {max(meanV_values) - min(meanV_values):.6f} V")

print("\n📉 VOLTAGE RIPPLE STATISTICS:")
print(f"  Min:    {min(rippleV_values):.6f} V")
print(f"  Max:    {max(rippleV_values):.6f} V")
print(f"  Mean:   {np.mean(rippleV_values):.6f} V")
print(f"  Median: {np.median(rippleV_values):.6f} V")
print(f"  Std:    {np.std(rippleV_values):.6f} V")
print(f"  Range:  {max(rippleV_values) - min(rippleV_values):.6f} V")

print("\n💡 INTERPRETATION:")
if p_value < 0.05:
    print(f"  ✓ The correlation is statistically significant (p < 0.05)")
    if abs(correlation) > 0.7:
        if correlation > 0:
            print(f"  ✓ Higher mean voltages ARE strongly connected to higher voltage ripples")
        else:
            print(f"  ✓ Higher mean voltages ARE strongly connected to LOWER voltage ripples")
        print(f"  ✓ About {(r_value**2)*100:.1f}% of ripple variation can be explained")
        print(f"    by mean voltage variation")
    elif abs(correlation) > 0.5:
        if correlation > 0:
            print(f"  ⚠ There is a moderate positive connection: higher mean → higher ripple")
        else:
            print(f"  ⚠ There is a moderate negative connection: higher mean → lower ripple")
        print(f"  ⚠ About {(r_value**2)*100:.1f}% of ripple variation can be explained")
        print(f"    by mean voltage variation")
    else:
        print(f"  ⚠ The correlation is weak, suggesting other factors influence the ripples")
        print(f"    more than the mean voltage level")
else:
    print(f"  ✗ The correlation is NOT statistically significant (p >= 0.05)")
    print(f"  ✗ Cannot conclude a meaningful relationship between mean voltage and ripple")

# Additional insight
print("\n🔍 ADDITIONAL INSIGHTS:")
cv_values = [rippleV_values[i]/meanV_values[i] for i in range(len(data))]
print(f"  Coefficient of Variation (Ripple/Mean):")
print(f"    Min:  {min(cv_values):.6f} ({min(cv_values)*100:.3f}%)")
print(f"    Max:  {max(cv_values):.6f} ({max(cv_values)*100:.3f}%)")
print(f"    Mean: {np.mean(cv_values):.6f} ({np.mean(cv_values)*100:.3f}%)")

print("\n🎯 PRACTICAL MEANING:")
print(f"  Ripple represents {np.mean(cv_values)*100:.3f}% of mean voltage on average")
print(f"  This indicates the relative stability of the voltage output")

print("="*70)