import RulGauge from './RulGauge'
import SensorTrend from './SensorTrend'
import WhatIfPanel from './WhatIfPanel'
import './EngineDetail.css'

const RISK_COPY = {
  healthy: 'Operating within normal parameters. No action required.',
  warning: 'Degradation trend detected. Schedule inspection within next maintenance window.',
  critical: 'Failure risk elevated. Recommend immediate inspection.',
}

export default function EngineDetail({ unit, prediction, loading, onPredict }) {
  if (!unit) {
    return (
      <div className="engine-detail engine-detail--empty">
        <p>Select an engine from the manifest to view telemetry.</p>
      </div>
    )
  }

  return (
    <div className="engine-detail">
      <div className="engine-detail__top">
        <div>
          <div className="engine-detail__eyebrow mono">UNIT</div>
          <h2 className="engine-detail__title mono">
            ENGINE-{String(unit.unit_number).padStart(3, '0')}
          </h2>
          <div className="engine-detail__meta mono">
            {unit.last_cycle} cycles logged
          </div>
        </div>

        <div className="engine-detail__gauge-wrap">
          {loading ? (
            <div className="engine-detail__loading mono">PREDICTING…</div>
          ) : prediction ? (
            <RulGauge value={prediction.predicted_rul} riskLevel={prediction.risk_level} />
          ) : null}
        </div>
      </div>

      {prediction && (
        <div className={`engine-detail__banner banner-${prediction.risk_level}`}>
          <span className="engine-detail__banner-label mono">
            {prediction.risk_level.toUpperCase()}
          </span>
          <span>{RISK_COPY[prediction.risk_level]}</span>
        </div>
      )}

      <SensorTrend readings={unit.readings} />

      <WhatIfPanel unit={unit} onPredict={onPredict} />

      <div className="engine-detail__footer mono">
        model: {prediction?.model_used ?? '—'} · actual RUL (ground truth, for demo comparison): {unit.actual_rul}
      </div>
    </div>
  )
}
