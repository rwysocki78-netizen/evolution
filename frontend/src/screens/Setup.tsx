import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import ParamForm from '../components/ParamForm'
import { api } from '../api/client'
import type { SimParamsRequest, SimulationResponse } from '../types'

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

function statusClass(s: string) {
  if (s === 'running') return 'running'
  if (s === 'completed') return 'completed'
  return 'stopped'
}

export default function Setup() {
  const navigate = useNavigate()
  const [params, setParams] = useState<SimParamsRequest | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [errors, setErrors] = useState<string[]>([])
  const [apiError, setApiError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [history, setHistory] = useState<SimulationResponse[]>([])

  useEffect(() => {
    api.simulations.defaults().then(setParams).catch(() => setLoadError('Failed to load default parameters.'))
    api.simulations.list().then(list => setHistory([...list].reverse())).catch(() => {})
  }, [])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!params) return
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

      {loadError && <div className="error-box"><p>{loadError}</p></div>}

      {params === null && !loadError && (
        <p style={{ color: '#8a9bb5' }}>Loading parameters…</p>
      )}

      {params !== null && (
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
      )}

      {history.length > 0 && (
        <div className="run-history">
          <h2>Recent Runs</h2>
          <div className="history-list">
            {history.map(run => (
              <div key={run.id} className="history-item" onClick={() => navigate(`/results/${run.id}`)}>
                <span className="run-id">#{run.id}</span>
                <span className={`run-status ${statusClass(run.status)}`}>{run.status}</span>
                <span>{run.behavior_strategy}</span>
                <span>{run.board_size}×{run.board_size}</span>
                <span>{run.initial_population} pop</span>
                <span className="run-meta">
                  {run.total_turns_run} / {run.total_turns_configured} ticks
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
