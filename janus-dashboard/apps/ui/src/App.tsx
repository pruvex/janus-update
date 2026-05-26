import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { ActiveView } from './views/ActiveView'
import { HistoryView } from './views/HistoryView'
import { KPIView } from './views/KPIView'
import { ErrorHistoryView } from './views/ErrorHistoryView'
import { TestResultsView } from './views/TestResultsView'
import { TestOverviewView } from './views/TestOverviewView'
import { TestSuiteView } from './views/TestSuiteView'

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
            <Route path="/test-results" element={<TestResultsView />} />
            <Route path="/test-overview" element={<TestOverviewView />} />
            <Route path="/testsuite" element={<TestSuiteView />} />
            <Route path="/error-history" element={<ErrorHistoryView />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
