import { useEffect, useState, useCallback } from 'react'
import FleetList from './components/FleetList'
import FleetSummary from './components/FleetSummary'
import EngineDetail from './components/EngineDetail'
import './App.css'

const API_BASE = '/api'

export default function App() {
  const [fleet, setFleet] = useState([])
  const [predictions, setPredictions] = useState({})
  const [selectedUnit, setSelectedUnit] = useState(null)
  const [loadingUnit, setLoadingUnit] = useState(null)
  const [error, setError] = useState(null)
  const [modelInfo, setModelInfo] = useState(null)
  const [riskFilter, setRiskFilter] = useState(null)

  const runPrediction = useCallback(async (readings) => {
    const res = await fetch(`${API_BASE}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ readings }),
    })
    if (!res.ok) throw new Error(`Prediction failed (${res.status})`)
    return res.json()
  }, [])

  const predictUnit = useCallback(
    async (unit) => {
      setLoadingUnit(unit.unit_number)
      try {
        const data = await runPrediction(unit.readings)
        setPredictions((prev) => ({ ...prev, [unit.unit_number]: data }))
      } catch (e) {
        setError(e.message)
      } finally {
        setLoadingUnit(null)
      }
    },
    [runPrediction]
  )

  useEffect(() => {
    async function load() {
      try {
        const [fleetRes, infoRes] = await Promise.all([
          fetch(`${API_BASE}/sample-fleet`),
          fetch(`${API_BASE}/model-info`),
        ])
        if (!fleetRes.ok) throw new Error('Could not load fleet data')
        const fleetData = await fleetRes.json()
        setFleet(fleetData)
        if (infoRes.ok) setModelInfo(await infoRes.json())

        if (fleetData.length > 0) {
          setSelectedUnit(fleetData[0].unit_number)
        }
        fleetData.forEach((u) => predictUnit(u))
      } catch (e) {
        setError(e.message)
      }
    }
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const selected = fleet.find((u) => u.unit_number === selectedUnit)

  return (
    <div className="app">
      <header className="app__header">
        <div>
          <h1 className="app__title">Fleet RUL Monitor</h1>
          <p className="app__subtitle mono">
            turbofan remaining-useful-life prediction · c-mapss pipeline
          </p>
        </div>
        {modelInfo && (
          <div className="app__model-badge mono">
            model: {modelInfo.best_model} · RUL cap: {modelInfo.rul_cap}c
          </div>
        )}
      </header>

      {error && (
        <div className="app__error mono">
          {error} — is the backend running on :8000?
        </div>
      )}

      <FleetSummary
        predictions={predictions}
        activeFilter={riskFilter}
        onFilterChange={setRiskFilter}
      />

      <main className="app__body">
        <aside className="app__sidebar">
          <FleetList
            fleet={fleet}
            predictions={predictions}
            selectedUnit={selectedUnit}
            onSelect={setSelectedUnit}
            riskFilter={riskFilter}
          />
        </aside>
        <section className="app__main">
          <EngineDetail
            unit={selected}
            prediction={selected ? predictions[selected.unit_number] : null}
            loading={selected ? loadingUnit === selected.unit_number : false}
            onPredict={runPrediction}
          />
        </section>
      </main>
    </div>
  )
}
