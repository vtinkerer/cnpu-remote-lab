import numpy as np
import matplotlib.pyplot as plt
import csv
import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *

# Logging setup
Logging.setup_logging()

# Define default parameters in one place as a global dictionary
DEFAULT_PARAMS = {
    'vin': 12,          # input voltage (V)
    'duty_cycle': 0.5,  # PWM duty cycle
    'frequency': 312500, # PWM frequency (Hz)
    'inductor': 10e-6,  # inductance (H)
    'capacitor': 44e-6, # capacitance (F)
    'load': 20,       # load resistance (Ohm)
    'esr_cap': 0.1,     # capacitor ESR (Ohm)
    'esr_ind': 19.5e-3, # inductor ESR (Ohm)
    'rds_on': 1e-3,     # transistor RDS(on) (Ohm)
    'diode_rs': 1e-3     # diode resistance (Ohm)
}

# Function to create a buck converter
def create_buck_converter(
    vin=DEFAULT_PARAMS['vin'],
    duty_cycle=DEFAULT_PARAMS['duty_cycle'],
    frequency=DEFAULT_PARAMS['frequency'],
    inductor=DEFAULT_PARAMS['inductor'],
    capacitor=DEFAULT_PARAMS['capacitor'],
    load=DEFAULT_PARAMS['load'],
    esr_cap=DEFAULT_PARAMS['esr_cap'],
    esr_ind=DEFAULT_PARAMS['esr_ind'],
    rds_on=DEFAULT_PARAMS['rds_on'],
    diode_rs=DEFAULT_PARAMS['diode_rs']
):
    
    circuit = Circuit('Buck Converter')
    circuit.V('in', 'vin', 'gnd', vin)
    
    period = 1/frequency
    ton = duty_cycle * period * 1e6
    period_us = period * 1e6
    circuit.V('gate', 'g', 'gnd', f'DC 0 PULSE(0 10 0 1n 1n {ton}us {period_us}us)')
    
    circuit.S('1', 'vin', 'sw', 'g', 'gnd', model='SWITCH')
    circuit.model('SWITCH', 'SW', ron=rds_on, vt=1, vh=0)
    
    circuit.D('1', 'gnd', 'sw', model='MYDIODE')
    circuit.model('MYDIODE', 'D', is_=1e6)
        
    circuit.L('1', 'sw', 'out', inductor)
    circuit.R('L1', 'out', 'out_c', esr_ind)

    circuit.C('1', 'out_c', 'c_res', capacitor)
    circuit.R('C1', 'c_res', 'gnd', esr_cap)
    
    circuit.R('load', 'out_c', 'gnd', load)
    
    return circuit

# Function for simulation and parameter extraction
def simulate_and_analyze(circuit, esr_ind, settling_cycles=600 ):
    try:
        # Calculate settling time
        freq = 312500  # PWM frequency (Hz)
        period = 1/freq
        settling_time = settling_cycles * period
        
        delta = period * 600
        end_time = delta + period * 2
        step_time = period / 300
        # Run simulation
        simulator = circuit.simulator()
        analysis = simulator.transient(step_time=step_time, end_time=end_time)
        
        # Determine the index to start analysis after settling
        time_points = np.array(analysis.time)
        start_idx = np.searchsorted(time_points, settling_time)
        
        if start_idx >= len(time_points) - 10:
            # Not enough points after settling
            start_idx = len(time_points) // 2
        
        # Output parameter analysis
        vout = np.array(analysis['out_c'])[start_idx:]
        il = (np.array(analysis['out'])[start_idx:] - np.array(analysis['out_c'])[start_idx:]) / esr_ind
        
        vout_avg = np.mean(vout)
        vout_ripple = np.max(vout) - np.min(vout)
        il_avg = np.mean(il)
        il_ripple = np.max(il) - np.min(il)
        
        return {
            'vout_avg': vout_avg,
            'vout_ripple': vout_ripple,
            'il_avg': il_avg,
            'il_ripple': il_ripple,

        }
    
    except Exception as e:
        print(f"Simulation error: {e}")
        # Return default values in case of error
        return {
            'vout_avg': 0,
            'vout_ripple': 0,
            'il_avg': 0,
            'il_ripple': 0
        }

