import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import KnowledgeCenter from './components/KnowledgeCenter';

declare global {
  interface Window {
    openJanusKnowledge?: (documentId?: number) => void;
  }
}

const ReactKnowledgeBridge: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [documentId, setDocumentId] = useState<number | undefined>(undefined);

  useEffect(() => {
    const openFromBridge = (docId?: number | null) => {
      const isToggleIntent = docId === null || typeof docId === 'undefined';

      if (isToggleIntent) {
        setVisible((prev) => !prev);
        setDocumentId(undefined);
        return;
      }

      setDocumentId(docId);
      setVisible(true);
    };

    const handleOpenEvent = (event: Event) => {
      const customEvent = event as CustomEvent<{ documentId?: number | null }>;
      openFromBridge(customEvent.detail?.documentId);
    };

    window.openJanusKnowledge = openFromBridge;
    window.addEventListener('open-knowledge-center', handleOpenEvent);

    const legacyModal = document.getElementById('knowledge-center-modal') as HTMLElement | null;
    if (legacyModal) {
      legacyModal.style.display = 'none';
    }

    console.log('React Knowledge bridge mounted.');

    return () => {
      window.removeEventListener('open-knowledge-center', handleOpenEvent);
      if (window.openJanusKnowledge === openFromBridge) {
        delete window.openJanusKnowledge;
      }
    };
  }, []);

  return (
    <KnowledgeCenter
      visible={visible}
      onClose={() => setVisible(false)}
      initialDocumentId={documentId}
    />
  );
};

const mountId = 'janus-react-knowledge-bridge-root';
let mount = document.getElementById(mountId);

if (!mount) {
  mount = document.createElement('div');
  mount.id = mountId;
  document.body.appendChild(mount);
}

createRoot(mount).render(<ReactKnowledgeBridge />);
