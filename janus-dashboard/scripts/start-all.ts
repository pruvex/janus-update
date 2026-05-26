import { spawn, exec, execSync } from 'child_process'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import { platform } from 'os'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const rootDir = join(__dirname, '..')
const apiDir = join(rootDir, 'apps', 'api')
const desktopDir = join(rootDir, 'apps', 'desktop')
const uiDir = join(rootDir, 'apps', 'ui')

console.log('🚀 Starting Janus Dashboard...')

try {
  execSync('npm run sync:backlog', { cwd: rootDir, stdio: 'inherit' })
} catch (err) {
  console.warn('Backlog snapshot sync failed, dashboard API will use fallback handling.')
}

// Function to forcefully kill processes by port on Windows
function forceKillPortWindows(port: number) {
  if (platform() !== 'win32') return
  try {
    // Find the PID holding the port
    const output = execSync(`netstat -ano | findstr :${port}`).toString()
    const lines = output.split('\n').filter(line => line.includes('LISTENING'))
    for (const line of lines) {
      const parts = line.trim().split(/\s+/)
      const pid = parts[parts.length - 1]
      if (pid && pid !== '0') {
        console.log(`Force killing PID ${pid} on port ${port}...`)
        execSync(`taskkill /F /T /PID ${pid}`)
      }
    }
  } catch (err) {
    // Port already free or command failed, ignore
  }
}

// Start API server
const apiProcess = spawn('npm', ['run', 'dev'], {
  cwd: apiDir,
  shell: true,
  stdio: 'inherit',
  detached: false,
})

apiProcess.on('error', (err) => {
  console.error('Failed to start API:', err)
  process.exit(1)
})

// Wait for API to be ready
setTimeout(() => {
  console.log('✅ API should be ready, starting UI...')
  
  // Start UI dev server
  const uiProcess = spawn('npm', ['run', 'dev'], {
    cwd: uiDir,
    shell: true,
    stdio: 'inherit',
    detached: false,
  })

  uiProcess.on('error', (err) => {
    console.error('Failed to start UI:', err)
    process.exit(1)
  })

  // Wait for UI to be ready
  setTimeout(() => {
    console.log('✅ UI should be ready, starting Electron...')
    
    // Start Electron
    const electronProcess = spawn('npm', ['run', 'start'], {
      cwd: desktopDir,
      shell: true,
      stdio: 'inherit',
      detached: false,
    })

    electronProcess.on('error', (err) => {
      console.error('Failed to start Electron:', err)
      process.exit(1)
    })

    // Function to forcefully kill a process tree on Windows
    const forceKill = (pid: number) => {
      if (platform() === 'win32') {
        // Use taskkill with /T (kill process tree) and /F (force)
        exec(`taskkill /PID ${pid} /T /F`, (err) => {
          if (err) {
            // If taskkill fails, try SIGKILL as fallback
            try {
              process.kill(pid, 'SIGKILL')
            } catch (e) {
              // Ignore if process already dead
            }
          }
        })
      } else {
        try {
          process.kill(pid, 'SIGKILL')
        } catch (e) {
          // Ignore
        }
      }
    }

    // Handle shutdown
    const shutdown = () => {
      console.log('Shutting down...')
      // Try standard kill first
      if (electronProcess.pid) forceKill(electronProcess.pid)
      if (uiProcess.pid) forceKill(uiProcess.pid)
      if (apiProcess.pid) forceKill(apiProcess.pid)
      
      // Force kill by port to ensure no orphans are left
      if (platform() === 'win32') {
        forceKillPortWindows(5174) // Vite (Dashboard UI)
        forceKillPortWindows(3001) // Local API
      }
      
      // Remove all listeners to prevent hanging
      process.removeAllListeners()
      // Force the main Node process to exit so the terminal closes
      setTimeout(() => {
        process.exit(0)
      }, 1000)
    }

    process.on('SIGINT', shutdown)
    process.on('SIGTERM', shutdown)

    // Kill background processes when Electron exits (window closed)
    electronProcess.on('exit', () => {
      console.log('Electron exited, shutting down background processes...')
      // Try standard kill first
      if (uiProcess.pid) forceKill(uiProcess.pid)
      if (apiProcess.pid) forceKill(apiProcess.pid)
      
      // Force kill by port to ensure no orphans are left
      if (platform() === 'win32') {
        forceKillPortWindows(5174) // Vite (Dashboard UI)
        forceKillPortWindows(3001) // Local API
      }
      
      // Remove all listeners to prevent hanging
      process.removeAllListeners()
      // Force the main Node process to exit so the terminal closes
      setTimeout(() => {
        process.exit(0)
      }, 1000)
    })
  }, 5000)
}, 2000)
