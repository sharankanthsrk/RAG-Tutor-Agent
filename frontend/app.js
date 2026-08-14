/* ─── Config ─────────────────────────────────────── */
const API = 'http://localhost:8000';
let quizData = [];
let quizAnswers = {};

/* ─── Init ───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  checkHealth();
  loadDocuments();
  setupSidebar();
  setupUploadModal();
  setupSettingsModal();
  setupDropzone();
  autoResizeTextarea();
  setInterval(checkHealth, 15000);
});

/* ─── Health Check ───────────────────────────────── */
async function checkHealth() {
  const dot  = document.getElementById('statusDot');
  const text = document.getElementById('statusText');
  try {
    const r = await fetch(`${API}/health`, { signal: AbortSignal.timeout(4000) });
    const d = await r.json();
    dot.className = 'status-dot online';
    text.textContent = `Online · ${d.provider}`;
  } catch {
    dot.className = 'status-dot offline';
    text.textContent = 'Backend offline';
  }
}

/* ─── Sidebar Navigation ─────────────────────────── */
function setupSidebar() {
  document.querySelectorAll('.sidebar-item[data-tab]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sidebar-item').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.workspace').forEach(w => w.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`workspace-${btn.dataset.tab}`).classList.add('active');
    });
  });
}

/* ─── Documents ──────────────────────────────────── */
async function loadDocuments() {
  try {
    const r = await fetch(`${API}/documents`);
    const d = await r.json();
    renderDocList(d.documents || []);
  } catch {
    document.getElementById('docList').innerHTML = '<div class="doc-loading">Unavailable</div>';
  }
}

function renderDocList(docs) {
  const el = document.getElementById('docList');
  if (!docs.length) {
    el.innerHTML = '<div class="doc-loading">No documents yet</div>';
    return;
  }
  el.innerHTML = docs.map(d =>
    `<div class="doc-item"><span class="doc-icon">📄</span><span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d}</span></div>`
  ).join('');
}

document.getElementById('clearDocsBtn').addEventListener('click', async () => {
  if (!confirm('Clear all indexed documents?')) return;
  await fetch(`${API}/documents`, { method: 'DELETE' });
  loadDocuments();
});

/* ─── DOUBT SOLVER ───────────────────────────────── */
function handleDoubtKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitDoubt(); }
}

function askSample(q) {
  document.getElementById('doubtInput').value = q;
  submitDoubt();
}

async function submitDoubt() {
  const input = document.getElementById('doubtInput');
  const q = input.value.trim();
  if (!q) return;

  const chat = document.getElementById('chatArea');
  // Remove welcome card on first message
  const welcome = chat.querySelector('.welcome-card');
  if (welcome) welcome.remove();

  appendMsg(chat, 'user', q, '🎓');
  input.value = '';

  const thinkingEl = appendThinking(chat);

  try {
    const r = await fetch(`${API}/query/doubt`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q })
    });
    const d = await r.json();
    thinkingEl.remove();
    appendMsg(chat, 'ai', d.answer, '🤖', d.sources);
  } catch (err) {
    thinkingEl.remove();
    appendMsg(chat, 'ai', '❌ Could not reach the backend. Is it running on port 8000?', '🤖');
  }
  chat.scrollTop = chat.scrollHeight;
}

