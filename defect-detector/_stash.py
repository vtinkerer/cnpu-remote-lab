import math
import time
from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['axes.formatter.useoffset'] = False


class BuckConverter:
    def __init__(self, 
                 vin=20,           # Input voltage (V)
                 freq=312500,      # Switching frequency (Hz)
                 l_value=10e-6,    # Inductor value (H)
                 c_value=113e-6,   # Capacitor value (F)
                 duty_cycle=0.5):  # Duty cycle
        
        self.vin = vin
        self.freq = freq
        self.l_value = l_value
        self.c_value = c_value
        self.l_resistance = 19.5e-3 # from datasheet
        self.l_parasitic_c = 1 / (4 * math.pi ** 2 * 17e6 ** 2 * self.l_value) # from the C = 1/((2π*SRF)^2*L) formula, SRF=17e6 according to datasheet
        print(f"Parasitic capacitance: {self.l_parasitic_c}")
        self.duty_cycle = duty_cycle

        self.vout = vin * duty_cycle
        self.r_load = self.vout / 2.9
            
        self.period = 1 / freq
        self.circuit = None
            
    def build_circuit(self):
        """Creates the buck converter circuit"""
        circuit = Circuit('Buck Converter')

        # Create voltage source
        circuit.V('in', 'vin', 'gnd', self.vin)
        
        # Add gate drive voltage source for the switch
        ton = self.duty_cycle * self.period * 1e6  # in μs
        period_us = self.period * 1e6              # in μs
        circuit.V('gate', 'g', 'gnd', f'PULSE(0 10 0 1n 1n {ton}us {period_us}us)')
        
        # Add voltage-controlled switch
        circuit.S('1', 'vin', 'sw', 'g', 'gnd', model='SWITCH')
        circuit.model('SWITCH', 'SW', ron=1e-9, roff=1e12, vt=1, vh=0)
        
        # Add ideal switch as a diode replacement
        circuit.D('1', 'gnd', 'sw', model='MYDIODE')
        # circuit.model('MYDIODE', 'D', is_=1e-6, n=1.05, rs=0.005 ) # From datasheet according to chatgpt:  (IS=1e-6 N=1.05 RS=0.005 BV=50 CJO=50p M=0.33)
        # circuit.model('MYDIODE', 'D', is_=1e-6 , n=1.05, rs=0.005)
        circuit.model('MYDIODE', 'D', is_=1e6)

        # Add inductor with series resistance
        circuit.L('1', 'sw', 'out', self.l_value)
        circuit.R('L1', 'out', 'out_c', self.l_resistance)
        # circuit.C('L1', 'sw', 'out', self.l_parasitic_c) # Almost no effect, but adds some weird current spikes
        
        # Add output capacitor
        circuit.C('1', 'out_c', 'gnd', self.c_value)
        
        # Add load resistor
        circuit.R('load', 'out_c', 'gnd', self.r_load)
        
        self.circuit = circuit
        return circuit
    
    def run_simulation(self, step=1e-7):
        """Runs the simulation for the specified duration"""
        if self.circuit is None:
            self.build_circuit()
            
        simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        # duration=self.period * 10000
        # Run transient analysis
        analysis = simulator.transient(step_time=step, 
                                    #  end_time=duration / 2 + self.period,
                                    end_time=self.period * 2000,
                                    #  start_time=duration / 2,
                                    start_time=0,
                                     use_initial_condition=False)
        
        return analysis
    
    def plot_results(self, analysis):
        """Plot simulation results"""
        time_ms = np.array([float(t) for t in analysis.time]) * 1000
        
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
        
        # Plot output voltage
        vout = [float(v) for v in analysis['out_c']]
        ax1.plot(time_ms, vout)
        ax1.set_ylabel('Output Voltage (V)')
        ax1.set_title('Buck Converter Waveforms')
        ax1.grid(True)

        vout_mean = np.mean(vout)
        print(f"Output voltage mean: {vout_mean}")

        
        # Plot switch node voltage
        vsw = [float(v) for v in analysis['g']]
        ax2.plot(time_ms, vsw)
        ax2.set_ylabel('Switch Gate (V)')
        ax2.grid(True)
        
        # Plot inductor current
        v_l_sense = np.array([float(v) for v in analysis['out']]) - np.array([float(v) for v in analysis['out_c']])
        i_l = v_l_sense / self.l_resistance
        i_l_mean = np.mean(i_l)
        print(f"Inductor current mean: {i_l_mean}")
        ax3.plot(time_ms, i_l)
        ax3.set_xlabel('Time (ms)')
        ax3.set_ylabel('Inductor Current (A)')
        ax3.grid(True)
        
        v_sw = np.array([float(v) for v in analysis['sw']])
        ax4.plot(time_ms, v_sw)
        ax4.set_xlabel('Time (ms)')
        ax4.set_ylabel('Switch Node (V)')
        ax4.grid(True)


        plt.tight_layout()
        plt.show()

# Test the converter
if __name__ == "__main__":
    # Create a buck converter with default values
    before = time.time()
    buck = BuckConverter()

    
    # Build and simulate the circuit
    analysis = buck.run_simulation()
    after = time.time()
    print(f"Time taken to create the buck converter: {after - before} seconds")
    # Plot results
    buck.plot_results(analysis)