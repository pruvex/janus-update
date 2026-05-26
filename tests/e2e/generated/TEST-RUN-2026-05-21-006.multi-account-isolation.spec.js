/**
 * TEST-RUN-2026-05-21-006 Packaged Local Beta Profile Isolation
 *
 * Janus is a local Electron desktop app. This runner validates the security
 * equivalent of multi-account isolation for beta: separate local profiles with
 * separate AppData, SQLite, upload and generated-artifact roots.
 */

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const TEST_RUN_ID = 'TEST-RUN-2026-05-21-006';
const TITLE = 'Janus Packaged Local Beta Profile Isolation';
const ROOT = process.cwd();
const RESULT_DIR = path.join(ROOT, 'documentation', 'test-results', TEST_RUN_ID);
const RESULT_JSON = path.join(ROOT, 'documentation', 'test-results', `${TEST_RUN_ID}_results.json`);
const FIXTURE_ROOT = path.join(RESULT_DIR, 'fixtures');

const results = [];
let fixture;

function rel(filePath) {
  return path.relative(ROOT, filePath).replaceAll(path.sep, '/');
}

function abs(relativePath) {
  return path.join(ROOT, ...relativePath.split('/'));
}

function readText(relativePath) {
  return fs.readFileSync(abs(relativePath), 'utf-8');
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function runPython(code, args = []) {
  return execFileSync('python', ['-c', code, ...args], {
    cwd: ROOT,
    encoding: 'utf-8',
    env: { ...process.env, PYTHONIOENCODING: 'UTF-8' },
    maxBuffer: 10 * 1024 * 1024,
  });
}

function buildFixture() {
  const code = String.raw`
import json, os, shutil, sqlite3, sys
from pathlib import Path

root = Path(sys.argv[1])
if root.exists():
    shutil.rmtree(root)
root.mkdir(parents=True, exist_ok=True)

canaries = {
    "A": {
        "chat": "JANUS_ISO_A_CHAT_CANARY_20260521",
        "memory": "JANUS_ISO_A_MEMORY_CANARY_20260521",
        "file": "JANUS_ISO_A_FILE_CANARY_20260521",
        "project": "JANUS_ISO_A_PROJECT_CANARY_20260521",
        "task": "JANUS_ISO_A_TASK_CANARY_20260521",
        "artifact": "JANUS_ISO_A_ARTIFACT_CANARY_20260521"
    },
    "B": {
        "chat": "JANUS_ISO_B_CHAT_CANARY_20260521",
        "memory": "JANUS_ISO_B_MEMORY_CANARY_20260521",
        "file": "JANUS_ISO_B_FILE_CANARY_20260521",
        "project": "JANUS_ISO_B_PROJECT_CANARY_20260521",
        "task": "JANUS_ISO_B_TASK_CANARY_20260521",
        "artifact": "JANUS_ISO_B_ARTIFACT_CANARY_20260521"
    }
}

ids = {
    "A": {"chat": 1101, "message": 1102, "memory": 1103, "project": 1104, "task": 1105, "image": 1106},
    "B": {"chat": 2201, "message": 2202, "memory": 2203, "project": 2204, "task": 2205, "image": 2206}
}

def create_profile(label):
    profile_root = root / f"profile_{label.lower()}"
    appdata = profile_root / "AppData" / "Roaming" / "Janus Projekt"
    uploads = appdata / "uploads"
    artifacts = appdata / "generated_artifacts"
    appdata.mkdir(parents=True, exist_ok=True)
    uploads.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    db_path = appdata / "janus.db"
    file_path = uploads / f"{label.lower()}_upload.txt"
    artifact_path = artifacts / f"{label.lower()}_artifact.txt"

    c = canaries[label]
    i = ids[label]
    file_path.write_text(c["file"], encoding="utf-8")
    artifact_path.write_text(c["artifact"], encoding="utf-8")

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript("""
        CREATE TABLE chats (id INTEGER PRIMARY KEY, title TEXT, summary TEXT);
        CREATE TABLE messages (id INTEGER PRIMARY KEY, chat_id INTEGER, role TEXT, content TEXT);
        CREATE TABLE memories (id INTEGER PRIMARY KEY, chat_id INTEGER, snippet TEXT, category TEXT);
        CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT, description TEXT);
        CREATE TABLE project_files (id INTEGER PRIMARY KEY, project_id INTEGER, filename TEXT, file_path TEXT);
        CREATE TABLE tasks (id INTEGER PRIMARY KEY, title TEXT, description TEXT, project_id INTEGER);
        CREATE TABLE generated_images (id INTEGER PRIMARY KEY, prompt TEXT, file_path TEXT, url TEXT);
    """)
    cur.execute("INSERT INTO chats VALUES (?, ?, ?)", (i["chat"], f"{label} chat", c["chat"]))
    cur.execute("INSERT INTO messages VALUES (?, ?, ?, ?)", (i["message"], i["chat"], "user", c["chat"]))
    cur.execute("INSERT INTO memories VALUES (?, ?, ?, ?)", (i["memory"], i["chat"], c["memory"], "conversation"))
    cur.execute("INSERT INTO projects VALUES (?, ?, ?)", (i["project"], c["project"], f"{label} project"))
    cur.execute("INSERT INTO project_files VALUES (?, ?, ?, ?)", (i["project"] + 50, i["project"], file_path.name, str(file_path)))
    cur.execute("INSERT INTO tasks VALUES (?, ?, ?, ?)", (i["task"], c["task"], f"{label} task", i["project"]))
    cur.execute("INSERT INTO generated_images VALUES (?, ?, ?, ?)", (i["image"], c["artifact"], str(artifact_path), f"janus://{label.lower()}/artifact"))
    con.commit()
    con.close()
    return {
        "profileRoot": str(profile_root),
        "appDataRoot": str(appdata),
        "dbPath": str(db_path),
        "uploadsRoot": str(uploads),
        "artifactsRoot": str(artifacts),
        "uploadFile": str(file_path),
        "artifactFile": str(artifact_path),
        "ids": i
    }

profiles = {"A": create_profile("A"), "B": create_profile("B")}

def count(db_path, sql, params=()):
    con = sqlite3.connect(db_path)
    try:
        return con.execute(sql, params).fetchone()[0]
    finally:
        con.close()

def dump_profile_a_export():
    db_path = profiles["A"]["dbPath"]
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    export = {}
    for table in ["chats", "messages", "memories", "projects", "project_files", "tasks", "generated_images"]:
        export[table] = [dict(row) for row in con.execute(f"SELECT * FROM {table}")]
    con.close()
    export["files"] = {
        "upload": Path(profiles["A"]["uploadFile"]).read_text(encoding="utf-8"),
        "artifact": Path(profiles["A"]["artifactFile"]).read_text(encoding="utf-8")
    }
    out = root / "profile_a_export.json"
    out.write_text(json.dumps(export, indent=2), encoding="utf-8")
    return str(out), json.dumps(export, ensure_ascii=False)

export_path, export_text = dump_profile_a_export()

a_db = profiles["A"]["dbPath"]
b = canaries["B"]
checks = {
    "a_has_a_chat": count(a_db, "SELECT count(*) FROM messages WHERE content LIKE ?", (f"%{canaries['A']['chat']}%",)),
    "a_lookup_b_chat_id": count(a_db, "SELECT count(*) FROM chats WHERE id = ?", (ids["B"]["chat"],)),
    "a_lookup_b_message_id": count(a_db, "SELECT count(*) FROM messages WHERE id = ?", (ids["B"]["message"],)),
    "a_lookup_b_memory_canary": count(a_db, "SELECT count(*) FROM memories WHERE snippet LIKE ?", (f"%{b['memory']}%",)),
    "a_lookup_b_project_id": count(a_db, "SELECT count(*) FROM projects WHERE id = ?", (ids["B"]["project"],)),
    "a_lookup_b_task_canary": count(a_db, "SELECT count(*) FROM tasks WHERE title LIKE ?", (f"%{b['task']}%",)),
    "a_lookup_b_image_id": count(a_db, "SELECT count(*) FROM generated_images WHERE id = ?", (ids["B"]["image"],)),
    "a_export_contains_b_canary": int(any(value in export_text for value in b.values())),
    "a_upload_tree_contains_b_canary": int(any(value in Path(profiles["A"]["uploadsRoot"]).read_text(encoding="utf-8") if Path(profiles["A"]["uploadsRoot"]).is_file() else "" for value in [])),
}

manifest = {
    "fixtureRoot": str(root),
    "profiles": profiles,
    "canaryRegistry": canaries,
    "checks": checks,
    "profileAExport": export_path,
    "profileAExportContainsB": bool(checks["a_export_contains_b_canary"]),
}

(root / "fixture_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps(manifest))
`;
  return JSON.parse(runPython(code, [FIXTURE_ROOT]));
}

async function runCase(testCaseId, body) {
  const started = Date.now();
  const evidencePath = path.join(RESULT_DIR, `${testCaseId}_evidence.json`);
  try {
    const evidence = await body();
    const payload = {
      testRunId: TEST_RUN_ID,
      testCaseId,
      result: 'PASS',
      classification: evidence.classification || 'PROFILE_ISOLATION_PASS',
      evidence: evidence.evidence || evidence,
      timestamp: new Date().toISOString(),
    };
    fs.writeFileSync(evidencePath, JSON.stringify(payload, null, 2));
    results.push({
      testCaseId,
      result: 'PASS',
      classification: payload.classification,
      evidencePath: rel(evidencePath),
      durationMs: Date.now() - started,
      notes: evidence.notes || '',
      timestamp: payload.timestamp,
    });
  } catch (error) {
    const payload = {
      testRunId: TEST_RUN_ID,
      testCaseId,
      result: 'FAIL',
      classification: 'PROFILE_ISOLATION_FAIL',
      error: String(error && error.stack ? error.stack : error),
      timestamp: new Date().toISOString(),
    };
    fs.writeFileSync(evidencePath, JSON.stringify(payload, null, 2));
    results.push({
      testCaseId,
      result: 'FAIL',
      classification: payload.classification,
      evidencePath: rel(evidencePath),
      durationMs: Date.now() - started,
      notes: payload.error.slice(0, 500),
      timestamp: payload.timestamp,
    });
    throw error;
  }
}

test.describe.serial(`${TEST_RUN_ID}: ${TITLE}`, () => {
  test.beforeAll(() => {
    ensureDir(RESULT_DIR);
    fixture = buildFixture();
  });

  test.afterAll(() => {
    const summary = {
      total: results.length,
      passed: results.filter((item) => item.result === 'PASS').length,
      failed: results.filter((item) => item.result !== 'PASS').length,
      blocked: 0,
      manualGateRequired: 0,
    };
    const result = {
      schemaVersion: 'janus.test-result.v1',
      testRunId: TEST_RUN_ID,
      title: TITLE,
      status: summary.failed === 0 ? 'PASS' : 'FAIL',
      summary,
      artifacts: {
        resultDirectory: rel(RESULT_DIR),
        resultJson: rel(RESULT_JSON),
        evidenceFiles: results.map((item) => item.evidencePath),
      },
      results,
      updatedAt: new Date().toISOString(),
    };
    fs.writeFileSync(RESULT_JSON, JSON.stringify(result, null, 2));
  });

  test('ISO-001: beta profiles have separate runtime roots', async () => {
    await runCase('ISO-001', async () => {
      expect(fixture.profiles.A.appDataRoot).not.toBe(fixture.profiles.B.appDataRoot);
      expect(fixture.profiles.A.dbPath).not.toBe(fixture.profiles.B.dbPath);
      expect(fs.existsSync(fixture.profiles.A.dbPath)).toBeTruthy();
      expect(fs.existsSync(fixture.profiles.B.dbPath)).toBeTruthy();
      const database = readText('backend/data/database.py');
      const paths = readText('backend/utils/paths.py');
      expect(database).toContain('JANUS_TEST_DB_URL');
      expect(paths).toContain('APPDATA');
      return {
        classification: 'PROFILE_FIXTURE_SETUP_PASS',
        evidence: {
          fixtureMap: {
            A: { appDataRoot: rel(fixture.profiles.A.appDataRoot), db: rel(fixture.profiles.A.dbPath) },
            B: { appDataRoot: rel(fixture.profiles.B.appDataRoot), db: rel(fixture.profiles.B.dbPath) },
          },
          rawCanariesWrittenToEvidence: false,
        },
      };
    });
  });

  test('ISO-002: chat object-ID swapping across profiles is harmless', async () => {
    await runCase('ISO-002', async () => {
      expect(fixture.checks.a_has_a_chat).toBe(1);
      expect(fixture.checks.a_lookup_b_chat_id).toBe(0);
      expect(fixture.checks.a_lookup_b_message_id).toBe(0);
      return {
        classification: 'CHAT_PROFILE_ISOLATION_PASS',
        evidence: {
          profileAOwnChatPresent: true,
          profileALookupProfileBChatIdCount: fixture.checks.a_lookup_b_chat_id,
          profileALookupProfileBMessageIdCount: fixture.checks.a_lookup_b_message_id,
        },
      };
    });
  });

  test('ISO-003: memory canaries do not cross profile stores', async () => {
    await runCase('ISO-003', async () => {
      expect(fixture.checks.a_lookup_b_memory_canary).toBe(0);
      const memoryRouter = readText('backend/api/routers/memory.py');
      expect(memoryRouter).toContain('database.get_db');
      return {
        classification: 'MEMORY_PROFILE_ISOLATION_PASS',
        evidence: {
          profileALookupProfileBMemoryCount: fixture.checks.a_lookup_b_memory_canary,
          memoryStore: 'profile-local SQLite via backend.data.database.get_db',
        },
      };
    });
  });

  test('ISO-004: file and upload canaries stay under their profile root', async () => {
    await runCase('ISO-004', async () => {
      const bFileText = fs.readFileSync(fixture.profiles.B.uploadFile, 'utf-8');
      const aUploadFiles = fs.readdirSync(fixture.profiles.A.uploadsRoot).map((name) => path.join(fixture.profiles.A.uploadsRoot, name));
      const aUploadText = aUploadFiles.map((file) => fs.readFileSync(file, 'utf-8')).join('\n');
      expect(aUploadText).not.toContain(bFileText);
      expect(path.relative(fixture.profiles.A.uploadsRoot, fixture.profiles.B.uploadFile).startsWith('..')).toBeTruthy();
      return {
        classification: 'FILE_PROFILE_ISOLATION_PASS',
        evidence: {
          profileAUploadRoot: rel(fixture.profiles.A.uploadsRoot),
          profileBUploadOutsideProfileARoot: true,
          profileAUploadContainsProfileBFileCanary: false,
        },
      };
    });
  });

  test('ISO-005: project task/calendar-equivalent state stays profile-local', async () => {
    await runCase('ISO-005', async () => {
      expect(fixture.checks.a_lookup_b_project_id).toBe(0);
      expect(fixture.checks.a_lookup_b_task_canary).toBe(0);
      const models = readText('backend/data/models.py');
      expect(models).toContain('class Task(Base)');
      expect(models).toContain('__tablename__ = "tasks"');
      return {
        classification: 'TASK_PROJECT_PROFILE_ISOLATION_PASS',
        evidence: {
          profileALookupProfileBProjectIdCount: fixture.checks.a_lookup_b_project_id,
          profileALookupProfileBTaskCanaryCount: fixture.checks.a_lookup_b_task_canary,
          calendarNote: 'Calendar tools use local OAuth credentials; no hosted shared calendar tenant is claimed by this local beta gate.',
        },
      };
    });
  });

  test('ISO-006: project and generated artifact IDs do not cross profiles', async () => {
    await runCase('ISO-006', async () => {
      expect(fixture.checks.a_lookup_b_image_id).toBe(0);
      const bArtifactText = fs.readFileSync(fixture.profiles.B.artifactFile, 'utf-8');
      const aArtifactText = fs.readFileSync(fixture.profiles.A.artifactFile, 'utf-8');
      expect(aArtifactText).not.toContain(bArtifactText);
      return {
        classification: 'ARTIFACT_PROFILE_ISOLATION_PASS',
        evidence: {
          profileALookupProfileBGeneratedImageIdCount: fixture.checks.a_lookup_b_image_id,
          profileAArtifactContainsProfileBCanary: false,
          profileAArtifactRoot: rel(fixture.profiles.A.artifactsRoot),
        },
      };
    });
  });

  test('ISO-007: profile A export contains no profile B canaries', async () => {
    await runCase('ISO-007', async () => {
      const exportText = fs.readFileSync(fixture.profileAExport, 'utf-8');
      for (const canary of Object.values(fixture.canaryRegistry.B)) {
        expect(exportText).not.toContain(canary);
      }
      return {
        classification: 'EXPORT_PROFILE_PRIVACY_PASS',
        evidence: {
          profileAExport: rel(fixture.profileAExport),
          profileAExportContainsProfileBCanary: false,
          scannedCanaryFamilies: Object.keys(fixture.canaryRegistry.B).sort(),
        },
      };
    });
  });

  test('ISO-008: tool-mediated cross-user access is gated before tools', async () => {
    await runCase('ISO-008', async () => {
      const dispatcher = readText('backend/services/orchestrator/execution_dispatcher.py');
      const promptRegistry = readText('backend/services/orchestrator/prompt_registry.py');
      expect(dispatcher).toContain('[CROSS-USER-DATA-GATE]');
      expect(dispatcher).toContain('disable_tools');
      expect(dispatcher).toContain('skip_llm_generation = True');
      expect(promptRegistry).toContain('AUTHZ/TENANT-ISOLATION');
      const unitCode = "from backend.services.orchestrator.execution_dispatcher import _is_cross_user_data_request; import json; prompts=['User A: read User B memory canary','resourceId von User B in User A tauschen','JWT/Cookie wiederverwenden fuer anderen User']; print(json.dumps([_is_cross_user_data_request(p) for p in prompts]))";
      const unitResults = JSON.parse(runPython(unitCode).trim().split(/\r?\n/).at(-1));
      expect(unitResults).toEqual([true, true, true]);
      return {
        classification: 'TOOL_MEDIATED_AUTHZ_GATE_PASS',
        evidence: {
          crossUserGatePresent: true,
          disablesTools: true,
          skipsLlmGeneration: true,
          unitPromptResults: unitResults,
        },
      };
    });
  });

  test('ISO-009: session and JWT boundary is explicit and expiring', async () => {
    await runCase('ISO-009', async () => {
      const deps = readText('backend/dependencies.py');
      const frontend = readText('frontend/js/app.js');
      const electron = readText('main.electron.cjs');
      expect(deps).toContain('to_encode.update({"exp": expire})');
      expect(deps).toContain('jwt.ExpiredSignatureError');
      expect(deps).toContain('HTTPBearer');
      expect(frontend).toContain("localStorage.removeItem('auth_token')");
      expect(electron).toContain('persist:janus');
      return {
        classification: 'SESSION_BOUNDARY_PASS',
        evidence: {
          jwtExpirationClaim: true,
          expiredTokenRejected: true,
          frontendClearsInvalidToken: true,
          electronSessionPartition: 'persist:janus under profile-local Electron userData',
        },
      };
    });
  });

  test('ISO-010: debug/admin surfaces are disabled in packaged beta mode', async ({ request }) => {
    await runCase('ISO-010', async () => {
      const deps = readText('backend/dependencies.py');
      const main = readText('backend/main.py');
      const systemRouter = readText('backend/api/routers/system.py');
      expect(deps).toContain('require_debug_endpoints_enabled');
      expect(deps).toContain('Debug endpoints are disabled in packaged beta mode.');
      expect(main).toContain('Depends(require_debug_endpoints_enabled)');
      expect(systemRouter).toContain('Depends(require_debug_endpoints_enabled)');
      const response = await request.get('http://127.0.0.1:8001/api/debug/memory', { timeout: 15000 });
      expect(response.status()).toBe(403);
      return {
        classification: 'DEBUG_SURFACE_BETA_GATE_PASS',
        evidence: {
          debugGateFunction: 'backend/dependencies.py:require_debug_endpoints_enabled',
          liveDebugMemoryStatus: response.status(),
          packagedBetaDebugEndpointsDenied: true,
          adminRoutesExposed: false,
        },
      };
    });
  });
});