function appendMsg(container, role, text, avatar, sources) {
  const div = document.createElement('div');
  div.className = `msg ${role}`;
  let sourcesHTML = '';
  if (sources && sources.length) {
    const chips = [...new Set(sources.map(s => s.source).filter(Boolean))]
      .map(s => `<span class="source-chip">📄 ${s}</span>`).join('');
    if (chips) sourcesHTML = `<div class="sources-row">${chips}</div>`;
  }
  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-body">
      <div class="msg-text">${escapeHtml(text)}</div>
      ${sourcesHTML}
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function appendThinking(container) {
  const div = document.createElement('div');
  div.className = 'msg ai';
  div.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-body">
      <div class="thinking"><span>Thinking</span><span class="dots"><span></span><span></span><span></span></span></div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

/* ─── QUIZ ───────────────────────────────────────── */
async function generateQuiz() {
  const topic = document.getElementById('quizTopic').value.trim();
  if (!topic) { alert('Please enter a topic.'); return; }
  const n = parseInt(document.getElementById('quizCount').value);
  const btn = document.getElementById('quizBtnText');
  btn.textContent = 'Generating…';

  try {
    const r = await fetch(`${API}/query/quiz`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic, num_questions: n })
    });
    const d = await r.json();
    quizData = d.questions || [];
    quizAnswers = {};
    renderQuiz(d);
  } catch {
    document.getElementById('quizArea').innerHTML = '<div class="welcome-card"><p style="color:#FCA5A5">❌ Backend unavailable.</p></div>';
  } finally {
    btn.textContent = 'Generate Quiz';
  }
}

function renderQuiz(data) {
  const area = document.getElementById('quizArea');
  if (!data.questions || !data.questions.length) {
    area.innerHTML = '<div class="welcome-card"><p>No questions generated. Upload relevant material first.</p></div>';
    return;
  }
  area.innerHTML = '';
  data.questions.forEach((q, i) => {
    const card = document.createElement('div');
    card.className = 'quiz-card';
    card.innerHTML = `
      <div class="quiz-q">Q${i+1}. ${escapeHtml(q.question)}</div>
      <div class="quiz-options" id="opts-${i}">
        ${(q.options || []).map((opt, j) => {
          const letter = String.fromCharCode(65+j);
          return `<button class="quiz-opt" onclick="selectOpt(${i},'${letter}','${q.answer}')" id="opt-${i}-${letter}">
            <span class="opt-label">${letter}</span>${escapeHtml(opt)}
          </button>`;
        }).join('')}
      </div>
      <div class="quiz-explanation" id="exp-${i}">💡 ${escapeHtml(q.explanation || '')}</div>`;
    area.appendChild(card);
  });
  // Submit button
  const submitRow = document.createElement('div');
  submitRow.innerHTML = `<button class="btn-primary" onclick="scoreQuiz()">Submit & See Results</button>`;
  area.appendChild(submitRow);
}

function selectOpt(qi, letter, correct) {
  if (quizAnswers[qi] !== undefined) return; // already answered
  quizAnswers[qi] = letter;
  const opts = document.querySelectorAll(`#opts-${qi} .quiz-opt`);
  opts.forEach(opt => opt.disabled = true);
  document.getElementById(`opt-${qi}-${letter}`).classList.add(letter === correct ? 'correct' : 'wrong');
  if (letter !== correct) document.getElementById(`opt-${qi}-${correct}`).classList.add('correct');
  document.getElementById(`exp-${qi}`).style.display = 'block';
}

function scoreQuiz() {
  let score = 0;
  quizData.forEach((q, i) => {
    if (quizAnswers[i] === q.answer) score++;
  });
  const total = quizData.length;
  const pct = Math.round((score / total) * 100);
  const area = document.getElementById('quizArea');
  const scoreDiv = document.createElement('div');
  scoreDiv.className = 'quiz-score';
  scoreDiv.innerHTML = `
    <div class="score-big">${pct}%</div>
    <div class="score-label">${score} / ${total} correct</div>
    <div style="color:var(--text-sec);margin-top:8px;font-size:.85rem">${pct >= 80 ? '🎉 Excellent work!' : pct >= 60 ? '👍 Good effort!' : '📚 Keep studying!'}</div>
    <button class="btn-primary" style="margin-top:16px" onclick="generateQuiz()">Try Again</button>`;
  area.insertBefore(scoreDiv, area.firstChild);
  area.scrollTop = 0;
}

