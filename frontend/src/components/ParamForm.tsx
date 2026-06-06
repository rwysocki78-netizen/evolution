import type { SimParamsRequest } from '../types'

interface Props {
  params: SimParamsRequest
  onChange: (p: SimParamsRequest) => void
}

export default function ParamForm({ params, onChange }: Props) {
  const set = <K extends keyof SimParamsRequest>(key: K, value: SimParamsRequest[K]) =>
    onChange({ ...params, [key]: value } as SimParamsRequest)

  const intInput = (key: keyof SimParamsRequest, label: string, min?: number) => (
    <tr key={key}>
      <td>{label}</td>
      <td>
        <input
          type="number"
          step={1}
          min={min}
          value={params[key] as number}
          onChange={e => {
            const v = e.target.valueAsNumber
            // Cast required: key is generic keyof SimParamsRequest; value is known to be numeric
            if (Number.isFinite(v)) set(key, Math.round(v) as SimParamsRequest[typeof key])
          }}
        />
      </td>
    </tr>
  )

  const floatInput = (
    key: keyof SimParamsRequest,
    label: string,
    step = 0.1,
    min?: number,
    max?: number,
  ) => (
    <tr key={key}>
      <td>{label}</td>
      <td>
        <input
          type="number"
          step={step}
          min={min}
          max={max}
          value={params[key] as number}
          onChange={e => {
            const v = e.target.valueAsNumber
            if (Number.isFinite(v)) set(key, v as SimParamsRequest[typeof key])
          }}
        />
      </td>
    </tr>
  )

  const rangeInput = (
    key: keyof SimParamsRequest,
    label: string,
    step = 1,
  ) => {
    const [lo, hi] = params[key] as [number, number]
    return (
      <tr key={key}>
        <td>{label}</td>
        <td>
          <div className="range-inputs">
            <input
              type="number"
              step={step}
              value={lo}
              style={{ width: 80 }}
              onChange={e => {
                const v = e.target.valueAsNumber
                if (Number.isFinite(v)) set(key, [v, hi] as SimParamsRequest[typeof key])
              }}
            />
            <span>–</span>
            <input
              type="number"
              step={step}
              value={hi}
              style={{ width: 80 }}
              onChange={e => {
                const v = e.target.valueAsNumber
                if (Number.isFinite(v)) set(key, [lo, v] as SimParamsRequest[typeof key])
              }}
            />
          </div>
        </td>
      </tr>
    )
  }

  const updateWeight = (i: number, weight: number) => {
    const updated = params.reproduction_weights.map((w, idx) =>
      idx === i ? { ...w, weight } : w,
    )
    set('reproduction_weights', updated)
  }

  return (
    <div className="param-form">
      <div className="param-section">
        <h3>Board &amp; Population</h3>
        <table>
          <tbody>
            {intInput('board_size', 'Board size', 5)}
            {intInput('initial_population', 'Initial population', 2)}
            {intInput('total_turns', 'Total turns', 1)}
            <tr>
              <td>Behavior strategy</td>
              <td>
                <select
                  value={params.behavior_strategy}
                  onChange={e => set('behavior_strategy', e.target.value)}
                >
                  <option value="threshold">Threshold</option>
                  <option value="priority">Priority</option>
                </select>
              </td>
            </tr>
            <tr>
              <td>RNG seed (blank = random)</td>
              <td>
                <input
                  type="number"
                  step={1}
                  value={params.seed ?? ''}
                  onChange={e => {
                    if (e.target.value === '') { set('seed', null); return }
                    const v = e.target.valueAsNumber
                    if (Number.isFinite(v)) set('seed', Math.round(v))
                  }}
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="param-section">
        <h3>Energy</h3>
        <table>
          <tbody>
            {floatInput('initial_energy', 'Initial energy', 1, 0)}
            {floatInput('max_energy', 'Max energy', 1, 0)}
            {floatInput('energy_decay_per_tick', 'Decay / tick', 0.1, 0)}
            {floatInput('fight_energy_cost', 'Fight cost', 1, 0)}
            {floatInput('reproduction_energy_cost', 'Reproduction cost', 1, 0)}
            {floatInput('reproduction_min_energy', 'Reproduction min energy', 1, 0)}
          </tbody>
        </table>
      </div>

      <div className="param-section">
        <h3>Life Stage</h3>
        <table>
          <tbody>
            {intInput('maturity_age', 'Maturity age', 1)}
            {floatInput('juvenile_max_energy_factor', 'Juvenile max energy factor', 0.05, 0, 1)}
          </tbody>
        </table>
      </div>

      <div className="param-section">
        <h3>World</h3>
        <table>
          <tbody>
            {floatInput('fruit_energy_value', 'Fruit energy value', 1, 0)}
            {floatInput('poison_energy_value', 'Poison energy value', 1, 0)}
            {floatInput('resistance_reduction_per_point', 'Resistance reduction / point', 0.01, 0, 1)}
            {intInput('max_fruits_on_board', 'Max fruits on board', 0)}
            {intInput('max_poisons_on_board', 'Max poisons on board', 0)}
          </tbody>
        </table>
      </div>

      <div className="param-section">
        <h3>Mutation</h3>
        <table>
          <tbody>
            {floatInput('mutation_rate', 'Mutation rate', 0.01, 0, 1)}
            {floatInput('mutation_magnitude', 'Mutation magnitude', 0.1, 0)}
          </tbody>
        </table>
      </div>

      <div className="param-section">
        <h3>Initial Genome Ranges</h3>
        <table>
          <tbody>
            {rangeInput('initial_lifespan', 'Lifespan')}
            {rangeInput('initial_vision_range', 'Vision range')}
            {rangeInput('initial_metabolism', 'Metabolism', 0.1)}
            {rangeInput('initial_aggression', 'Aggression', 0.05)}
            {rangeInput('initial_hunger_threshold', 'Hunger threshold')}
            {rangeInput('initial_safe_threshold', 'Safe threshold')}
            {rangeInput('initial_resistance', 'Resistance', 0.1)}
          </tbody>
        </table>
      </div>

      <div className="param-section">
        <h3>Reproduction Weights</h3>
        <table>
          <thead>
            <tr>
              <th scope="col">Children</th>
              <th scope="col">Weight</th>
            </tr>
          </thead>
          <tbody>
            {params.reproduction_weights.map((rw, i) => (
              <tr key={i}>
                <td>{rw.children}</td>
                <td>
                  <input
                    type="number"
                    step={0.05}
                    min={0.01}
                    max={1}
                    value={rw.weight}
                    onChange={e => {
                      const v = e.target.valueAsNumber
                      if (Number.isFinite(v) && v > 0) updateWeight(i, v)
                    }}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="param-section">
        <h3>Snapshots</h3>
        <table>
          <tbody>
            <tr>
              <td>Snapshot enabled</td>
              <td>
                <input
                  type="checkbox"
                  checked={params.snapshot_enabled}
                  onChange={e => set('snapshot_enabled', e.target.checked)}
                />
              </td>
            </tr>
            {intInput('snapshot_interval', 'Snapshot interval (ticks)', 1)}
          </tbody>
        </table>
      </div>
    </div>
  )
}
