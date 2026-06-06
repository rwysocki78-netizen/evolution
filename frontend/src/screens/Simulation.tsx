import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Board from '../components/Board'
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
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(300)

  const isDone = sim?.status === 'completed' || sim?.status === 'stopped'
  const isDoneRef = useRef(isDone)
  const speedRef = useRef(speed)
  useEffect(() => { isDoneRef.current = isDone }, [isDone])
  useEffect(() => { speedRef.current = speed }, [speed])

  useEffect(() => {
    if (!validId) { setError('Invalid simulation ID.'); return }
    setError(null)
    api.simulations.get(simId).then(setSim).catch(() => setError('Failed to load simulation.'))
    api.simulations.getState(simId).then(setState).catch(() => {})
  }, [simId, validId])

  const doStep = async (): Promise<boolean> => {
    try {
      const res = await api.simulations.step(simId)
      setState(res.state)
      setSim(s => s ? { ...s, total_turns_run: res.turns_run, ...(res.completed ? { status: 'completed' } : {}) } : s)
      return res.completed
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Step failed.')
      return true
    }
  }

  const handleStep = async () => {
    if (busy || isDone) return
    setBusy(true)
    setError(null)
    await doStep()
    setBusy(false)
  }

  const handleStop = async () => {
    setPlaying(false)
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

  useEffect(() => {
    if (!playing) return
    let active = true

    const loop = async () => {
      while (active && !isDoneRef.current) {
        const done = await doStep()
        if (done || !active) break
        await new Promise<void>(r => setTimeout(r, speedRef.current))
      }
      if (active) setPlaying(false)
    }

    loop()
    return () => { active = false }
  }, [playing, simId])

  const males = state?.creatures.filter(c => c.sex === 'male').length ?? 0
  const females = state?.creatures.filter(c => c.sex === 'female').length ?? 0

  const ticksPerSec = speed < 100 ? `${(1000 / speed).toFixed(0)} t/s` : `${(1000 / speed).toFixed(1)} t/s`

  return (
    <div className="screen sim-screen">
      <h1>Simulation #{validId ? simId : '?'}</h1>

      {error && <div className="error-box"><p>{error}</p></div>}

      {sim && (
        <div className="sim-info">
          <span>Status: <strong>{sim.status}</strong></span>
          <span>Tick: <strong>{state?.tick ?? 0}</strong> / {sim.total_turns_configured}</span>
          <span>Population: <strong>{state?.creatures.length ?? '—'}</strong></span>
          <span title="male">♂ <strong>{males}</strong></span>
          <span title="female">♀ <strong>{females}</strong></span>
          <span>Board: {sim.board_size}×{sim.board_size}</span>
          <span>Strategy: {sim.behavior_strategy}</span>
        </div>
      )}

      <div className="controls">
        <button onClick={handleStep} disabled={busy || isDone || playing || !validId}>
          Step
        </button>
        <button
          onClick={() => { setError(null); setPlaying(p => !p) }}
          disabled={isDone || busy || !validId}
          className="btn-accent"
        >
          {playing ? 'Pause' : 'Play'}
        </button>
        <button onClick={handleStop} disabled={busy || isDone || !validId} className="btn-danger">
          Stop
        </button>
        <button onClick={() => navigate(`/results/${simId}`)}>View Results</button>
        <button onClick={() => navigate('/')}>New Simulation</button>
      </div>

      <div className="speed-control">
        <label>Speed: <strong>{ticksPerSec}</strong></label>
        <input
          type="range"
          min={50}
          max={2000}
          step={50}
          value={2050 - speed}
          onChange={e => setSpeed(2050 - parseInt(e.target.value, 10))}
        />
        <span className="speed-hint">slow</span>
        <span className="speed-hint">fast</span>
      </div>

      <div className="board-wrap">
        <Board state={state} pixelSize={600} />
        <div className="board-legend">
          <span className="legend-dot male" />Male
          <span className="legend-dot female" />Female
          <span className="legend-dot fruit" />Fruit
          <span className="legend-dot poison" />Poison
        </div>
      </div>
    </div>
  )
}
