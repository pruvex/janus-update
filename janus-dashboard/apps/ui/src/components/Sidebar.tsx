import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, History, BarChart3, AlertCircle, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { path: '/', label: 'Active', icon: LayoutDashboard },
  { path: '/kpi', label: 'KPI', icon: BarChart3 },
  { path: '/history', label: 'History', icon: History },
  { path: '/error-history', label: 'Error History', icon: AlertCircle },
]

export function Sidebar({ onRefresh }: { onRefresh: () => void }) {
  const location = useLocation()

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-6 border-b border-border">
        <h1 className="text-xl font-bold text-foreground">Janus Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">Backlog Overview</p>
      </div>
      
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-border space-y-3">
        <button
          onClick={onRefresh}
          className="w-full flex items-center gap-2 px-4 py-2 rounded-lg bg-accent hover:bg-accent/80 text-accent-foreground transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          <span className="text-sm font-medium">Refresh Data</span>
        </button>
        <div className="text-xs text-muted-foreground">
          <p>Read-only Dashboard</p>
          <p className="mt-1">Local API: http://127.0.0.1:3001</p>
        </div>
      </div>
    </aside>
  )
}