# Function to determine the octant
def determine_octant(baseline, modified, threshold=10):
    """
    Determines the octant of parameter changes considering a 10% threshold
    
    Parameters:
    baseline: dict with baseline parameters
    modified: dict with modified parameters
    threshold: change threshold in percentage (10%)
    
    Returns:
    Tuple (dVmean, dVpulse, dImean, dIpulse), where each element is:
    1: increase (>threshold%)
    0: no change (±threshold%)
    -1: decrease (<-threshold%)
    """
    results = []
    
    for param in ['vout_avg', 'vout_ripple', 'il_avg', 'il_ripple']:
        baseline_value = baseline[param]
        modified_value = modified[param]
        
        if abs(baseline_value) < 1e-9:  # Prevent division by zero
            if abs(modified_value) < 1e-9:
                change = 0
            else:
                change = 1 if modified_value > 0 else -1
        else:
            percent_change = ((modified_value - baseline_value) / baseline_value) * 100
            
            if percent_change > threshold:
                change = 1  # increase
            elif percent_change < -threshold:
                change = -1  # decrease
            else:
                change = 0  # no change
        
        results.append(change)
    
    return tuple(results)

# Main function for parameter impact analysis
def analyze_parameter_impact():
    print("Creating baseline circuit...")
    # Create the base circuit and get reference values
    base_circuit = create_buck_converter()
    baseline_results = simulate_and_analyze(base_circuit, esr_ind=DEFAULT_PARAMS['esr_ind'])
    
    print("Baseline results:")
    for param, value in baseline_results.items():
        print(f"{param}: {value:.6f}")
    
    # Parameters for analysis and their multipliers with symbolic labels
    parameters = {
        'duty_cycle': [
            {'label': '>>>', 'mult': 1.95},
            {'label': '>>', 'mult': 1.5},
            {'label': '>', 'mult': 1.2},
            {'label': '<', 'mult': 1/1.2},
            {'label': '<<', 'mult': 1/1.5},
            {'label': '<<<', 'mult': 1/1.95}
        ],
        'inductor': [
            {'label': '>>>', 'mult': 1e12},
            {'label': '>>', 'mult': 10},
            {'label': '>', 'mult': 3},
            {'label': '<', 'mult': 1/3},
            {'label': '<<', 'mult': 1/10},
            {'label': '<<<', 'mult': 1e-12}
        ],
        'capacitor': [
            {'label': '>>>', 'mult': 1e12},
            {'label': '>>', 'mult': 10},
            {'label': '>', 'mult': 3},
            {'label': '<', 'mult': 1/3},
            {'label': '<<', 'mult': 1/10},
            {'label': '<<<', 'mult': 1e-12}
        ],
        'load': [
            {'label': '>>>', 'mult': 1e12},
            {'label': '>>', 'mult': 10},
            {'label': '>', 'mult': 3},
            {'label': '<', 'mult': 1/3},
            {'label': '<<', 'mult': 1/10},
            {'label': '<<<', 'mult': 1e-12}
        ],
        'esr_cap': [
            {'label': '>>>', 'mult': 1e12},
            {'label': '>>', 'mult': 10},
            {'label': '>', 'mult': 3},
            {'label': '<', 'mult': 1/3},
            {'label': '<<', 'mult': 1/10},
            {'label': '<<<', 'mult': 1e-12}
        ],
        'esr_ind': [
            {'label': '>>>', 'mult': 1e12},
            {'label': '>>', 'mult': 10},
            {'label': '>', 'mult': 3},
            {'label': '<', 'mult': 1/3},
            {'label': '<<', 'mult': 1/10},
            {'label': '<<<', 'mult': 1e-12}
        ],
        'rds_on': [
            {'label': '>>>', 'mult': 1e12},
            {'label': '>>', 'mult': 10},
            {'label': '>', 'mult': 3},
            {'label': '<', 'mult': 1/3},
            {'label': '<<', 'mult': 1/10},
            {'label': '<<<', 'mult': 1e-12}
        ],
        # 'diode_rs': [
        #     {'label': '>>>', 'mult': 1e12},
        #     {'label': '>>', 'mult': 10},
        #     {'label': '>', 'mult': 3},
        #     {'label': '<', 'mult': 1/3},
        #     {'label': '<<', 'mult': 1/10},
        #     {'label': '<<<', 'mult': 1e-12}
        # ]
    }
    
    results = {}
    
    for param_name, modifiers in parameters.items():
        print(f"\nAnalyzing parameter: {param_name}")
        param_results = {}
        
        for mod_info in modifiers:
            label = mod_info['label']
            mult = mod_info['mult']
            print(f"  Testing modifier: {label} (x{mult})")
            
            # Create a copy of base parameters
            modified_params = DEFAULT_PARAMS.copy()
            
            # Update the specific parameter
            original_value = modified_params[param_name]
            modified_params[param_name] = original_value * mult
            
            try:
                # Create and simulate the circuit with the modified parameter
                circuit = create_buck_converter(**modified_params)
                modified_results = simulate_and_analyze(circuit, esr_ind=modified_params['esr_ind'])
                
                # Skip invalid results
                if (modified_results['vout_avg'] <= 0 or 
                    modified_results['il_avg'] <= 0):
                    
                    

                    print(f"  Skipping invalid results for {param_name} {label}")
                    continue
                


                # Determine the octant of change
                octant = determine_octant(baseline_results, modified_results)
                
                # Save the results
                param_results[label] = {
                    'octant': octant,
                    'values': modified_results,
                    'mult': mult  # Save multiplier for reference
                }
                
                print(f"  {param_name} {label}: Octant {octant}")
                for p, v in modified_results.items():
                    change = ((v - baseline_results[p]) / baseline_results[p]) * 100
                    print(f"    {p}: {v:.6f} ({change:+.2f}%)")
                
            except Exception as e:
                print(f"  Error simulating {param_name} {label}: {e}")
        
        results[param_name] = param_results
    
    return baseline_results, results

