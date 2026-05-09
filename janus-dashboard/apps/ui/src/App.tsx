import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { ActiveView } from './views/ActiveView'
import { HistoryView } from './views/HistoryView'
import { KPIView } from './views/KPIView'
import { RoutingHealthView } from './views/RoutingHealthView'

function App() {
  const handleRefresh = () => {
    window.location.reload()
  }

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-background">
        <Sidebar onRefresh={handleRefresh} />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<ActiveView />} />
            <Route path="/active" element={<ActiveView />} />
            <Route path="/history" element={<HistoryView />} />
            <Route path="/kpi" element={<KPIView />} />
            <Route path="/routing" element={<RoutingHealthView />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
