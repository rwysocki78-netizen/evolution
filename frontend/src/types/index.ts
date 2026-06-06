// Mirrors Pydantic schemas from the backend — keep in sync manually.

export interface ReproductionWeight {
  children: number
  weight: number
}

export interface SimParamsRequest {
  board_size: number
  initial_energy: number
  max_energy: number
  energy_decay_per_tick: number
  fight_energy_cost: number
  reproduction_energy_cost: number
  reproduction_min_energy: number
  maturity_age: number
  juvenile_max_energy_factor: number
  fruit_energy_value: number
  poison_energy_value: number
  resistance_reduction_per_point: number
  max_fruits_on_board: number
  max_poisons_on_board: number
  mutation_rate: number
  mutation_magnitude: number
  initial_lifespan: [number, number]
  initial_vision_range: [number, number]
  initial_metabolism: [number, number]
  initial_aggression: [number, number]
  initial_hunger_threshold: [number, number]
  initial_safe_threshold: [number, number]
  initial_resistance: [number, number]
  reproduction_weights: ReproductionWeight[]
  initial_population: number
  total_turns: number
  behavior_strategy: string
  snapshot_enabled: boolean
  snapshot_interval: number
  seed: number | null
}

export interface SimulationResponse {
  id: number
  status: string
  seed: number
  started_at: string
  finished_at: string | null
  total_turns_configured: number
  total_turns_run: number
  behavior_strategy: string
  board_size: number
  initial_population: number
  snapshot_enabled: boolean
  snapshot_interval: number
}

export interface PositionOut {
  x: number
  y: number
}

export interface CreatureOut {
  id: number
  x: number
  y: number
  sex: string
  energy: number
  age: number
}

export interface BoardStateResponse {
  simulation_id: number
  tick: number
  board_size: number
  status: string
  creatures: CreatureOut[]
  fruits: PositionOut[]
  poisons: PositionOut[]
}

export interface TickResponse {
  state: BoardStateResponse
  completed: boolean
  turns_run: number
}

export interface TickSnapshotResponse {
  tick: number
  population_total: number
  population_male: number
  population_female: number
  avg_energy: number
  min_energy: number
  max_energy: number
  births: number
  deaths_total: number
  deaths_starvation: number
  deaths_age: number
  deaths_fight: number
  fights_total: number
  reproductions_successful: number
  reproductions_failed_space: number
  reproductions_failed_energy: number
  fruits_on_board: number
  poisons_on_board: number
  avg_lifespan: number
  avg_vision_range: number
  avg_metabolism: number
  avg_aggression: number
  avg_hunger_threshold: number
  avg_safe_threshold: number
  avg_resistance: number
}
