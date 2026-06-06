import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { BoardStateResponse, SimulationResponse } from '../types'
import Board from '../components/Board'

const SPEEDS = [1, 2, 5, 10] as const

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
  const [speed, setSpeed] = useState<number>(2)

  useEffect(() => {
    if (!validId) { setError('Invalid simulation ID.'); return }
    setError(null)
    api.simulations.get(simId).then(setSim).catch(() => setError('Failed to load simulation.'))
    api.simulations.getState(simId).then(setState).catch(() => {})
  }, [simId, validId])

  const isDone = sim?.status === 'completed' || sim?.status === 'stopped'

  useEffect(() => { if (isDone) setPlaying(false) }, [isDone])

  // Autoplay loop — chains steps at configured speed
  const cancelledRef = useRef(false)
  useEffect(() => {
    if (!playing) return
    cancelledRef.current = false
    let timer: ReturnType<typeof setTimeout>

    const runStep = async () => {
      if (cancelledRef.current) return
      setBusy(true)
      setError(null)
      let stop = false
      try {
        const res = await api.simulations.step(simId)
        if (!cancelledRef.current) {
          setState(res.state)
          if (res.completed) {
            setSim(s => s ? { ...s, status: 'completed', total_turns_run: res.turns_run } : s)
            stop = true
          }
        }
      } catch (e) {
        if (!cancelledRef.current) {
          setError(e instanceof Error ? e.message : 'Step failed.')
          stop = true
        }
      }
      if (!cancelledRef.current) {
        setBusy(false)
        if (stop) setPlaying(false)
        else timer = setTimeout(runStep, 1000 / speed)
      }
    }

    timer = setTimeout(runStep, 0)
    return () => { cancelledRef.current = true; clearTimeout(timer) }
  }, [playing, simId, speed])

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
        <button
          onClick={() => setPlaying(p => !p)}
          disabled={isDone || !validId}
          className={playing ? 'btn-pause' : 'btn-accent'}
        >
          {playing ? 'Pause' : 'Play'}
        </button>
        <button onClick={handleStep} disabled={busy || playing || isDone || !validId}>
          Step
        </button>
        <button onClick={handleStop} disabled={busy || isDone || !validId} className="btn-danger">
          Stop
        </button>
        <div className="speed-control">
          <label>Speed</label>
          <select value={speed} onChange={e => setSpeed(Number(e.target.value))}>
            {SPEEDS.map(s => <option key={s} value={s}>{s} t/s</option>)}
          </select>
        </div>
        <button onClick={() => navigate(`/results/${simId}`)}>Results</button>
        <button onClick={() => navigate('/')}>New</button>
      </div>

      {state ? (
        <Board state={state} />
      ) : (
        <div className="board-placeholder">
          <span>{validId ? 'No board state — click Step or Play to begin.' : 'Invalid simulation ID.'}</span>
        </div>
      )}
    </div>
  )
}
