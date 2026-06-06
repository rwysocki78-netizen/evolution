// Zero-dependency SVG line chart.

const PL = 48, PR = 12, PT = 12, PB = 28
const VW = 560, VH = 190
const PLOT_W = VW - PL - PR
const PLOT_H = VH - PT - PB

export interface Series {
  label: string
  color: string
  values: number[]
}

interface Props {
  title: string
  xValues: number[]
  series: Series[]
}

function fmtY(v: number): string {
  if (Math.abs(v) >= 100) return v.toFixed(0)
  if (Math.abs(v) >= 10) return v.toFixed(1)
  return v.toFixed(2)
}

export default function LineChart({ title, xValues, series }: Props) {
  const allData = series.flatMap(s => s.values).filter(Number.isFinite)

  if (!xValues.length || !allData.length) {
    return (
      <div className="chart-wrap">
        <h3 className="chart-title">{title}</h3>
        <p className="chart-empty">No snapshot data</p>
      </div>
    )
  }

  let yMin = Math.min(...allData)
  let yMax = Math.max(...allData)
  if (yMin === yMax) { yMin -= 1; yMax += 1 }
  yMax += (yMax - yMin) * 0.05

  const xMin = xValues[0]
  const xRange = (xValues[xValues.length - 1] - xMin) || 1

  const sx = (v: number) => PL + ((v - xMin) / xRange) * PLOT_W
  const sy = (v: number) => PT + PLOT_H - ((v - yMin) / (yMax - yMin)) * PLOT_H

  const yStep = (yMax - yMin) / 4
  const yGrids = [0, 1, 2, 3, 4].map(i => yMin + i * yStep)

  const stride = Math.max(1, Math.ceil((xValues.length - 1) / 5))
  const xLabels: number[] = []
  for (let i = 0; i < xValues.length; i += stride) xLabels.push(xValues[i])
  if (xLabels[xLabels.length - 1] !== xValues[xValues.length - 1]) {
    xLabels.push(xValues[xValues.length - 1])
  }

  const showDots = xValues.length <= 20

  return (
    <div className="chart-wrap">
      <h3 className="chart-title">{title}</h3>
      <svg viewBox={`0 0 ${VW} ${VH}`} className="chart-svg">
        {yGrids.map((y, i) => (
          <g key={i}>
            <line x1={PL} x2={PL + PLOT_W} y1={sy(y)} y2={sy(y)}
              stroke="#1e1e28" strokeWidth={1} />
            <text x={PL - 4} y={sy(y)} textAnchor="end" dominantBaseline="middle"
              fontSize={9} fill="#5a6880">
              {fmtY(y)}
            </text>
          </g>
        ))}

        <line x1={PL} x2={PL} y1={PT} y2={PT + PLOT_H} stroke="#2a2a38" strokeWidth={1} />
        <line x1={PL} x2={PL + PLOT_W} y1={PT + PLOT_H} y2={PT + PLOT_H} stroke="#2a2a38" strokeWidth={1} />

        {xLabels.map(x => (
          <text key={x} x={sx(x)} y={PT + PLOT_H + 12} textAnchor="middle"
            fontSize={9} fill="#5a6880">
            {x}
          </text>
        ))}

        {series.map(s => (
          <polyline
            key={s.label}
            points={xValues.map((x, i) => `${sx(x).toFixed(1)},${sy(s.values[i]).toFixed(1)}`).join(' ')}
            fill="none"
            stroke={s.color}
            strokeWidth={1.5}
            strokeLinejoin="round"
            strokeLinecap="round"
          />
        ))}

        {showDots && series.map(s =>
          xValues.map((x, i) => (
            <circle key={`${s.label}-${i}`}
              cx={sx(x)} cy={sy(s.values[i])} r={2.5} fill={s.color} />
          ))
        )}
      </svg>

      {series.length > 1 && (
        <div className="chart-legend">
          {series.map(s => (
            <span key={s.label} className="chart-legend-item">
              <span className="chart-legend-dot" style={{ background: s.color }} />
              {s.label}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
