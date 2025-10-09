import { API_BASE_URL } from './config.js';

let ttsEnabled = false;
let ttsVoice = null;
let ttsSpeed = 1.0;
let ttsPreset = null; // NEU
let currentAudio = null;

/**
 * Load available TTS voices from the backend
 */
export async function loadTTSVoices(lang = null) {
  try {
    const url = lang ? `${API_BASE_URL}/api/tts/voices?lang=${encodeURIComponent(lang)}` : `${API_BASE_URL}/api/tts/voices`;
    const response = await fetch(url);
    if (!response.ok) throw new Error("Failed to load voices");
    const data = await response.json();
    return data.voices;
  } catch (error) {
    console.error("Error loading TTS voices:", error);
    return [];
  }
}

/**
 * Synthesize speech from text
 */
export async function synthesizeSpeech({ text, lang, voice_id, speed = 1.0, format = "mp3", provider = null, preset = null }) {
  try {
    const params = new URLSearchParams({ 
      text, 
      lang, 
      speed: String(speed), 
      fmt: format 
    });
    
    if (voice_id) params.append("voice_id", voice_id); // NEU: voice_id statt voice
    if (provider) params.append("provider", provider);
    if (preset) params.append("preset", preset); // NEU
    
    const response = await fetch(`${API_BASE_URL}/api/tts/synthesize?${params.toString()}`, { 
      method: "POST" 
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "TTS synthesis failed");
    }
    
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  } catch (error) {
    console.error("TTS synthesis error:", error);
    throw error;
  }
}

/**
 * Play text as speech
 */
export async function speakText(text, lang = "de") {
  if (!ttsEnabled) return;
  
  // Stop any currently playing audio
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  
  try {
    const audioUrl = await synthesizeSpeech({
      text,
      lang,
      voice_id: ttsVoice, // NEU: voice_id statt voice
      speed: ttsSpeed,
      format: "mp3",
      preset: ttsPreset // NEU
    });
    
    currentAudio = new Audio(audioUrl);
    currentAudio.play();
    
    currentAudio.addEventListener('ended', () => {
      URL.revokeObjectURL(audioUrl);
      currentAudio = null;
    });
  } catch (error) {
    console.error("Error speaking text:", error);
  }
}

/**
 * Enable/disable TTS
 */
export function setTTSEnabled(enabled) {
  ttsEnabled = enabled;
  localStorage.setItem('tts_enabled', enabled ? 'true' : 'false');
  
  // Update button state
  const ttsBtn = document.getElementById('tts-toggle-btn');
  if (ttsBtn) {
    ttsBtn.classList.toggle('active', enabled);
    ttsBtn.title = enabled ? 'TTS aktiviert' : 'TTS deaktiviert';
  }
}

/**
 * Get TTS enabled state
 */
export function isTTSEnabled() {
  return ttsEnabled;
}

/**
 * Set TTS voice
 */
export function setTTSVoice(voice) {
  ttsVoice = voice;
  localStorage.setItem('tts_voice', voice);
}

/**
 * Set TTS speed
 */
export function setTTSSpeed(speed) {
  ttsSpeed = speed;
  localStorage.setItem('tts_speed', String(speed));
}

/**
 * Initialize TTS system
 */
export async function initTTS() {
  // Load saved settings
  const savedEnabled = localStorage.getItem('tts_enabled') === 'true';
  const savedVoice = localStorage.getItem('tts_voice');
  const savedSpeed = parseFloat(localStorage.getItem('tts_speed')) || 1.0;
  const savedPreset = localStorage.getItem('tts_preset') || "assistenz"; // NEU
  
  ttsEnabled = savedEnabled;
  ttsVoice = savedVoice;
  ttsSpeed = savedSpeed;
  ttsPreset = savedPreset; // NEU
  
  // Set up toggle button
  const ttsBtn = document.getElementById('tts-toggle-btn');
  if (ttsBtn) {
    ttsBtn.classList.toggle('active', ttsEnabled);
    ttsBtn.addEventListener('click', () => {
      setTTSEnabled(!ttsEnabled);
    });
  }
}
