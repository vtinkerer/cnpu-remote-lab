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
    is_defective: bool

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
        self.circuit = None

    def build_circuit(self):
        circuit = Circuit('Buck Converter')
        circuit.V('in', 'vin', 'gnd', self.vin)
        
        ton = self.duty_cycle * self.period * 1e6
        period_us = self.period * 1e6
        circuit.V('gate', 'g', 'gnd', f'PULSE(0 10 0 1n 1n {ton}us {period_us}us)')
        
        circuit.S('1', 'vin', 'sw', 'g', 'gnd', model='SWITCH')
        circuit.model('SWITCH', 'SW', ron=1e-9, roff=1e12, vt=1, vh=0)
        
        circuit.D('1', 'gnd', 'sw', model='MYDIODE')
        circuit.model('MYDIODE', 'D', is_=1e6)

        circuit.L('1', 'sw', 'out', self.l_value)
        circuit.R('L1', 'out', 'out_c', self.l_resistance)
        circuit.C('1', 'out_c', 'gnd', self.c_value)
        circuit.R('load', 'out_c', 'gnd', self.r_load)
        
        self.circuit = circuit
        return circuit

    def run_simulation(self, measurement_time_points: List[float]):
        if self.circuit is None:
            self.build_circuit()
                
        simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        
        # Convert measurement times to seconds
        time_points = np.array(measurement_time_points) * 1e-6  # Convert μs to seconds
        
        delta = self.period * 600

        # Determine simulation parameters
        end_time = delta + time_points[-1]
        step_time = (time_points[1] - time_points[0]) * 0.5
        
        # Run transient analysis
        analysis = simulator.transient(
            step_time=step_time,
            end_time=end_time,
            start_time=delta,
            use_initial_condition=False
        )
            
        # Extract simulation results
        sim_pwm = np.array([float(v) for v in analysis['g']])
        sim_voltage = np.array([float(v) for v in analysis['out_c']])
        sim_out = np.array([float(v) for v in analysis['out']])
        sim_time = np.array([float(t) - delta for t in analysis.time]) * 1e6  # Convert to μs
        
        v_l_sense = sim_out - sim_voltage
        sim_current = v_l_sense / self.l_resistance
        
        # Map each measurement time to the closest simulation time
        measurement_time = np.array(measurement_time_points)

        # Find the indices of the closest simulation times
        indices = np.abs(sim_time[:, None] - measurement_time).argmin(axis=0)

        sim_voltage_matched = sim_voltage[indices]
        sim_current_matched = sim_current[indices]
        sim_pwm_matched = sim_pwm[indices]
        sim_time_matched = sim_time[indices]
        
        return {
            'out_c': sim_voltage_matched,
            'sim_current': sim_current_matched,
            'time': sim_time_matched,
            'pwm': sim_pwm_matched
        }

def calculate_rms_error(measured: List[float], simulated: List[float]) -> float:
    measured_array = np.array(measured)
    simulated_array = np.array(simulated)
    return np.sqrt(np.mean(np.square(measured_array - simulated_array)))

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
        # Extract measurement data directly from the input format
        measured_voltage = measurements.voltage
        measured_current = measurements.current
        measured_time = measurements.time
        measured_pwm = measurements.pwm
        # Run simulation
        buck = BuckConverter(circuit_params)
        analysis = buck.run_simulation(measured_time)
        
        # Extract matched simulation results
        sim_voltage = analysis['out_c']
        sim_current = analysis['sim_current']
        sim_time = analysis['time']
        sim_pwm = analysis['pwm']
        # Calculate errors
        voltage_error = calculate_rms_error(measured_voltage, sim_voltage)
        current_error = calculate_rms_error(measured_current, sim_current)
        
        # Determine if circuit is defective
        voltage_threshold = 0.05  
        current_threshold = 0.15
        is_defective = (voltage_error > voltage_threshold * np.mean(np.abs(measured_voltage)) or 
                       current_error > current_threshold * np.mean(np.abs(measured_current)))
        

        # After getting simulation results, visualize the comparison
        visualize_comparison(
            measured_time=measured_time,
            measured_voltage=measured_voltage,
            measured_current=measured_current,
            sim_voltage_matched=sim_voltage,
            sim_current_matched=sim_current,
            sim_pwm_matched=sim_pwm,
            measured_pwm=measured_pwm
        )
        
        return ComparisonResult(
            is_defective=is_defective,
            simulation_voltage=sim_voltage.tolist(),
            simulation_current=sim_current.tolist(),
            simulation_time=sim_time.tolist(),
            measured_voltage=measured_voltage,
            measured_current=measured_current,
            measured_time=measured_time,
            voltage_error_rms=voltage_error,
            current_error_rms=current_error,
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3801)