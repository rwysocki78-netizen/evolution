import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import ParamForm from '../components/ParamForm'
import { api } from '../api/client'
import type { SimParamsRequest } from '../types'

const DEFAULTS: SimParamsRequest = {
  board_size: 20,
  initial_energy: 50,
  max_energy: 100,
  energy_decay_per_tick: 1,
  fight_energy_cost: 10,
  reproduction_energy_cost: 20,
  reproduction_min_energy: 40,
  maturity_age: 5,
  juvenile_max_energy_factor: 0.5,
  fruit_energy_value: 20,
  poison_energy_value: 30,
  resistance_reduction_per_point: 0.1,
  max_fruits_on_board: 20,
  max_poisons_on_board: 10,
  mutation_rate: 0.05,
  mutation_magnitude: 1,
  initial_lifespan: [80, 120],
  initial_vision_range: [1, 3],
  initial_metabolism: [0.8, 1.2],
  initial_aggression: [0.3, 0.7],
  initial_hunger_threshold: [20, 40],
  initial_safe_threshold: [60, 80],
  initial_resistance: [0, 2],
  reproduction_weights: [
    { children: 1, weight: 0.50 },
    { children: 2, weight: 0.30 },
    { children: 3, weight: 0.15 },
    { children: 4, weight: 0.05 },
  ],
  initial_population: 50,
  total_turns: 1000,
  behavior_strategy: 'threshold',
  snapshot_enabled: true,
  snapshot_interval: 10,
  seed: null,
}

function validate(p: SimParamsRequest): string[] {
  const errors: string[] = []
  if (p.board_size < 5) errors.push('Board size must be at least 5.')
  if (p.initial_population < 2) errors.push('Initial population must be at least 2.')
  if (p.initial_population > Math.floor(p.board_size * p.board_size / 2)) {
    errors.push('Initial population is too large for the board (max board_size² / 2).')
  }
  if (p.max_energy <= p.initial_energy) {
    errors.push('Max energy must be greater than initial energy.')
  }
  if (p.reproduction_min_energy >= p.max_energy) {
    errors.push('Reproduction min energy must be less than max energy.')
  }
  if (p.mutation_rate < 0 || p.mutation_rate > 1) {
    errors.push('Mutation rate must be between 0 and 1.')
  }
  const rangePairs: [keyof SimParamsRequest, string][] = [
    ['initial_lifespan', 'Lifespan'],
    ['initial_vision_range', 'Vision range'],
    ['initial_metabolism', 'Metabolism'],
    ['initial_aggression', 'Aggression'],
    ['initial_hunger_threshold', 'Hunger threshold'],
    ['initial_safe_threshold', 'Safe threshold'],
    ['initial_resistance', 'Resistance'],
  ]
  for (const [key, label] of rangePairs) {
    const [lo, hi] = p[key] as [number, number]
    if (lo > hi) errors.push(`${label}: min must be ≤ max.`)
  }
  if (p.total_turns < 1) errors.push('Total turns must be at least 1.')
  if (p.reproduction_weights.some(w => w.weight <= 0)) {
    errors.push('Each reproduction weight must be greater than 0.')
  }
  return errors
}

export default function Setup() {
  const navigate = useNavigate()
  const [params, setParams] = useState<SimParamsRequest>(DEFAULTS)
  const [errors, setErrors] = useState<string[]>([])
  const [apiError, setApiError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const errs = validate(params)
    setErrors(errs)
    if (errs.length > 0) return

    setSubmitting(true)
    setApiError(null)
    try {
      const sim = await api.simulations.create(params)
      navigate(`/simulation/${sim.id}`)
    } catch (err) {
      setApiError(err instanceof Error ? err.message : 'Failed to create simulation.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="screen">
      <h1>Evolution — Setup</h1>
      <form onSubmit={handleSubmit}>
        <ParamForm params={params} onChange={setParams} />
        {errors.length > 0 && (
          <div className="error-box">
            {errors.map(e => <p key={e}>{e}</p>)}
          </div>
        )}
        {apiError && (
          <div className="error-box"><p>{apiError}</p></div>
        )}
        <button type="submit" className="btn-primary" disabled={submitting}>
          {submitting ? 'Creating…' : 'Start Simulation'}
        </button>
      </form>
    </div>
  )
}
