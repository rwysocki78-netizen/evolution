import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { SimulationResponse, TickSnapshotResponse } from '../types'
import LineChart from '../components/charts/LineChart'

export default function Results() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const simId = parseInt(id ?? '', 10)
  const validId = Number.isFinite(simId)

  const [sim, setSim] = useState<SimulationResponse | null>(null)
  const [stats, setStats] = useState<TickSnapshotResponse[]>([])
  const [statsLoading, setStatsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statsError, setStatsError] = useState<string | null>(null)

  useEffect(() => {
    if (!validId) { setError('Invalid simulation ID.'); setStatsLoading(false); return }
    setError(null)
    setStatsError(null)
    api.simulations.get(simId).then(setSim).catch(() => setError('Failed to load simulation.'))
    api.simulations.getStats(simId)
      .then(setStats)
      .catch(() => setStatsError('Failed to load snapshot data.'))
      .finally(() => setStatsLoading(false))
  }, [simId, validId])

  // Build all chart series in one pass
  const ticks: number[] = []
  const pop_total: number[] = [], pop_male: number[] = [], pop_female: number[] = []
  const births: number[] = [], deaths_total: number[] = []
  const d_starv: number[] = [], d_age: number[] = [], d_fight: number[] = []
  const avg_lifespan: number[] = [], avg_hunger: number[] = [], avg_safe: number[] = []
  const avg_meta: number[] = [], avg_aggr: number[] = [], avg_resist: number[] = [], avg_vision: number[] = []
  for (const s of stats) {
    ticks.push(s.tick)
    pop_total.push(s.population_total); pop_male.push(s.population_male); pop_female.push(s.population_female)
    births.push(s.births); deaths_total.push(s.deaths_total)
    d_starv.push(s.deaths_starvation); d_age.push(s.deaths_age); d_fight.push(s.deaths_fight)
    avg_lifespan.push(s.avg_lifespan); avg_hunger.push(s.avg_hunger_threshold); avg_safe.push(s.avg_safe_threshold)
    avg_meta.push(s.avg_metabolism); avg_aggr.push(s.avg_aggression)
    avg_resist.push(s.avg_resistance); avg_vision.push(s.avg_vision_range)
  }
  const last = stats[stats.length - 1]

  return (
    <div className="screen">
      <h1>Results — Simulation #{validId ? simId : '?'}</h1>

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

      {statsLoading ? (
        <p style={{ color: '#8a9bb5' }}>Loading stats…</p>
      ) : statsError ? (
        <div className="error-box"><p>{statsError}</p></div>
      ) : stats.length === 0 ? (
        <p style={{ color: '#8a9bb5' }}>No snapshots recorded for this run.</p>
      ) : (
        <div className="charts-section">

          <LineChart
            title="Population over time"
            xValues={ticks}
            series={[
              { label: 'Total',  color: '#7ecfa4', values: pop_total },
              { label: 'Male',   color: '#5ba3d9', values: pop_male },
              { label: 'Female', color: '#d97ab8', values: pop_female },
            ]}
          />

          <LineChart
            title="Births vs Deaths (per snapshot)"
            xValues={ticks}
            series={[
              { label: 'Births',  color: '#7ecfa4', values: births },
              { label: 'Deaths',  color: '#cf7e7e', values: deaths_total },
            ]}
          />

          <LineChart
            title="Death causes (per snapshot)"
            xValues={ticks}
            series={[
              { label: 'Starvation', color: '#cf7e5e', values: d_starv },
              { label: 'Old age',    color: '#7ea8cf', values: d_age },
              { label: 'Fight',      color: '#d97ab8', values: d_fight },
            ]}
          />

          <div className="charts-grid">
            <LineChart
              title="Genome drift — thresholds"
              xValues={ticks}
              series={[
                { label: 'Lifespan',         color: '#7ecfa4', values: avg_lifespan },
                { label: 'Hunger threshold', color: '#cfb87e', values: avg_hunger },
                { label: 'Safe threshold',   color: '#7ea8cf', values: avg_safe },
              ]}
            />

            <LineChart
              title="Genome drift — rates"
              xValues={ticks}
              series={[
                { label: 'Metabolism',   color: '#cf7e7e', values: avg_meta },
                { label: 'Aggression',   color: '#d97ab8', values: avg_aggr },
                { label: 'Resistance',   color: '#a87ecf', values: avg_resist },
                { label: 'Vision range', color: '#7ecfa4', values: avg_vision },
              ]}
            />
          </div>

          <div className="charts-grid">
            <div className="stats-card">
              <h3>Final population (tick {last.tick})</h3>
              <table><tbody>
                <tr><td>Total</td><td>{last.population_total}</td></tr>
                <tr><td>Male / Female</td><td>{last.population_male} / {last.population_female}</td></tr>
                <tr><td>Avg energy</td><td>{last.avg_energy.toFixed(1)}</td></tr>
                <tr><td>Min / Max energy</td><td>{last.min_energy.toFixed(1)} / {last.max_energy.toFixed(1)}</td></tr>
                <tr><td>Births</td><td>{last.births}</td></tr>
                <tr><td>Deaths (starv / age / fight)</td>
                  <td>{last.deaths_starvation} / {last.deaths_age} / {last.deaths_fight}</td></tr>
                <tr><td>Fights</td><td>{last.fights_total}</td></tr>
                <tr><td>Reproductions</td><td>{last.reproductions_successful}</td></tr>
              </tbody></table>
            </div>

            <div className="stats-card">
              <h3>Final genome averages (tick {last.tick})</h3>
              <table><tbody>
                <tr><td>Lifespan</td><td>{last.avg_lifespan.toFixed(1)}</td></tr>
                <tr><td>Vision range</td><td>{last.avg_vision_range.toFixed(2)}</td></tr>
                <tr><td>Metabolism</td><td>{last.avg_metabolism.toFixed(3)}</td></tr>
                <tr><td>Aggression</td><td>{last.avg_aggression.toFixed(3)}</td></tr>
                <tr><td>Hunger threshold</td><td>{last.avg_hunger_threshold.toFixed(1)}</td></tr>
                <tr><td>Safe threshold</td><td>{last.avg_safe_threshold.toFixed(1)}</td></tr>
                <tr><td>Resistance</td><td>{last.avg_resistance.toFixed(3)}</td></tr>
              </tbody></table>
            </div>
          </div>
        </div>
      )}

      <div className="controls" style={{ marginTop: 24 }}>
        <button onClick={() => navigate(`/simulation/${simId}`)}>Back to Simulation</button>
        <button onClick={() => navigate('/')}>New Simulation</button>
      </div>
    </div>
  )
}
