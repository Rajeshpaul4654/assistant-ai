const healthEl = document.getElementById("health");
const voiceStatusEl = document.getElementById("voice-status");
const chatLogEl = document.getElementById("chat-log");
const chatFormEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");
const micButtonEl = document.getElementById("mic-button");
const ttsToggleButtonEl = document.getElementById("tts-toggle-button");
const wakeToggleButtonEl = document.getElementById("wake-toggle-button");

const wakeWord = (document.body.dataset.wakeWord || "jarvis").toLowerCase();

let ttsEnabled = true;

/**
 * If user said only the wake word, we open the mic again for the real command.
 * If they said "wake + command", return the command part only.
 */
function splitWakeFromTranscript(spoken) {
    const lower = spoken.toLowerCase().trim();
    if (!lower.includes(wakeWord)) {
        return { hadWake: false, command: spoken.trim() };
    }
    const idx = lower.indexOf(wakeWord);
    let after = lower.slice(idx + wakeWord.length).trim().replace(/^[,.\s!?]+/, "");
    if (after) {
        return { hadWake: true, command: after };
    }
    return { hadWake: true, command: "" };
}

function appendMessage(role, text) {
    const div = document.createElement("div");
    div.className = `msg ${role}`;
    div.textContent = (role === "user" ? "You: " : "JARVIS: ") + text;
    chatLogEl.appendChild(div);
    chatLogEl.scrollTop = chatLogEl.scrollHeight;
}

function speakReply(text) {
    if (!ttsEnabled || !("speechSynthesis" in window)) {
        return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
}

async function loadHealth() {
    try {
        const res = await fetch("/api/health");
        const data = await res.json();
        if (data.ok) {
            healthEl.textContent = "Server status: healthy";
            return;
        }
        healthEl.textContent = `Server status: config issues - ${data.errors.join("; ")}`;
    } catch (error) {
        healthEl.textContent = "Server status: unavailable";
    }
}

async function sendMessage(message) {
    if (!message) {
        return;
    }

    appendMessage("user", message);

    try {
        const res = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });
        const data = await res.json();
        if (!data.ok) {
            appendMessage("jarvis", data.error || "Request failed.");
            return;
        }
        appendMessage("jarvis", data.reply);
        speakReply(data.reply);
    } catch (error) {
        appendMessage("jarvis", "Network error while calling JARVIS.");
    }
}

chatFormEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = inputEl.value.trim();
    inputEl.value = "";
    await sendMessage(message);
});

