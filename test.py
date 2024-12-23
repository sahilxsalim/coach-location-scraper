import random
import numpy as np

class PermutationFlowshopGA:
    def __init__(self, processing_times, population_size=150, generations=500, crossover_rate=0.85, mutation_rate=0.08, elitism_size=2, local_search_probability=0.5):
        self.processing_times = np.array(processing_times)
        self.num_jobs = len(processing_times[0])
        self.num_machines = len(processing_times)
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.elitism_size = elitism_size
        self.local_search_probability = local_search_probability

    def initialize_population(self):
        population = []
        for _ in range(self.population_size):
            permutation = list(range(self.num_jobs))
            random.shuffle(permutation)
            population.append(permutation)
        return population

    def calculate_makespan(self, permutation):
        completion_times = np.zeros((self.num_machines, self.num_jobs))
        completion_times[0][0] = self.processing_times[0][permutation[0]]
        for j in range(1, self.num_jobs):
            completion_times[0][j] = completion_times[0][j-1] + self.processing_times[0][permutation[j]]

        for i in range(1, self.num_machines):
            completion_times[i][0] = completion_times[i-1][0] + self.processing_times[i][permutation[0]]
            for j in range(1, self.num_jobs):
                completion_times[i][j] = max(completion_times[i-1][j], completion_times[i][j-1]) + self.processing_times[i][permutation[j]]

        return completion_times[-1][-1]

    def evaluate_population(self, population):
        fitness_scores = []
        for individual in population:
            fitness_scores.append(self.calculate_makespan(individual))
        return fitness_scores

    def selection(self, population, fitness_scores):
        selected_parents = []
        for _ in range(self.population_size):
            tournament_individuals = random.sample(range(self.population_size), 3)
            tournament_fitnesses = [fitness_scores[i] for i in tournament_individuals]
            winner_index = tournament_individuals[tournament_fitnesses.index(min(tournament_fitnesses))]
            selected_parents.append(population[winner_index])
        return selected_parents

    def pmx_crossover(self, parent1, parent2):
        if random.random() > self.crossover_rate:
            return parent1, parent2

        size = len(parent1)
        p1, p2 = sorted(random.sample(range(size), 2))

        child1 = [-1] * size
        child2 = [-1] * size

        # Copy the mapping section
        for i in range(p1, p2 + 1):
            child1[i] = parent1[i]
            child2[i] = parent2[i]

        # Mapping dictionaries
        mapping1 = {parent2[i]: parent1[i] for i in range(p1, p2 + 1)}
        mapping2 = {parent1[i]: parent2[i] for i in range(p1, p2 + 1)}

        # Fill the remaining positions for child1
        for i in range(size):
            if child1[i] == -1:
                gene = parent2[i]
                while gene in mapping1:
                    gene = mapping1[gene]
                child1[i] = gene

        # Fill the remaining positions for child2
        for i in range(size):
            if child2[i] == -1:
                gene = parent1[i]
                while gene in mapping2:
                    gene = mapping2[gene]
                child2[i] = gene

        return child1, child2

    def mutate(self, individual):
        if random.random() < self.mutation_rate:
            idx1, idx2 = random.sample(range(len(individual)), 2)
            individual[idx1], individual[idx2] = individual[idx2], individual[idx1]
        return individual

    def local_search(self, individual):
        best_individual = list(individual)
        best_makespan = self.calculate_makespan(best_individual)

        for i in range(self.num_jobs):
            for j in range(i + 1, self.num_jobs):
                neighbor = list(individual)
                neighbor[i], neighbor[j] = neighbor[j], neighbor[i]
                neighbor_makespan = self.calculate_makespan(neighbor)
                if neighbor_makespan < best_makespan:
                    best_makespan = neighbor_makespan
                    best_individual = neighbor
        return best_individual

    def create_offspring(self, parents):
        offspring = []
        for i in range(0, len(parents), 2):
            parent1 = parents[i]
            parent2 = parents[i+1]
            child1, child2 = self.pmx_crossover(parent1, parent2)
            offspring.append(self.mutate(child1))
            offspring.append(self.mutate(child2))

        # Apply local search to some offspring
        for i in range(len(offspring)):
            if random.random() < self.local_search_probability:
                offspring[i] = self.local_search(offspring[i])

        return offspring

    def run(self):
        population = self.initialize_population()
        best_makespan = float('inf')
        best_solution = None

        for generation in range(self.generations):
            fitness_scores = self.evaluate_population(population)

            # Elitism
            sorted_population_indices = np.argsort(fitness_scores)
            elite_individuals = [population[i] for i in sorted_population_indices[:self.elitism_size]]

            best_in_generation_index = np.argmin(fitness_scores)
            current_best_makespan = fitness_scores[best_in_generation_index]
            current_best_solution = population[best_in_generation_index]

            if current_best_makespan < best_makespan:
                best_makespan = current_best_makespan
                best_solution = current_best_solution

            parents = self.selection(population, fitness_scores)
            offspring = self.create_offspring(parents)

            # Replace the worst individuals with the elite
            offspring.sort(key=lambda ind: self.calculate_makespan(ind), reverse=True)
            population = elite_individuals + offspring[self.elitism_size:]

            print(f"Generation {generation+1}/{self.generations}, Best Makespan: {best_makespan}")

        return best_makespan, best_solution

if __name__ == "__main__":
    processing_times_data = [
        [54, 83, 15, 71, 77, 36, 53, 38, 27, 87, 76, 91, 14, 29, 12, 77, 32, 87, 68, 94],
        [79,  3, 11, 99, 56, 70, 99, 60,  5, 56,  3, 61, 73, 75, 47, 14, 21, 86,  5, 77],
        [16, 89, 49, 15, 89, 45, 60, 23, 57, 64,  7,  1, 63, 41, 63, 47, 26, 75, 77, 40],
        [66, 58, 31, 68, 78, 91, 13, 59, 49, 85, 85,  9, 39, 41, 56, 40, 54, 77, 51, 31],
        [58, 56, 20, 85, 53, 35, 53, 41, 69, 13, 86, 72,  8, 49, 47, 87, 58, 18, 68, 28]
    ]

    ga = PermutationFlowshopGA(processing_times_data, population_size=150, generations=500, crossover_rate=0.85, mutation_rate=0.08, elitism_size=2, local_search_probability=0.6)
    best_makespan, best_permutation = ga.run()

    print("\n--- Results ---")
    print("Best Makespan:", best_makespan)
    print("Best Job Order (permutation):", best_permutation)