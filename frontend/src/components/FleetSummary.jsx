import './FleetSummary.css'

const BANDS = [
  { key: 'critical', label: 'CRITICAL' },
  { key: 'warning', label: 'WARNING' },
  { key: 'healthy', label: 'HEALTHY' },
]

export default function FleetSummary({ predictions, activeFilter, onFilterChange }) {
  const counts = { critical: 0, warning: 0, healthy: 0, pending: 0 }
  Object.values(predictions).forEach((p) => {
    if (counts[p.risk_level] !== undefined) counts[p.risk_level] += 1
  })

  const total = Object.keys(predictions).length

  return (
    <div className="fleet-summary">
      <button
        className={`fleet-summary__chip ${activeFilter === null ? 'fleet-summary__chip--active' : ''}`}
        onClick={() => onFilterChange(null)}
      >
        <span className="fleet-summary__count mono">{total}</span>
        <span className="fleet-summary__label">ALL</span>
      </button>
      {BANDS.map((band) => (
        <button
          key={band.key}
          className={`fleet-summary__chip fleet-summary__chip--${band.key} ${
            activeFilter === band.key ? 'fleet-summary__chip--active' : ''
          }`}
          onClick={() => onFilterChange(activeFilter === band.key ? null : band.key)}
        >
          <span className="fleet-summary__count mono">{counts[band.key]}</span>
          <span className="fleet-summary__label">{band.label}</span>
        </button>
      ))}
    </div>
  )
}
