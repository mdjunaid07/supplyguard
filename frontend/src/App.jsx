import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import ScanHistory from './pages/ScanHistory'
import PackagesPage from './pages/PackagesPage'
import PackageDetailPage from './pages/PackageDetailPage'

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <Routes>
          <Route path="/"                   element={<Dashboard />} />
          <Route path="/scans"              element={<ScanHistory />} />
          <Route path="/scans/:id"          element={<ScanHistory />} />
          <Route path="/packages"           element={<PackagesPage />} />
          <Route path="/packages/:name"     element={<PackageDetailPage />} />
        </Routes>
      </main>
    </div>
  )
}
