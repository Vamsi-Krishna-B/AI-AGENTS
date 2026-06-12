import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Dashboard } from './pages/Dashboard'
import { PipelineMonitor } from './pages/PipelineMonitor'
import { ScriptEditor } from './pages/ScriptEditor'
import { Thumbnail } from './pages/Thumbnail'
import { Calendar } from './pages/Calendar'
import { Analytics } from './pages/Analytics'
import { Settings } from './pages/Settings'

const NAV_LINKS = [
  { to: '/', label: '🏠 Dashboard' },
  { to: '/pipeline', label: '⚙️ Pipeline' },
  { to: '/script', label: '📝 Script' },
  { to: '/thumbnail', label: '🖼️ Thumbnail' },
  { to: '/calendar', label: '📅 Calendar' },
  { to: '/analytics', label: '📊 Analytics' },
  { to: '/settings', label: '🔧 Settings' },
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <aside className="w-56 flex-shrink-0 bg-white shadow-lg flex flex-col py-6 px-3 gap-1">
          <div className="px-3 mb-6">
            <h1 className="text-lg font-bold text-purple-700">YT Manager</h1>
            <p className="text-xs text-gray-400">AI Agents Dashboard</p>
          </div>
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isActive
                    ? 'bg-purple-100 text-purple-800'
                    : 'text-gray-600 hover:bg-gray-100'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </aside>
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/pipeline" element={<PipelineMonitor />} />
            <Route path="/pipeline/:jobId" element={<PipelineMonitor />} />
            <Route path="/script" element={<ScriptEditor />} />
            <Route path="/thumbnail" element={<Thumbnail />} />
            <Route path="/calendar" element={<Calendar />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
