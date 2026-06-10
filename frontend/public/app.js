const TARGET_RATE = 16000;
const BARGE_IN_RMS = 0.03;
const BARGE_IN_FRAMES = 4;

const toggleBtn = document.getElementById("toggleBtn");
const toneSelect = document.getElementById("toneSelect");
const statusEl = document.getElementById("status");
const englishPane = document.getElementById("englishPane");
const hindiPane = document.getElementById("hindiPane");
const latencyEl = document.getElementById("latency");

let ws = null;
let audioContext = null;
let mediaStream = null;
let processor = null;
let running = false;
let currentAudio = null;
let playbackQueue = [];
let loudFrames = 0;

async function getWsUrl() {
  const res = await fetch("/config");
  const cfg = await res.json();
  return cfg.wsUrl;
}

function setStatus(text, cls) {
  statusEl.textContent = text;
  statusEl.className = `status ${cls}`;
}

function appendLine(pane, text) {
  const p = document.createElement("p");
  p.textContent = text;
  pane.appendChild(p);
  pane.scrollTop = pane.scrollHeight;
}

function floatToPcm(sample) {
  const clamped = Math.max(-1, Math.min(1, sample));
  return clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
}

function downsample(input, inputRate) {
  if (inputRate <= TARGET_RATE) {
    const output = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      output[i] = floatToPcm(input[i]);
    }
    return output;
  }

  // Average each source window so high frequencies are low-passed out
  // instead of aliasing into the speech band (which wrecks ASR accuracy).
  const ratio = inputRate / TARGET_RATE;
  const length = Math.floor(input.length / ratio);
  const output = new Int16Array(length);
  for (let i = 0; i < length; i++) {
    const start = Math.floor(i * ratio);
    const end = Math.min(input.length, Math.floor((i + 1) * ratio));
    let sum = 0;
    let count = 0;
    for (let j = start; j < end; j++) {
      sum += input[j];
      count++;
    }
    output[i] = floatToPcm(count > 0 ? sum / count : 0);
  }
  return output;
}

function frameRms(input) {
  let sum = 0;
  for (let i = 0; i < input.length; i++) sum += input[i] * input[i];
  return Math.sqrt(sum / input.length);
}

function stopPlayback() {
  playbackQueue = [];
  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }
  setStatus("Listening", "listening");
}

function bargeIn() {
  stopPlayback();
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "barge_in" }));
  }
}

function playNext() {
  if (currentAudio || playbackQueue.length === 0) return;
  const b64 = playbackQueue.shift();
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const url = URL.createObjectURL(new Blob([bytes], { type: "audio/mpeg" }));
  currentAudio = new Audio(url);
  setStatus("Speaking Hindi", "speaking");
  currentAudio.onended = () => {
    URL.revokeObjectURL(url);
    currentAudio = null;
    if (playbackQueue.length > 0) {
      playNext();
    } else if (running) {
      setStatus("Listening", "listening");
    }
  };
  currentAudio.play();
}

function handleMessage(event) {
  const msg = JSON.parse(event.data);
  if (msg.type === "transcript") {
    appendLine(englishPane, msg.text);
  } else if (msg.type === "translation") {
    appendLine(hindiPane, msg.text);
  } else if (msg.type === "audio") {
    playbackQueue.push(msg.data);
    playNext();
    const l = msg.latency_ms;
    latencyEl.textContent = `Latency — ASR: ${l.asr}ms · Translation: ${l.translation}ms · TTS: ${l.tts}ms · Total: ${l.total}ms`;
  } else if (msg.type === "error") {
    appendLine(englishPane, `[error] ${msg.message}`);
  }
}

async function start() {
  const wsUrl = await getWsUrl();
  ws = new WebSocket(wsUrl);
  ws.onmessage = handleMessage;
  ws.onclose = () => running && stop();

  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });

  ws.send(JSON.stringify({ type: "config", tone: toneSelect.value }));

  mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      channelCount: 1,
    },
  });
  try {
    audioContext = new AudioContext({ sampleRate: TARGET_RATE });
  } catch (_) {
    audioContext = new AudioContext();
  }
  if (audioContext.state === "suspended") {
    await audioContext.resume();
  }
  const source = audioContext.createMediaStreamSource(mediaStream);
  processor = audioContext.createScriptProcessor(4096, 1, 1);

  processor.onaudioprocess = (e) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const input = e.inputBuffer.getChannelData(0);
    if (currentAudio) {
      loudFrames = frameRms(input) >= BARGE_IN_RMS ? loudFrames + 1 : 0;
      if (loudFrames >= BARGE_IN_FRAMES) {
        loudFrames = 0;
        bargeIn();
      }
    }
    const pcm = downsample(input, audioContext.sampleRate);
    ws.send(pcm.buffer);
  };

  source.connect(processor);
  processor.connect(audioContext.destination);

  running = true;
  toggleBtn.textContent = "Stop";
  toggleBtn.classList.add("active");
  setStatus("Listening", "listening");
}

function stop() {
  running = false;
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "flush" }));
    setTimeout(() => ws && ws.close(), 3000);
  }
  if (processor) processor.disconnect();
  if (audioContext) audioContext.close();
  if (mediaStream) mediaStream.getTracks().forEach((t) => t.stop());
  processor = null;
  audioContext = null;
  mediaStream = null;
  toggleBtn.textContent = "Start Listening";
  toggleBtn.classList.remove("active");
  setStatus("Idle", "idle");
}

toggleBtn.addEventListener("click", () => {
  if (running) {
    stop();
  } else {
    start().catch((err) => {
      setStatus("Error", "idle");
      appendLine(englishPane, `[error] ${err.message || err}`);
    });
  }
});

toneSelect.addEventListener("change", () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type: "config", tone: toneSelect.value }));
  }
});
