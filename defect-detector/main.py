import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from .utils import filter_signal, fix_signal_spike, trim_data_for_calculations
from .simulation import BuckConverter

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
        measured_current_filtered = filter_signal(measured_current, 'current')
        measured_voltage_filtered = filter_signal(measured_voltage, 'voltage')

        # Run simulation and get full dataset
        buck = BuckConverter(circuit_params)
        simulation_result = buck.run_simulation(measured_time)
        
        # Get FULL simulation dataset for plotting
        sim_voltage_full = simulation_result['sim_voltage_full']
        sim_current_full = simulation_result['sim_current_full']
        
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