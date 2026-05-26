/**
 * Startup Telemetry Logger for Electron Main Process
 * 
 * Provides structured logging for startup phases and IO events with error handling and log rotation.
 * Only active in development context.
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class StartupTelemetryLogger {
  /**
   * Initialize the logger with configuration.
   * 
   * @param {Object} config - Configuration object
   * @param {boolean} config.enabled - Whether logging is enabled
   * @param {string} config.logFilePath - Path to the log file
   * @param {number} config.maxFileSizeBytes - Maximum file size before rotation
   * @param {number} config.maxBackupFiles - Number of backup files to keep
   */
  constructor(config) {
    this.enabled = config.enabled;
    this.logFilePath = config.logFilePath;
    this.maxFileSizeBytes = config.maxFileSizeBytes;
    this.maxBackupFiles = config.maxBackupFiles;
    
    this.currentRunId = null;
    this.runStartTime = null;
    this.phases = [];
    this.ioEvents = [];
    this.loggingDisabled = false;
  }

  /**
   * Start a new startup run.
   * 
   * @returns {string} Unique run ID for this startup
   */
  startRun() {
    if (!this.enabled || this.loggingDisabled) {
      return '';
    }

    this.currentRunId = crypto.randomUUID();
    this.runStartTime = Date.now();
    this.phases = [];
    this.ioEvents = [];

    return this.currentRunId;
  }

  /**
   * Log a phase with duration and metadata.
   * 
   * @param {string} phaseName - Name of the phase
   * @param {number} durationMs - Duration of the phase in milliseconds
   * @param {Object} metadata - Optional metadata dictionary
   */
  logPhase(phaseName, durationMs, metadata = {}) {
    if (!this.enabled || this.loggingDisabled) {
      return;
    }

    this.phases.push({
      name: phaseName,
      duration_ms: durationMs,
      metadata: metadata
    });
  }

  /**
   * Log an IO event.
   * 
   * @param {string} eventType - Type of IO event (e.g., "read", "write", "delete")
   * @param {string} filePath - File or directory path
   * @param {number} durationMs - Duration of the IO operation in milliseconds
   */
  logIOEvent(eventType, filePath, durationMs) {
    if (!this.enabled || this.loggingDisabled) {
      return;
    }

    this.ioEvents.push({
      event_type: eventType,
      path: filePath,
      duration_ms: durationMs
    });
  }

  /**
   * End the current run and write the log block.
   *
   * @param {boolean} success - Whether the startup completed successfully
   * @param {string} errorMessage - Optional error message if startup failed
   */
  endRun(success = true, errorMessage = null) {
    if (!this.enabled || this.loggingDisabled) {
      return;
    }

    if (this.currentRunId === null || this.runStartTime === null) {
      return;
    }

    const totalDurationMs = Date.now() - this.runStartTime;

    // Try to read npm_start and backend_startup_start markers to calculate total time
    let npmStart = null;
    let backendStartupStart = null;
    try {
      if (fs.existsSync(this.logFilePath)) {
        const logContent = fs.readFileSync(this.logFilePath, 'utf8');
        const lines = logContent.trim().split('\n');

        // Find the most recent npm_start marker
        for (let i = lines.length - 1; i >= 0; i--) {
          try {
            const line = lines[i];
            if (line.trim()) {
              const parsed = JSON.parse(line);
              if (parsed.marker === 'npm_start') {
                npmStart = new Date(parsed.timestamp).getTime();
                break;
              }
            }
          } catch (e) {
            // Skip invalid JSON lines
          }
        }

        // Find the most recent backend_startup_start marker
        for (let i = lines.length - 1; i >= 0; i--) {
          try {
            const line = lines[i];
            if (line.trim()) {
              const parsed = JSON.parse(line);
              if (parsed.marker === 'backend_startup_start') {
                backendStartupStart = new Date(parsed.timestamp).getTime();
                break;
              }
            }
          } catch (e) {
            // Skip invalid JSON lines
          }
        }
      }
    } catch (e) {
      console.error('[Startup Telemetry] Failed to read backend startup marker:', e);
    }

    // Calculate total duration from npm start and backend startup if available
    let totalDurationFromNpmStart = totalDurationMs;
    let totalDurationFromBackendStart = totalDurationMs;

    if (npmStart) {
      totalDurationFromNpmStart = Date.now() - npmStart;
    }

    if (backendStartupStart) {
      totalDurationFromBackendStart = Date.now() - backendStartupStart;
    }

    const logBlock = {
      run_id: this.currentRunId,
      timestamp: new Date().toISOString(),
      total_duration_ms: totalDurationMs,
      total_duration_from_npm_start_ms: totalDurationFromNpmStart,
      npm_start_detected: npmStart !== null,
      total_duration_from_backend_start_ms: totalDurationFromBackendStart,
      backend_startup_start_detected: backendStartupStart !== null,
      phases: this.phases,
      io_events: this.ioEvents,
      success: success,
      error_message: errorMessage
    };

    this._writeLogBlock(logBlock);

    // Reset state
    this.currentRunId = null;
    this.runStartTime = null;
    this.phases = [];
    this.ioEvents = [];
  }

  /**
   * Write the log block to the log file with rotation.
   * 
   * @param {Object} logBlock - Log block to write
   * @private
   */
  _writeLogBlock(logBlock) {
    try {
      // Ensure directory exists
      const logDir = path.dirname(this.logFilePath);
      if (logDir && !fs.existsSync(logDir)) {
        try {
          fs.mkdirSync(logDir, { recursive: true });
        } catch (e) {
          this.loggingDisabled = true;
          console.error('[Startup Telemetry] Failed to create log directory:', e);
          return;
        }
      }

      // Check file size and rotate if needed
      if (fs.existsSync(this.logFilePath)) {
        try {
          const stats = fs.statSync(this.logFilePath);
          if (stats.size >= this.maxFileSizeBytes) {
            this._rotateLogFile();
          }
        } catch (e) {
          this.loggingDisabled = true;
          console.error('[Startup Telemetry] Failed to check file size:', e);
          return;
        }
      }

      // Write log block
      const logLine = JSON.stringify(logBlock) + '\n';
      fs.appendFileSync(this.logFilePath, logLine, 'utf8');

    } catch (e) {
      this.loggingDisabled = true;
      console.error('[Startup Telemetry] Failed to write log block:', e);
    }
  }

  /**
   * Rotate the log file by renaming with timestamp and cleaning up old backups.
   * @private
   */
  _rotateLogFile() {
    try {
      // Generate timestamp for backup filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
      const logDir = path.dirname(this.logFilePath);
      const logName = path.basename(this.logFilePath);
      const backupName = `${logName}.${timestamp}`;
      const backupPath = path.join(logDir, backupName);

      // Rename current file to backup
      if (fs.existsSync(this.logFilePath)) {
        fs.renameSync(this.logFilePath, backupPath);
      }

      // Clean up old backup files
      this._cleanupOldBackups(logDir, logName);

    } catch (e) {
      this.loggingDisabled = true;
      console.error('[Startup Telemetry] Failed to rotate log file:', e);
    }
  }

  /**
   * Clean up old backup files, keeping only maxBackupFiles.
   * 
   * @param {string} logDir - Directory containing log files
   * @param {string} logName - Base name of the log file
   * @private
   */
  _cleanupOldBackups(logDir, logName) {
    try {
      // List all backup files
      const backupPattern = `${logName}.`;
      const files = fs.readdirSync(logDir);
      const backupFiles = [];

      for (const filename of files) {
        if (filename.startsWith(backupPattern) && filename !== logName) {
          const filePath = path.join(logDir, filename);
          if (fs.statSync(filePath).isFile()) {
            backupFiles.push({
              path: filePath,
              mtime: fs.statSync(filePath).mtime.getTime()
            });
          }
        }
      }

      // Sort by modification time (oldest first)
      backupFiles.sort((a, b) => a.mtime - b.mtime);

      // Delete oldest files if we have too many
      while (backupFiles.length >= this.maxBackupFiles) {
        const oldest = backupFiles.shift();
        try {
          fs.unlinkSync(oldest.path);
        } catch (e) {
          console.error('[Startup Telemetry] Failed to delete old backup:', e);
        }
      }

    } catch (e) {
      console.error('[Startup Telemetry] Failed to cleanup old backups:', e);
    }
  }
}

