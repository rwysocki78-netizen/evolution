import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { BoardStateResponse, SimulationResponse } from '../types'

export default function Simulation() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const simId = parseInt(id ?? '', 10)
  const validId = Number.isFinite(simId)

  const [sim, setSim] = useState<SimulationResponse | null>(null)
  const [state, setState] = useState<BoardStateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!validId) { setError('Invalid simulation ID.'); return }
    api.simulations.get(simId).then(setSim).catch(() => setError('Failed to load simulation.'))
    api.simulations.getState(simId).then(setState).catch(() => {
      // State unavailable if server restarted — not fatal
    })
  }, [simId, validId])

  const isDone = sim?.status === 'completed' || sim?.status === 'stopped'

  const handleStep = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await api.simulations.step(simId)
      setState(res.state)
      if (res.completed) setSim(s => s ? { ...s, status: 'completed', total_turns_run: res.turns_run } : s)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Step failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleRun = async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await api.simulations.run(simId)
      setState(res.state)
      setSim(s => s
        ? { ...s, status: res.completed ? 'completed' : s.status, total_turns_run: res.turns_run }
        : s)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Run failed.')
    } finally {
      setBusy(false)
    }
  }

  const handleStop = async () => {
    setBusy(true)
    setError(null)
    try {
      const updated = await api.simulations.stop(simId)
      setSim(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Stop failed.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="screen">
      <h1>Simulation #{validId ? simId : '?'}</h1>

      {error && <div className="error-box"><p>{error}</p></div>}

      {sim && (
        <div className="sim-info">
          <span>Status: <strong>{sim.status}</strong></span>
          <span>Tick: <strong>{state?.tick ?? 0}</strong> / {sim.total_turns_configured}</span>
          <span>Population: <strong>{state?.creatures.length ?? '—'}</strong></span>
          <span>Board: {sim.board_size}×{sim.board_size}</span>
          <span>Strategy: {sim.behavior_strategy}</span>
          <span>Seed: {sim.seed}</span>
        </div>
      )}

      <div className="controls">
        <button onClick={handleStep} disabled={busy || isDone || !validId}>Step</button>
        <button onClick={handleRun} disabled={busy || isDone || !validId} className="btn-accent">
          Run to end
        </button>
        <button onClick={handleStop} disabled={busy || isDone || !validId} className="btn-danger">
          Stop
        </button>
        <button onClick={() => navigate(`/results/${simId}`)}>View Results</button>
        <button onClick={() => navigate('/')}>New Simulation</button>
      </div>

      <div className="board-placeholder">
        <span>Board rendering</span>
        <span className="phase-note">Canvas renderer coming in Phase 5</span>
      </div>
    </div>
  )
}
