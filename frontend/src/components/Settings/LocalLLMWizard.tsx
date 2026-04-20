import React, { useEffect, useMemo, useRef, useState } from 'react';

type OllamaCheckResponse = {
  installed: boolean;
  running: boolean;
};

type RecommendedModel = {
  name: string;
  id: string;
  size_gb: number;
  description: string;
  use_case: string;
  tools_supported?: boolean;
};

type HardwareResponse = {
  hardware: {
    ram_gb: number;
    cpu_cores: number;
    gpu: {
      name: string;
      type: string;
      vram_gb?: number | null;
      note?: string;
    };
    platform: string;
  };
  profile: string;
  recommended_models: RecommendedModel[];
  ollama_install_url: string;
};

type PullResponse = {
  status: string;
  model?: string;
  message?: string;
};

type PullStatusResponse = {
  status: 'idle' | 'queued' | 'running' | 'completed' | 'failed';
  message?: string;
  model: string;
  progress?: number;
  error?: string | null;
};

type LocalModelsResponse = {
  provider: string;
  models: Array<{
    id: string;
    name?: string;
    node_name?: string;
    base_model_id?: string;
    node_id?: string;
    update_available?: boolean;
    tools_supported?: boolean;
    size_gb?: number | null;
  }>;
};

type OllamaNode = {
  id: string;
  name: string;
  url: string;
  active: boolean;
  reachable?: boolean;
};

type OllamaNodesResponse = {
  nodes: OllamaNode[];
  active_node_id?: string;
  ollama_base_url?: string;
};

const API_BASE_URL = 'http://localhost:8001/api/local-llm';
const NODES_POLL_INTERVAL_VISIBLE_MS = 30000;
const NODES_POLL_INTERVAL_HIDDEN_MS = 60000;

type WizardPhase =
  | 'idle'
  | 'checking'
  | 'install_needed'
  | 'analyzing'
  | 'ready'
  | 'pulling'
  | 'done'
  | 'error';

const normalizedModelTokens = (modelId: string): string[] => {
  const normalized = String(modelId || '').trim().toLowerCase();
  if (!normalized) {
    return [];
  }
  const base = normalized.split(':')[0];
  if (!base || base === normalized) {
    return [normalized];
  }
  return [normalized, base];
};

