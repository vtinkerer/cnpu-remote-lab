from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import matplotlib.pyplot as plt

def fix_signal_spike(signal, extrapolate_percent=5, reference_start=5, reference_end=10):
    """
    Fix spike at beginning of signal by extrapolating from a stable reference region.
    
    Parameters:
    -----------
    signal : array-like
        Input signal with spike at beginning
    extrapolate_percent : float
        Percentage of signal length to replace (default: 5%)
    reference_start : float
        Start of reference region as percentage of signal length (default: 5%)
    reference_end : float
        End of reference region as percentage of signal length (default: 10%)

    Returns:
    --------
    corrected_signal : numpy array
        Signal with corrected beginning
    """
    signal = np.array(signal)
    n = len(signal)
    
    # Calculate indices
    replace_end = int(n * extrapolate_percent / 100)
    ref_start = int(n * reference_start / 100)
    ref_end = int(n * reference_end / 100)
    
    # Extract reference region for extrapolation
    ref_indices = np.arange(ref_start, ref_end)
    ref_values = signal[ref_start:ref_end]
    
    # Fit polynomial to reference region (linear or quadratic)
    # Try linear first, then quadratic if needed
    try:
        # Linear fit
        coeffs = np.polyfit(ref_indices, ref_values, 1)
        poly_func = np.poly1d(coeffs)
    except:
        # Fallback to mean if fitting fails
        poly_func = lambda x: np.mean(ref_values)
    
    # Generate extrapolated values for the beginning
    replace_indices = np.arange(0, replace_end)
    extrapolated_values = poly_func(replace_indices)
    
    # Create corrected signal
    corrected_signal = signal.copy()
    corrected_signal[:replace_end] = extrapolated_values
    
    # Smooth the transition to avoid discontinuity
    transition_length = min(20, replace_end // 2)
    if transition_length > 0:
        transition_start = replace_end - transition_length
        transition_end = replace_end + transition_length
        
        # Create smooth transition using cosine taper
        taper = np.linspace(0, np.pi, 2 * transition_length)
        weight = (1 + np.cos(taper)) / 2
        
        # Apply transition weights
        for i in range(transition_length):
            idx = transition_start + i
            if idx < len(corrected_signal):
                original_weight = 1 - weight[i]
                extrapolated_weight = weight[i]
                corrected_signal[idx] = (original_weight * signal[idx] + 
                                       extrapolated_weight * extrapolated_values[idx])
    
    return corrected_signal

def henries_to_femtohenries(henries):
    return f"{int(henries * 1e15)}fH"

def farads_to_femtofarads(farads):
    return f"{int(farads * 1e15)}fF"

app = FastAPI()

class CircuitParams(BaseModel):
    vin: float 
    c_value: float 
    pwm_percentage: float 
    r_load: float 

class ComparisonResult(BaseModel):
    percentage_difference_avg_vout: float
    percentage_difference_ripple_vout: float
    percentage_difference_avg_il: float
    percentage_difference_ripple_il: float
    sim_vout_avg: float
    sim_vout_ripple: float
    sim_il_avg: float
    sim_il_ripple: float
    measured_vout_avg: float
    measured_vout_ripple: float
    measured_il_avg: float
    measured_il_ripple: float


class MeasurementData(BaseModel):
    voltage: List[float]
    time: List[float]
    pwm: List[int]
    current: List[float]

def trim_data_for_calculations(data_array):
    """Trim 10% from beginning and end of data for calculations"""
    n = len(data_array)
    trim_size = n // 10
    if trim_size == 0:  # Handle small datasets
        return data_array
    return data_array[trim_size:-trim_size]

class BuckConverter:
    def __init__(self, params: CircuitParams):
        self.vin = params.vin
        self.freq = 312500
        self.l_value = 10e-6
        self.c_value = params.c_value * 1e-6  # Convert to Farads
        self.duty_cycle = params.pwm_percentage / 100.0
        self.l_resistance = 19.5e-3  # from datasheet
        self.r_load = params.r_load        
        self.period = 1 / self.freq

        self.circuit = None

    def calculate_steady_state_values(self):
        """
        Calculate theoretical steady-state values for initial conditions.
        This significantly reduces simulation warmup time.
        """
        # Output voltage (ideal buck converter)
        vout_ideal = self.vin * self.duty_cycle
        
        # Average output current (considering load resistance)
        iout_avg = vout_ideal / self.r_load
        
        # Average inductor current (equals output current in CCM)
        il_avg = iout_avg
        
        # Account for inductor resistance voltage drop
        v_drop_inductor = il_avg * self.l_resistance
        vout_with_loss = vout_ideal - v_drop_inductor
        
        # Recalculate current with actual output voltage
        il_avg = vout_with_loss / self.r_load
        v_drop_inductor = il_avg * self.l_resistance
        vout_with_loss = vout_ideal - v_drop_inductor
        
        # Inductor current ripple: ΔiL = (Vin - Vout) * D * T / L
        delta_il = (self.vin - vout_with_loss) * self.duty_cycle * self.period / self.l_value
        
        # Peak and valley inductor currents
        il_peak = il_avg + delta_il / 2
        il_valley = il_avg - delta_il / 2
        
        # Capacitor voltage (same as output voltage in steady state)
        vc = vout_with_loss
        
        # For initial condition, start at valley current (switch about to turn on)
        # This matches the natural start of the PWM cycle
        il_initial = il_valley
        
        return {
            'vout': vout_with_loss,
            'vc': vc,
            'il_avg': il_avg,
            'il_initial': il_initial,  # Use valley current for better initial sync
            'il_peak': il_peak,
            'il_valley': il_valley,
            'delta_il': delta_il
        }

    def build_circuit(self):
        circuit = Circuit('Buck Converter')
        circuit.V('in', 'vin', circuit.gnd, self.vin)
        
        ton = self.duty_cycle * self.period * 1e6
        period_us = self.period * 1e6

        circuit.V('gate', 'g', circuit.gnd, f'PULSE(0 10 0 1n 1n {ton}us {period_us}us)')
        circuit.S('1', 'vin', 'sw', 'g', circuit.gnd, model='switch_model')

        circuit.model('switch_model', 'SW', ron=1e-9, roff=1e12, vt=1, vh=0)
        
        circuit.D('1', circuit.gnd, 'sw', model='MYDIODE')
        circuit.model('MYDIODE', 'D', is_=1e6, rs=1e-4)

        # Store inductor reference for setting initial current
        self.inductor = circuit.L('1', 'sw', 'out', henries_to_femtohenries(self.l_value))
        circuit.R('L1', 'out', 'out_c', self.l_resistance)

        circuit.L('C1', 'out_c', 'c_r', henries_to_femtohenries(1e-9))
        circuit.R('C1', 'c_r', 'c_c', 0.05)
        circuit.C('1', 'c_c', circuit.gnd, farads_to_femtofarads(self.c_value))
        
        circuit.R('load', 'out_c', circuit.gnd, self.r_load)
        

        self.circuit = circuit
        return circuit

    def run_simulation(self, measurement_time_points: List[float]):
        if self.circuit is None:
            self.build_circuit()
                
        # Calculate optimal initial conditions
        steady_state = self.calculate_steady_state_values()
        
        simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)

        simulator.initial_condition(out_c=steady_state['vout'])
        simulator.initial_condition(c_c=steady_state['vc'])
        simulator.initial_condition(c_r=steady_state['vc'])
        simulator.initial_condition(out=steady_state['vout']) 
        self.inductor.ic = steady_state['il_initial']

        # Convert measurement times to seconds for simulation setup
        time_points = np.asarray(measurement_time_points, dtype=np.float64) * 1e-6
        
        delta = self.period * 100
        end_time = delta + time_points[-1]
        step_time = (time_points[1] - time_points[0]) * 0.5
        
        analysis = simulator.transient(
            step_time=step_time,
            end_time=end_time,
            start_time=delta,
            use_initial_condition=True
        )
            
        # Extract full simulation data (no time matching here)
        sim_gate = np.array([float(v) for v in analysis['g']])
        sim_voltage_full = np.array([float(v) for v in analysis['out_c']])
        sim_out_full = np.array([float(v) for v in analysis['out']])
        sim_time_full = (np.array([float(t) for t in analysis.time]) - delta) * 1e6
        
        # Calculate current from full dataset
        v_l_sense_full = sim_out_full - sim_voltage_full
        sim_current_full = v_l_sense_full / self.l_resistance
        
        # Return both full dataset for calculations and matched data for visualization
        result = {
            'sim_voltage_full': sim_voltage_full,
            'sim_current_full': sim_current_full,
            'sim_time_full': sim_time_full,
            'sim_gate_full': sim_gate,
            'measurement_time_points': measurement_time_points
        }
        
        return result

    def get_visualization_data(self, simulation_result):
        """Extract matched data points for visualization using searchsorted"""
        sim_voltage_full = simulation_result['sim_voltage_full']
        sim_current_full = simulation_result['sim_current_full']
        sim_time_full = simulation_result['sim_time_full']
        sim_gate_full = simulation_result['sim_gate_full']
        measurement_time_points = simulation_result['measurement_time_points']
        
        # Use searchsorted only for visualization matching
        measurement_time = np.asarray(measurement_time_points)
        indices = np.searchsorted(sim_time_full, measurement_time)
        indices = np.clip(indices, 0, len(sim_time_full) - 1)
        
        # Adjust indices to get closest point
        mask = indices > 0
        prev_diff = np.abs(sim_time_full[indices[mask] - 1] - measurement_time[mask])
        curr_diff = np.abs(sim_time_full[indices[mask]] - measurement_time[mask])
        indices[mask][prev_diff < curr_diff] -= 1
        
        return {
            'sim_voltage_matched': sim_voltage_full[indices],
            'sim_current_matched': sim_current_full[indices],
            'sim_pwm_matched': sim_gate_full[indices],
            'matched_time': measurement_time
        }

