import { useState } from 'react'
import ConsentScreen from './screens/ConsentScreen'
import CaptureScreen from './screens/CaptureScreen'
import ResultsScreen from './screens/ResultsScreen'

export default function App() {
  const [screen, setScreen] = useState('consent')
  const [skinVision, setSkinVision] = useState(null)
  const [regimen, setRegimen] = useState(null)

  function handleConsentAccepted() {
    setScreen('capture')
  }

  function handleAnalysisComplete(skinVisionResult, regimenResult) {
    setSkinVision(skinVisionResult)
    setRegimen(regimenResult)
    setScreen('results')
  }

  function handleRestart() {
    setSkinVision(null)
    setRegimen(null)
    setScreen('consent')
  }

  return (
    <div className="min-h-screen bg-brand-black text-brand-offwhite flex flex-col">
      {screen === 'consent' && (
        <ConsentScreen onAccept={handleConsentAccepted} />
      )}
      {screen === 'capture' && (
        <CaptureScreen onComplete={handleAnalysisComplete} />
      )}
      {screen === 'results' && (
        <ResultsScreen
          skinVision={skinVision}
          regimen={regimen}
          onRestart={handleRestart}
        />
      )}
    </div>
  )
}
