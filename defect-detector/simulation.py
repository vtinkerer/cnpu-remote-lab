from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import numpy as np
from typing import List
from .utils import henries_to_femtohenries, farads_to_femtofarads


class BuckConverter:
    def __init__(self, params, optimization_params=None):
        self.vin = params.vin
        self.freq = 312500
        self.l_value = 10e-6
        self.c_value = params.c_value * 1e-6  # Convert to Farads
        self.duty_cycle = params.pwm_percentage / 100.0
        self.l_resistance = 19.5e-3  # from datasheet (fixed, not optimized)
        self.r_load = params.r_load
        self.period = 1 / self.freq
        
        # Store optimization parameters (defaults will be used if None)
        self.optimization_params = optimization_params or {}

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
        # Get optimization parameters with defaults
        gate_rise_time = self.optimization_params.get('gate_rise_time', 1.015435566480695e-10)
        gate_fall_time = self.optimization_params.get('gate_fall_time', 7.677903815277957e-08)
        switch_ron = self.optimization_params.get('switch_ron', 1.8575783275122382e-11)
        diode_rs = self.optimization_params.get('diode_rs', 1.2711852475685458e-05)
        diode_is = self.optimization_params.get('diode_is', 7.705192529660374e-15)
        cap_esr = self.optimization_params.get('cap_esr', 0.08784075541117503)
        cap_inductance = self.optimization_params.get('cap_inductance', 4.36429542552223e-10)

        circuit = Circuit('Buck Converter')
        circuit.V('in', 'vin', circuit.gnd, self.vin)
        
        ton = self.duty_cycle * self.period * 1e6
        period_us = self.period * 1e6
        
        # Convert rise/fall times to proper format for SPICE (in seconds, will be shown in nanoseconds)
        rise_time_str = f'{gate_rise_time*1e9}n'
        fall_time_str = f'{gate_fall_time*1e9}n'

        circuit.V('gate', 'g', circuit.gnd, f'DC 0 PULSE(0 10 0 {rise_time_str} {fall_time_str} {ton}us {period_us}us)')
        circuit.S('1', 'vin', 'sw', 'g', circuit.gnd, model='switch_model')

        circuit.model('switch_model', 'SW', ron=switch_ron, roff=1e12, vt=1, vh=0)
        
        circuit.D('1', circuit.gnd, 'sw', model='MYDIODE')
        circuit.model('MYDIODE', 'D', is_=diode_is, rs=diode_rs)

        # Store inductor reference for setting initial current
        self.inductor = circuit.L('1', 'sw', 'out', henries_to_femtohenries(self.l_value))
        circuit.R('L1', 'out', 'out_c', self.l_resistance)

        circuit.L('C1', 'out_c', 'c_r', henries_to_femtohenries(cap_inductance))
        circuit.R('C1', 'c_r', 'c_c', cap_esr)
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