from PySpice.Spice.Netlist import Circuit
from PySpice.Unit import *
import matplotlib.pyplot as plt
import numpy as np

class BuckConverter:
    def __init__(self, 
                 vin=11,           # Input voltage (V)
                 vout=5.5,         # Expected output voltage (V) = 0.5 * 11V
                 freq=312500,      # Switching frequency (Hz)
                 l_value=10e-6,    # Inductor value (H)
                 c_value=113e-6,   # Capacitor value (F)
                 c_in_value=100.1e-6, # Input capacitor value (F)
                 r_load=8.6,       # Load resistance (Ω)
                 duty_cycle=None):  # 50% duty cycle
        
        self.vin = vin
        self.vout = vout
        self.freq = freq
        self.l_value = l_value
        self.c_value = c_value
        self.r_load = r_load
        
        self.l_resistance = 1e-9

        # Calculate duty cycle if not provided
        if duty_cycle is None:
            self.duty_cycle = vout / vin
        else:
            self.duty_cycle = duty_cycle
            
        self.period = 1 / freq
        self.circuit = None
        
    def build_circuit(self):
        """Creates the buck converter circuit"""
        circuit = Circuit('Buck Converter')

        # Create voltage source
        circuit.V('in', 'vin', 'gnd', self.vin)
        
        # Add gate drive voltage source for the switch
        circuit.V('gate', 'g', 'gnd', 'PULSE(0 10 0 1n 1n {0}us {1}us)'.format(
            self.duty_cycle * self.period * 1e6,
            self.period * 1e6
        ))
        
        # Add voltage-controlled switch
        circuit.S('1', 'vin', 'sw', 'g', 'gnd', model='SWITCH')
        circuit.model('SWITCH', 'SW', ron=1e-9, roff=1e12, vt=1, vh=0)
        
        # Add catch diode
        circuit.D('1', 'gnd', 'sw', model='DIODE')
        circuit.model('DIODE', 'D', Is=1e-14, Rs=1e-9, Vf=0)
        
        # Add inductor with series resistance
        circuit.L('1', 'sw', 'out', self.l_value)
        circuit.R('L1', 'out', 'out_c', self.l_resistance)  # Inductor series resistance
        
        # Add output capacitor with ESR
        circuit.C('1', 'out_c', 'gnd', self.c_value)
        
        # Add load resistor
        circuit.R('load', 'out_c', 'gnd', self.r_load)
        
        self.circuit = circuit
        return circuit
    
    def run_simulation(self, duration=5e-3, step=1e-7):
        """Runs the simulation for the specified duration"""
        if self.circuit is None:
            self.build_circuit()
            
        simulator = self.circuit.simulator(temperature=25, nominal_temperature=25)
        
        # Run transient analysis
        analysis = simulator.transient(step_time=step, 
                                     end_time=duration,
                                     start_time=0,
                                     use_initial_condition=False)
        
        return analysis
    
    def plot_results(self, analysis):
        """Plot simulation results"""
        # Convert time to milliseconds
        time_ms = np.array([float(t) for t in analysis.time]) * 1000
        
        # Create subplots
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 12))
        
        # Plot output voltage
        vout = [float(v) for v in analysis['out_c']]
        ax1.plot(time_ms, vout)
        ax1.set_ylabel('Output Voltage (V)')
        ax1.set_title('Buck Converter Waveforms')
        ax1.grid(True)
        
        # Plot switch node voltage
        vsw = [float(v) for v in analysis['g']]
        ax2.plot(time_ms, vsw)
        ax2.set_ylabel('Switch Node (V)')
        ax2.grid(True)
        
        # Plot inductor current (voltage across sense resistor / resistance)
        v_l_sense = np.array([float(v) for v in analysis['out']]) - np.array([float(v) for v in analysis['out_c']])
        i_l = v_l_sense / self.l_resistance  # Current = voltage / sense resistance
        ax3.plot(time_ms, i_l)
        ax3.set_xlabel('Time (ms)')
        ax3.set_ylabel('Inductor Current (A)')
        ax3.grid(True)
        
        plt.tight_layout()
        plt.show()

# Example usage
if __name__ == "__main__":
    # Create a buck converter with default values
    buck = BuckConverter()
    
    # Build and simulate the circuit
    analysis = buck.run_simulation()
    
    # Print circuit parameters
    print(f"Input voltage: {buck.vin}V")
    print(f"Target output voltage: {buck.vout}V")
    print(f"Duty cycle: {buck.duty_cycle:.2%}")
    print(f"Switching frequency: {buck.freq/1000:.1f}kHz")
    
    # Plot results
    buck.plot_results(analysis)