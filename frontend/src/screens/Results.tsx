import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { SimulationResponse, TickSnapshotResponse } from '../types'

export default function Results() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const simId = parseInt(id!, 10)

  const [sim, setSim] = useState<SimulationResponse | null>(null)
  const [stats, setStats] = useState<TickSnapshotResponse[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.simulations.get(simId)
      .then(setSim)
      .catch(() => setError('Failed to load simulation.'))
    api.simulations.getStats(simId)
      .then(setStats)
      .catch(() => {})
  }, [simId])

  const last = stats[stats.length - 1] ?? null

  return (
    <div className="screen">
      <h1>Results — Simulation #{simId}</h1>

      {error && <div className="error-box"><p>{error}</p></div>}

      {sim && (
        <div className="sim-info">
          <span>Status: <strong>{sim.status}</strong></span>
          <span>Turns run: <strong>{sim.total_turns_run}</strong> / {sim.total_turns_configured}</span>
          <span>Strategy: {sim.behavior_strategy}</span>
          <span>Board: {sim.board_size}×{sim.board_size}</span>
          <span>Seed: {sim.seed}</span>
        </div>
      )}

      {last ? (
        <>
          <div className="stats-card">
            <h3>Population (tick {last.tick})</h3>
            <table>
              <tbody>
                <tr><td>Total</td><td>{last.population_total}</td></tr>
                <tr><td>Male / Female</td><td>{last.population_male} / {last.population_female}</td></tr>
                <tr><td>Avg energy</td><td>{last.avg_energy.toFixed(1)}</td></tr>
                <tr><td>Min / Max energy</td><td>{last.min_energy.toFixed(1)} / {last.max_energy.toFixed(1)}</td></tr>
              </tbody>
            </table>
          </div>

          <div className="stats-card">
            <h3>Events (last snapshot)</h3>
            <table>
              <tbody>
                <tr><td>Births</td><td>{last.births}</td></tr>
                <tr><td>Deaths total</td><td>{last.deaths_total}</td></tr>
                <tr><td>— Starvation</td><td>{last.deaths_starvation}</td></tr>
                <tr><td>— Age</td><td>{last.deaths_age}</td></tr>
                <tr><td>— Fight</td><td>{last.deaths_fight}</td></tr>
                <tr><td>Fights total</td><td>{last.fights_total}</td></tr>
                <tr><td>Reproductions (ok / no space / low energy)</td>
                  <td>{last.reproductions_successful} / {last.reproductions_failed_space} / {last.reproductions_failed_energy}</td></tr>
              </tbody>
            </table>
          </div>

          <div className="stats-card">
            <h3>Genome averages (last snapshot)</h3>
            <table>
              <tbody>
                <tr><td>Lifespan</td><td>{last.avg_lifespan.toFixed(1)}</td></tr>
                <tr><td>Vision range</td><td>{last.avg_vision_range.toFixed(2)}</td></tr>
                <tr><td>Metabolism</td><td>{last.avg_metabolism.toFixed(3)}</td></tr>
                <tr><td>Aggression</td><td>{last.avg_aggression.toFixed(3)}</td></tr>
                <tr><td>Hunger threshold</td><td>{last.avg_hunger_threshold.toFixed(1)}</td></tr>
                <tr><td>Safe threshold</td><td>{last.avg_safe_threshold.toFixed(1)}</td></tr>
                <tr><td>Resistance</td><td>{last.avg_resistance.toFixed(3)}</td></tr>
              </tbody>
            </table>
          </div>

          <p className="phase-note">Trait-drift charts and death-cause breakdown coming in Phase 6.</p>
        </>
      ) : (
        <p style={{ color: '#8a9bb5' }}>
          {stats.length === 0 ? 'No snapshots recorded for this run.' : 'Loading stats…'}
        </p>
      )}

      <div className="controls">
        <button onClick={() => navigate(`/simulation/${simId}`)}>Back to Simulation</button>
        <button onClick={() => navigate('/')}>New Simulation</button>
      </div>
    </div>
  )
}