# Function to save results to CSV
def save_results_to_csv(baseline, results, filename='parameter_impact.csv'):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        
        # Header
        writer.writerow(['Parameter', 'Modifier', 'Vmean', 'Vpulse', 'Imean', 'Ipulse', 
                         'Vmean(%)', 'Vpulse(%)', 'Imean(%)', 'Ipulse(%)', 'Octant'])
        
        # Baseline values
        writer.writerow(['Baseline', 'x1', 
                         f"{baseline['vout_avg']:.6f}", 
                         f"{baseline['vout_ripple']:.6f}", 
                         f"{baseline['il_avg']:.6f}", 
                         f"{baseline['il_ripple']:.6f}",
                         "0.0%", "0.0%", "0.0%", "0.0%", "----"])
        
        # Parameter data
        for param, modifiers in results.items():
            for mod_name, data in modifiers.items():
                octant = data['octant']
                values = data['values']
                
                # Convert octant to a string with arrows
                octant_str = ""
                for o in octant:
                    if o == 1:
                        octant_str += "↑"
                    elif o == -1:
                        octant_str += "↓"
                    else:
                        octant_str += "-"
                
                # Calculate percentage changes
                changes = []
                for p in ['vout_avg', 'vout_ripple', 'il_avg', 'il_ripple']:
                    change = ((values[p] - baseline[p]) / baseline[p]) * 100
                    changes.append(f"{change:+.2f}%")
                
                writer.writerow([param, mod_name, 
                                f"{values['vout_avg']:.6f}", 
                                f"{values['vout_ripple']:.6f}", 
                                f"{values['il_avg']:.6f}", 
                                f"{values['il_ripple']:.6f}",
                                changes[0], changes[1], changes[2], changes[3], 
                                octant_str])
    
    print(f"Results saved to {filename}")

