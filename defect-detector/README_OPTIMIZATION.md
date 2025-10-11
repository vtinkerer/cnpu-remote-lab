# Buck Converter Parameter Optimization

This directory contains a genetic algorithm implementation for optimizing Buck Converter parameters to minimize the difference between simulated and measured data.

## Files

### Core Implementation

- **`simulation.py`** - Modified to support optional optimization parameters
- **`genetic_optimizer.py`** - Complete genetic algorithm implementation with Genome and GeneticOptimizer classes
- **`run_optimization.py`** - Executable script to run the optimization
- **`__init__.py`** - Package initialization file

### Data

- **`payload-for-genetic-algorithm.json`** - Measured data for optimization
- **`genetic_algorithm_architecture.md`** - Architecture documentation

### Utilities

- **`utils.py`** - Signal processing utilities (fix_signal_spike, etc.)
- **`main.py`** - FastAPI server (not modified)

## Parameters Being Optimized

The genetic algorithm optimizes 7 Buck Converter parameters:

1. **gate_rise_time** (0.1ns - 100ns, log scale) - Gate signal rise time
2. **gate_fall_time** (0.1ns - 100ns, log scale) - Gate signal fall time
3. **switch_ron** (1e-12 - 1e-3 Ω, log scale) - Switch on-resistance
4. **diode_rs** (1e-6 - 0.1 Ω, log scale) - Diode series resistance
5. **diode_is** (1e-15 - 1e10 A, log scale) - Diode saturation current
6. **cap_esr** (0.001 - 0.5 Ω, linear scale) - Capacitor ESR
7. **cap_inductance** (1e-12 - 1e-7 H, log scale) - Capacitor parasitic inductance

**Note:** `l_resistance` is fixed at 19.5 mΩ (from datasheet) and not optimized.

## Fitness Function

The fitness function is a weighted sum of 4 metrics:

- **Ripple Vout** (35%) - Voltage ripple percentage difference
- **Ripple IL** (30%) - Current ripple percentage difference
- **Avg Vout** (20%) - Average voltage percentage difference
- **Avg IL** (15%) - Average current percentage difference

Lower fitness is better.

## Genetic Algorithm Settings

- **Population size:** 50 individuals
- **Max generations:** 100
- **Convergence:** Stop if no improvement for 20 generations
- **Selection:** Tournament selection (size 3)
- **Crossover:** SBX (Simulated Binary Crossover) with η=15, probability 0.9
- **Mutation:** Polynomial mutation with η=20, adaptive rate
- **Elitism:** Preserve top 5 individuals each generation

## How to Run

### Prerequisites

Ensure you have all required dependencies installed:

```bash
pip install numpy PySpice scipy matplotlib pydantic fastapi
```

### Running the Optimization

From the project root directory:

```bash
python3 -m defect-detector.run_optimization
```

This will:

1. Load measurement data from `payload-for-genetic-algorithm.json`
2. Initialize the genetic algorithm
3. Run optimization for up to 100 generations
4. Save results to `defect-detector/optimized_parameters.json`
5. Print a summary with best parameters and improvement

### Expected Runtime

Depending on your system:

- Each individual evaluation: ~1-5 seconds
- Full optimization (50 individuals × ~30 generations): ~30-60 minutes

The optimization may converge earlier if improvement plateaus.

## Output

The optimization saves results to `optimized_parameters.json`:

```json
{
  "best_fitness": 12.34,
  "best_parameters": {
    "gate_rise_time": 1.5e-9,
    "gate_fall_time": 1.2e-9,
    "switch_ron": 5.6e-10,
    "diode_rs": 2.3e-4,
    "diode_is": 1.8e6,
    "cap_esr": 0.045,
    "cap_inductance": 8.7e-10
  },
  "generations": 35,
  "history": {
    "best_fitness": [...],
    "mean_fitness": [...],
    "worst_fitness": [...]
  }
}
```

## Using Optimized Parameters

To use the optimized parameters in simulation:

```python
import json
from defect_detector.simulation import BuckConverter
from defect_detector.main import CircuitParams

# Load optimized parameters
with open('defect-detector/optimized_parameters.json', 'r') as f:
    results = json.load(f)

optimized_params = results['best_parameters']

# Create circuit parameters
circuit_params = CircuitParams(
    vin=12.0,
    c_value=220.0,
    pwm_percentage=50.0,
    r_load=10.0
)

# Create converter with optimized parameters
buck = BuckConverter(circuit_params, optimization_params=optimized_params)

# Run simulation
result = buck.run_simulation(measurement_time_points)
```

## Code Structure

### Genome Class

Encodes/decodes parameters between normalized [0,1] range and actual values:

```python
from defect_detector.genetic_optimizer import Genome

# Create from actual parameters
genome = Genome.encode({
    'gate_rise_time': 1e-9,
    # ... other params
})

# Decode to actual values
params = genome.decode()
```

### GeneticOptimizer Class

Main optimization engine:

```python
from defect_detector.genetic_optimizer import GeneticOptimizer

optimizer = GeneticOptimizer(
    circuit_params=circuit_params,
    measured_data=measured_data,
    population_size=50,
    max_generations=100
)

optimizer.evolve()
optimizer.save_results('output.json')
```

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the project root:

```bash
cd /path/to/cnpu-remote-lab-nx
python3 -m defect-detector.run_optimization
```

### Simulation Failures

If many individuals fail simulation:

- Check that measured data is valid
- Verify circuit parameters are reasonable
- Look for error messages in console output

### Slow Convergence

If optimization is very slow:

- Reduce population size (e.g., to 30)
- Reduce max_generations (e.g., to 50)
- Increase convergence_threshold (e.g., to 10)

Edit these values in `run_optimization.py`:

```python
optimizer = GeneticOptimizer(
    circuit_params=circuit_params,
    measured_data=measured_data,
    population_size=30,  # Reduced
    max_generations=50,  # Reduced
    convergence_threshold=10  # More aggressive
)
```

## Monitoring Progress

The optimizer prints status every 5 generations:

```
Generation 5/100
  Best fitness: 15.2345
  Mean fitness: 28.4567
  Worst fitness: 45.6789
  Generations without improvement: 0
```

Watch for:

- **Best fitness decreasing** - optimization is working
- **Generations without improvement** - approaching convergence
- **Mean/worst fitness** - population diversity

## Next Steps

After optimization:

1. **Analyze results** - Check if fitness improved significantly
2. **Validate parameters** - Run
