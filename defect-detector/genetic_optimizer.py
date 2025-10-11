"""
Genetic Algorithm for Buck Converter Parameter Optimization

This module implements a genetic algorithm to optimize 7 Buck Converter parameters
to minimize the difference between simulated and measured data.

Parameter encoding (genes 0-6):
- Gene 0: gate_rise_time (0.1ns - 100ns, log scale)
- Gene 1: gate_fall_time (0.1ns - 100ns, log scale)
- Gene 2: switch_ron (1e-12 - 1e-3 Ω, log scale)
- Gene 3: diode_rs (1e-6 - 0.1 Ω, log scale)
- Gene 4: diode_is (1e-15 - 1e10 A, log scale)
- Gene 5: cap_esr (0.001 - 0.5 Ω, linear scale)
- Gene 6: cap_inductance (1e-12 - 1e-7 H, log scale)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import json
import time
from .simulation import BuckConverter


class Genome:
    """
    Represents a genome encoding 7 Buck Converter parameters.
    Genes are normalized to [0, 1] range for GA operations.
    """
    
    # Parameter bounds and scaling info
    PARAM_INFO = {
        0: {  # gate_rise_time
            'name': 'gate_rise_time',
            'min': 0.1e-9,  # 0.1ns
            'max': 100e-9,  # 100ns
            'scale': 'log',
            'unit': 's'
        },
        1: {  # gate_fall_time
            'name': 'gate_fall_time',
            'min': 0.1e-9,
            'max': 100e-9,
            'scale': 'log',
            'unit': 's'
        },
        2: {  # switch_ron
            'name': 'switch_ron',
            'min': 1e-12,
            'max': 1e-3,
            'scale': 'log',
            'unit': 'Ω'
        },
        3: {  # diode_rs
            'name': 'diode_rs',
            'min': 1e-6,
            'max': 0.1,
            'scale': 'log',
            'unit': 'Ω'
        },
        4: {  # diode_is
            'name': 'diode_is',
            'min': 1e-15,
            'max': 1e10,
            'scale': 'log',
            'unit': 'A'
        },
        5: {  # cap_esr
            'name': 'cap_esr',
            'min': 0.001,
            'max': 0.5,
            'scale': 'linear',
            'unit': 'Ω'
        },
        6: {  # cap_inductance
            'name': 'cap_inductance',
            'min': 1e-12,
            'max': 1e-7,
            'scale': 'log',
            'unit': 'H'
        }
    }
    
    def __init__(self, genes: Optional[List[float]] = None):
        """
        Initialize genome with normalized gene values [0, 1].
        
        Args:
            genes: List of 7 normalized gene values. If None, random initialization.
        """
        if genes is None:
            # Random initialization
            self.genes = np.random.random(7)
        else:
            self.genes = np.array(genes, dtype=np.float64)
            # Clip to valid range
            self.genes = np.clip(self.genes, 0.0, 1.0)
    
    def decode(self) -> Dict[str, float]:
        """
        Decode normalized genes to actual parameter values.
        
        Returns:
            Dictionary mapping parameter names to actual values
        """
        params = {}
        for i in range(7):
            info = self.PARAM_INFO[i]
            gene = self.genes[i]
            
            if info['scale'] == 'log':
                # Logarithmic scale
                log_min = np.log10(info['min'])
                log_max = np.log10(info['max'])
                log_value = log_min + gene * (log_max - log_min)
                value = 10 ** log_value
            else:
                # Linear scale
                value = info['min'] + gene * (info['max'] - info['min'])
            
            params[info['name']] = value
        
        return params
    
    @classmethod
    def encode(cls, params: Dict[str, float]) -> 'Genome':
        """
        Create a genome from actual parameter values.
        
        Args:
            params: Dictionary mapping parameter names to values
            
        Returns:
            New Genome instance
        """
        genes = []
        for i in range(7):
            info = cls.PARAM_INFO[i]
            value = params[info['name']]
            
            # Clip to valid range
            value = np.clip(value, info['min'], info['max'])
            
            if info['scale'] == 'log':
                log_min = np.log10(info['min'])
                log_max = np.log10(info['max'])
                log_value = np.log10(value)
                gene = (log_value - log_min) / (log_max - log_min)
            else:
                gene = (value - info['min']) / (info['max'] - info['min'])
            
            genes.append(gene)
        
        return cls(genes)
    
    def copy(self) -> 'Genome':
        """Create a deep copy of this genome."""
        return Genome(self.genes.copy())
    
    def __repr__(self) -> str:
        params = self.decode()
        return f"Genome({', '.join(f'{k}={v:.3e}' for k, v in params.items())})"


class GeneticOptimizer:
    """
    Genetic Algorithm optimizer for Buck Converter parameters.
    """
    
    # Fitness weights for the 4 metrics
    WEIGHTS = {
        'ripple_vout': 0.35,
        'ripple_il': 0.30,
        'avg_vout': 0.20,
        'avg_il': 0.15
    }
    
    def __init__(
        self,
        circuit_params,
        measured_data: Dict,
        population_size: int = 50,
        max_generations: int = 100,
        convergence_threshold: int = 20,
        elite_size: int = 5,
        tournament_size: int = 3,
        crossover_prob: float = 0.9,
        crossover_eta: float = 15.0,
        mutation_eta: float = 20.0
    ):
        """
        Initialize genetic algorithm optimizer.
        
        Args:
            circuit_params: CircuitParams object with circuit configuration
            measured_data: Dict with 'voltage', 'current', 'time' arrays
            population_size: Number of individuals in population
            max_generations: Maximum number of generations
            convergence_threshold: Stop if no improvement for this many generations
            elite_size: Number of best individuals to preserve
            tournament_size: Tournament selection size
            crossover_prob: Probability of crossover
            crossover_eta: SBX distribution index
            mutation_eta: Polynomial mutation distribution index
        """
        self.circuit_params = circuit_params
        self.measured_data = measured_data
        self.population_size = population_size
        self.max_generations = max_generations
        self.convergence_threshold = convergence_threshold
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        self.crossover_prob = crossover_prob
        self.crossover_eta = crossover_eta
        self.mutation_eta = mutation_eta
        
        self.measurement_time = self.measured_data['time']

        # Preprocess measured data
        # self._preprocess_measured_data()
        
        # Evolution tracking
        self.population = []
        self.fitness_scores = []
        self.best_genome = None
        self.best_fitness = float('inf')
        self.generation = 0
        self.history = {
            'best_fitness': [],
            'mean_fitness': [],
            'worst_fitness': []
        }
    
    def initialize_population(self):
        """
        Initialize population with random individuals and some seeded ones.
        """
        self.population = []
        
        # Add some seeded individuals with default parameters
        default_params = {
            'gate_rise_time': 1e-9,
            'gate_fall_time': 1e-9,
            'switch_ron': 1e-9,
            'diode_rs': 1e-4,
            'diode_is': 1e6,
            'cap_esr': 0.05,
            'cap_inductance': 1e-9
        }
        self.population.append(Genome.encode(default_params))
        
        # Add variations of default
        for _ in range(4):
            varied_params = default_params.copy()
            for key in varied_params:
                # Add random variation (±50%)
                variation = np.random.uniform(0.5, 1.5)
                varied_params[key] *= variation
            self.population.append(Genome.encode(varied_params))
        
        # Fill rest with random individuals
        while len(self.population) < self.population_size:
            self.population.append(Genome())
    
    def evaluate_individual(self, genome: Genome) -> float:
        """
        Evaluate fitness of a single genome.
        
        Args:
            genome: Genome to evaluate
            
        Returns:
            Fitness value (lower is better)
        """
        try:
            # Decode parameters
            params = genome.decode()
            
            # Create buck converter with these parameters
            buck = BuckConverter(self.circuit_params, optimization_params=params)
            
            # Run simulation
            sim_result = buck.run_simulation(self.measurement_time)
            
            # Get simulated data
            sim_voltage = sim_result['sim_voltage_full']
            sim_current = sim_result['sim_current_full']

            # Calculate metrics for simulated data
            sim_vout_avg = np.mean(sim_voltage)
            sim_vout_ripple = np.max(sim_voltage) - np.min(sim_voltage)
            sim_il_avg = np.mean(sim_current)
            sim_il_ripple = np.max(sim_current) - np.min(sim_current)
            
            # Calculate metrics for measured data
            meas_vout_avg = np.mean(self.measured_data['voltage'])
            meas_vout_ripple = np.max(self.measured_data['voltage']) - np.min(self.measured_data['voltage'])
            meas_il_avg = np.mean(self.measured_data['current'])
            meas_il_ripple = np.max(self.measured_data['current']) - np.min(self.measured_data['current'])

            # Calculate percentage differences (absolute values)
            diff_ripple_vout = abs((meas_vout_ripple - sim_vout_ripple) / (sim_vout_ripple + 1e-10)) * 100
            diff_ripple_il = abs((meas_il_ripple - sim_il_ripple) / (sim_il_ripple + 1e-10)) * 100
            diff_avg_vout = abs((meas_vout_avg - sim_vout_avg) / (sim_vout_avg + 1e-10)) * 100
            diff_avg_il = abs((meas_il_avg - sim_il_avg) / (sim_il_avg + 1e-10)) * 100
            
            # Calculate weighted fitness
            fitness = (
                self.WEIGHTS['ripple_vout'] * diff_ripple_vout +
                self.WEIGHTS['ripple_il'] * diff_ripple_il +
                self.WEIGHTS['avg_vout'] * diff_avg_vout +
                self.WEIGHTS['avg_il'] * diff_avg_il
            )
            
            return fitness
            
        except Exception as e:
            # Return high penalty for simulation failures
            print(f"Simulation failed: {e}")
            return 1000.0
    
    def tournament_selection(self, population: List[Genome], fitness_scores: List[float]) -> Genome:
        """
        Select parent using tournament selection.
        
        Args:
            population: List of genomes
            fitness_scores: Corresponding fitness scores
            
        Returns:
            Selected genome
        """
        # Randomly select tournament_size individuals
        indices = np.random.choice(len(population), self.tournament_size, replace=False)
        
        # Find best (lowest fitness) in tournament
        best_idx = indices[0]
        best_fitness = fitness_scores[best_idx]
        
        for idx in indices[1:]:
            if fitness_scores[idx] < best_fitness:
                best_fitness = fitness_scores[idx]
                best_idx = idx
        
        return population[best_idx].copy()
    
    def sbx_crossover(self, parent1: Genome, parent2: Genome) -> Tuple[Genome, Genome]:
        """
        Simulated Binary Crossover (SBX).
        
        Args:
            parent1: First parent genome
            parent2: Second parent genome
            
        Returns:
            Tuple of two offspring genomes
        """
        child1_genes = parent1.genes.copy()
        child2_genes = parent2.genes.copy()
        
        for i in range(len(child1_genes)):
            if np.random.random() < 0.5:
                if abs(parent1.genes[i] - parent2.genes[i]) > 1e-6:
                    # Calculate beta
                    u = np.random.random()
                    if u <= 0.5:
                        beta = (2 * u) ** (1 / (self.crossover_eta + 1))
                    else:
                        beta = (1 / (2 * (1 - u))) ** (1 / (self.crossover_eta + 1))
                    
                    # Create offspring
                    child1_genes[i] = 0.5 * ((1 + beta) * parent1.genes[i] + (1 - beta) * parent2.genes[i])
                    child2_genes[i] = 0.5 * ((1 - beta) * parent1.genes[i] + (1 + beta) * parent2.genes[i])
                    
                    # Ensure bounds
                    child1_genes[i] = np.clip(child1_genes[i], 0.0, 1.0)
                    child2_genes[i] = np.clip(child2_genes[i], 0.0, 1.0)
        
        return Genome(child1_genes), Genome(child2_genes)
    
    def polynomial_mutation(self, genome: Genome) -> Genome:
        """
        Polynomial mutation with adaptive mutation rate.
        
        Args:
            genome: Genome to mutate
            
        Returns:
            Mutated genome
        """
        mutated_genes = genome.genes.copy()
        
        # Adaptive mutation rate: higher early, lower later
        mutation_rate = 1.0 / len(mutated_genes)
        if self.generation > 0:
            mutation_rate *= (1.0 - self.generation / self.max_generations)
            mutation_rate = max(mutation_rate, 0.01)  # Minimum 1%
        
        for i in range(len(mutated_genes)):
            if np.random.random() < mutation_rate:
                gene = mutated_genes[i]
                u = np.random.random()
                
                if u < 0.5:
                    delta = (2 * u) ** (1 / (self.mutation_eta + 1)) - 1
                else:
                    delta = 1 - (2 * (1 - u)) ** (1 / (self.mutation_eta + 1))
                
                mutated_genes[i] = gene + delta
                mutated_genes[i] = np.clip(mutated_genes[i], 0.0, 1.0)
        
        return Genome(mutated_genes)
    
    def evolve(self):
        """
        Main evolution loop.
        """
        print("Initializing population...")
        self.initialize_population()
        
        # Evaluate initial population
        print("Evaluating initial population...")
        self.fitness_scores = [self.evaluate_individual(ind) for ind in self.population]
        
        # Track best
        best_idx = np.argmin(self.fitness_scores)
        self.best_fitness = self.fitness_scores[best_idx]
        self.best_genome = self.population[best_idx].copy()
        
        # Track convergence
        generations_without_improvement = 0
        
        print(f"\nInitial best fitness: {self.best_fitness:.4f}")
        print(f"Starting evolution for up to {self.max_generations} generations...\n")
        
        for gen in range(self.max_generations):
            self.generation = gen
            
            # Create new population
            new_population = []
            
            # Elitism: preserve best individuals
            elite_indices = np.argsort(self.fitness_scores)[:self.elite_size]
            for idx in elite_indices:
                new_population.append(self.population[idx].copy())
            
            # Generate offspring
            while len(new_population) < self.population_size:
                # Selection
                parent1 = self.tournament_selection(self.population, self.fitness_scores)
                parent2 = self.tournament_selection(self.population, self.fitness_scores)
                
                # Crossover
                if np.random.random() < self.crossover_prob:
                    child1, child2 = self.sbx_crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                # Mutation
                child1 = self.polynomial_mutation(child1)
                child2 = self.polynomial_mutation(child2)

                new_population.append(child1)
                if len(new_population) < self.population_size:
                    new_population.append(child2)
            
            # Trim to exact population size
            new_population = new_population[:self.population_size]
            
            # Evaluate new population
            self.population = new_population
            self.fitness_scores = [self.evaluate_individual(ind) for ind in self.population]
            
            # Update best
            current_best_idx = np.argmin(self.fitness_scores)
            current_best_fitness = self.fitness_scores[current_best_idx]
            
            if current_best_fitness < self.best_fitness:
                self.best_fitness = current_best_fitness
                self.best_genome = self.population[current_best_idx].copy()
                generations_without_improvement = 0
            else:
                generations_without_improvement += 1
            
            # Record history
            self.history['best_fitness'].append(current_best_fitness)
            self.history['mean_fitness'].append(np.mean(self.fitness_scores))
            self.history['worst_fitness'].append(np.max(self.fitness_scores))
            
            # Logging every 5 generations
            if (gen + 1) % 5 == 0:
                print(f"Generation {gen + 1}/{self.max_generations}")
                print(f"  Best fitness: {current_best_fitness:.4f}")
                print(f"  Mean fitness: {np.mean(self.fitness_scores):.4f}")
                print(f"  Worst fitness: {np.max(self.fitness_scores):.4f}")
                print(f"  Generations without improvement: {generations_without_improvement}")
                print()
            
            # Check convergence
            if generations_without_improvement >= self.convergence_threshold:
                print(f"Converged after {gen + 1} generations (no improvement for {self.convergence_threshold} generations)")
                break
        
        print(f"\nOptimization complete!")
        print(f"Final best fitness: {self.best_fitness:.4f}")
        print(f"Best parameters:")
        best_params = self.best_genome.decode()
        for name, value in best_params.items():
            print(f"  {name}: {value:.6e}")
    
    def save_results(self, filename: str):
        """
        Save optimization results to JSON file.
        
        Args:
            filename: Path to output JSON file
        """
        results = {
            'best_fitness': float(self.best_fitness),
            'best_parameters': {k: float(v) for k, v in self.best_genome.decode().items()},
            'generations': self.generation + 1,
            'history': {
                'best_fitness': [float(x) for x in self.history['best_fitness']],
                'mean_fitness': [float(x) for x in self.history['mean_fitness']],
                'worst_fitness': [float(x) for x in self.history['worst_fitness']]
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nResults saved to {filename}")