def visualize_comparison(measured_time, measured_voltage, measured_current, measured_pwm,
                        sim_voltage_matched, sim_current_matched, sim_pwm_matched):
    # Create figure with three subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    
    # Plot voltage comparison - USE ALL DATA
    ax1.plot(measured_time, measured_voltage, 'b-', label='Measured', linewidth=2)
    ax1.plot(measured_time, sim_voltage_matched, 'r--', label='Simulated', linewidth=2)
    ax1.set_xlabel('Time (μs)')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_title('Voltage Comparison (Full Dataset)')
    ax1.grid(True)
    ax1.legend()
    ax1.set_ylim(bottom=0, top=15)  # Set y-axis from 0 to 15V
    
    # Plot current comparison - USE ALL DATA
    ax2.plot(measured_time, measured_current, 'b-', label='Measured', linewidth=2)
    ax2.plot(measured_time, sim_current_matched, 'r--', label='Simulated', linewidth=2)
    ax2.plot(measured_time, fix_signal_spike(measured_current), 'g--', label='Fixed', linewidth=2)
    ax2.set_xlabel('Time (μs)')
    ax2.set_ylabel('Current (A)')
    ax2.set_title('Current Comparison (Full Dataset)')
    ax2.grid(True)
    ax2.legend()
    ax2.set_ylim(bottom=0)  # Set y-axis to start from 0
    
    # Plot PWM signal - USE ALL DATA
    ax3.plot(measured_time, measured_pwm, 'g-', label='PWM', linewidth=2)
    ax3.plot(measured_time, sim_pwm_matched, 'r--', label='Simulated', linewidth=2)
    ax3.set_xlabel('Time (μs)')
    ax3.set_ylabel('PWM Value')
    ax3.set_title('PWM Signal (Full Dataset)')
    ax3.grid(True)
    ax3.legend()
    ax3.set_ylim(bottom=0)  # Set y-axis to start from 0
    
    plt.tight_layout()
    plt.show()

