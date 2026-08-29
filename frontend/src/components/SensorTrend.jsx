import { useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import './SensorTrend.css'

// All sensors kept by the feature pipeline (see ml/src/features.py ACTIVE_SENSORS).
const ALL_SENSORS = [
  { key: 'sensor_2', color: '#4fa8a0' },
  { key: 'sensor_3', color: '#e8a33d' },
  { key: 'sensor_4', color: '#c4453a' },
  { key: 'sensor_7', color: '#8b7fd6' },
  { key: 'sensor_8', color: '#5aa3d0' },
  { key: 'sensor_9', color: '#d98fc0' },
  { key: 'sensor_11', color: '#e8a33d' },
  { key: 'sensor_12', color: '#78c47e' },
  { key: 'sensor_13', color: '#4fa8a0' },
  { key: 'sensor_14', color: '#d0785a' },
  { key: 'sensor_15', color: '#c4453a' },
  { key: 'sensor_17', color: '#9d8ce8' },
  { key: 'sensor_20', color: '#6fb8d9' },
  { key: 'sensor_21', color: '#e0a5d8' },
]

const DEFAULT_SELECTED = ['sensor_4', 'sensor_11', 'sensor_15']

export default function SensorTrend({ readings }) {
  const [selected, setSelected] = useState(DEFAULT_SELECTED)
  const [showAllToggle, setShowAllToggle] = useState(false)

  const visibleSensors = showAllToggle
    ? ALL_SENSORS
    : ALL_SENSORS.filter((s) => selected.includes(s.key))

  const data = readings.map((r) => {
    const row = { cycle: r.time_in_cycles }
    ALL_SENSORS.forEach((s) => {
      if (r[s.key] != null) row[s.key] = Number(r[s.key].toFixed(1))
    })
    return row
  })

  function toggleSensor(key) {
    setSelected((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    )
  }

  return (
    <div className="sensor-trend">
      <div className="sensor-trend__header">
        <span>SENSOR TELEMETRY — LAST {readings.length} CYCLES</span>
        <button
          className="sensor-trend__toggle-all"
          onClick={() => setShowAllToggle((v) => !v)}
        >
          {showAllToggle ? 'SHOW SELECTED ONLY' : 'SHOW ALL 14 SENSORS'}
        </button>
      </div>

      {!showAllToggle && (
        <div className="sensor-trend__picker">
          {ALL_SENSORS.map((s) => {
            const active = selected.includes(s.key)
            return (
              <button
                key={s.key}
                className={`sensor-chip ${active ? 'sensor-chip--active' : ''}`}
                style={active ? { borderColor: s.color, color: s.color } : undefined}
                onClick={() => toggleSensor(s.key)}
              >
                {s.key.replace('sensor_', 'S')}
              </button>
            )
          })}
        </div>
      )}

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
          <CartesianGrid stroke="#2c343c" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="cycle"
            stroke="#5a6570"
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke: '#2c343c' }}
          />
          <YAxis
            stroke="#5a6570"
            fontSize={11}
            tickLine={false}
            axisLine={{ stroke: '#2c343c' }}
          />
          <Tooltip
            contentStyle={{
              background: '#1b2126',
              border: '1px solid #3a444e',
              borderRadius: 4,
              fontSize: 12,
              fontFamily: 'JetBrains Mono, monospace',
            }}
            labelFormatter={(v) => `Cycle ${v}`}
          />
          {visibleSensors.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              stroke={s.color}
              strokeWidth={1.75}
              dot={false}
              isAnimationActive={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
