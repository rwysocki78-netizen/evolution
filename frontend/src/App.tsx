import { HashRouter, Routes, Route } from 'react-router-dom'
import Setup from './screens/Setup'
import Simulation from './screens/Simulation'
import Results from './screens/Results'

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<Setup />} />
        <Route path="/simulation/:id" element={<Simulation />} />
        <Route path="/results/:id" element={<Results />} />
      </Routes>
    </HashRouter>
  )
}