@app.post("/analyze", response_model=ComparisonResult)
async def analyze_measurements(
    measurements: MeasurementData,
    circuit_params: CircuitParams
):
    try:
        # Convert to numpy arrays once
        measured_voltage = np.asarray(measurements.voltage)
        measured_current = np.asarray(measurements.current)
        measured_time = measurements.time
        
        # Apply median filter to remove current spikes
        window_size_current = 17  # Adjust this value based on your spike width
        measured_current_filtered = np.median(
            np.lib.stride_tricks.sliding_window_view(
                np.pad(measured_current, (window_size_current//2, window_size_current//2), mode='edge'),
                window_size_current
            ),
            axis=1
        )

        window_size_voltage = 3 
        measured_voltage_filtered = np.median(
            np.lib.stride_tricks.sliding_window_view(
                np.pad(measured_voltage, (window_size_voltage//2, window_size_voltage//2), mode='edge'),
                window_size_voltage
            ),
            axis=1
        )

        # Run simulation and get full dataset
        buck = BuckConverter(circuit_params)
        simulation_result = buck.run_simulation(measured_time)
        
        # Get FULL simulation dataset for plotting
        sim_voltage_full = simulation_result['sim_voltage_full']
        sim_current_full = simulation_result['sim_current_full']
        
        # measured_voltage_filtered_trimmed = trim_data_for_calculations(measured_voltage_filtered)
        # measured_current_filtered_trimmed = trim_data_for_calculations(measured_current_filtered)
        measured_voltage_filtered_trimmed = fix_signal_spike(measured_voltage_filtered)
        measured_current_filtered_trimmed = fix_signal_spike(measured_current_filtered)
        
        # Calculate statistics from TRIMMED datasets
        sim_vout_avg = np.mean(sim_voltage_full)
        sim_vout_ripple = np.max(sim_voltage_full) - np.min(sim_voltage_full)
        sim_il_avg = np.mean(sim_current_full)
        sim_il_ripple = np.max(sim_current_full) - np.min(sim_current_full)

        # Calculate statistics from TRIMMED measured data
        measured_vout_avg = np.mean(measured_voltage_filtered_trimmed)
        measured_vout_ripple = np.max(measured_voltage_filtered_trimmed) - np.min(measured_voltage_filtered_trimmed)
        measured_il_avg = np.mean(measured_current_filtered_trimmed)
        measured_il_ripple = np.max(measured_current_filtered_trimmed) - np.min(measured_current_filtered_trimmed)

        # Get matched data for visualization (using FULL datasets)
        viz_data = buck.get_visualization_data(simulation_result)
        
        # Visualize comparison using FULL matched data (not trimmed)
        visualize_comparison(
            measured_time, 
            measured_voltage_filtered,  # Full dataset for plotting
            measured_current_filtered,  # Full dataset for plotting
            measurements.pwm,
            viz_data['sim_voltage_matched'], 
            viz_data['sim_current_matched'], 
            viz_data['sim_pwm_matched']
        )
        
        return ComparisonResult(
            sim_vout_avg=sim_vout_avg,
            sim_vout_ripple=sim_vout_ripple,
            sim_il_avg=sim_il_avg,
            sim_il_ripple=sim_il_ripple,
            measured_vout_avg=measured_vout_avg,
            measured_vout_ripple=measured_vout_ripple,
            measured_il_avg=measured_il_avg,
            measured_il_ripple=measured_il_ripple,
            percentage_difference_avg_vout=((measured_vout_avg - sim_vout_avg) / sim_vout_avg) * 100,
            percentage_difference_ripple_vout=((measured_vout_ripple - sim_vout_ripple) / sim_vout_ripple) * 100,
            percentage_difference_avg_il=((measured_il_avg - sim_il_avg) / sim_il_avg) * 100,
            percentage_difference_ripple_il=((measured_il_ripple - sim_il_ripple) / sim_il_ripple) * 100,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3803)