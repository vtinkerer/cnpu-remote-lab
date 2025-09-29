import numpy as np
import matplotlib.pyplot as plt
import json
import PySpice.Logging.Logging as Logging
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import u_F, u_uF
import os

def henries_to_femtohenries(henries):
    return f"{int(henries * 1e15)}fH"

def farads_to_femtofarads(farads):
    return f"{int(farads * 1e15)}fF"

# Logging setup
Logging.setup_logging()

# Define default parameters in one place as a global dictionary
DEFAULT_PARAMS = {
    'Vin': 12,          # input voltage (V)
    'D': 0.5,  # PWM duty cycle
    'frequency': 312500, # PWM frequency (Hz)
    'L': 10e-6,  # inductance (H)
    'C': 44e-6, # capacitance (F)
    'Rload': 3.8,       # load resistance (Ohm)
    'RC': 0.02,     # capacitor ESR (Ohm)
    'RL': 19.5e-3, # inductor ESR (Ohm)
    'RD': 1e-9,     # transistor RDS(on) (Ohm)
    'RDS_ON': 0.05,     # diode resistance (Ohm)
}

# Function to create a buck converter
def create_buck_converter(
    Vin=DEFAULT_PARAMS['Vin'],
    D=DEFAULT_PARAMS['D'],
    frequency=DEFAULT_PARAMS['frequency'],
    L=DEFAULT_PARAMS['L'],
    C=DEFAULT_PARAMS['C'],
    Rload=DEFAULT_PARAMS['Rload'],
    RC=DEFAULT_PARAMS['RC'],
    RL=DEFAULT_PARAMS['RL'],
    RD=DEFAULT_PARAMS['RD'],
    RDS_ON=DEFAULT_PARAMS['RDS_ON'],
):
    
    circuit = Circuit('Buck Converter')
    circuit.V('in', 'vin', 'gnd', Vin)
    
    period = 1/frequency
    ton = D * period * 1e6
    period_us = period * 1e6
    circuit.V('gate', 'g', 'gnd', f'DC 0 PULSE(0 10 0 1n 1n {ton}us {period_us}us)')
    
    circuit.C('1', 'out_c', 'c_res', farads_to_femtofarads(C))

    circuit.S('1', 'vin', 'sw', 'g', 'gnd', model='SWITCH')
    circuit.model('SWITCH', 'SW', ron=RD, vt=1, vh=0)
    
    circuit.D('1', 'gnd', 'sw', model='MYDIODE')
    circuit.model('MYDIODE', 'D', is_=1e6, rs=RDS_ON)
    
    circuit.L('1', 'sw', 'out', henries_to_femtohenries(L))
    circuit.R('L1', 'out', 'out_c', RL)

    circuit.R('C1', 'c_res', 'gnd', RC)
    
    circuit.R('load', 'out_c', 'gnd', Rload)

    return circuit

