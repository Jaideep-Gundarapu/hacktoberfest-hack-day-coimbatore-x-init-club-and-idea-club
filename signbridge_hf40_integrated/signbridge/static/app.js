let sequence = [];
let index = 0;
const textEl = document.getElementById('text');
const video = document.getElementById('video');
const placeholder = document.getElementById('placeholder');
const counter = document.getElementById('counter');
const sequenceEl = document.getElementById('sequence');
const conceptsEl = document.getElementById('concepts');
const warningEl = document.getElementById('warning');
const missingEl = document.getElementById('missing');

function renderSequence() {
  sequenceEl.innerHTML = '';
  sequence.forEach((item, i) => {
    const span = document.createElement('span');
    span.className = 'seq-item' + (i === index ? ' active' : '');
    span.textContent = item.label + (item.available ? '' : ' · asset missing');
    span.onclick = () => playAt(i);
    sequenceEl.appendChild(span);
  });
  counter.textContent = sequence.length ? `${Math.min(index + 1, sequence.length)} / ${sequence.length}` : '0 / 0';
}

function playAt(i) {
  index = i;
  const item = sequence[i];
  renderSequence();
  if (!item || !item.available) {
    video.style.display = 'none';
    placeholder.classList.remove('hidden');
    placeholder.innerHTML = `<div class="avatar">🤟</div><div><strong>${item?.label || 'Sign'}</strong><br>Video asset is not loaded yet.</div>`;
    return;
  }
  placeholder.classList.add('hidden');
  video.style.display = 'block';
  video.src = item.asset_url;
  video.playbackRate = Number(document.getElementById('speed').value);
  video.currentTime = 0;
  video.play().catch(() => {});
}

video.addEventListener('ended', () => {
  if (index + 1 < sequence.length) playAt(index + 1);
});

document.getElementById('speed').addEventListener('input', (e) => { video.playbackRate = Number(e.target.value); });
document.getElementById('replay').addEventListener('click', () => { if (sequence.length) playAt(0); });
document.getElementById('speak').addEventListener('click', () => {
  const txt = textEl.value.trim();
  if (!txt || !('speechSynthesis' in window)) return;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(txt);
  utterance.rate = 0.92;
  speechSynthesis.speak(utterance);
});

document.querySelectorAll('[data-example]').forEach(btn => btn.addEventListener('click', () => { textEl.value = btn.dataset.example; }));

document.getElementById('translate').addEventListener('click', async () => {
  warningEl.classList.add('hidden');
  missingEl.classList.add('hidden');
  const text = textEl.value.trim();
  if (!text) return;
  const btn = document.getElementById('translate');
  btn.disabled = true; btn.textContent = 'Translating…';
  try {
    const res = await fetch('/api/translate', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({text}) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Translation failed');
    sequence = data.sequence || [];
    index = 0;
    conceptsEl.innerHTML = (data.concepts || []).map(c => `<span class="chip">${c}</span>`).join('');
    document.getElementById('rationale').textContent = data.rationale || '';
    if (data.warning) { warningEl.textContent = data.warning; warningEl.classList.remove('hidden'); }
    const missing = [...(data.missing_concepts || []), ...(data.unavailable_assets || []).map(x => `${x} sign video`)];
    if (missing.length) { missingEl.textContent = `Unavailable for full playback: ${missing.join(', ')}`; missingEl.classList.remove('hidden'); }
    renderSequence();
    if (sequence.length) playAt(0);
    else {
      placeholder.classList.remove('hidden');
      placeholder.innerHTML = `<div class="avatar">🧩</div><div>No matching sign concepts were found in the current vocabulary.</div>`;
    }
  } catch (err) {
    warningEl.textContent = err.message;
    warningEl.classList.remove('hidden');
  } finally {
    btn.disabled = false; btn.textContent = 'Translate to ISL';
  }
});

async function checkHealth() {
  try {
    const res = await fetch('/health');
    const h = await res.json();
    document.getElementById('health').textContent = `${h.gemma_enabled ? 'Gemma ON' : 'Offline mode'} · ${h.loaded_assets}/${h.vocabulary_size} assets`;
  } catch { document.getElementById('health').textContent = 'Server unavailable'; }
}
checkHealth();