function setupVoiceInput() {
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        voiceStatusEl.textContent =
            "Voice: not supported in this browser (use Chrome/Edge).";
        micButtonEl.disabled = true;
        wakeToggleButtonEl.disabled = true;
        return;
    }

    let wakeModeActive = false;
    let wakePaused = false;
    let micListening = false;
    let commandListening = false;
    let lastWakeHandledMs = 0;
    const WAKE_DEBOUNCE_MS = 1400;

    const micRec = new SpeechRecognition();
    micRec.lang = "en-IN";
    micRec.interimResults = false;
    micRec.continuous = false;

    const wakeRec = new SpeechRecognition();
    wakeRec.lang = "en-IN";
    wakeRec.interimResults = false;
    wakeRec.continuous = true;

    function restartWakeDelayed() {
        if (!wakeModeActive || wakePaused || commandListening || micListening) {
            return;
        }
        window.setTimeout(() => {
            if (!wakeModeActive || wakePaused || commandListening || micListening) {
                return;
            }
            try {
                wakeRec.start();
            } catch (e) {
                /* InvalidStateError: already running */
            }
        }, 280);
    }

    wakeRec.onend = () => {
        if (wakeModeActive && !wakePaused && !commandListening && !micListening) {
            restartWakeDelayed();
        }
    };

    wakeRec.onerror = (event) => {
        if (event.error === "no-speech" || event.error === "aborted") {
            restartWakeDelayed();
            return;
        }
        voiceStatusEl.textContent = `Wake listener: ${event.error}`;
        if (wakeModeActive && !wakePaused) {
            restartWakeDelayed();
        }
    };

    async function handleFinalUtterance(spoken) {
        if (!spoken) {
            return;
        }

        const { hadWake, command } = splitWakeFromTranscript(spoken);

        if (wakeModeActive) {
            if (!hadWake) {
                return;
            }
            if (Date.now() - lastWakeHandledMs < WAKE_DEBOUNCE_MS) {
                return;
            }
            lastWakeHandledMs = Date.now();

            wakePaused = true;
            try {
                wakeRec.stop();
            } catch (e) {
                /* ignore */
            }

            try {
                if (command) {
                    voiceStatusEl.textContent = `Voice: "${spoken}"`;
                    inputEl.value = command;
                    await sendMessage(command);
                    inputEl.value = "";
                } else {
                    voiceStatusEl.textContent =
                        `Heard "${wakeWord}" — microphone open. Speak your command.`;
                    await listenCommandOnce();
                }
            } finally {
                wakePaused = false;
                if (wakeModeActive) {
                    restartWakeDelayed();
                }
            }
            return;
        }

        /* Manual mic (wake mode off) */
        const { hadWake: hw, command: cmd } = splitWakeFromTranscript(spoken);
        if (hw && !cmd) {
            voiceStatusEl.textContent =
                `Heard "${wakeWord}" — microphone open. Speak your command now.`;
            window.setTimeout(() => {
                try {
                    micRec.start();
                } catch (e) {
                    voiceStatusEl.textContent =
                        "Voice: tap Mic again to speak your command.";
                }
            }, 350);
            return;
        }

        const toSend = hw ? cmd : spoken;
        voiceStatusEl.textContent = `Voice: recognized "${spoken}"`;
        inputEl.value = toSend;
        inputEl.focus();
        inputEl.setSelectionRange(toSend.length, toSend.length);
        await sendMessage(toSend);
        inputEl.value = "";
    }

    function listenCommandOnce() {
        return new Promise((resolve) => {
            commandListening = true;
            const cmdRec = new SpeechRecognition();
            cmdRec.lang = "en-IN";
            cmdRec.interimResults = false;
            cmdRec.continuous = false;

            cmdRec.onstart = () => {
                voiceStatusEl.textContent = "Voice: listening for command...";
            };

            cmdRec.onresult = async (event) => {
                const spoken = event.results?.[0]?.[0]?.transcript?.trim() || "";
                if (!spoken) {
                    voiceStatusEl.textContent = "Voice: no command heard.";
                    return;
                }
                voiceStatusEl.textContent = `Voice: recognized "${spoken}"`;
                inputEl.value = spoken;
                await sendMessage(spoken);
                inputEl.value = "";
            };

            cmdRec.onerror = () => {
                voiceStatusEl.textContent = "Voice: command listen error.";
            };

            cmdRec.onend = () => {
                commandListening = false;
                resolve();
            };

            try {
                cmdRec.start();
            } catch (e) {
                commandListening = false;
                voiceStatusEl.textContent = "Voice: could not open command mic.";
                resolve();
            }
        });
    }

    wakeRec.onresult = async (event) => {
        for (let i = event.resultIndex; i < event.results.length; i++) {
            if (!wakeModeActive || wakePaused || commandListening || micListening) {
                break;
            }
            if (!event.results[i].isFinal) {
                continue;
            }
            const spoken = event.results[i][0].transcript.trim();
            await handleFinalUtterance(spoken);
        }
    };

    micRec.onstart = () => {
        micListening = true;
        micButtonEl.classList.add("listening");
        voiceStatusEl.textContent = "Voice: listening...";
    };

    micRec.onend = () => {
        micListening = false;
        micButtonEl.classList.remove("listening");
        if (!voiceStatusEl.textContent.includes("recognized") &&
                !voiceStatusEl.textContent.includes("Heard")) {
            voiceStatusEl.textContent = wakeModeActive
                ? `Listening for "${wakeWord}"...`
                : "Voice: ready";
        }
        if (wakeModeActive && !wakePaused) {
            restartWakeDelayed();
        }
    };

    micRec.onerror = (event) => {
        voiceStatusEl.textContent = `Voice error: ${event.error}`;
        if (wakeModeActive && !wakePaused) {
            restartWakeDelayed();
        }
    };

    micRec.onresult = async (event) => {
        const spoken = event.results?.[0]?.[0]?.transcript?.trim() || "";
        if (!spoken) {
            voiceStatusEl.textContent = "Voice: no speech recognized.";
            return;
        }
        await handleFinalUtterance(spoken);
    };

    micButtonEl.addEventListener("click", () => {
        if (wakeModeActive) {
            voiceStatusEl.textContent =
                "Turn off Wake word to use the Mic button, or just say the wake name.";
            return;
        }
        if (micListening) {
            micRec.stop();
            return;
        }
        voiceStatusEl.textContent = "Voice: starting microphone...";
        micRec.start();
    });

    wakeToggleButtonEl.addEventListener("click", () => {
        wakeModeActive = !wakeModeActive;
        wakeToggleButtonEl.textContent = wakeModeActive
            ? "Wake word: on"
            : "Wake word: off";
        wakeToggleButtonEl.classList.toggle("on", wakeModeActive);
        micButtonEl.disabled = wakeModeActive;

        if (wakeModeActive) {
            lastWakeHandledMs = 0;
            voiceStatusEl.textContent =
                `Listening for "${wakeWord}" — say it anytime to open the command mic.`;
            try {
                wakeRec.start();
            } catch (e) {
                voiceStatusEl.textContent =
                    "Wake word: could not start (try Chrome, allow microphone).";
                wakeModeActive = false;
                wakeToggleButtonEl.textContent = "Wake word: off";
                wakeToggleButtonEl.classList.remove("on");
                micButtonEl.disabled = false;
            }
        } else {
            wakePaused = true;
            try {
                wakeRec.stop();
            } catch (e) {
                /* ignore */
            }
            wakePaused = false;
            micButtonEl.disabled = false;
            voiceStatusEl.textContent = "Wake word listener stopped. Voice: ready";
        }
    });

    voiceStatusEl.textContent =
        "Voice: ready — turn on Wake word to listen for your assistant name automatically.";
}

appendMessage("jarvis", "Web dashboard is ready. Ask me anything.");
loadHealth();
setupVoiceInput();

ttsToggleButtonEl.addEventListener("click", () => {
    ttsEnabled = !ttsEnabled;
    ttsToggleButtonEl.textContent = ttsEnabled ? "Voice On" : "Voice Off";
    if (!ttsEnabled && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
    }
});