# Function for simulation and parameter extraction
def simulate_and_analyze(circuit, esr_ind):
    try:
        # Calculate settling time
        freq = 312500  # PWM frequency (Hz)
        period = 1/freq
        
        delta = period * 5000
        end_time = delta + period
        step_time = period / 200
        # Run simulation
        simulator = circuit.simulator()
        analysis = simulator.transient(start_time=delta, step_time=step_time, end_time=end_time)
        
        # Determine the index to start analysis after settling
        time_points = np.array(analysis.time)

        # Output parameter analysis
        vout = np.array(analysis['out_c'])
        il = (np.array(analysis['out']) - np.array(analysis['out_c'])) / esr_ind

        vout_avg = np.mean(vout)
        vout_ripple = np.max(vout) - np.min(vout)
        il_avg = np.mean(il)
        il_ripple = np.max(il) - np.min(il)
        
        return {
            'vout_avg': vout_avg,
            'vout_ripple': vout_ripple,
            'il_avg': il_avg,
            'il_ripple': il_ripple,
            'vout': vout,
            'il': il,
            'time': time_points
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
        
        percent_change = ((modified_value - baseline_value) / baseline_value) * 100
        
        if percent_change > threshold:
            change = 1  # increase
        elif percent_change < -threshold:
            change = -1  # decrease
        else:
            change = 0  # no change
        
        results.append(change)
    
    return tuple(results)

def octant_to_string(octant):
    """Convert octant tuple to string representation"""
    mapping = {1: '+', 0: '0', -1: '-'}
    return ''.join(mapping[val] for val in octant)

def generate_waveform_plots(baseline, modified_results, param_name, modifier, folder="defect-detector/output/waveform_plots"):
    """
    Creates and saves voltage and current plots for comparing the baseline and modified circuit
    """
    # Create folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Create voltage plot
    plt.figure(figsize=(12, 6))

    print(len(baseline['time']))
    print(len(baseline['vout']))
    print(len(baseline['il']))
    print(len(modified_results['time']))
    print(len(modified_results['vout']))
    print(len(modified_results['il']))

    # Voltage plot
    plt.subplot(2, 1, 1)
    plt.plot(baseline['time'], baseline['vout'], 'b-', label='Baseline Vout')
    plt.plot(modified_results['time'], modified_results['vout'], 'r-', label=f'Modified Vout ({param_name} {modifier})')
    plt.title(f'Voltage Comparison - {param_name} {modifier}')
    plt.xlabel('Time')
    plt.ylabel('Voltage (V)')
    plt.grid(True)
    plt.legend()
    
    # Current plot
    plt.subplot(2, 1, 2)
    plt.plot(baseline['time'], baseline['il'], 'b-', label='Baseline Current')
    plt.plot(modified_results['time'], modified_results['il'], 'r-', label=f'Modified Current ({param_name} {modifier})')
    plt.title('Current Comparison')
    plt.xlabel('Time')
    plt.ylabel('Current (A)')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    
    # Save the plot
    filename = f"{folder}/{param_name}_{modifier.replace('>', 'inc').replace('<', 'dec')}.png"
    plt.savefig(filename)
    plt.close()
    
    print(f"Waveform plot saved to {filename}")

def analyze_parameter_impact():
    print("Creating baseline circuit...")
    # Create the base circuit and get reference values
    base_circuit = create_buck_converter()
    baseline_results = simulate_and_analyze(base_circuit, esr_ind=DEFAULT_PARAMS['RL'])
    
    print("Baseline results:")
    for param, value in baseline_results.items():
        if param not in ['vout', 'il', 'time']:
            print(f"{param}: {value:.6f}")
    
    # Parameters for analysis and their multipliers with symbolic labels
    parameters = {
        'Vin': [
            {'label': '+++', 'mult': 2},
            {'label': '++', 'mult': 1.5},
            {'label': '+', 'mult': 1.1},
            {'label': '-', 'mult': 1/1.1},
            {'label': '--', 'mult': 1/1.5},
            {'label': '---', 'mult': 1/2}
        ],
        'D': [
            {'label': '+++', 'mult': 2},
            {'label': '++', 'mult': 1.7},
            {'label': '+', 'mult': 1.2},
            {'label': '-', 'mult': 1/1.2},
            {'label': '--', 'mult': 1/1.7},
            {'label': '---', 'mult': 1e-6}
        ],
        'L': [
            {'label': '+++', 'mult': 100},
            {'label': '++', 'mult': 10},
            {'label': '+', 'mult': 3},
            {'label': '-', 'mult': 1/3},
            {'label': '--', 'mult': 1/10},
            {'label': '---', 'mult': 0}
        ],
        'C': [
            {'label': '+++', 'mult': 100},
            {'label': '++', 'mult': 10},
            {'label': '+', 'mult': 3},
            {'label': '-', 'mult': 1/3},
            {'label': '--', 'mult': 1/10},
            {'label': '---', 'mult': 0}
        ],
        'Rload': [
            {'label': '+++', 'mult': 1e18},
            {'label': '++', 'mult': 10},
            {'label': '+', 'mult': 3},
            {'label': '-', 'mult': 1/3},
            {'label': '--', 'mult': 1/10},
            {'label': '---', 'mult': 0}
        ],
        'RC': [
            {'label': '+++', 'mult': 1e18},
            {'label': '++', 'mult': 10},
            {'label': '+', 'mult': 3},
            {'label': '-', 'mult': 1/3},
            {'label': '--', 'mult': 1/10},
            {'label': '---', 'mult': 0}
        ],
        'RL': [
            {'label': '+++', 'mult': 1e18},
            {'label': '++', 'mult': 10},
            {'label': '+', 'mult': 3},
            {'label': '-', 'mult': 1/3},
            {'label': '--', 'mult': 1/10},
            {'label': '---', 'mult': 1e-12}
        ],
        'RD': [
            {'label': '+++', 'mult': 1e18},
            {'label': '++', 'mult': 1e5},
            {'label': '+', 'mult': 100},
            {'label': '-', 'mult': 1/3},
            {'label': '--', 'mult': 1/10},
            {'label': '---', 'mult': 1e-24}
        ],
        'RDS_ON': [
            {'label': '+++', 'mult': 1e18},
            {'label': '++', 'mult': 1e5},
            {'label': '+', 'mult': 100},
            {'label': '-', 'mult': 1/3},
            {'label': '--', 'mult': 1/10},
            {'label': '---', 'mult': 0}
        ]
    }
    
    results = {}
    
    # Dictionary to store the JSON structure
    # Key: octant string (e.g., '0000'), Value: list of parameter modifier lists
    json_data = {}
    
    # Parameter order for the JSON output
    param_order = ['Vin', 'D', 'L', 'C', 'Rload', 'RC', 'RL', 'RD', 'RDS_ON']
    
    for param_name, modifiers in parameters.items():
        print(f"\nAnalyzing parameter: {param_name}")
        param_results = {}
        
        for mod_info in modifiers:
            label = mod_info['label']
            mult = mod_info['mult']
            print(f"\nTesting modifier: {label} (x{mult})")
            
            # Create a copy of base parameters
            modified_params = DEFAULT_PARAMS.copy()
            
            # Update the specific parameter
            original_value = modified_params[param_name]
            modified_params[param_name] = original_value * mult
            
            try:
                # Create and simulate the circuit with the modified parameter
                circuit = create_buck_converter(**modified_params)
                modified_results = simulate_and_analyze(circuit, esr_ind=modified_params['RL'])
                
                # Create and save waveform plots
                generate_waveform_plots(baseline_results, modified_results, param_name, label)
                    
                # Determine the octant of change
                octant = determine_octant(baseline_results, modified_results)
                octant_str = octant_to_string(octant)
                
                # Initialize the octant key in json_data if not exists
                if octant_str not in json_data:
                    # Initialize with empty lists for each parameter
                    json_data[octant_str] = [[] for _ in range(len(param_order))]
                
                # Find the index of current parameter and add the modifier label
                param_index = param_order.index(param_name)
                if label not in json_data[octant_str][param_index]:
                    json_data[octant_str][param_index].append(label)
                
                # Save the results
                param_results[label] = {
                    'octant': octant,
                    'values': modified_results,
                    'mult': mult
                }
                
                print(f"  {param_name} {label}: Octant {octant} -> {octant_str}")
                for p, v in modified_results.items():
                    if p not in ['vout', 'il', 'time']:
                        change = ((v - baseline_results[p]) / baseline_results[p]) * 100
                        print(f"    {p}: {v:.6f} ({change:+.2f}%)")
                
            except Exception as e:
                print(f"  Error simulating {param_name} {label}: {e}")
        
        results[param_name] = param_results
    
    # Fill empty parameter lists with ['0'] for octants that don't have changes for all parameters
    for octant_str in json_data:
        for i in range(len(param_order)):
            if not json_data[octant_str][i]:  # If list is empty
                json_data[octant_str][i] = ['0']
    
    return baseline_results, results, json_data

def visualize_parameter_impact(baseline, results):
    # Create heat maps for each parameter
    parameter_names = ['Vmean', 'Vpulse', 'Imean', 'Ipulse']
    
    # Collect parameters and modifiers
    all_params = list(results.keys())
    
    # Use predefined order of modifiers
    all_modifiers = ['---', '--', '-', '+', '++', '+++']
    
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
    
    plt.rcParams.update({'font.size': 18})

    for k in range(4):
        # Use masked array for NaN values
        masked_data = np.ma.array(heat_data[:, :, k], mask=np.isnan(heat_data[:, :, k]))
        
        im = axes[k].imshow(masked_data, cmap='RdBu', vmin=-1, vmax=1)
        axes[k].set_title(f'Impact on {parameter_names[k]}', fontsize=18)
        axes[k].set_yticks(np.arange(len(all_params)))
        axes[k].set_xticks(np.arange(len(all_modifiers)))
        axes[k].set_yticklabels(all_params, fontsize=18)
        axes[k].set_xticklabels(all_modifiers, fontsize=16)
        plt.colorbar(im, ax=axes[k], ticks=[-1, 0, 1], label='- = -1, 0 = 0, + = 1')
    
    plt.tight_layout()
    plt.savefig('defect-detector/output/parameter_heatmaps.svg', format='svg')
    print("Heat maps saved to defect-detector/output/parameter_heatmaps.svg")

def save_json_data(json_data, filename="defect-detector/output/parameter_octant_mapping.json"):
    """Save the JSON data structure to file"""
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"JSON data saved to {filename}")
    
    # Also print a summary
    print(f"\nJSON Data Summary:")
    print(f"Number of unique octants: {len(json_data)}")
    for octant_str, param_lists in json_data.items():
        print(f"Octant '{octant_str}': {param_lists}")

# Main function
def main():
    print("Starting parameter impact analysis...")
    
    # Run analysis
    baseline, impact_results, json_data = analyze_parameter_impact()
    
    # Save JSON data
    save_json_data(json_data)
    
    # Visualize results
    visualize_parameter_impact(baseline, impact_results)
    
    print("Analysis complete!")

if __name__ == "__main__":
    main()