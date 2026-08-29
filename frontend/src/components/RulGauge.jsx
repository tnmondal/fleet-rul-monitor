import './RulGauge.css'

// Semicircular instrument dial, styled after a cockpit/engine gauge.
// Zones: red (critical, <20 cycles), amber (warning, <50), teal (healthy).
const RUL_CAP = 130
const ZONES = [
  { max: 20, color: '#c4453a', label: 'CRIT' },
  { max: 50, color: '#e8a33d', label: 'WARN' },
  { max: RUL_CAP, color: '#4fa8a0', label: 'OK' },
]

function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 180) * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function describeArc(cx, cy, r, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, r, endAngle)
  const end = polarToCartesian(cx, cy, r, startAngle)
  const largeArc = endAngle - startAngle <= 180 ? '0' : '1'
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`
}

export default function RulGauge({ value, riskLevel }) {
  const clamped = Math.max(0, Math.min(value, RUL_CAP))
  const needleAngle = (clamped / RUL_CAP) * 180

  const cx = 110
  const cy = 105
  const r = 88

  let start = 0
  const zoneArcs = ZONES.map((z) => {
    const end = (z.max / RUL_CAP) * 180
    const arc = { ...z, path: describeArc(cx, cy, r, start, end) }
    start = end
    return arc
  })

  const needleTip = polarToCartesian(cx, cy, r - 14, needleAngle)

  return (
    <div className="rul-gauge">
      <svg viewBox="0 0 220 130" width="220" height="130">
        {zoneArcs.map((z, i) => (
          <path
            key={i}
            d={z.path}
            fill="none"
            stroke={z.color}
            strokeWidth="10"
            strokeLinecap="butt"
            opacity="0.85"
          />
        ))}
        <line
          x1={cx}
          y1={cy}
          x2={needleTip.x}
          y2={needleTip.y}
          stroke="#edeff2"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <circle cx={cx} cy={cy} r="5" fill="#edeff2" />
        <circle cx={cx} cy={cy} r="2" fill="var(--bg)" />
      </svg>
      <div className="rul-gauge__readout">
        <span className={`rul-gauge__value mono risk-${riskLevel}`}>
          {clamped.toFixed(0)}
        </span>
        <span className="rul-gauge__unit">CYCLES REMAINING</span>
      </div>
    </div>
  )
}
