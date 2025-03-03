from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import matplotlib.pyplot as plt

app = FastAPI()


class CircuitParams(BaseModel):
    vin: float = 13
    c_value: float = 44e-6
    duty_cycle: float = 0.45
    current_out: float = 2.9

class ComparisonResult(BaseModel):
    simulation_voltage: List[float]
    simulation_current: List[float]
    simulation_time: List[float]
    measured_voltage: List[float]
    measured_current: List[float]
    measured_time: List[float]
    voltage_error_rms: float
    current_error_rms: float
    voltage_error_percentage: float
    current_error_percentage: float
    is_defective: bool
    mean_voltage: float
    mean_current: float
    model_mean_voltage: float
    model_mean_current: float
    model_min_voltage: float
    model_max_voltage: float
    model_min_current: float
    model_max_current: float


class MeasurementData(BaseModel):
    voltage: List[float]
    time: List[float]
    pwm: List[int]
    current: List[float]

class BuckConverter:
    def __init__(self, params: CircuitParams):
        self.vin = params.vin
        self.freq = 312500
        self.l_value = 10e-6
        self.c_value = params.c_value
        self.duty_cycle = params.duty_cycle
        self.l_resistance = 19.5e-3  # from datasheet
        self.current_out = params.current_out
        
        self.vout = self.vin * self.duty_cycle
        self.r_load = self.vout / self.current_out
        self.period = 1 / self.freq

        periods_in_time_constant = np.sqrt(self.c_value / self.l_value) / self.period

        self.circuit = None

    def build_circuit(self):
        circuit = Circuit('Buck Converter')
        circuit.V('in', 'vin', circuit.gnd, self.vin)
        
        ton = self.duty_cycle * self.period * 1e6
        period_us = self.period * 1e6
        circuit.V('gate', 'g', circuit.gnd, f'PULSE(0 10 0 1n 1n {ton}us {period_us}us)')
        circuit.S('1', 'vin', 'sw', 'g', circuit.gnd, model='switch_model')
        # circuit.PulseVoltageSource('pulse', 'g', circuit.gnd,
        #                 initial_value=0, pulsed_value=self.vin,
        #                 pulse_width=self.duty_cycle*self.period,
        #                 period=self.period)
        # May be set VT to 0?
        # Looks like the roff is not used
        # circuit.VoltageControlledSwitch('sw', 'vin', 'sw', 'g', circuit.gnd, 
        #                           model='switch_model')
        circuit.model('switch_model', 'SW', ron=1e-9, roff=1e12, vt=1, vh=0)
        
        circuit.D('1', circuit.gnd, 'sw', model='MYDIODE')
        circuit.model('MYDIODE', 'D', is_=1e6, rs=1e-5)

        circuit.L('1', 'sw', 'out', self.l_value)
        circuit.R('L1', 'out', 'out_c', self.l_resistance)

        circuit.C('1', 'out_c', 'c_res', self.c_value )
        circuit.R('C1', 'c_res', circuit.gnd, 0.1)
        
        circuit.R('load', 'out_c', circuit.gnd, self.r_load)
        

        self.circuit = circuit
        return circuit

    def run_simulation(self, measurement_time_points: List[float]):
        if self.circuit is None:
            self.build_circuit()
                
        simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        
        # Convert measurement times to seconds and pre-allocate numpy array
        time_points = np.asarray(measurement_time_points, dtype=np.float64) * 1e-6
        
        delta = self.period * 600
        end_time = delta + time_points[-1]
        step_time = (time_points[1] - time_points[0]) * 0.5
        
        analysis = simulator.transient(
            step_time=step_time,
            end_time=end_time,
            start_time=delta,
            use_initial_condition=False
        )
            
        # Vectorize data extraction
        sim_data = np.array([
            [float(v) for v in analysis['g']],
            [float(v) for v in analysis['out_c']],
            [float(v) for v in analysis['out']]
        ])
        
        sim_time = (np.array([float(t) for t in analysis.time]) - delta) * 1e6
        
        # Vectorized calculations
        v_l_sense = sim_data[2] - sim_data[1]
        sim_current = v_l_sense / self.l_resistance
        
        # Optimized time matching using searchsorted
        measurement_time = np.asarray(measurement_time_points)
        indices = np.searchsorted(sim_time, measurement_time)
        indices = np.clip(indices, 0, len(sim_time) - 1)
        
        # Adjust indices to get closest point
        mask = indices > 0
        prev_diff = np.abs(sim_time[indices[mask] - 1] - measurement_time[mask])
        curr_diff = np.abs(sim_time[indices[mask]] - measurement_time[mask])
        indices[mask][prev_diff < curr_diff] -= 1
        
        result = {
            'out_c': sim_data[1][indices],
            'sim_current': sim_current[indices],
            'time': sim_time[indices],
            'pwm': sim_data[0][indices]
        }
        
        return result

