#!/usr/bin/env python3
"""
Run Genetic Algorithm Optimization for Buck Converter Parameters

This script loads measured data, runs the genetic algorithm to find optimal
parameters, and saves the results.

Usage:
    python -m defect-detector.run_optimization
"""

import json
import time
import sys
from pathlib import Path
from .main import CircuitParams
from .genetic_optimizer import GeneticOptimizer


def load_payload(filename: str) -> dict:
    """
    Load measurement data from JSON file.
    
    Args:
        filename: Path to payload JSON file
        
    Returns:
        Dictionary with measurement data
    """
    with open(filename, 'r') as f:
        return json.load(f)


def main():
    """Main optimization routine."""
    print("=" * 80)
    print("Buck Converter Parameter Optimization using Genetic Algorithm")
    print("=" * 80)
    print()
    
    # Load payload data
    payload_path = Path(__file__).parent / 'payload-for-genetic-algorithm.json'
    print(f"Loading payload from: {payload_path}")
    
    try:
        payload = load_payload(payload_path)
    except FileNotFoundError:
        print(f"Error: Payload file not found at {payload_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in payload file: {e}")
        sys.exit(1)
    
    # Extract data
    measured_data = {
        'voltage': payload['measurements']['voltage'],
        'current': payload['measurements']['current'],
        'time': payload['measurements']['time']
    }
    
    # Create circuit parameters
    circuit_params = CircuitParams(
        vin=payload['circuit_params']['vin'],
        c_value=payload['circuit_params']['c_value'],
        pwm_percentage=payload['circuit_params']['pwm_percentage'],
        r_load=payload['circuit_params']['r_load']
    )
    
    print(f"Circuit parameters:")
    print(f"  Vin: {circuit_params.vin} V")
    print(f"  Capacitance: {circuit_params.c_value} µF")
    print(f"  PWM duty cycle: {circuit_params.pwm_percentage}%")
    print(f"  Load resistance: {circuit_params.r_load} Ω")
    print()
    print(f"Measurement data points: {len(measured_data['time'])}")
    print()
    
    # Initialize genetic optimizer
    print("Initializing Genetic Algorithm Optimizer...")
    print(f"  Population size: 50")
    print(f"  Max generations: 100")
    print(f"  Convergence threshold: 20 generations without improvement")
    print(f"  Fitness weights:")
    print(f"    - Ripple Vout: 35%")
    print(f"    - Ripple IL: 30%")
    print(f"    - Avg Vout: 20%")
    print(f"    - Avg IL: 15%")
    print()
    
    optimizer = GeneticOptimizer(
        circuit_params=circuit_params,
        measured_data=measured_data,
        population_size=50,
        max_generations=100,
        convergence_threshold=20,
        elite_size=5,
        tournament_size=3,
        crossover_prob=0.9,
        crossover_eta=15.0,
        mutation_eta=20.0
    )
    
    # Get initial fitness for comparison
    print("Calculating initial fitness with default parameters...")
    from .genetic_optimizer import Genome

    default_parameters = {
        'gate_rise_time': 1e-9,
        'gate_fall_time': 1e-9,
        'switch_ron': 1e-9,
        'diode_rs': 1e-4,
        'diode_is': 1e6,
        'cap_esr': 0.05,
        'cap_inductance': 1e-9
    }

    print("\nDefault parameters:")
    for key, value in default_parameters.items():
        print(f"  {key}: {value}")

    default_genome = Genome.encode(default_parameters)

    initial_fitness = optimizer.evaluate_individual(default_genome)
    print(f"Initial fitness (default parameters): {initial_fitness:.4f}")
    print()
    
    # Run optimization
    print("-" * 80)
    start_time = time.time()
    
    try:
        optimizer.evolve()
    except KeyboardInterrupt:
        print("\n\nOptimization interrupted by user!")
        print("Saving partial results...")
    except Exception as e:
        print(f"\n\nError during optimization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    print("-" * 80)
    print()
    
    # Save results
    output_path = Path(__file__).parent / 'optimized_parameters.json'
    optimizer.save_results(str(output_path))
    
    # Print summary
    print()
    print("=" * 80)
    print("OPTIMIZATION SUMMARY")
    print("=" * 80)
    print()
    print(f"Execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    print(f"Generations completed: {optimizer.generation + 1}")
    print()
    print(f"Initial fitness (default params): {initial_fitness:.4f}")
    print(f"Final fitness (optimized params): {optimizer.best_fitness:.4f}")
    
    if optimizer.best_fitness < initial_fitness:
        improvement = ((initial_fitness - optimizer.best_fitness) / initial_fitness) * 100
        print(f"Improvement: {improvement:.2f}% better")
    else:
        print(f"Note: Optimization did not improve over defaults")
    
    print()
    print("Best parameters found:")
    print("-" * 40)
    best_params = optimizer.best_genome.decode()
    
    # Format parameters nicely
    param_display = {
        'gate_rise_time': ('Gate rise time', 'ns', 1e9),
        'gate_fall_time': ('Gate fall time', 'ns', 1e9),
        'switch_ron': ('Switch Ron', 'Ω', 1),
        'diode_rs': ('Diode Rs', 'Ω', 1),
        'diode_is': ('Diode Is', 'A', 1),
        'cap_esr': ('Capacitor ESR', 'Ω', 1),
        'cap_inductance': ('Cap inductance', 'H', 1)
    }
    
    for param_name, value in best_params.items():
        if param_name in param_display:
            display_name, unit, scale = param_display[param_name]
            display_value = value * scale
            print(f"  {display_name:20s}: {display_value:12.6e} {unit}")
    
    print()
    print("=" * 80)
    print()
    print(f"Results saved to: {output_path}")
    print()
    print("To use these parameters in simulation, load them from the JSON file")
    print("and pass as 'optimization_params' to BuckConverter constructor.")
    print()


if __name__ == '__main__':
    main()