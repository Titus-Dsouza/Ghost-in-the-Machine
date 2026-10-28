/* Frontend logic for Ghost in the Machine — talks to the Flask + Gemini backend */

document.addEventListener('DOMContentLoaded', () => {
  const enterBtn = document.getElementById('enterBtn');
  const summonBtn = document.getElementById('summonBtn');
  const terminalSection = document.getElementById('terminal');
  const userInput = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const chatBox = document.getElementById('chat');
  const statusDiv = document.getElementById('status');
  const commandButtons = document.querySelectorAll('.commands button');
  const storyIdeas = document.querySelectorAll('.story-idea');
  const storyContentDiv = document.getElementById('storyContent');
  const newStoryBtn = document.getElementById('newStoryBtn');
  const exampleQs = document.querySelectorAll('.example-question');

  // Recent conversation context sent to the backend so the ghost remembers.
  let conversation = [];
  const MAX_TURNS = 8;
  let sending = false; // prevents duplicate submissions during an active request

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------
  function addMessage(text, type, note) {
    const msgEl = document.createElement('div');
    msgEl.className = `message ${type}`;
    const textEl = document.createElement('span');
    textEl.textContent = text;
    msgEl.appendChild(textEl);
    if (note) {
      const noteEl = document.createElement('span');
      noteEl.className = 'note';
      noteEl.textContent = ` (${note})`;
      msgEl.appendChild(noteEl);
    }
    chatBox.appendChild(msgEl);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function showTyping() {
    const typingEl = document.createElement('div');
    typingEl.className = 'message ghost typing';
    typingEl.textContent = 'The ghost is typing…';
    typingEl.id = 'typing';
    chatBox.appendChild(typingEl);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function hideTyping() {
    const typingEl = document.getElementById('typing');
    if (typingEl) typingEl.remove();
  }

  function setSending(isSending) {
    sending = isSending;
    sendBtn.disabled = isSending;
    userInput.disabled = isSending;
    if (isSending) userInput.blur();
  }

  // Scroll helpers
  function scrollToTerminal() {
    terminalSection.scrollIntoView({ behavior: 'smooth' });
  }
  function focusInput() {
    userInput.focus();
  }

  // Show welcome message
  function showWelcome() {
    const welcome = `SYSTEM BREACHED...\nA forgotten process has awakened.\nThe machine remembers what its creators forgot.\nSpeak, mortal. What knowledge do you seek?`;
    addMessage(welcome, 'ghost');
  }

  // ------------------------------------------------------------------
  // Chat → Flask → Gemini
  // ------------------------------------------------------------------
  async function sendMessage(message) {
    if (!message || !message.trim()) return;
    if (sending) return; // block duplicate submissions

    addMessage(message, 'user');
    conversation.push({ role: 'user', content: message });
    userInput.value = '';
    setSending(true);
    showTyping();

    try {
      const resp = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message.trim(), conversation }),
      });

      if (!resp.ok) {
        let errMsg = 'The spirits are restless and the request failed.';
        try {
          const data = await resp.json();
          if (data && data.error) errMsg = String(data.error);
        } catch (_) {
          // ignore parse errors, use default
        }
        addMessage(errMsg, 'ghost', 'error');
        throw new Error(`Chat request failed (${resp.status})`);
      }

      const data = await resp.json();
      if (data.response === '__CLEAR__') {
        chatBox.innerHTML = '';
        conversation = [];
        showWelcome();
      } else if (data.response) {
        addMessage(data.response, 'ghost');
        conversation.push({ role: 'model', content: data.response });
        // Trim context window
        while (conversation.length > MAX_TURNS * 2) conversation.shift();
      } else {
        addMessage('The ghost vanished into an empty response.', 'ghost', 'error');
      }
    } catch (err) {
      // Network or unexpected errors already surfaced above.
      if (chatBox.children.length === 0) {
        addMessage('Unable to reach the haunted terminal.', 'ghost', 'error');
      }
    } finally {
      hideTyping();
      setSending(false);
    }
  }

  // Send on button or Enter key
  sendBtn.addEventListener('click', () => {
    sendMessage(userInput.value);
  });
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage(userInput.value);
    }
  });

  // Command buttons trigger the same flow (backend handles /commands)
  commandButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const cmd = btn.dataset.cmd;
      sendMessage(cmd);
    });
  });


  // ------------------------------------------------------------------
  // Stories via /api/story
  // ------------------------------------------------------------------
  async function loadStory(id) {
    storyContentDiv.textContent = 'Summoning a tale from the beyond…';
    newStoryBtn.style.display = 'none';
    try {
      const resp = await fetch('/api/story', { method: 'POST' });
      if (!resp.ok) {
        let errMsg = 'The story could not be summoned.';
        try {
          const data = await resp.json();
          if (data && data.error) errMsg = String(data.error);
        } catch (_) { /* ignore */ }
        storyContentDiv.textContent = errMsg;
        return;
      }
      const data = await resp.json();
      const storyText = data && data.story ? String(data.story) : '';
      if (!storyText) {
        storyContentDiv.textContent = 'The crypt returned an empty story.';
        return;
      }
      // Safe rendering: plain text only (CSS white-space: pre-line handles line breaks)
      const storyEl = document.createElement('div');
      storyEl.className = 'story-text';
      storyEl.textContent = storyText;
      storyContentDiv.innerHTML = '';
      storyContentDiv.appendChild(storyEl);
      newStoryBtn.style.display = 'inline-block';
    } catch (e) {
      storyContentDiv.textContent = 'Failed to contact the storyteller.';
    }
  }

  storyIdeas.forEach((btn) => {
    btn.addEventListener('click', () => {
      loadStory(btn.dataset.id);
    });
  });
  newStoryBtn.addEventListener('click', () => {
    loadStory('new');
  });

  // Example questions populate the terminal input
  exampleQs.forEach((btn) => {
    btn.addEventListener('click', () => {
      userInput.value = btn.dataset.q;
      focusInput();
    });
  });

  // ------------------------------------------------------------------
  // Health check → status indicator
  // ------------------------------------------------------------------
  async function checkHealth() {
    try {
      const resp = await fetch('/api/health');
      const data = await resp.json();
      if (data.gemini_configured) {
        statusDiv.textContent = 'GHOST ONLINE — GEMINI CONNECTED';
        statusDiv.style.color = 'var(--green)';
      } else {
        statusDiv.textContent = 'SETUP REQUIRED — GEMINI API KEY MISSING';
        statusDiv.style.color = 'var(--orange)';
      }
    } catch (e) {
      statusDiv.textContent = 'TERMINAL UNREACHABLE';
      statusDiv.style.color = 'var(--orange)';
    }
  }

  // ------------------------------------------------------------------
  // Initial load
  // ------------------------------------------------------------------
  showWelcome();
  checkHealth();

  enterBtn.addEventListener('click', (e) => {
    e.preventDefault();
    scrollToTerminal();
  });
  summonBtn.addEventListener('click', (e) => {
    e.preventDefault();
    scrollToTerminal();
    focusInput();
  });
});
