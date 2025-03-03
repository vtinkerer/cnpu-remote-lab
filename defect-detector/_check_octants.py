from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import numpy as np
from typing import List, Dict, Optional
import matplotlib.pyplot as plt

class CircuitParams():
    vin: float = 12
    c_value: float = 44e-6
    duty_cycle: float = 0.5
    current_out: float = 2.9
    esr: float = 0.1
    l_value: float = 10e-6
    l_resistance: float = 19.5e-3
    transistor_on_resistance: float = 1e-9
    overwrite_resistance: bool = False
    overwrite_resistance_multiplier: float = 1 / 10
    frequency: float = 312500

class BuckConverter:
    def __init__(self, params: CircuitParams):
        self.vin = params.vin
        self.freq = params.frequency
        self.l_value = params.l_value
        self.c_value = params.c_value
        self.duty_cycle = params.duty_cycle
        self.l_resistance = params.l_resistance
        self.current_out = params.current_out
        self.transistor_on_resistance = params.transistor_on_resistance
        self.vout = self.vin * self.duty_cycle
        self.r_load = self.vout / self.current_out
        self.period = 1 / self.freq
        self.circuit = None
        self.esr = params.esr
        if params.overwrite_resistance:
            self.r_load = self.r_load * params.overwrite_resistance_multiplier

    def build_circuit(self):
        circuit = Circuit('Buck Converter')
        circuit.V('in', 'vin', 'gnd', self.vin)
        
        ton = self.duty_cycle * self.period * 1e6
        period_us = self.period * 1e6
        circuit.V('gate', 'g', 'gnd', f'PULSE(0 10 0 1n 1n {ton}us {period_us}us)')
        
        circuit.S('1', 'vin', 'sw', 'g', 'gnd', model='SWITCH')
        circuit.model('SWITCH', 'SW', ron=self.transistor_on_resistance, vt=1, vh=0)
        
        circuit.D('1', 'gnd', 'sw', model='MYDIODE')
        circuit.model('MYDIODE', 'D', is_=1e6)
            
        circuit.L('1', 'sw', 'out', self.l_value)
        circuit.R('L1', 'out', 'out_c', self.l_resistance)

        circuit.C('1', 'out_c', 'c_res', self.c_value)
        circuit.R('C1', 'c_res', 'gnd', self.esr)
        
        circuit.R('load', 'out_c', 'gnd', self.r_load)
        
        self.circuit = circuit
        return circuit

    def run_simulation(self):
        if self.circuit is None:
            self.build_circuit()
                
        simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        
        delta = self.period * 600
        end_time = delta + self.period * 2
        step_time = self.period / 300
        
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
        
        
        result = {
            'out_c': sim_data[1],
            'sim_current': sim_current,
            'time': sim_time,
            'pwm': sim_data[0]
        }
        
        return result
    
def main(): 

    params = CircuitParams()

    converter = BuckConverter(params)
    converter.build_circuit()
    results = converter.run_simulation()

    mean_voltage_before = np.mean(results['out_c'])
    mean_current_before = np.mean(results['sim_current'])
    voltage_ripple_before = np.max(results['out_c']) - np.min(results['out_c'])
    current_ripple_before = np.max(results['sim_current']) - np.min(results['sim_current'])

    print(f"Mean voltage before: {mean_voltage_before}")
    print(f"Voltage ripple before: {voltage_ripple_before}")
    print(f"Mean current before: {mean_current_before}")
    print(f"Current ripple before: {current_ripple_before}")

    print("===================================")

    params.overwrite_resistance = True
    params.overwrite_resistance_multiplier = 1000
    converter = BuckConverter(params)
    converter.build_circuit()
    results = converter.run_simulation()

    mean_voltage_after = np.mean(results['out_c'])
    mean_current_after = np.mean(results['sim_current'])
    voltage_ripple_after = np.max(results['out_c']) - np.min(results['out_c'])
    current_ripple_after = np.max(results['sim_current']) - np.min(results['sim_current'])

    print(f"Mean voltage after: {mean_voltage_after}")
    print(f"Voltage ripple after: {voltage_ripple_after}")
    print(f"Mean current after: {mean_current_after}")
    print(f"Current ripple after: {current_ripple_after}")

    print("===================================")

    mean_voltage_ratio = mean_voltage_after / mean_voltage_before
    mean_current_ratio = mean_current_after / mean_current_before
    voltage_ripple_ratio = voltage_ripple_after / voltage_ripple_before
    current_ripple_ratio = current_ripple_after / current_ripple_before

    print(f"Mean voltage ratio: {mean_voltage_ratio}")
    print(f"Voltage ripple ratio: {voltage_ripple_ratio}")
    print(f"Mean current ratio: {mean_current_ratio}")
    print(f"Current ripple ratio: {current_ripple_ratio}")

if __name__ == "__main__":
    main()