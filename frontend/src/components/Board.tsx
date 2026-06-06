import { useEffect, useRef } from 'react'
import type { BoardStateResponse } from '../types'

interface Props {
  state: BoardStateResponse
}

function cellPx(boardSize: number): number {
  return Math.max(6, Math.min(20, Math.floor(560 / boardSize)))
}

export default function Board({ state }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const { board_size, creatures, fruits, poisons } = state

    const cell = cellPx(board_size)
    const dim = board_size * cell
    canvas.width = dim
    canvas.height = dim

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.fillStyle = '#0f0f13'
    ctx.fillRect(0, 0, dim, dim)

    ctx.strokeStyle = '#1e1e28'
    ctx.lineWidth = 0.5
    for (let i = 0; i <= board_size; i++) {
      ctx.beginPath(); ctx.moveTo(i * cell, 0); ctx.lineTo(i * cell, dim); ctx.stroke()
      ctx.beginPath(); ctx.moveTo(0, i * cell); ctx.lineTo(dim, i * cell); ctx.stroke()
    }

    const r = Math.max(2, cell * 0.35)
    const rSmall = r * 0.72

    ctx.fillStyle = '#7ecfa4'
    for (const { x, y } of fruits) {
      ctx.beginPath()
      ctx.arc(x * cell + cell / 2, y * cell + cell / 2, rSmall, 0, Math.PI * 2)
      ctx.fill()
    }

    ctx.fillStyle = '#cf7e5e'
    for (const { x, y } of poisons) {
      ctx.beginPath()
      ctx.arc(x * cell + cell / 2, y * cell + cell / 2, rSmall, 0, Math.PI * 2)
      ctx.fill()
    }

    for (const c of creatures) {
      ctx.fillStyle = c.sex === 'male' ? '#5c9bd6' : '#d66fa0'
      ctx.beginPath()
      ctx.arc(c.x * cell + cell / 2, c.y * cell + cell / 2, r, 0, Math.PI * 2)
      ctx.fill()
    }
  }, [state])

  const cell = cellPx(state.board_size)
  const dim = state.board_size * cell

  return (
    <div className="board-wrap">
      <canvas ref={canvasRef} width={dim} height={dim} />
      <div className="board-legend">
        <span className="legend-dot" style={{ background: '#5c9bd6' }} />Male
        <span className="legend-dot" style={{ background: '#d66fa0' }} />Female
        <span className="legend-dot" style={{ background: '#7ecfa4' }} />Fruit
        <span className="legend-dot" style={{ background: '#cf7e5e' }} />Poison
      </div>
    </div>
  )
}