/* ─── SUMMARIZER ─────────────────────────────────── */
async function generateSummary() {
  const topic = document.getElementById('summarizeTopic').value.trim();
  if (!topic) { alert('Please enter a topic.'); return; }
  const btn = document.getElementById('sumBtnText');
  btn.textContent = 'Summarizing…';

  try {
    const r = await fetch(`${API}/query/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ topic })
    });
    const d = await r.json();
    renderSummary(d);
  } catch {
    document.getElementById('summaryArea').innerHTML = '<div class="welcome-card"><p style="color:#FCA5A5">❌ Backend unavailable.</p></div>';
  } finally {
    btn.textContent = 'Summarize';
  }
}

function renderSummary(data) {
  const area = document.getElementById('summaryArea');
  const sources = (data.sources || []).filter(s => s.source).map(s =>
    `<span class="source-chip">📄 ${s.source} (${s.score})</span>`).join('');
  area.innerHTML = `
    <div class="summary-card">
      <div>${escapeHtml(data.summary || '')}</div>
      ${sources ? `<div class="summary-sources">${sources}</div>` : ''}
    </div>`;
}

/* ─── UPLOAD MODAL ───────────────────────────────── */
function setupUploadModal() {
  document.getElementById('uploadBtn').addEventListener('click', () => openModal('uploadModal'));
}

function openModal(id) { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }

// Close on overlay click
document.querySelectorAll('.modal-overlay').forEach(o => {
  o.addEventListener('click', e => { if (e.target === o) o.classList.remove('open'); });
});

function setupDropzone() {
  const dz = document.getElementById('dropZone');
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', e => {
    e.preventDefault(); dz.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) uploadFile(file);
}

async function uploadFile(file) {
  const status = document.getElementById('uploadStatus');
  status.className = 'upload-status';
  status.textContent = `Uploading ${file.name}…`;
  status.style.display = 'block';

  const form = new FormData();
  form.append('file', file);
  try {
    const r = await fetch(`${API}/upload`, { method: 'POST', body: form });
    const d = await r.json();
    if (r.ok) {
      showStatus(status, `✅ ${d.message}`, 'success');
      loadDocuments();
    } else {
      showStatus(status, `❌ ${d.detail}`, 'error');
    }
  } catch {
    showStatus(status, '❌ Upload failed — backend offline?', 'error');
  }
}

async function uploadText() {
  const text  = document.getElementById('pasteText').value.trim();
  const title = document.getElementById('pasteTitle').value.trim() || 'Pasted Text';
  const status = document.getElementById('uploadStatus');
  if (!text) { showStatus(status, '❌ Please enter some text.', 'error'); return; }

  try {
    const r = await fetch(`${API}/upload/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, title })
    });
    const d = await r.json();
    if (r.ok) {
      showStatus(status, `✅ ${d.message}`, 'success');
      document.getElementById('pasteText').value = '';
      loadDocuments();
    } else {
      showStatus(status, `❌ ${d.detail}`, 'error');
    }
  } catch {
    showStatus(status, '❌ Failed — backend offline?', 'error');
  }
}

function showStatus(el, msg, type) {
  el.textContent = msg;
  el.className = `upload-status ${type}`;
}

/* ─── SETTINGS MODAL ─────────────────────────────── */
function setupSettingsModal() {
  document.getElementById('settingsBtn').addEventListener('click', () => openModal('settingsModal'));
  document.getElementById('llmProvider').addEventListener('change', function () {
    const isOllama = this.value === 'ollama';
    document.getElementById('ollamaLabel').style.display = isOllama ? 'block' : 'none';
    document.getElementById('ollamaUrl').style.display   = isOllama ? 'block' : 'none';
  });
}

async function saveSettings() {
  const status = document.getElementById('settingsStatus');
  const body = {
    provider:   document.getElementById('llmProvider').value,
    api_key:    document.getElementById('llmApiKey').value,
    model:      document.getElementById('llmModel').value,
    ollama_url: document.getElementById('ollamaUrl').value
  };
  try {
    const r = await fetch(`${API}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const d = await r.json();
    showStatus(status, `✅ Saved! Provider: ${d.provider}`, 'success');
    checkHealth();
  } catch {
    showStatus(status, '❌ Could not save — backend offline?', 'error');
  }
}

/* ─── Helpers ────────────────────────────────────── */
function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function autoResizeTextarea() {
  const ta = document.getElementById('doubtInput');
  ta.addEventListener('input', () => {
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  });
}
