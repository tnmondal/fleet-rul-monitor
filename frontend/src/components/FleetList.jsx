import { useMemo, useState } from 'react'
import './FleetList.css'

const SORT_OPTIONS = [
  { key: 'rul_asc', label: 'RUL (LOW→HIGH)' },
  { key: 'rul_desc', label: 'RUL (HIGH→LOW)' },
  { key: 'id', label: 'ENGINE ID' },
]

export default function FleetList({ fleet, predictions, selectedUnit, onSelect, riskFilter }) {
  const [sortKey, setSortKey] = useState('rul_asc')

  const visible = useMemo(() => {
    let list = fleet.filter((unit) => {
      if (!riskFilter) return true
      return predictions[unit.unit_number]?.risk_level === riskFilter
    })

    list = [...list].sort((a, b) => {
      if (sortKey === 'id') return a.unit_number - b.unit_number
      const ra = predictions[a.unit_number]?.predicted_rul
      const rb = predictions[b.unit_number]?.predicted_rul
      if (ra == null && rb == null) return 0
      if (ra == null) return 1
      if (rb == null) return -1
      return sortKey === 'rul_asc' ? ra - rb : rb - ra
    })

    return list
  }, [fleet, predictions, sortKey, riskFilter])

  return (
    <div className="fleet-list">
      <div className="fleet-list__header">
        <span>MANIFEST</span>
        <span className="fleet-list__count mono">{visible.length} / {fleet.length} UNITS</span>
      </div>
      <div className="fleet-list__sort">
        {SORT_OPTIONS.map((opt) => (
          <button
            key={opt.key}
            className={`fleet-list__sort-btn ${sortKey === opt.key ? 'fleet-list__sort-btn--active' : ''}`}
            onClick={() => setSortKey(opt.key)}
          >
            {opt.label}
          </button>
        ))}
      </div>
      <div className="fleet-list__items">
        {visible.length === 0 && (
          <div className="fleet-list__empty mono">No engines match this filter.</div>
        )}
        {visible.map((unit) => {
          const pred = predictions[unit.unit_number]
          const risk = pred?.risk_level
          return (
            <button
              key={unit.unit_number}
              className={`fleet-item ${
                selectedUnit === unit.unit_number ? 'fleet-item--active' : ''
              }`}
              onClick={() => onSelect(unit.unit_number)}
            >
              <span className={`fleet-item__dot risk-dot-${risk || 'pending'}`} />
              <span className="fleet-item__id mono">
                ENGINE-{String(unit.unit_number).padStart(3, '0')}
              </span>
              <span className="fleet-item__cycles mono">
                {unit.last_cycle}c
              </span>
              <span className="fleet-item__rul mono">
                {pred ? `${pred.predicted_rul.toFixed(0)}` : '—'}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