/**
 * Check if running in development context.
 *
 * @returns {boolean} True if in dev context, False otherwise
 */
function isDevContext() {
  // Check for explicit dev mode flag
  if (process.env.JANUS_DEV_MODE === 'true') {
    return true;
  }

  // Check for NODE_ENV
  if (process.env.NODE_ENV === 'development') {
    return true;
  }

  return false;
}

/**
 * Get custom log directory path based on environment.
 *
 * @returns {string} Path to the custom log directory
 */
function getDocumentsFolderPath() {
  const { app } = require('electron');
  const fs = require('fs');

  // Check if we're in production (packaged) or development
  const isProduction = app.isPackaged;

  if (isProduction) {
    // Production: AppData\Roaming\Janus Projekt\logs
    const prodLogDir = path.join(app.getPath('userData'), 'logs');

    try {
      if (!fs.existsSync(prodLogDir)) {
        fs.mkdirSync(prodLogDir, { recursive: true });
      }
      return prodLogDir;
    } catch (e) {
      // Fallback to userData folder
      return app.getPath('userData');
    }
  } else {
    // Development: C:\KI\Janus-Projekt\documentation\Startup log
    const devLogDir = 'C:\\KI\\Janus-Projekt\\documentation\\Startup log';

    try {
      if (!fs.existsSync(devLogDir)) {
        fs.mkdirSync(devLogDir, { recursive: true });
      }
      return devLogDir;
    } catch (e) {
      // Fallback to documents folder
      return app.getPath('documents');
    }
  }
}

/**
 * Get startup telemetry configuration.
 * 
 * @param {string} logFileName - Name of the log file (default: janus_startup_telemetry.log)
 * @param {number} maxFileSizeMb - Maximum file size in MB before rotation (default: 10)
 * @param {number} maxBackupFiles - Number of backup files to keep (default: 5)
 * @returns {Object} Configuration object
 */
function getStartupTelemetryConfig(
  logFileName = 'janus_startup_telemetry.log',
  maxFileSizeMb = 10,
  maxBackupFiles = 5
) {
  const enabled = isDevContext();

  let logFilePath = '';
  let maxFileSizeBytes = 0;

  if (enabled) {
    try {
      const docsPath = getDocumentsFolderPath();
      logFilePath = path.join(docsPath, logFileName);
      maxFileSizeBytes = maxFileSizeMb * 1024 * 1024; // Convert MB to bytes
    } catch (e) {
      console.error('[Startup Telemetry] Failed to get documents path:', e);
      // Fall back to disabled state
    }
  }

  return {
    enabled,
    log_file_path: logFilePath,
    max_file_size_bytes: maxFileSizeBytes,
    max_backup_files: maxBackupFiles
  };
}

module.exports = {
  StartupTelemetryLogger,
  isDevContext,
  getDocumentsFolderPath,
  getStartupTelemetryConfig
};
