import { useEffect, useMemo, useState } from 'react'
import RulGauge from './RulGauge'
import './WhatIfPanel.css'

// Sliders for the sensors with the strongest degradation signal (see
// ml/notebooks/01_eda.ipynb correlation analysis). Range is derived from
// a wide but plausible band around typical CMAPSS sensor values.
const SLIDER_SENSORS = [
  { key: 'sensor_4', label: 'Sensor 4', min: 480, max: 660 },
  { key: 'sensor_11', label: 'Sensor 11', min: 460, max: 640 },
  { key: 'sensor_15', label: 'Sensor 15', min: 460, max: 640 },
]

const DEBOUNCE_MS = 350

export default function WhatIfPanel({ unit, onPredict }) {
  const baseline = useMemo(() => {
    if (!unit) return null
    return unit.readings[unit.readings.length - 1]
  }, [unit])

  const [overrides, setOverrides] = useState({})
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setOverrides({})
    setResult(null)
  }, [unit?.unit_number])

  useEffect(() => {
    if (!unit || Object.keys(overrides).length === 0) return
    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const modifiedReadings = unit.readings.map((r, i) =>
          i === unit.readings.length - 1 ? { ...r, ...overrides } : r
        )
        const res = await onPredict(modifiedReadings)
        setResult(res)
      } finally {
        setLoading(false)
      }
    }, DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [overrides, unit, onPredict])

  if (!unit || !baseline) return null

  function handleChange(key, value) {
    setOverrides((prev) => ({ ...prev, [key]: Number(value) }))
  }

  function reset() {
    setOverrides({})
    setResult(null)
  }

  return (
    <div className="what-if">
      <div className="what-if__header">
        <span>WHAT-IF SIMULATOR</span>
        <button className="what-if__reset" onClick={reset} disabled={Object.keys(overrides).length === 0}>
          RESET
        </button>
      </div>
      <p className="what-if__hint">
        Drag a sensor to simulate a reading and see the predicted RUL update live.
      </p>

      <div className="what-if__body">
        <div className="what-if__sliders">
          {SLIDER_SENSORS.map((s) => {
            const value = overrides[s.key] ?? baseline[s.key]
            return (
              <div key={s.key} className="what-if__slider-row">
                <div className="what-if__slider-label">
                  <span>{s.label}</span>
                  <span className="mono what-if__slider-value">{value.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min={s.min}
                  max={s.max}
                  step={0.5}
                  value={value}
                  onChange={(e) => handleChange(s.key, e.target.value)}
                />
              </div>
            )
          })}
        </div>

        <div className="what-if__result">
          {loading ? (
            <div className="what-if__loading mono">RECALCULATING…</div>
          ) : result ? (
            <RulGauge value={result.predicted_rul} riskLevel={result.risk_level} />
          ) : (
            <div className="what-if__idle mono">move a slider to simulate</div>
          )}
        </div>
      </div>
    </div>
  )
}
