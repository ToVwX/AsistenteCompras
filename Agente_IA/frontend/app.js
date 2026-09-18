const messages = document.querySelector("#messages");
const chatForm = document.querySelector("#chatForm");
const input = document.querySelector("#messageInput");
const sendButton = document.querySelector("#sendButton");
const clearButton = document.querySelector("#clearButton");
const voiceButton = document.querySelector("#voiceButton");
const botStage = document.querySelector("#botStage");
const botStatus = document.querySelector("#botStatus");

let sessionId = localStorage.getItem("compratech-session") || crypto.randomUUID();
let voiceEnabled = localStorage.getItem("compratech-voice") !== "off";
let busy = false;

function setBotState(state) {
  const labels = {
    idle: "Listo para ayudarte",
    thinking: "Analizando tu compra...",
    speaking: "Hablando contigo...",
  };
  botStage.dataset.state = state;
  botStatus.textContent = labels[state] || labels.idle;
}

function updateVoiceButton() {
  voiceButton.classList.toggle("active", voiceEnabled);
  voiceButton.setAttribute("aria-label", voiceEnabled ? "Desactivar voz" : "Activar voz");
}

function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "user-message" : "assistant-message"}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "TÚ" : "CT";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const author = document.createElement("span");
  author.className = "message-author";
  author.textContent = role === "user" ? "Tú" : "CompraTech";
  const paragraph = document.createElement("p");
  paragraph.textContent = text;

  bubble.append(author, paragraph);
  if (role !== "user") {
    const actions = document.createElement("div");
    actions.className = "message-actions";
    const listenButton = document.createElement("button");
    listenButton.type = "button";
    listenButton.className = "speak-message";
    listenButton.textContent = "◖)) Escuchar";
    listenButton.setAttribute("aria-label", "Escuchar respuesta de CompraTech");
    listenButton.addEventListener("click", () => {
      voiceEnabled = true;
      localStorage.setItem("compratech-voice", "on");
      updateVoiceButton();
      speak(text, true);
    });
    actions.append(listenButton);
    bubble.append(actions);
  }
  article.append(avatar, bubble);
  messages.append(article);
  window.requestAnimationFrame(() => {
    messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" });
  });
  return article;
}

function showTyping() {
  const article = document.createElement("article");
  article.id = "typingMessage";
  article.className = "message assistant-message";
  article.innerHTML = '<div class="avatar">CT</div><div class="bubble"><span class="message-author">CompraTech</span><div class="typing" aria-label="Escribiendo"><i></i><i></i><i></i></div></div>';
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

function removeTyping() {
  document.querySelector("#typingMessage")?.remove();
}

async function preferredSpanishVoice() {
  if (!("speechSynthesis" in window)) return null;
  let voices = window.speechSynthesis.getVoices();
  if (!voices.length) {
    await new Promise((resolve) => {
      const timer = window.setTimeout(resolve, 900);
      window.speechSynthesis.addEventListener("voiceschanged", () => {
        window.clearTimeout(timer);
        resolve();
      }, { once: true });
    });
    voices = window.speechSynthesis.getVoices();
  }
  const normalizeLanguage = (voice) => voice.lang.toLowerCase().replace("_", "-");
  const mexicanVoices = voices.filter((voice) => {
    const name = voice.name.toLowerCase();
    return normalizeLanguage(voice) === "es-mx"
      || name.includes("mexico")
      || name.includes("méxico");
  });

  return mexicanVoices.find((voice) => voice.name.toLowerCase().includes("dalia"))
    || mexicanVoices.find((voice) => voice.name.toLowerCase().includes("jorge"))
    || mexicanVoices[0]
    || null;
}

async function speak(text, force = false) {
  if (!voiceEnabled && !force) {
    const duration = Math.min(7000, Math.max(1800, text.length * 22));
    setBotState("speaking");
    window.setTimeout(() => setBotState("idle"), duration);
    return;
  }

  if (!("speechSynthesis" in window)) {
    botStatus.textContent = "La voz no está disponible en este navegador";
    return;
  }

  window.speechSynthesis.cancel();
  const selectedVoice = await preferredSpanishVoice();

  const utterance = new SpeechSynthesisUtterance(text);
  // Fuerza el motor de voz a pronunciar con la configuración regional de México.
  utterance.lang = "es-MX";
  if (selectedVoice) {
    utterance.voice = selectedVoice;
  }
  utterance.rate = 0.98;
  utterance.pitch = 1;
  utterance.volume = 1;
  utterance.onstart = () => setBotState("speaking");
  utterance.onend = () => setBotState("idle");
  utterance.onerror = () => {
    setBotState("idle");
    botStatus.textContent = "Pulsa Escuchar para reproducir la respuesta";
  };
  window.speechSynthesis.speak(utterance);
  window.setTimeout(() => window.speechSynthesis.resume(), 200);
}

async function sendMessage(text) {
  if (busy || !text.trim()) return;
  busy = true;
  sendButton.disabled = true;
  appendMessage("user", text.trim());
  input.value = "";
  resizeInput();
  showTyping();
  setBotState("thinking");

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text.trim(), session_id: sessionId }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "No fue posible obtener una respuesta.");
    removeTyping();
    appendMessage("assistant", payload.response);
    speak(payload.response);
  } catch (error) {
    removeTyping();
    setBotState("idle");
    appendMessage("assistant", `No pude conectarme con el asistente. ${error.message}`);
  } finally {
    busy = false;
    sendButton.disabled = false;
    input.focus();
  }
}

function resizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(input.value);
});

input.addEventListener("input", resizeInput);
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    chatForm.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.prompt));
});

voiceButton.addEventListener("click", () => {
  voiceEnabled = !voiceEnabled;
  localStorage.setItem("compratech-voice", voiceEnabled ? "on" : "off");
  if (!voiceEnabled) {
    window.speechSynthesis?.cancel();
    setBotState("idle");
  }
  updateVoiceButton();
});

clearButton.addEventListener("click", async () => {
  window.speechSynthesis?.cancel();
  await fetch(`/sessions/${encodeURIComponent(sessionId)}`, { method: "DELETE" }).catch(() => null);
  sessionId = crypto.randomUUID();
  localStorage.setItem("compratech-session", sessionId);
  messages.innerHTML = "";
  appendMessage("assistant", "Empecemos de nuevo. ¿Qué periférico necesitas y cuál es tu presupuesto?");
  setBotState("idle");
});

localStorage.setItem("compratech-session", sessionId);
updateVoiceButton();
resizeInput();
input.focus();
