import { useRef, useEffect } from 'react'
import type { BoardStateResponse } from '../types'

interface BoardProps {
  state: BoardStateResponse | null
  pixelSize?: number
}

const MALE_COLOR = '#5ba3d9'
const FEMALE_COLOR = '#d97ab8'
const FRUIT_COLOR = '#7ecfa4'
const POISON_COLOR = '#cf7e7e'
const GRID_BG = '#0f0f13'
const GRID_LINE = '#1e1e28'

export default function Board({ state, pixelSize = 600 }: BoardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const boardSize = state?.board_size ?? 20
    const cell = pixelSize / boardSize

    ctx.fillStyle = GRID_BG
    ctx.fillRect(0, 0, pixelSize, pixelSize)

    ctx.strokeStyle = GRID_LINE
    ctx.lineWidth = 0.5
    for (let i = 0; i <= boardSize; i++) {
      ctx.beginPath()
      ctx.moveTo(i * cell, 0)
      ctx.lineTo(i * cell, pixelSize)
      ctx.stroke()
      ctx.beginPath()
      ctx.moveTo(0, i * cell)
      ctx.lineTo(pixelSize, i * cell)
      ctx.stroke()
    }

    if (!state) return

    const cx = (x: number) => x * cell + cell / 2
    const cy = (y: number) => y * cell + cell / 2
    const itemR = Math.max(2, cell * 0.22)
    const creatureR = Math.max(3, cell * 0.38)

    ctx.fillStyle = FRUIT_COLOR
    for (const f of state.fruits) {
      ctx.beginPath()
      ctx.arc(cx(f.x), cy(f.y), itemR, 0, Math.PI * 2)
      ctx.fill()
    }

    ctx.fillStyle = POISON_COLOR
    for (const p of state.poisons) {
      ctx.beginPath()
      ctx.arc(cx(p.x), cy(p.y), itemR, 0, Math.PI * 2)
      ctx.fill()
    }

    for (const c of state.creatures) {
      ctx.fillStyle = c.sex === 'male' ? MALE_COLOR : FEMALE_COLOR
      ctx.beginPath()
      ctx.arc(cx(c.x), cy(c.y), creatureR, 0, Math.PI * 2)
      ctx.fill()
    }
  }, [state, pixelSize])

  return (
    <canvas
      ref={canvasRef}
      width={pixelSize}
      height={pixelSize}
      style={{ display: 'block', borderRadius: 8, border: '1px solid #2a2a38' }}
    />
  )
}
