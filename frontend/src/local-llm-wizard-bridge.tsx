import React from 'react';
import { createRoot } from 'react-dom/client';
import LocalLLMWizard from './components/Settings/LocalLLMWizard';

const mountId = 'local-llm-wizard-root';
const mount = document.getElementById(mountId);

if (mount) {
  createRoot(mount).render(<LocalLLMWizard />);
  console.log('Local LLM Wizard bridge mounted.');
} else {
  console.warn('Local LLM Wizard mount point not found.');
}