def visualize_parameter_impact(baseline, results):
    # Create heat maps for each parameter
    parameter_names = ['Vmean', 'Vpulse', 'Imean', 'Ipulse']
    
    # Collect parameters and modifiers
    all_params = list(results.keys())
    
    # Use predefined order of modifiers
    all_modifiers = ['<<<', '<<', '<', '>', '>>', '>>>']
    
    # Data for heat maps
    heat_data = np.zeros((len(all_params), len(all_modifiers), 4))
    heat_data.fill(np.nan)
    
    for i, param in enumerate(all_params):
        for j, mod in enumerate(all_modifiers):
            if mod in results[param] and 'octant' in results[param][mod]:
                octant = results[param][mod]['octant']
                for k in range(4):
                    heat_data[i, j, k] = octant[k]
    
    # Create heat maps
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    axes = axes.flatten()
    
    for k in range(4):
        # Use masked array for NaN values
        masked_data = np.ma.array(heat_data[:, :, k], mask=np.isnan(heat_data[:, :, k]))
        
        im = axes[k].imshow(masked_data, cmap='RdBu', vmin=-1, vmax=1)
        axes[k].set_title(f'Impact on {parameter_names[k]}')
        axes[k].set_yticks(np.arange(len(all_params)))
        axes[k].set_xticks(np.arange(len(all_modifiers)))
        axes[k].set_yticklabels(all_params)
        axes[k].set_xticklabels(all_modifiers)
        plt.colorbar(im, ax=axes[k], ticks=[-1, 0, 1], label='↓ = -1, — = 0, ↑ = 1')
    
    plt.tight_layout()
    plt.savefig('parameter_heatmaps.png')
    print("Heat maps saved to parameter_heatmaps.png")
    
    # Create a summary table of octants
    unique_octants = {}
    
    # Collect data for octants
    for param, modifiers in results.items():
        for mod_name, data in modifiers.items():
            octant = data['octant']
            
            # Convert to string representation for use as a key
            octant_key = ''.join(['↑' if o == 1 else '↓' if o == -1 else '-' for o in octant])
            octant_key = f"{octant_key[0]},{octant_key[1]},{octant_key[2]},{octant_key[3]}"
            
            if octant_key not in unique_octants:
                unique_octants[octant_key] = []
            
            unique_octants[octant_key].append((param, mod_name))
    
    # Create a distribution diagram by octants
    fig, ax = plt.subplots(figsize=(15, 8))
    
    octant_counts = {key: len(value) for key, value in unique_octants.items()}
    sorted_octants = sorted(octant_counts.items(), key=lambda x: x[1], reverse=True)
    
    octant_labels = [octant for octant, _ in sorted_octants]
    octant_values = [count for _, count in sorted_octants]
    
    # Create a color scheme for octants
    cmap = plt.cm.tab20
    colors = [cmap(i % 20) for i in range(len(octant_labels))]
    
    bars = ax.bar(octant_labels, octant_values, color=colors)
    
    ax.set_title('Distribution of parameters by octants', fontsize=16)
    ax.set_xlabel('Octant (Vmean,Vpulse,Imean,Ipulse)', fontsize=14)
    ax.set_ylabel('Number of parameters', fontsize=14)
    
    # Add labels and rotate them for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Add labels to columns
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                str(int(height)), ha='center', va='bottom')
    
    # Instead of adding text to the plot, save it to a separate text file
    plt.tight_layout()
    plt.savefig('octant_distribution.png')
    print("Octant distribution saved to octant_distribution.png")
    
    # NEW FUNCTIONALITY: Save detailed information about octants to a separate file
    with open('octant_details.txt', 'w', encoding='utf-8') as f:
        f.write("Detailed information about parameters in each octant\n")
        f.write("=================================================\n\n")
        for octant, params in sorted_octants:
            f.write(f"Octant {octant}:\n")
            # Group parameters by type for better readability
            param_groups = {}
            for p, m in unique_octants[octant]:
                param_name = p
                modifier = m
                if param_name not in param_groups:
                    param_groups[param_name] = []
                param_groups[param_name].append(modifier)
            
            # Output in "parameter: modifiers" format
            for param, modifiers in param_groups.items():
                f.write(f"  {param}: {', '.join(modifiers)}\n")
            f.write("\n")
    
    print("Detailed octant information saved to octant_details.txt")
    
    # ADDITIONALLY: Create a more compact visualization of the relationship between parameters and octants
    num_octants = len(sorted_octants)
    unique_params = sorted(all_params)
    
    # Create figure with parameter heatmap by octants
    plt.figure(figsize=(18, 10))
    matrix_data = np.zeros((len(unique_params), num_octants))
    
    for param_idx, param in enumerate(unique_params):
        for octant_idx, (octant, _) in enumerate(sorted_octants):
            # Count how many modifiers of this parameter fall into this octant
            count = sum(1 for p, m in unique_octants[octant] if p == param)
            matrix_data[param_idx, octant_idx] = count
    
    # Show the heat map
    plt.imshow(matrix_data, cmap='YlOrRd', aspect='auto')
    plt.colorbar(label='Number of modifiers')
    
    # Axis labels
    plt.yticks(range(len(unique_params)), unique_params)
    plt.xticks(range(num_octants), octant_labels, rotation=45, ha='right')
    
    plt.title('Distribution of parameters by octants (heatmap)', fontsize=16)
    plt.tight_layout()
    plt.savefig('octant_heatmap.png')
    print("Octant heatmap saved to octant_heatmap.png")
    
    # ADDITIONALLY: Create a summary table for each parameter
    plt.figure(figsize=(14, len(unique_params) * 2))
    
    for param_idx, param in enumerate(unique_params):
        plt.subplot(len(unique_params), 1, param_idx + 1)
        
        # Collect data by octants for this parameter
        param_octants = {}
        for octant, items in unique_octants.items():
            for p, m in items:
                if p == param:
                    if octant not in param_octants:
                        param_octants[octant] = []
                    param_octants[octant].append(m)
        
        # Sort octants by the number of modifiers
        sorted_param_octants = sorted(param_octants.items(), key=lambda x: len(x[1]), reverse=True)
        
        # Create a bar plot
        octant_labels = [o for o, _ in sorted_param_octants]
        octant_values = [len(m) for _, m in sorted_param_octants]
        
        colors = [cmap(i % 20) for i in range(len(octant_labels))]
        bars = plt.bar(octant_labels, octant_values, color=colors)
        
        # Add labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    str(int(height)), ha='center', va='bottom')
        
        plt.title(f'Distribution of parameter {param} by octants')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
    
    plt.tight_layout()
    plt.savefig('parameter_octant_distribution.png')
    print("Parameter octant distribution saved to parameter_octant_distribution.png")

# Main function
def main():
    print("Starting parameter impact analysis...")
    
    # Run analysis
    baseline, impact_results = analyze_parameter_impact()
    
    # Save results
    save_results_to_csv(baseline, impact_results)
    
    # Visualize results
    visualize_parameter_impact(baseline, impact_results)
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()