const LocalLLMWizard: React.FC = () => {
  const [phase, setPhase] = useState<WizardPhase>('idle');
  const [checkResult, setCheckResult] = useState<OllamaCheckResponse | null>(null);
  const [analysis, setAnalysis] = useState<HardwareResponse | null>(null);
  const [installedModelIds, setInstalledModelIds] = useState<Set<string>>(new Set());
  const [installedModelMeta, setInstalledModelMeta] = useState<
    Array<{
      id: string;
      name?: string;
      node_name?: string;
      base_model_id?: string;
      node_id?: string;
      update_available?: boolean;
      tools_supported?: boolean;
      size_gb?: number | null;
    }>
  >([]);
  const [isBootstrapping, setIsBootstrapping] = useState<boolean>(true);
  const [activePullModel, setActivePullModel] = useState<string>('');
  const [activeDeleteModel, setActiveDeleteModel] = useState<string>('');
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [pullProgress, setPullProgress] = useState<number>(0);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [ollamaNodes, setOllamaNodes] = useState<OllamaNode[]>([]);
  const [newNodeName, setNewNodeName] = useState<string>('');
  const [newNodeUrl, setNewNodeUrl] = useState<string>('http://localhost:11434');
  const [newNodeUrlEdited, setNewNodeUrlEdited] = useState<boolean>(false);
  const newNodeUrlEditedRef = useRef<boolean>(false);
  const newNodeUrlInputRef = useRef<HTMLInputElement | null>(null);
  const [isSavingConnection, setIsSavingConnection] = useState<boolean>(false);
  const nodeModelCounts = useMemo(() => {
    return installedModelMeta.reduce<Record<string, number>>((acc, entry) => {
      const nodeId = entry.node_id;
      if (!nodeId) return acc;
      acc[nodeId] = (acc[nodeId] || 0) + 1;
      return acc;
    }, {});
  }, [installedModelMeta]);
  const [downloadNodeSelection, setDownloadNodeSelection] = useState<Record<string, string>>({});
  const downloadMetaRef = useRef<{ downloadKey: string; modelId: string } | null>(null);
  const [activeNodeActionId, setActiveNodeActionId] = useState<string>('');
  const progressTimerRef = useRef<number | null>(null);
  const pollTimerRef = useRef<number | null>(null);
  const pollingRef = useRef<boolean>(false);
  const pollInFlightRef = useRef<boolean>(false);
  const statusRequestAbortRef = useRef<AbortController | null>(null);
  const nodesPollTimerRef = useRef<number | null>(null);
  const nodesPollActiveRef = useRef<boolean>(false);
  const nodesPollInFlightRef = useRef<boolean>(false);
  const nodesRequestAbortRef = useRef<AbortController | null>(null);
  const nodesRescheduleRef = useRef<() => void>(() => {});
  const installNodeOptions = useMemo(() => {
    return ollamaNodes.map((node) => ({ id: node.id, label: node.name }));
  }, [ollamaNodes]);
  const defaultDownloadNodeId = useMemo(() => {
    if (!ollamaNodes.length) return '';
    const active = ollamaNodes.find((node) => node.active);
    return active?.id ?? ollamaNodes[0]?.id ?? '';
  }, [ollamaNodes]);

  useEffect(() => {
    return () => {
      if (progressTimerRef.current !== null) {
        window.clearInterval(progressTimerRef.current);
      }
      if (pollTimerRef.current !== null) {
        window.clearTimeout(pollTimerRef.current);
      }
      if (nodesPollTimerRef.current !== null) {
        window.clearTimeout(nodesPollTimerRef.current);
      }
      pollingRef.current = false;
      pollInFlightRef.current = false;
      if (statusRequestAbortRef.current) {
        statusRequestAbortRef.current.abort();
      }
      statusRequestAbortRef.current = null;
      if (nodesRequestAbortRef.current) {
        nodesRequestAbortRef.current.abort();
      }
      nodesRequestAbortRef.current = null;
      nodesPollActiveRef.current = false;
      nodesPollInFlightRef.current = false;
    };
  }, []);

  const canStart = !isBootstrapping && (phase === 'idle' || phase === 'install_needed' || phase === 'error' || phase === 'done');

  const buildNodeQualifiedModelId = (modelId: string, nodeId?: string): string => {
    const normalizedNodeId = (nodeId || '').trim();
    if (!normalizedNodeId) {
      return '';
    }
    return `${modelId}@${normalizedNodeId}`;
  };

  const isModelInstalled = (modelId: string, installed: Set<string>, nodeId?: string): boolean => {
    const nodeQualified = buildNodeQualifiedModelId(modelId, nodeId);
    if (nodeQualified) {
      return installed.has(nodeQualified);
    }

    const installedTokens = new Set<string>();
    installed.forEach((installedId) => {
      normalizedModelTokens(installedId).forEach((token) => installedTokens.add(token));
    });
    return normalizedModelTokens(modelId).some((token) => installedTokens.has(token));
  };

  const hasUpdateAvailable = (modelId: string): boolean => {
    const modelTokens = new Set(normalizedModelTokens(modelId));
    return installedModelMeta.some((entry) => {
      if (!entry.update_available) {
        return false;
      }
      const entryTokens = normalizedModelTokens(entry.id);
      return entryTokens.some((token) => modelTokens.has(token));
    });
  };

  const resolveInstalledModelId = (modelId: string): string => {
    const modelTokens = new Set(normalizedModelTokens(modelId));
    const match = installedModelMeta.find((entry) => {
      const entryTokens = normalizedModelTokens(entry.id);
      return entryTokens.some((token) => modelTokens.has(token));
    });
    return match?.id || modelId;
  };

  const isSkillReady = (modelId: string, fallbackFlag?: boolean): boolean => {
    if (typeof fallbackFlag === 'boolean') {
      return fallbackFlag;
    }
    const modelTokens = new Set(normalizedModelTokens(modelId));
    const match = installedModelMeta.find((entry) => {
      const entryTokens = normalizedModelTokens(entry.id);
      return entryTokens.some((token) => modelTokens.has(token));
    });
    return Boolean(match?.tools_supported);
  };

  const isRecommendedInstalledModel = (installedId: string): boolean => {
    if (!analysis) {
      return false;
    }
    const installedTokens = new Set(normalizedModelTokens(installedId));
    return analysis.recommended_models.some((recommended) =>
      normalizedModelTokens(recommended.id).some((token) => installedTokens.has(token)),
    );
  };

  const hardwareSummary = useMemo(() => {
    if (!analysis) return '';
    const gpuName = analysis.hardware.gpu?.name || 'Unbekannt';
    return `Dein PC hat ${analysis.hardware.ram_gb} GB RAM und eine ${gpuName}. Wir haben die optimalen Modelle für dich gefunden.`;
  }, [analysis]);

  const sortedInstalledModels = useMemo(() => {
    const sorted = [...installedModelMeta];
    sorted.sort((a, b) => {
      const aRecommended = isRecommendedInstalledModel(a.id);
      const bRecommended = isRecommendedInstalledModel(b.id);
      if (aRecommended !== bRecommended) {
        return aRecommended ? -1 : 1;
      }
      return a.id.localeCompare(b.id, 'de', { sensitivity: 'base' });
    });
    return sorted;
  }, [installedModelMeta, analysis]);

  const syncInstalledModels = async (): Promise<Set<string>> => {
    try {
      const modelsRes = await fetch(`${API_BASE_URL}/models`);
      if (!modelsRes.ok) {
        return installedModelIds;
      }
      const payload: LocalModelsResponse = await modelsRes.json();
      const nextModels = payload.models || [];
      const nextInstalled = new Set(nextModels.map((m) => m.id));
      setInstalledModelMeta(nextModels);
      setInstalledModelIds(nextInstalled);
      return nextInstalled;
    } catch {
      return installedModelIds;
    }
  };

  const deleteModel = async (modelId: string, modelName: string) => {
    const installedId = resolveInstalledModelId(modelId);
    const confirmed = window.confirm(
      `Moechtest du das Modell ${installedId || modelName} wirklich von der Festplatte loeschen?`,
    );
    if (!confirmed) {
      return;
    }

    setActiveDeleteModel(installedId);
    setStatusMessage(`Loesche ${installedId}...`);
    try {
      const deleteRes = await fetch(`${API_BASE_URL}/models/${encodeURIComponent(installedId)}`, {
        method: 'DELETE',
      });
      if (!deleteRes.ok) {
        const detail = await deleteRes.json().catch(() => ({}));
        throw new Error(detail.detail || `Loeschen fehlgeschlagen (${deleteRes.status})`);
      }

      await syncInstalledModels();
      setStatusMessage(`Modell ${installedId} wurde geloescht.`);
      emitModelsUpdated();
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Loeschen fehlgeschlagen.');
    } finally {
      setActiveDeleteModel('');
    }
  };

  const emitModelsUpdated = () => {
    document.dispatchEvent(new CustomEvent('models-updated'));
    window.dispatchEvent(new CustomEvent('models-updated'));
  };

  const markNodeUrlEdited = () => {
    setNewNodeUrlEdited(true);
    newNodeUrlEditedRef.current = true;
  };

  const loadNodes = async (signal?: AbortSignal): Promise<OllamaNode[]> => {
    let localController: AbortController | null = null;
    if (!signal) {
      if (nodesRequestAbortRef.current) {
        nodesRequestAbortRef.current.abort();
      }
      localController = new AbortController();
      nodesRequestAbortRef.current = localController;
      signal = localController.signal;
    }

    try {
      const nodesRes = await fetch(`${API_BASE_URL}/nodes`, { signal });
      if (!nodesRes.ok) {
        return ollamaNodes;
      }
      const payload: OllamaNodesResponse = await nodesRes.json();
      const nextNodes = payload.nodes || [];
      setOllamaNodes(nextNodes);
      const activeNode = nextNodes.find((node) => node.active);
      if (activeNode && !newNodeUrlEditedRef.current) {
        setNewNodeUrl(activeNode.url || 'http://localhost:11434');
      }
      return nextNodes;
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return ollamaNodes;
      }
      return ollamaNodes;
    } finally {
      if (localController && nodesRequestAbortRef.current === localController) {
        nodesRequestAbortRef.current = null;
      }
    }
  };

  useEffect(() => {
    const bootstrapWizard = async () => {
      setIsBootstrapping(true);
      await loadNodes();
      setPhase('checking');
      setStatusMessage('Pruefe Status...');

      try {
        const checkRes = await fetch(`${API_BASE_URL}/check`);
        if (!checkRes.ok) {
          throw new Error(`Check fehlgeschlagen (${checkRes.status})`);
        }
        const checkData: OllamaCheckResponse = await checkRes.json();
        setCheckResult(checkData);

        if (!checkData.installed || !checkData.running) {
          setPhase('install_needed');
          setStatusMessage('Ollama nicht gefunden oder nicht gestartet.');
          return;
        }

        const installedNow = await syncInstalledModels();
        void fetch(`${API_BASE_URL}/updates/refresh`, { method: 'POST' }).catch(() => undefined);
        if (installedNow.size > 0) {
          setPhase('analyzing');
          setStatusMessage('Lade Modell-Dashboard...');

          const analysisRes = await fetch(`${API_BASE_URL}/recommendations`);
          if (!analysisRes.ok) {
            throw new Error(`Systemanalyse fehlgeschlagen (${analysisRes.status})`);
          }
          const analysisData: HardwareResponse = await analysisRes.json();
          setAnalysis(analysisData);
          setPhase('ready');
          setStatusMessage('Lokale Modelle erkannt. Dashboard bereit.');
          return;
        }

        setPhase('idle');
        setStatusMessage('Lokales LLM bereit. Starte die Einrichtung fuer Modell-Empfehlungen.');
        await syncInstalledModels();
      } catch (error) {
        setPhase('install_needed');
        setStatusMessage(error instanceof Error ? error.message : 'Initialer Status-Check fehlgeschlagen.');
      } finally {
        setIsBootstrapping(false);
      }
    };

    void bootstrapWizard();
  }, []);

  useEffect(() => {
    nodesPollActiveRef.current = true;

    const getCurrentPollInterval = () =>
      document.visibilityState === 'visible' ? NODES_POLL_INTERVAL_VISIBLE_MS : NODES_POLL_INTERVAL_HIDDEN_MS;

    const clearExistingTimer = () => {
      if (nodesPollTimerRef.current !== null) {
        window.clearTimeout(nodesPollTimerRef.current);
        nodesPollTimerRef.current = null;
      }
    };

    async function pollNodes() {
      if (!nodesPollActiveRef.current) {
        return;
      }
      nodesPollInFlightRef.current = true;
      try {
        await loadNodes();
      } finally {
        nodesPollInFlightRef.current = false;
      }
      scheduleNextNodePoll();
    }

    function scheduleNextNodePoll() {
      if (!nodesPollActiveRef.current) {
        return;
      }
      clearExistingTimer();
      const delay = getCurrentPollInterval();
      nodesPollTimerRef.current = window.setTimeout(() => {
        nodesPollTimerRef.current = null;
        if (!nodesPollActiveRef.current) {
          return;
        }
        if (document.visibilityState !== 'visible' || nodesPollInFlightRef.current) {
          scheduleNextNodePoll();
          return;
        }
        void pollNodes();
      }, delay);
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState !== 'visible' || !nodesPollActiveRef.current) {
        return;
      }
      if (nodesPollInFlightRef.current) {
        return;
      }
      clearExistingTimer();
      void pollNodes();
    };

    nodesRescheduleRef.current = () => {
      if (!nodesPollActiveRef.current) {
        return;
      }
      clearExistingTimer();
      scheduleNextNodePoll();
    };

    scheduleNextNodePoll();
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      nodesPollActiveRef.current = false;
      nodesPollInFlightRef.current = false;
      clearExistingTimer();
      if (nodesRequestAbortRef.current) {
        nodesRequestAbortRef.current.abort();
        nodesRequestAbortRef.current = null;
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const saveNode = async () => {
    const trimmedName = newNodeName.trim();
    const currentInputUrl = newNodeUrlInputRef.current?.value ?? newNodeUrl;
    const trimmedUrl = currentInputUrl.trim();
    if (!trimmedName || !trimmedUrl) {
      setStatusMessage('Bitte Name und URL fuer den Node eingeben.');
      return;
    }

    setNewNodeUrl(trimmedUrl);
    markNodeUrlEdited();
    setIsSavingConnection(true);
    setStatusMessage('Speichere Node-Profil...');

    try {
      const saveRes = await fetch(`${API_BASE_URL}/nodes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: trimmedName, url: trimmedUrl }),
      });
      const payload = await saveRes.json().catch(() => ({}));
      if (!saveRes.ok) {
        const detail = payload && typeof payload === 'object' ? payload.detail : undefined;
        throw new Error(detail || `Node speichern fehlgeschlagen (${saveRes.status})`);
      }

      setNewNodeName('');
      await loadNodes();
      const nodeReachable = Boolean(
        payload && typeof payload === 'object' && payload.node && payload.node.reachable,
      );
      if (nodeReachable) {
        void syncInstalledModels();
      }
      const status = payload && typeof payload === 'object' ? String((payload as { status?: string }).status || '') : '';
      if (status === 'updated') {
        setStatusMessage('Node-URL existierte bereits: Name wurde aktualisiert.');
      } else if (status === 'exists') {
        setStatusMessage('Node mit dieser URL existiert bereits.');
      } else {
        setStatusMessage('Node gespeichert. Du kannst ihn jetzt aktivieren.');
      }
      window.dispatchEvent(new CustomEvent('models-updated'));
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Node speichern fehlgeschlagen.');
    } finally {
      setIsSavingConnection(false);
    }
  };

  const activateNode = async (nodeId: string, nodeName: string) => {
    setActiveNodeActionId(nodeId);
    setStatusMessage(`Aktiviere Node ${nodeName}...`);
    try {
      const res = await fetch(`${API_BASE_URL}/nodes/activate/${encodeURIComponent(nodeId)}`, {
        method: 'POST',
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `Aktivieren fehlgeschlagen (${res.status})`);
      }

      await loadNodes();
      await runCheckAndAnalyze();
      setStatusMessage(`Node ${nodeName} aktiv. Verbindung wurde neu geprueft.`);
      window.dispatchEvent(new CustomEvent('models-updated'));
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Node-Aktivierung fehlgeschlagen.');
    } finally {
      setActiveNodeActionId('');
    }
  };

  const deleteNode = async (node: OllamaNode) => {
    const confirmed = window.confirm(`Node ${node.name} wirklich loeschen?`);
    if (!confirmed) {
      return;
    }
    setActiveNodeActionId(node.id);
    try {
      const res = await fetch(`${API_BASE_URL}/nodes/${encodeURIComponent(node.id)}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `Loeschen fehlgeschlagen (${res.status})`);
      }
      await loadNodes();
      setStatusMessage(`Node ${node.name} wurde geloescht.`);
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : 'Node konnte nicht geloescht werden.');
    } finally {
      setActiveNodeActionId('');
    }
  };

  const runCheckAndAnalyze = async () => {
    setPhase('checking');
    setStatusMessage('Pruefe Ollama-Installation und Dienststatus...');

    try {
      const checkRes = await fetch(`${API_BASE_URL}/check`);
      if (!checkRes.ok) {
        throw new Error(`Check fehlgeschlagen (${checkRes.status})`);
      }
      const checkData: OllamaCheckResponse = await checkRes.json();
      setCheckResult(checkData);

      if (!checkData.installed || !checkData.running) {
        setPhase('install_needed');
        setStatusMessage('Ollama nicht gefunden oder nicht gestartet.');
        return;
      }

      setPhase('analyzing');
      setStatusMessage('Analysiere System-Ressourcen...');

      const analysisRes = await fetch(`${API_BASE_URL}/recommendations`);
      if (!analysisRes.ok) {
        throw new Error(`Systemanalyse fehlgeschlagen (${analysisRes.status})`);
      }
      const analysisData: HardwareResponse = await analysisRes.json();
      setAnalysis(analysisData);
      await syncInstalledModels();
      void fetch(`${API_BASE_URL}/updates/refresh`, { method: 'POST' }).catch(() => undefined);
      setPhase('ready');
      setStatusMessage('Systemanalyse abgeschlossen.');
    } catch (error) {
      setPhase('install_needed');
      setStatusMessage(error instanceof Error ? error.message : 'Verbindungscheck fehlgeschlagen. Du kannst trotzdem Nodes verwalten.');
    }
  };

  const resolveDownloadNode = (modelId: string) => {
    const selected = downloadNodeSelection[modelId];
    if (selected && ollamaNodes.some((node) => node.id === selected)) {
      return selected;
    }
    return defaultDownloadNodeId;
  };

  const pullModel = async (modelId: string) => {
    const nodeId = resolveDownloadNode(modelId);
    if (progressTimerRef.current !== null) {
      window.clearInterval(progressTimerRef.current);
      progressTimerRef.current = null;
    }
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    pollingRef.current = false;
    pollInFlightRef.current = false;
    setIsPolling(false);
    if (statusRequestAbortRef.current) {
      statusRequestAbortRef.current.abort();
      statusRequestAbortRef.current = null;
    }

    setActivePullModel(modelId);
    setPhase('pulling');
    setPullProgress(5);
    setStatusMessage(`Starte Download von ${modelId} im Hintergrund...`);

    progressTimerRef.current = window.setInterval(() => {
      setPullProgress((prev) => {
        if (prev >= 95) return prev;
        return prev + 2;
      });
    }, 1200);

    const finalizeAsSuccess = (message: string) => {
      if (progressTimerRef.current !== null) {
        window.clearInterval(progressTimerRef.current);
        progressTimerRef.current = null;
      }
      if (pollTimerRef.current !== null) {
        window.clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      pollingRef.current = false;
      pollInFlightRef.current = false;
      setIsPolling(false);
      if (statusRequestAbortRef.current) {
        statusRequestAbortRef.current.abort();
        statusRequestAbortRef.current = null;
      }
      setPullProgress(100);
      setInstalledModelIds((prev) => {
        const next = new Set(prev);
        next.add(modelId);
        return next;
      });
      setStatusMessage(message);
      setPhase('done');
      setActivePullModel('');
      downloadMetaRef.current = null;
      emitModelsUpdated();
      window.setTimeout(() => {
        emitModelsUpdated();
      }, 1000);
    };

    const finalizeAsError = (message: string) => {
      if (progressTimerRef.current !== null) {
        window.clearInterval(progressTimerRef.current);
        progressTimerRef.current = null;
      }
      if (pollTimerRef.current !== null) {
        window.clearTimeout(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      pollingRef.current = false;
      pollInFlightRef.current = false;
      setIsPolling(false);
      if (statusRequestAbortRef.current) {
        statusRequestAbortRef.current.abort();
        statusRequestAbortRef.current = null;
      }
      setPhase('error');
      setStatusMessage(message);
      setActivePullModel('');
      downloadMetaRef.current = null;
    };

    const runPollingStep = async (): Promise<boolean> => {
      if (!pollingRef.current || pollInFlightRef.current || isPolling) {
        return false;
      }
      pollInFlightRef.current = true;
      setIsPolling(true);
      const statusController = new AbortController();
      if (statusRequestAbortRef.current) {
        statusRequestAbortRef.current.abort();
      }
      statusRequestAbortRef.current = statusController;
      try {
        return await pollStatusOnce(statusController.signal);
      } finally {
        if (statusRequestAbortRef.current === statusController) {
          statusRequestAbortRef.current = null;
        }
        pollInFlightRef.current = false;
        setIsPolling(false);
      }
    };

    const scheduleNextPoll = () => {
      if (pollTimerRef.current !== null) {
        window.clearTimeout(pollTimerRef.current);
      }
      if (!pollingRef.current) {
        return;
      }
      pollTimerRef.current = window.setTimeout(async () => {
        if (!pollingRef.current) {
          return;
        }
        try {
          const done = await runPollingStep();
          if (!done && pollingRef.current) {
            scheduleNextPoll();
          }
        } catch (error) {
          finalizeAsError(error instanceof Error ? error.message : 'Status-Polling fehlgeschlagen.');
        }
      }, 5000);
    };

    const pollStatusOnce = async (signal: AbortSignal): Promise<boolean> => {
      const installedNow = await syncInstalledModels();
      const targetNodeId = resolveDownloadNode(modelId);
      if (isModelInstalled(modelId, installedNow, targetNodeId)) {
        if (hasUpdateAvailable(modelId)) {
          setStatusMessage(`Update fuer ${modelId} verfuegbar - lade Update...`);
        } else {
          finalizeAsSuccess(`Modell ${modelId} ist bereits installiert.`);
          return true;
        }
      }

      const statusModelId = downloadMetaRef.current?.downloadKey || modelId;
      const statusRes = await fetch(`${API_BASE_URL}/pull-status/${encodeURIComponent(statusModelId)}`, { signal });
      if (!statusRes.ok) {
        throw new Error(`Statusabfrage fehlgeschlagen (${statusRes.status})`);
      }

      const statusData: PullStatusResponse = await statusRes.json();
      if (typeof statusData.progress === 'number') {
        setPullProgress((prev) => Math.max(prev, Math.min(100, statusData.progress || 0)));
      }

      if (statusData.status === 'completed') {
        await syncInstalledModels();
        finalizeAsSuccess(statusData.message || `Modell ${modelId} erfolgreich installiert.`);
        return true;
      }

      if (statusData.status === 'failed') {
        finalizeAsError(statusData.error || statusData.message || 'Download fehlgeschlagen.');
        return true;
      }

      if (statusData.message) {
        setStatusMessage(statusData.message);
      }
      return false;
    };

    try {
      pollingRef.current = true;
      const pullRes = await fetch(`${API_BASE_URL}/pull`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId, node_id: nodeId || undefined }),
      });

      if (!pullRes.ok) {
        const detail = await pullRes.json().catch(() => ({}));
        throw new Error(detail.detail || `Download fehlgeschlagen (${pullRes.status})`);
      }

      const pullData: PullResponse = await pullRes.json();
      downloadMetaRef.current = {
        downloadKey: pullData.model || modelId,
        modelId,
      };
      setStatusMessage(pullData.message || `Download von ${modelId} wurde gestartet.`);

      const completedDirectly = await runPollingStep();
      if (completedDirectly) {
        return;
      }

      scheduleNextPoll();
    } catch (error) {
      pollingRef.current = false;
      finalizeAsError(error instanceof Error ? error.message : 'Download fehlgeschlagen.');
    }
  };

  return (
    <div className="local-llm-wizard">
      <h3>Lokales LLM (Ollama) Setup-Wizard</h3>
      <p>
        Richte lokale Modelle ohne API-Key ein. Die eigentliche Installation von Ollama erfolgt aus Sicherheitsgruenden ueber die offizielle Website.
      </p>

      <div className="local-llm-connection-settings">
        <h4>Ollama Server-Profile (Nodes)</h4>

        <div className="local-llm-node-list">
          {ollamaNodes.map((node) => {
            const isBusy = activeNodeActionId === node.id;
            const canDelete = !node.active && node.id !== 'localhost';
            const nodeModelCount = nodeModelCounts[node.id] || 0;
            const showNoModelsWarning = node.reachable && nodeModelCount === 0;
            return (
              <div key={node.id} className={`local-llm-node-row ${node.active ? 'is-active' : ''}`}>
                <div className="local-llm-node-main">
                  <label>
                    <input
                      type="radio"
                      checked={node.active}
                      onChange={() => activateNode(node.id, node.name)}
                      disabled={isBusy || isSavingConnection || isBootstrapping}
                    />
                    <span className="local-llm-node-name">{node.name}</span>
                  </label>
                  <span className="local-llm-node-url">{node.url}</span>
                  <span className="local-llm-node-count">Modelle: {nodeModelCount}</span>
                </div>
                <div className="local-llm-node-actions">
                  <span className={`local-llm-node-health ${node.reachable ? 'ok' : 'down'}`}>
                    {node.reachable ? '🟢 erreichbar' : '🔴 offline'}
                  </span>
                  {showNoModelsWarning && (
                    <span className="local-llm-node-warning">
                      Node online, aber keine Modelle installiert
                    </span>
                  )}
                  {canDelete && (
                    <button
                      className="local-llm-node-delete"
                      onClick={() => deleteNode(node)}
                      disabled={isBusy || isSavingConnection || isBootstrapping}
                    >
                      {isBusy ? '...' : 'Loeschen'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="local-llm-connection-row">
          <input
            type="text"
            value={newNodeName}
            onChange={(event) => setNewNodeName(event.target.value)}
            placeholder="Name (z.B. Gaming-PC)"
            aria-label="Node Name"
          />
          <input
            type="text"
            value={newNodeUrl}
            ref={newNodeUrlInputRef}
            onChange={(event) => {
              setNewNodeUrl(event.target.value);
              markNodeUrlEdited();
            }}
            onInput={markNodeUrlEdited}
            onPaste={markNodeUrlEdited}
            placeholder="http://192.168.178.20:11434"
            aria-label="Node URL"
          />
          <button onClick={saveNode} disabled={isSavingConnection || isBootstrapping}>
            {isSavingConnection ? 'Speichere...' : 'Node speichern'}
          </button>
        </div>
      </div>

      <div className="local-llm-wizard-actions">
        <button onClick={runCheckAndAnalyze} disabled={!canStart}>
          Lokales LLM einrichten
        </button>
      </div>

      {statusMessage && <p className="local-llm-status">{statusMessage}</p>}

      {isBootstrapping && (
        <div className="local-llm-sync-indicator">
          <span className="spinner" />
          <span>Synchronisiere lokale Modelle...</span>
        </div>
      )}

      {phase === 'checking' && <div className="local-llm-spinner">Pruefung laeuft...</div>}

      {phase === 'install_needed' && (
        <div className="local-llm-install-box">
          <p>Ollama nicht gefunden oder Dienst nicht aktiv.</p>
          <ol>
            <li>Oeffne die offizielle Download-Seite.</li>
            <li>Installiere Ollama manuell (.exe/.dmg).</li>
            <li>Starte Ollama und fuehre den Check erneut aus.</li>
          </ol>
          <a href="https://ollama.com/download" target="_blank" rel="noreferrer">
            Zu ollama.com/download
          </a>
          {checkResult && <p>Installiert: {String(checkResult.installed)} | Running: {String(checkResult.running)}</p>}
        </div>
      )}

      {phase === 'analyzing' && (
        <div className="local-llm-analysis-progress">
          <div className="bar" />
          <p>Analysiere System-Ressourcen...</p>
        </div>
      )}

      {(phase === 'ready' || phase === 'pulling' || phase === 'done') && analysis && (
        <div className="local-llm-results">
          <p className="local-llm-hardware-summary">{hardwareSummary}</p>

          <div className="local-llm-model-grid">
            {analysis.recommended_models.map((model) => {
              const isDownloading = phase === 'pulling' && activePullModel === model.id;
              const isInstalled = isModelInstalled(model.id, installedModelIds);
              const hasUpdate = hasUpdateAvailable(model.id);
              const skillReady = isSkillReady(model.id, model.tools_supported);
              const isDeleting = activeDeleteModel === resolveInstalledModelId(model.id);
              const isDisabled = (isInstalled && !hasUpdate) || phase === 'pulling';

              let buttonLabel = 'Modell herunterladen';
              let buttonClassName = 'local-llm-download-btn';
              if (isDownloading) {
                buttonLabel = `Lade herunter... ${Math.round(pullProgress)}%`;
                buttonClassName = 'local-llm-downloading-btn';
              } else if (isInstalled) {
                buttonLabel = 'Bereits installiert';
                buttonClassName = 'local-llm-model-btn installed';
                if (hasUpdate) {
                  buttonLabel = 'Update laden';
                  buttonClassName = 'local-llm-update-btn';
                }
              }

              return (
                <article key={model.id} className="local-llm-model-card">
                  <h4>{model.name}</h4>
                  {skillReady && <span className="local-llm-skill-ready-badge">Skill-Ready</span>}
                  {hasUpdate && <span className="local-llm-update-badge">Update verfuegbar</span>}
                  <p className="size">Groesse: {model.size_gb} GB</p>
                  <p>{model.description}</p>
                  <p className="use-case">Use-Case: {model.use_case}</p>
                  <div className="local-llm-model-node-target">
                    <label htmlFor={`target-${model.id}`}>Ziel-Node</label>
                    <select
                      id={`target-${model.id}`}
                      value={resolveDownloadNode(model.id)}
                      onChange={(event) => {
                        const value = event.target.value;
                        setDownloadNodeSelection((prev) => ({
                          ...prev,
                          [model.id]: value,
                        }));
                      }}
                    >
                      {ollamaNodes.map((node) => (
                        <option key={node.id} value={node.id} disabled={!node.reachable}>
                          {node.name} {node.reachable ? '' : '(offline)'}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button className={buttonClassName} onClick={() => pullModel(model.id)} disabled={isDisabled}>
                    {buttonLabel}
                  </button>

                  {isInstalled && (
                    <button
                      className="local-llm-delete-btn"
                      onClick={() => deleteModel(model.id, model.name)}
                      disabled={phase === 'pulling' || isDeleting}
                    >
                      {isDeleting ? 'Loesche...' : 'Papierkorb | Loeschen'}
                    </button>
                  )}

                  {isDownloading && (
                    <div className="local-llm-progress">
                      <div className="progress-fill" style={{ width: `${pullProgress}%` }} />
                    </div>
                  )}
                </article>
              );
            })}
          </div>

          <div className="local-llm-installed-inventory">
            <h4>Installierte Modelle verwalten</h4>

            {sortedInstalledModels.length === 0 ? (
              <p className="local-llm-installed-empty">Aktuell sind keine lokalen Modelle installiert.</p>
            ) : (
              <div className="local-llm-installed-list">
                {sortedInstalledModels.map((installedModel) => {
                  const isDeleting = activeDeleteModel === installedModel.id;
                  const isRecommended = isRecommendedInstalledModel(installedModel.id);
                  const skillReady = Boolean(installedModel.tools_supported);
                  const sizeLabel =
                    typeof installedModel.size_gb === 'number' && installedModel.size_gb > 0
                      ? `${installedModel.size_gb.toFixed(2)} GB`
                      : 'Unbekannt';

                  return (
                    <div
                      key={installedModel.id}
                      className={`local-llm-installed-row ${isRecommended ? 'local-llm-installed-row--recommended' : ''}`}
                    >
                      <div className="local-llm-installed-main">
                        <strong>{installedModel.name || installedModel.id}</strong>
                        <div className="local-llm-installed-meta">
                          {installedModel.node_name && <span className="local-llm-installed-badge">{installedModel.node_name}</span>}
                          <span className="local-llm-installed-badge">Aktiv</span>
                          {skillReady && <span className="local-llm-skill-ready-badge">Skill-Ready</span>}
                          {isRecommended && <span className="local-llm-recommended-badge">Empfohlen</span>}
                        </div>
                      </div>

                      <div className="local-llm-installed-size">{sizeLabel}</div>

                      <button
                        className="local-llm-delete-inline-btn"
                        onClick={() => deleteModel(installedModel.id, installedModel.id)}
                        disabled={phase === 'pulling' || isDeleting}
                      >
                        {isDeleting ? 'Loesche...' : 'Papierkorb | Loeschen'}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}

      {phase === 'error' && (
        <div className="local-llm-error-box">
          <p>Setup fehlgeschlagen. Bitte pruefe Ollama und versuche es erneut.</p>
        </div>
      )}
    </div>
  );
};

export default LocalLLMWizard;