def calculate_rms_error(measured: List[float], simulated: List[float]) -> float:
    # Vectorized calculation
    return np.sqrt(np.mean(np.square(np.asarray(measured) - np.asarray(simulated))))

def visualize_comparison(measured_time, measured_voltage, measured_current, measured_pwm,
                        sim_voltage_matched, sim_current_matched, sim_pwm_matched, ):
    # Create figure with three subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
    
    # Plot voltage comparison
    ax1.plot(measured_time, measured_voltage, 'b-', label='Measured', linewidth=2)
    ax1.plot(measured_time, sim_voltage_matched, 'r--', label='Simulated', linewidth=2)
    ax1.set_xlabel('Time (μs)')
    ax1.set_ylabel('Voltage (V)')
    ax1.set_title('Voltage Comparison')
    ax1.grid(True)
    ax1.legend()
    ax1.set_ylim(bottom=0, top=15)  # Set y-axis from 0 to 15V
    
    # Plot current comparison
    ax2.plot(measured_time, measured_current, 'b-', label='Measured', linewidth=2)
    ax2.plot(measured_time, sim_current_matched, 'r--', label='Simulated', linewidth=2)
    ax2.set_xlabel('Time (μs)')
    ax2.set_ylabel('Current (A)')
    ax2.set_title('Current Comparison')
    ax2.grid(True)
    ax2.legend()
    ax2.set_ylim(bottom=0)  # Set y-axis to start from 0
    
    # Plot PWM signal
    ax3.plot(measured_time, measured_pwm, 'g-', label='PWM', linewidth=2)
    ax3.plot(measured_time, sim_pwm_matched, 'r--', label='Simulated', linewidth=2)
    ax3.set_xlabel('Time (μs)')
    ax3.set_ylabel('PWM Value')
    ax3.set_title('PWM Signal')
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
        window_size = 15  # Adjust this value based on your spike width
        measured_current_filtered = np.median(
            np.lib.stride_tricks.sliding_window_view(
                np.pad(measured_current, (window_size//2, window_size//2), mode='edge'),
                window_size
            ),
            axis=1
        )
        
        # Run simulation
        buck = BuckConverter(circuit_params)
        analysis = buck.run_simulation(measured_time)
        
        # Extract results (already numpy arrays)
        sim_voltage = analysis['out_c']
        sim_current = analysis['sim_current']
        
        # Use filtered current for calculations
        mean_measured_voltage = np.mean(np.abs(measured_voltage))
        mean_measured_current = np.mean(np.abs(measured_current_filtered))
        
        model_min_voltage = np.min(np.abs(sim_voltage))
        model_max_voltage = np.max(np.abs(sim_voltage))
        model_min_current = np.min(np.abs(sim_current))
        model_max_current = np.max(np.abs(sim_current))

        voltage_error = calculate_rms_error(measured_voltage, sim_voltage)
        current_error = calculate_rms_error(measured_current_filtered, sim_current)
        
        voltage_error_percentage = (voltage_error / mean_measured_voltage) * 100
        current_error_percentage = (current_error / mean_measured_current) * 100
        
        # Simplified defective check
        voltage_threshold = 0.1
        current_threshold = 0.2
        is_defective = (
            voltage_error > voltage_threshold * mean_measured_voltage or 
            current_error > current_threshold * mean_measured_current
        )
        

        # Visualize comparison
        # visualize_comparison(
        #     measured_time, 
        #     measured_voltage, 
        #     measured_current_filtered, 
        #     analysis['pwm'], 
        #     sim_voltage, 
        #     sim_current, 
        #     analysis['pwm'])
        
        return ComparisonResult(
            is_defective=is_defective,
            simulation_voltage=sim_voltage.tolist(),
            simulation_current=sim_current.tolist(),
            simulation_time=analysis['time'].tolist(),
            measured_voltage=measured_voltage.tolist(),
            measured_current=measured_current_filtered.tolist(),
            measured_time=measured_time,
            voltage_error_rms=voltage_error,
            current_error_rms=current_error,
            voltage_error_percentage=voltage_error_percentage,
            current_error_percentage=current_error_percentage,
            mean_voltage=mean_measured_voltage,
            mean_current=mean_measured_current,
            model_mean_voltage=np.mean(np.abs(sim_voltage)),
            model_mean_current=np.mean(np.abs(sim_current)),
            model_min_voltage=model_min_voltage,
            model_max_voltage=model_max_voltage,
            model_min_current=model_min_current,
            model_max_current=model_max_current
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3802)
