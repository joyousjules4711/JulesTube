const form = document.querySelector('#search-form');
const input = document.querySelector('#search-input');
const suggestions = document.querySelector('#search-suggestions');
const results = document.querySelector('#results');
const message = document.querySelector('#message');

const nowTitle = document.querySelector('#now-title');
const nowMeta = document.querySelector('#now-meta');
const nowThumb = document.querySelector('#now-thumb');
const pauseBtn = document.querySelector('#pause-btn');
const nextBtn = document.querySelector('#next-btn');
const volume = document.querySelector('#volume');

const queue = document.querySelector('#queue');
const queueEmpty = document.querySelector('#queue-empty');
const clearQueueBtn = document.querySelector('#clear-queue-btn');

const historyList = document.querySelector('#history-list');
const historyEmpty = document.querySelector('#history-empty');
const refreshHistoryBtn = document.querySelector('#refresh-history-btn');

const similarList = document.querySelector('#similar-list');
const similarEmpty = document.querySelector('#similar-empty');
const refreshSimilarBtn = document.querySelector('#refresh-similar-btn');
const autoplayToggle = document.querySelector('#autoplay-toggle');

const joinUrl = document.querySelector('#join-url');
const joinQr = document.querySelector('#join-qr');
const copyJoinUrlBtn = document.querySelector('#copy-join-url');
const refreshQrBtn = document.querySelector('#refresh-qr');

const userCard = document.querySelector('#user-card');
const djBadge = document.querySelector('#dj-badge');
const usernameInput = document.querySelector('#username-input');
const saveUsernameBtn = document.querySelector('#save-username-btn');
const changeUsernameBtn = document.querySelector('#change-username-btn');
const djNameLabel = document.querySelector('#dj-name-label');

let latestState = null;
let suggestionTimer = null;
let suggestionAbort = null;
let lastSimilarKey = '';
let similarLoading = false;

let autoplayBusy = false;
let autoplayLastSourceKey = '';
let autoplayLastSourceTrack = null;
let autoplayCooldownUntil = 0;

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Unbekannter Fehler');
  }

  return data;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function setMessage(text) {
  message.textContent = text || '';
}

function formatDateTime(value) {
  if (!value) return '';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString('de-AT', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getJulesTubeUsername() {
  const stored = localStorage.getItem('julestube.username') || '';
  const typed = usernameInput?.value || '';
  const name = (stored || typed || '').trim();

  return name || 'Gast';
}

function withAddedBy(item) {
  return {
    ...item,
    added_by: getJulesTubeUsername(),
  };
}

function trackMeta(item) {
  return [
    item.channel || '',
    item.added_by ? `von ${item.added_by}` : '',
    item.duration || '',
  ].filter(Boolean).join(' · ');
}

function thumbnailHtml(item, className) {
  if (item.thumbnail) {
    return `<img src="${escapeHtml(item.thumbnail)}" alt="">`;
  }

  return `<span class="${className}-fallback">♪</span>`;
}

function renderResults(items) {
  results.innerHTML = '';

  if (!items || items.length === 0) {
    results.innerHTML = '<p class="empty-note">Nichts gefunden.</p>';
    return;
  }

  for (const item of items) {
    const card = document.createElement('article');
    card.className = 'track-card result-card';

    card.innerHTML = `
      <div class="track-thumb">
        ${thumbnailHtml(item, 'track-thumb')}
      </div>

      <div class="track-main">
        <h3>${escapeHtml(item.title || 'Unbekannter Titel')}</h3>
        <p>${escapeHtml(trackMeta(item))}</p>

        <div class="track-actions">
          <button data-action="play" type="button">▶ Jetzt</button>
          <button data-action="queue" type="button">＋ Queue</button>
        </div>
      </div>
    `;

    card.querySelector('[data-action="play"]').addEventListener('click', () => playNow(item));
    card.querySelector('[data-action="queue"]').addEventListener('click', () => enqueue(item));

    results.appendChild(card);
  }
}

function renderStatus(data) {
  latestState = data;

  const player = data.player || {};
  const current = data.current || null;
  const items = data.queue || [];

  nowTitle.textContent = current?.title || (player.running ? 'mpv läuft' : 'Noch nichts gestartet');

  const nowMetaParts = [
    player.running ? (player.paused ? 'Pausiert' : 'Spielt') : '',
    current?.channel || '',
    current?.added_by ? `von ${current.added_by}` : '',
    current?.duration || '',
  ].filter(Boolean);

  nowMeta.textContent = nowMetaParts.length
    ? nowMetaParts.join(' · ')
    : 'Player wartet auf den ersten Song.';

  if (current?.thumbnail) {
    nowThumb.innerHTML = `<img src="${escapeHtml(current.thumbnail)}" alt="">`;
  } else {
    nowThumb.textContent = '▶';
  }

  if (typeof player.volume === 'number') {
    volume.value = Math.round(player.volume);
  }

  updateMainPlayButton(data);
  renderQueue(items, Boolean(current));
  rememberAutoplaySource(data);
  maybeLoadSimilar(data);
  maybeAutoplay(data);
}

function updateMainPlayButton(data) {
  const player = data.player || {};
  const hasCurrent = Boolean(data.current);
  const hasQueue = Array.isArray(data.queue) && data.queue.length > 0;

  if (player.running && !player.paused) {
    pauseBtn.dataset.mode = 'pause';
    pauseBtn.textContent = '⏸';
    pauseBtn.title = 'Pause';
    pauseBtn.setAttribute('aria-label', 'Pause');
    return;
  }

  if (hasCurrent || hasQueue || player.running) {
    pauseBtn.dataset.mode = 'play';
    pauseBtn.textContent = '▶';
    pauseBtn.title = 'Abspielen';
    pauseBtn.setAttribute('aria-label', 'Abspielen');
    return;
  }

  pauseBtn.dataset.mode = 'empty';
  pauseBtn.textContent = '▶';
  pauseBtn.title = 'Noch kein Song ausgewählt';
  pauseBtn.setAttribute('aria-label', 'Noch kein Song ausgewählt');
}

function renderQueue(items, hasCurrent) {
  queue.innerHTML = '';

  const reallyEmpty = !hasCurrent && (!items || items.length === 0);
  queueEmpty.hidden = !reallyEmpty;

  if (!items || items.length === 0) {
    return;
  }

  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'queue-item';

    li.innerHTML = `
      <div class="queue-row">
        <div class="queue-thumb">
          ${thumbnailHtml(item, 'queue-thumb')}
        </div>

        <div class="queue-main">
          <strong>${escapeHtml(item.title || 'Unbekannter Titel')}</strong>
          <span>${escapeHtml(trackMeta(item))}</span>
        </div>
      </div>
    `;

    queue.appendChild(li);
  }
}

async function refreshStatus() {
  try {
    const data = await api('/api/status');
    renderStatus(data);
  } catch (error) {
    setMessage(error.message);
  }
}

async function playNow(item) {
  setMessage('Starte Wiedergabe …');

  try {
    const data = await api('/api/play-now', {
      method: 'POST',
      body: JSON.stringify(withAddedBy(item)),
    });

    renderStatus(data);
    setMessage('Läuft.');
    loadHistory();
  } catch (error) {
    setMessage(error.message);
  }
}

async function enqueue(item) {
  setMessage('Wird zur Queue hinzugefügt …');

  try {
    const data = await api('/api/queue', {
      method: 'POST',
      body: JSON.stringify(withAddedBy(item)),
    });

    renderStatus(data);
    setMessage('Hinzugefügt.');
  } catch (error) {
    setMessage(error.message);
  }
}

async function mainPlayAction() {
  const data = latestState || {};
  const player = data.player || {};
  const hasCurrent = Boolean(data.current);
  const hasQueue = Array.isArray(data.queue) && data.queue.length > 0;

  try {
    let nextData;

    if (player.running || hasCurrent) {
      nextData = await api('/api/control/pause', { method: 'POST' });
    } else if (hasQueue) {
      nextData = await api('/api/control/next', { method: 'POST' });
    } else {
      setMessage('Erst einen Song suchen oder zur Queue hinzufügen.');
      return;
    }

    renderStatus(nextData);
  } catch (error) {
    setMessage(error.message);
  }
}

async function search(query) {
  setMessage('Suche läuft …');
  results.innerHTML = '';

  try {
    const data = await api(`/api/search?q=${encodeURIComponent(query)}`);
    renderResults(data.results || []);
    setMessage('');
  } catch (error) {
    setMessage(error.message);
  }
}

function hideSuggestions() {
  suggestions.hidden = true;
  suggestions.innerHTML = '';
}

function renderSuggestions(items) {
  suggestions.innerHTML = '';

  if (!items || items.length === 0) {
    hideSuggestions();
    return;
  }

  const list = document.createElement('div');
  list.className = 'suggestion-list';

  for (const item of items.slice(0, 6)) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'suggestion-item';

    button.innerHTML = `
      <span class="suggestion-thumb">
        ${thumbnailHtml(item, 'suggestion-thumb')}
      </span>

      <span class="suggestion-text">
        <strong>${escapeHtml(item.title || 'Unbekannter Titel')}</strong>
        <small>${escapeHtml([item.channel || '', item.duration || ''].filter(Boolean).join(' · '))}</small>
      </span>
    `;

    button.addEventListener('click', () => {
      input.value = item.title || input.value;
      hideSuggestions();
      form.requestSubmit();
    });

    list.appendChild(button);
  }

  suggestions.appendChild(list);
  suggestions.hidden = false;
}

async function loadSuggestions(query) {
  if (suggestionAbort) {
    suggestionAbort.abort();
  }

  suggestionAbort = new AbortController();

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, {
      signal: suggestionAbort.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    renderSuggestions(data.results || []);
  } catch (error) {
    if (error.name !== 'AbortError') {
      hideSuggestions();
    }
  }
}

async function loadHistory() {
  try {
    const response = await fetch('/api/history?limit=20');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    renderHistory(data.history || []);
  } catch (error) {
    historyEmpty.hidden = false;
    historyEmpty.textContent = 'Hörverlauf konnte nicht geladen werden.';
  }
}

function normalizeHistoryTrack(item) {
  return {
    title: item.title || 'Unbekannter Titel',
    url: item.url || '',
    channel: item.channel || '',
    duration: item.duration || '',
    video_id: item.video_id || '',
    thumbnail: item.thumbnail || '',
  };
}

function renderHistory(items) {
  historyList.innerHTML = '';

  if (!items || items.length === 0) {
    historyEmpty.hidden = false;
    return;
  }

  historyEmpty.hidden = true;

  for (const item of [...items].reverse()) {
    const track = normalizeHistoryTrack(item);

    const li = document.createElement('li');
    li.className = 'history-item';

    const meta = [
      track.channel,
      item.added_by ? `von ${item.added_by}` : '',
      track.duration,
      formatDateTime(item.played_at),
    ].filter(Boolean).join(' · ');

    li.innerHTML = `
      <div class="history-thumb">
        ${thumbnailHtml(track, 'history-thumb')}
      </div>

      <div class="history-main">
        <p class="history-title">${escapeHtml(track.title)}</p>
        <p class="history-meta">${escapeHtml(meta)}</p>

        <div class="history-actions">
          <button data-action="play" type="button">▶ Jetzt</button>
          <button data-action="queue" type="button">＋ Queue</button>
        </div>
      </div>
    `;

    li.querySelector('[data-action="play"]').addEventListener('click', () => playNow(track));
    li.querySelector('[data-action="queue"]').addEventListener('click', () => enqueue(track));

    historyList.appendChild(li);
  }
}

async function loadSimilar(force = false) {
  if (similarLoading) return;

  similarLoading = true;

  try {
    const response = await fetch('/api/similar');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const current = data.current || null;
    const key = current?.queue_id || current?.video_id || current?.url || '';

    if (!force && key && key === lastSimilarKey && similarList.children.length > 0) {
      return;
    }

    lastSimilarKey = key;
    renderSimilar(data.results || []);
  } catch (error) {
    similarEmpty.hidden = false;
    similarEmpty.textContent = 'Ähnliche Videos konnten nicht geladen werden.';
  } finally {
    similarLoading = false;
  }
}

function maybeLoadSimilar(data) {
  const current = data.current || null;
  const key = current?.queue_id || current?.video_id || current?.url || '';

  if (!key || key === lastSimilarKey) {
    return;
  }

  loadSimilar(true);
}

function renderSimilar(items) {
  similarList.innerHTML = '';

  if (!items || items.length === 0) {
    similarEmpty.hidden = false;
    return;
  }

  similarEmpty.hidden = true;

  for (const item of items) {
    const card = document.createElement('article');
    card.className = 'track-card similar-card';

    card.innerHTML = `
      <div class="track-thumb">
        ${thumbnailHtml(item, 'track-thumb')}
      </div>

      <div class="track-main">
        <h3>${escapeHtml(item.title || 'Unbekannter Titel')}</h3>
        <p>${escapeHtml(trackMeta(item))}</p>

        <div class="track-actions">
          <button data-action="play" type="button">▶ Jetzt</button>
          <button data-action="queue" type="button">＋ Queue</button>
        </div>
      </div>
    `;

    card.querySelector('[data-action="play"]').addEventListener('click', () => playNow(item));
    card.querySelector('[data-action="queue"]').addEventListener('click', () => enqueue(item));

    similarList.appendChild(card);
  }
}

async function loadJoinInfo() {
  try {
    const response = await fetch('/api/join');

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    const url = data.join_url;

    joinUrl.textContent = url;
    joinUrl.href = url;
    joinQr.src = `/join/qr.png?t=${Date.now()}`;
  } catch (error) {
    joinUrl.textContent = 'QR-Code konnte nicht geladen werden.';
    joinUrl.removeAttribute('href');
  }
}


function getTrackKey(track) {
  if (!track) return '';

  return String(
    track.queue_id ||
    track.video_id ||
    track.url ||
    track.title ||
    ''
  );
}

function isAutoplayEnabled() {
  return Boolean(autoplayToggle?.checked);
}

function initAutoplay() {
  if (!autoplayToggle) return;

  const saved = localStorage.getItem('julestube.autoplay') === '1';
  autoplayToggle.checked = saved;

  autoplayToggle.addEventListener('change', () => {
    localStorage.setItem('julestube.autoplay', autoplayToggle.checked ? '1' : '0');

    if (autoplayToggle.checked) {
      setMessage('Autoplay ist an.');
      maybeAutoplay(latestState);
    } else {
      setMessage('Autoplay ist aus.');
    }
  });
}

function rememberAutoplaySource(data) {
  const player = data?.player || {};
  const current = data?.current || null;

  if (!current) return;

  const key = getTrackKey(current);
  if (!key) return;

  /*
    Merken nur, wenn wirklich etwas lief.
    Dadurch startet Autoplay nicht wild los, nur weil die Seite neu geladen wurde.
  */
  if (player.running && !player.paused) {
    autoplayLastSourceKey = key;
    autoplayLastSourceTrack = current;
  }
}

function queueIsEmpty(data) {
  return !Array.isArray(data?.queue) || data.queue.length === 0;
}

function sameTrack(a, b) {
  if (!a || !b) return false;

  const aKey = getTrackKey(a);
  const bKey = getTrackKey(b);

  if (aKey && bKey && aKey === bKey) return true;

  const aTitle = String(a.title || '').trim().toLowerCase();
  const bTitle = String(b.title || '').trim().toLowerCase();

  return Boolean(aTitle && bTitle && aTitle === bTitle);
}

function pickAutoplayCandidate(items, sourceTrack) {
  if (!Array.isArray(items)) return null;

  return items.find((item) => {
    if (!item?.url) return false;
    return !sameTrack(item, sourceTrack);
  }) || null;
}

async function loadAutoplayCandidates(sourceTrack) {
  /*
    Erst die Similar-API versuchen.
    Falls die aus irgendeinem Grund nichts liefert, fallback auf normale Suche.
  */
  try {
    const similarResponse = await fetch('/api/similar');

    if (similarResponse.ok) {
      const similarData = await similarResponse.json();
      const candidate = pickAutoplayCandidate(similarData.results || [], sourceTrack);

      if (candidate) {
        return candidate;
      }
    }
  } catch {
    // Fallback kommt direkt darunter.
  }

  const query = [sourceTrack?.title || '', sourceTrack?.channel || '']
    .filter(Boolean)
    .join(' ')
    .trim();

  if (!query) return null;

  const searchResponse = await fetch(`/api/search?q=${encodeURIComponent(query)}`);

  if (!searchResponse.ok) {
    return null;
  }

  const searchData = await searchResponse.json();
  return pickAutoplayCandidate(searchData.results || [], sourceTrack);
}

async function maybeAutoplay(data) {
  if (!data) return;
  if (!isAutoplayEnabled()) return;
  if (autoplayBusy) return;

  const now = Date.now();
  if (now < autoplayCooldownUntil) return;

  const player = data.player || {};

  /*
    mpv bleibt nach Song-Ende als Prozess aktiv.
    Deshalb blockieren wir nur, wenn wirklich gerade abgespielt wird.
    Wenn idle_active true ist, ist der Song zu Ende und Autoplay darf starten.
  */
  const isIdle = player.idle_active === true;

  if (player.paused && !isIdle) return;
  if (player.running && !isIdle) return;

  if (!queueIsEmpty(data)) return;

  const sourceTrack = data.current || autoplayLastSourceTrack;
  const sourceKey = getTrackKey(sourceTrack);

  if (!sourceTrack || !sourceKey) return;

  /*
    Pro beendetem Song nur einmal Autoplay versuchen.
    Verhindert Endlosschleifen bei Fehlern.
  */
  if (sourceKey === autoplayLastSourceKey && autoplayCooldownUntil > now) {
    return;
  }

  autoplayBusy = true;
  autoplayCooldownUntil = now + 15000;

  try {
    setMessage('Autoplay sucht ähnlichen Song …');

    const candidate = await loadAutoplayCandidates(sourceTrack);

    if (!candidate) {
      setMessage('Autoplay: keine ähnlichen Videos gefunden.');
      return;
    }

    const nextData = await api('/api/play-now', {
      method: 'POST',
      body: JSON.stringify(withAddedBy(candidate)),
    });

    autoplayLastSourceKey = sourceKey;
    renderStatus(nextData);
    setMessage('Autoplay: ähnlicher Song gestartet.');
    loadHistory();
  } catch (error) {
    setMessage(`Autoplay: ${error.message}`);
  } finally {
    autoplayBusy = false;
  }
}


function initUsername() {
  const savedName = localStorage.getItem('julestube.username') || '';

  usernameInput.value = savedName;

  function showBadge(name) {
    djNameLabel.textContent = name;
    userCard.hidden = true;
    djBadge.hidden = false;
  }

  function showForm() {
    djBadge.hidden = true;
    userCard.hidden = false;
    usernameInput.focus();
  }

  function saveName() {
    const cleanName = usernameInput.value.trim();

    if (!cleanName) {
      localStorage.removeItem('julestube.username');
      showForm();
      return;
    }

    localStorage.setItem('julestube.username', cleanName);
    showBadge(cleanName);
  }

  saveUsernameBtn.addEventListener('click', saveName);

  usernameInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      saveName();
    }
  });

  changeUsernameBtn.addEventListener('click', showForm);

  if (savedName.trim()) {
    showBadge(savedName.trim());
  } else {
    showForm();
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();

  const query = input.value.trim();
  if (!query) return;

  hideSuggestions();
  search(query);
});

input.addEventListener('input', () => {
  const query = input.value.trim();

  clearTimeout(suggestionTimer);

  if (query.length < 3) {
    hideSuggestions();
    return;
  }

  suggestionTimer = setTimeout(() => {
    loadSuggestions(query);
  }, 450);
});

document.addEventListener('click', (event) => {
  if (!form.contains(event.target) && !suggestions.contains(event.target)) {
    hideSuggestions();
  }
});

pauseBtn.addEventListener('click', mainPlayAction);

nextBtn.addEventListener('click', async () => {
  try {
    const data = await api('/api/control/next', { method: 'POST' });
    renderStatus(data);
  } catch (error) {
    setMessage(error.message);
  }
});

volume.addEventListener('change', async () => {
  try {
    const data = await api('/api/control/volume', {
      method: 'POST',
      body: JSON.stringify({ volume: volume.value }),
    });

    renderStatus(data);
  } catch (error) {
    setMessage(error.message);
  }
});

clearQueueBtn.addEventListener('click', async () => {
  try {
    const data = await api('/api/queue/clear', { method: 'POST' });
    renderStatus(data);
  } catch (error) {
    setMessage(error.message);
  }
});

refreshHistoryBtn.addEventListener('click', loadHistory);
refreshSimilarBtn.addEventListener('click', () => loadSimilar(true));
refreshQrBtn.addEventListener('click', loadJoinInfo);

copyJoinUrlBtn.addEventListener('click', async () => {
  const url = joinUrl.textContent.trim();

  try {
    await navigator.clipboard.writeText(url);
    copyJoinUrlBtn.textContent = 'Kopiert';
    setTimeout(() => {
      copyJoinUrlBtn.textContent = 'Link kopieren';
    }, 1400);
  } catch {
    setMessage('Kopieren nicht möglich. Link bitte manuell markieren.');
  }
});

initUsername();
initAutoplay();
loadJoinInfo();
refreshStatus();
loadHistory();
loadSimilar(true);

setInterval(refreshStatus, 4000);
setInterval(loadHistory, 15000);

/* --- Playlist Import Stabilizer: Paste/Load sichtbar machen --- */

;(() => {
  function initPlaylistImportStabilizer() {
    const input = document.querySelector('#playlist-url-input');
    const loadBtn = document.querySelector('#playlist-load-btn');
    const pasteBtn = document.querySelector('#playlist-paste-btn');
    const info = document.querySelector('#playlist-info');

    if (!input || !loadBtn || !info) {
      return;
    }

    if (loadBtn.dataset.playlistStabilized === '1') {
      return;
    }

    loadBtn.dataset.playlistStabilized = '1';

    let autoTimer = null;

    function setInfo(text) {
      info.textContent = text || '';
    }

    function looksLikePlaylistUrl(value) {
      const url = String(value || '').trim();
      return (
        url.includes('youtube.com/playlist') ||
        url.includes('youtube.com/watch') && url.includes('list=') ||
        url.includes('music.youtube.com') && url.includes('list=') ||
        url.includes('youtu.be') && url.includes('list=')
      );
    }

    async function loadPlaylist() {
      const url = input.value.trim();

      if (!url) {
        setInfo('Bitte Playlist-Link einfügen.');
        return;
      }

      if (!looksLikePlaylistUrl(url)) {
        setInfo('Link erkannt, aber das sieht nicht nach einer YouTube-Playlist aus.');
        return;
      }

      setInfo('Playlist wird geladen …');

      try {
        const response = await fetch('/api/playlist/preview', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            url,
            limit: 20,
          }),
        });

        let data = {};
        try {
          data = await response.json();
        } catch {
          data = {};
        }

        if (!response.ok) {
          throw new Error(data.error || `Playlist-API antwortet mit HTTP ${response.status}`);
        }

        if (typeof renderPlaylistPreview === 'function') {
          renderPlaylistPreview(data.playlist, data.tracks || []);
        } else {
          setInfo('Playlist geladen, aber renderPlaylistPreview fehlt im Frontend.');
        }
      } catch (error) {
        setInfo(`Playlist konnte nicht geladen werden: ${error.message}`);
      }
    }

    function scheduleAutoLoad() {
      clearTimeout(autoTimer);

      autoTimer = setTimeout(() => {
        const url = input.value.trim();

        if (looksLikePlaylistUrl(url)) {
          loadPlaylist();
        }
      }, 450);
    }

    loadBtn.addEventListener('click', (event) => {
      event.preventDefault();
      loadPlaylist();
    });

    input.addEventListener('paste', () => {
      setTimeout(scheduleAutoLoad, 80);
    });

    input.addEventListener('input', () => {
      const url = input.value.trim();

      if (looksLikePlaylistUrl(url)) {
        setInfo('Playlist-Link erkannt …');
        scheduleAutoLoad();
      }
    });

    input.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        loadPlaylist();
      }
    });

    if (pasteBtn) {
      pasteBtn.addEventListener('click', async (event) => {
        event.preventDefault();

        try {
          const text = await navigator.clipboard.readText();
          input.value = text.trim();
          await loadPlaylist();
        } catch {
          setInfo('Zwischenablage konnte nicht gelesen werden. Link bitte manuell einfügen.');
        }
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPlaylistImportStabilizer);
  } else {
    initPlaylistImportStabilizer();
  }
})();

/* --- Playlist Render Fallback --- */

window.currentPlaylistTracks = window.currentPlaylistTracks || [];

window.renderPlaylistPreview = function renderPlaylistPreview(playlist, tracks) {
  const playlistResults = document.querySelector('#playlist-results');
  const playlistInfo = document.querySelector('#playlist-info');
  const playlistActions = document.querySelector('#playlist-actions');

  if (!playlistResults || !playlistInfo) {
    return;
  }

  const loadedTracks = Array.isArray(tracks) ? tracks : [];
  window.currentPlaylistTracks = loadedTracks;

  playlistResults.innerHTML = '';

  if (!loadedTracks.length) {
    if (playlistActions) {
      playlistActions.hidden = true;
    }

    playlistInfo.textContent = 'Keine Videos in der Playlist gefunden.';
    return;
  }

  if (playlistActions) {
    playlistActions.hidden = false;
  }

  const title = playlist?.title || 'YouTube Playlist';
  const channel = playlist?.channel || '';
  const count = loadedTracks.length;

  playlistInfo.textContent = `${title}${channel ? ` · ${channel}` : ''} · ${count} Videos geladen`;

  for (const item of loadedTracks) {
    const card = document.createElement('article');
    card.className = 'track-card playlist-track-card';

    const thumbnail = item.thumbnail
      ? `<img src="${escapeHtml(item.thumbnail)}" alt="">`
      : `<span class="track-thumb-fallback">♪</span>`;

    const meta = [
      item.channel || '',
      item.added_by ? `von ${item.added_by}` : '',
      item.duration || '',
    ].filter(Boolean).join(' · ');

    card.innerHTML = `
      <div class="track-thumb">
        ${thumbnail}
      </div>

      <div class="track-main">
        <h3>${escapeHtml(item.title || 'Unbekannter Titel')}</h3>
        <p>${escapeHtml(meta)}</p>

        <div class="track-actions">
          <button data-action="play" type="button">▶ Jetzt</button>
          <button data-action="queue" type="button">＋ Queue</button>
        </div>
      </div>
    `;

    card.querySelector('[data-action="play"]').addEventListener('click', () => {
      playNow(item);
    });

    card.querySelector('[data-action="queue"]').addEventListener('click', () => {
      enqueue(item);
    });

    playlistResults.appendChild(card);
  }
};

/* --- Playlist Render Fallback --- */

window.currentPlaylistTracks = window.currentPlaylistTracks || [];

window.renderPlaylistPreview = function renderPlaylistPreview(playlist, tracks) {
  const playlistResults = document.querySelector('#playlist-results');
  const playlistInfo = document.querySelector('#playlist-info');
  const playlistActions = document.querySelector('#playlist-actions');

  if (!playlistResults || !playlistInfo) {
    return;
  }

  const loadedTracks = Array.isArray(tracks) ? tracks : [];
  window.currentPlaylistTracks = loadedTracks;

  playlistResults.innerHTML = '';

  if (!loadedTracks.length) {
    if (playlistActions) {
      playlistActions.hidden = true;
    }

    playlistInfo.textContent = 'Keine Videos in der Playlist gefunden.';
    return;
  }

  if (playlistActions) {
    playlistActions.hidden = false;
  }

  const title = playlist?.title || 'YouTube Playlist';
  const channel = playlist?.channel || '';
  const count = loadedTracks.length;

  playlistInfo.textContent = `${title}${channel ? ` · ${channel}` : ''} · ${count} Videos geladen`;

  for (const item of loadedTracks) {
    const card = document.createElement('article');
    card.className = 'track-card playlist-track-card';

    const thumbnail = item.thumbnail
      ? `<img src="${escapeHtml(item.thumbnail)}" alt="">`
      : `<span class="track-thumb-fallback">♪</span>`;

    const meta = [
      item.channel || '',
      item.added_by ? `von ${item.added_by}` : '',
      item.duration || '',
    ].filter(Boolean).join(' · ');

    card.innerHTML = `
      <div class="track-thumb">
        ${thumbnail}
      </div>

      <div class="track-main">
        <h3>${escapeHtml(item.title || 'Unbekannter Titel')}</h3>
        <p>${escapeHtml(meta)}</p>

        <div class="track-actions">
          <button data-action="play" type="button">▶ Jetzt</button>
          <button data-action="queue" type="button">＋ Queue</button>
        </div>
      </div>
    `;

    card.querySelector('[data-action="play"]').addEventListener('click', () => {
      playNow(item);
    });

    card.querySelector('[data-action="queue"]').addEventListener('click', () => {
      enqueue(item);
    });

    playlistResults.appendChild(card);
  }
};

/* --- Playlist Buttons Reliable Fix --- */

;(() => {
  window.julesPlaylistTracks = window.julesPlaylistTracks || [];

  const previousRenderPlaylistPreview =
    window.renderPlaylistPreview || null;

  window.renderPlaylistPreview = function renderPlaylistPreviewFixed(playlist, tracks) {
    const safeTracks = Array.isArray(tracks) ? tracks : [];

    window.julesPlaylistTracks = safeTracks;
    window.currentPlaylistTracks = safeTracks;

    if (typeof previousRenderPlaylistPreview === 'function') {
      previousRenderPlaylistPreview(playlist, safeTracks);
      return;
    }

    const playlistResults = document.querySelector('#playlist-results');
    const playlistInfo = document.querySelector('#playlist-info');
    const playlistActions = document.querySelector('#playlist-actions');

    if (!playlistResults || !playlistInfo) {
      return;
    }

    playlistResults.innerHTML = '';

    if (!safeTracks.length) {
      if (playlistActions) playlistActions.hidden = true;
      playlistInfo.textContent = 'Keine Videos in der Playlist gefunden.';
      return;
    }

    if (playlistActions) playlistActions.hidden = false;

    const title = playlist?.title || 'YouTube Playlist';
    const channel = playlist?.channel || '';

    playlistInfo.textContent =
      `${title}${channel ? ` · ${channel}` : ''} · ${safeTracks.length} Videos geladen`;

    for (const item of safeTracks) {
      const card = document.createElement('article');
      card.className = 'track-card playlist-track-card';

      card.innerHTML = `
        <div class="track-thumb">
          ${thumbnailHtml(item, 'track-thumb')}
        </div>

        <div class="track-main">
          <h3>${escapeHtml(item.title || 'Unbekannter Titel')}</h3>
          <p>${escapeHtml(trackMeta(item))}</p>

          <div class="track-actions">
            <button data-action="play" type="button">▶ Jetzt</button>
            <button data-action="queue" type="button">＋ Queue</button>
          </div>
        </div>
      `;

      card.querySelector('[data-action="play"]').addEventListener('click', () => playNow(item));
      card.querySelector('[data-action="queue"]').addEventListener('click', () => enqueue(item));

      playlistResults.appendChild(card);
    }
  };

  function shuffleTracks(tracks) {
    const copy = [...tracks];

    for (let i = copy.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }

    return copy;
  }

  async function enqueueMany(tracks) {
    const list = Array.isArray(tracks) ? tracks.filter(track => track && track.url) : [];

    if (!list.length) {
      setMessage('Keine Playlist-Tracks geladen.');
      return;
    }

    let added = 0;

    for (const track of list) {
      try {
        await enqueue(track);
        added += 1;
        setMessage(`Playlist wird hinzugefügt … ${added}/${list.length}`);
      } catch (error) {
        setMessage(`Playlist-Fehler nach ${added}/${list.length}: ${error.message}`);
        return;
      }
    }

    setMessage(`Playlist hinzugefügt: ${added}/${list.length} Songs.`);
    refreshStatus();
  }

  document.addEventListener('click', (event) => {
    const queueAll = event.target.closest('#playlist-queue-all-btn');
    const shuffleAll = event.target.closest('#playlist-shuffle-queue-btn');

    if (!queueAll && !shuffleAll) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    const tracks =
      window.julesPlaylistTracks ||
      window.currentPlaylistTracks ||
      [];

    if (queueAll) {
      enqueueMany(tracks);
      return;
    }

    if (shuffleAll) {
      enqueueMany(shuffleTracks(tracks));
    }
  }, true);
})();

/* --- Playlist History: zuletzt geladene Playlists merken --- */

;(() => {
  if (window.__julesPlaylistHistoryInstalled) {
    return;
  }

  window.__julesPlaylistHistoryInstalled = true;

  const STORAGE_KEY = 'julestube.playlist.history';
  const MAX_PLAYLISTS = 8;

  function readPlaylistHistory() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      const parsed = JSON.parse(raw || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function writePlaylistHistory(items) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_PLAYLISTS)));
  }

  function playlistTitle(playlist) {
    return String(playlist?.title || 'YouTube Playlist').trim();
  }

  function playlistUrl(playlist) {
    return String(playlist?.source_url || '').trim();
  }

  function savePlaylistToHistory(playlist, tracks) {
    const url = playlistUrl(playlist);

    if (!url) {
      return;
    }

    const item = {
      title: playlistTitle(playlist),
      channel: String(playlist?.channel || '').trim(),
      url,
      count: Array.isArray(tracks) ? tracks.length : Number(playlist?.count || 0),
      saved_at: new Date().toISOString(),
    };

    const existing = readPlaylistHistory()
      .filter((entry) => entry.url !== item.url);

    writePlaylistHistory([item, ...existing]);
  }

  function ensurePlaylistHistoryUi() {
    const card = document.querySelector('#playlist-card');
    const info = document.querySelector('#playlist-info');

    if (!card || !info) {
      return null;
    }

    let wrapper = document.querySelector('#playlist-history');

    if (wrapper) {
      return wrapper;
    }

    wrapper = document.createElement('section');
    wrapper.id = 'playlist-history';
    wrapper.className = 'playlist-history';
    wrapper.innerHTML = `
      <div class="playlist-history-heading">
        <p class="mini-label">Shortcuts</p>
        <h3>Zuletzt geladene Playlists</h3>
      </div>
      <div id="playlist-history-list" class="playlist-history-list"></div>
    `;

    info.insertAdjacentElement('afterend', wrapper);

    return wrapper;
  }

  function renderPlaylistHistory() {
    const wrapper = ensurePlaylistHistoryUi();

    if (!wrapper) {
      return;
    }

    const list = wrapper.querySelector('#playlist-history-list');
    const items = readPlaylistHistory();

    list.innerHTML = '';

    if (!items.length) {
      const empty = document.createElement('p');
      empty.className = 'playlist-history-empty';
      empty.textContent = 'Noch keine Playlist geladen.';
      list.appendChild(empty);
      return;
    }

    for (const item of items) {
      const row = document.createElement('article');
      row.className = 'playlist-history-item';

      const main = document.createElement('button');
      main.type = 'button';
      main.className = 'playlist-history-load';
      main.dataset.playlistLoadUrl = item.url;

      const title = document.createElement('strong');
      title.textContent = item.title || 'YouTube Playlist';

      const meta = document.createElement('span');
      meta.textContent = [
        item.channel || '',
        item.count ? `${item.count} Videos` : '',
      ].filter(Boolean).join(' · ');

      main.appendChild(title);
      main.appendChild(meta);

      const remove = document.createElement('button');
      remove.type = 'button';
      remove.className = 'playlist-history-remove';
      remove.dataset.playlistRemoveUrl = item.url;
      remove.textContent = '×';
      remove.title = 'Aus Verlauf entfernen';

      row.appendChild(main);
      row.appendChild(remove);
      list.appendChild(row);
    }
  }

  async function loadPlaylistUrl(url) {
    const input = document.querySelector('#playlist-url-input');
    const info = document.querySelector('#playlist-info');
    const actions = document.querySelector('#playlist-actions');
    const results = document.querySelector('#playlist-results');

    if (input) {
      input.value = url;
    }

    if (info) {
      info.textContent = 'Playlist wird geladen …';
    }

    if (actions) {
      actions.hidden = true;
    }

    if (results) {
      results.innerHTML = '';
    }

    try {
      const response = await fetch('/api/playlist/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url,
          limit: 20,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      if (typeof window.renderPlaylistPreview === 'function') {
        window.renderPlaylistPreview(data.playlist, data.tracks || []);
      } else if (info) {
        info.textContent = 'Playlist geladen, aber Anzeige-Funktion fehlt.';
      }
    } catch (error) {
      if (info) {
        info.textContent = `Playlist konnte nicht geladen werden: ${error.message}`;
      }
    }
  }

  const previousRenderPlaylistPreview = window.renderPlaylistPreview;

  window.renderPlaylistPreview = function renderPlaylistPreviewWithHistory(playlist, tracks) {
    savePlaylistToHistory(playlist, tracks);

    if (typeof previousRenderPlaylistPreview === 'function') {
      previousRenderPlaylistPreview(playlist, tracks);
    }

    renderPlaylistHistory();
  };

  document.addEventListener('click', (event) => {
    const loadButton = event.target.closest('[data-playlist-load-url]');
    const removeButton = event.target.closest('[data-playlist-remove-url]');

    if (loadButton) {
      event.preventDefault();
      loadPlaylistUrl(loadButton.dataset.playlistLoadUrl);
      return;
    }

    if (removeButton) {
      event.preventDefault();

      const url = removeButton.dataset.playlistRemoveUrl;
      const nextItems = readPlaylistHistory()
        .filter((item) => item.url !== url);

      writePlaylistHistory(nextItems);
      renderPlaylistHistory();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderPlaylistHistory);
  } else {
    renderPlaylistHistory();
  }
})();

/* --- YouTube Account Lists --- */

;(() => {
  if (window.__julesYoutubeAccountListsInstalled) {
    return;
  }

  window.__julesYoutubeAccountListsInstalled = true;

  function ensureYoutubeAccountUi() {
    const playlistCard = document.querySelector('#playlist-card');
    const playlistInfo = document.querySelector('#playlist-info');

    if (!playlistCard || !playlistInfo) {
      return null;
    }

    let wrapper = document.querySelector('#youtube-account-lists');

    if (wrapper) {
      return wrapper;
    }

    wrapper = document.createElement('section');
    wrapper.id = 'youtube-account-lists';
    wrapper.className = 'youtube-account-lists';

    wrapper.innerHTML = `
      <div class="youtube-account-heading">
        <div>
          <p class="mini-label">YouTube Login</p>
          <h3>Meine YouTube-Listen</h3>
        </div>
        <button id="youtube-account-refresh-btn" class="ghost-button" type="button">Aktualisieren</button>
      </div>

      <p id="youtube-account-status" class="empty-note">
        Lädt deine YouTube-Listen über Firefox-Cookies …
      </p>

      <div id="youtube-account-feed-list" class="youtube-account-feed-list"></div>
    `;

    playlistInfo.insertAdjacentElement('afterend', wrapper);
    return wrapper;
  }

  function setYoutubeAccountStatus(text) {
    const status = document.querySelector('#youtube-account-status');

    if (status) {
      status.textContent = text || '';
    }
  }

  function renderYoutubeAccountFeeds(feeds) {
    const wrapper = ensureYoutubeAccountUi();

    if (!wrapper) {
      return;
    }

    const list = wrapper.querySelector('#youtube-account-feed-list');
    list.innerHTML = '';

    if (!Array.isArray(feeds) || !feeds.length) {
      setYoutubeAccountStatus('Keine YouTube-Listen gefunden.');
      return;
    }

    setYoutubeAccountStatus('Wähle eine YouTube-Liste aus.');

    for (const feed of feeds) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'youtube-account-feed-button';
      button.dataset.youtubeFeedId = feed.id;

      button.innerHTML = `
        <strong>${escapeHtml(feed.title || 'YouTube-Liste')}</strong>
        <span>${escapeHtml(feed.description || '')}</span>
      `;

      list.appendChild(button);
    }
  }

  async function loadYoutubeAccountFeeds() {
    ensureYoutubeAccountUi();
    setYoutubeAccountStatus('YouTube-Listen werden geladen …');

    try {
      const response = await fetch('/api/youtube/account-feeds');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      renderYoutubeAccountFeeds(data.feeds || []);
    } catch (error) {
      setYoutubeAccountStatus(`YouTube-Listen konnten nicht geladen werden: ${error.message}`);
    }
  }

  async function loadYoutubeAccountFeedPreview(feedId) {
    const playlistInfo = document.querySelector('#playlist-info');
    const playlistActions = document.querySelector('#playlist-actions');
    const playlistResults = document.querySelector('#playlist-results');

    if (playlistInfo) {
      playlistInfo.textContent = 'YouTube-Liste wird geladen …';
    }

    if (playlistActions) {
      playlistActions.hidden = true;
    }

    if (playlistResults) {
      playlistResults.innerHTML = '';
    }

    try {
      const response = await fetch('/api/youtube/account-feed/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          feed_id: feedId,
          limit: 20,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      if (typeof window.renderPlaylistPreview !== 'function') {
        throw new Error('Playlist-Anzeige fehlt im Frontend.');
      }

      window.renderPlaylistPreview(data.playlist, data.tracks || []);

      const playlistInput = document.querySelector('#playlist-url-input');
      if (playlistInput) {
        playlistInput.value = '';
      }

      setYoutubeAccountStatus('YouTube-Liste geladen.');
    } catch (error) {
      if (playlistInfo) {
        playlistInfo.textContent = `YouTube-Liste konnte nicht geladen werden: ${error.message}`;
      }

      setYoutubeAccountStatus('Fehler beim Laden der YouTube-Liste.');
    }
  }

  document.addEventListener('click', (event) => {
    const feedButton = event.target.closest('[data-youtube-feed-id]');
    const refreshButton = event.target.closest('#youtube-account-refresh-btn');

    if (feedButton) {
      event.preventDefault();
      loadYoutubeAccountFeedPreview(feedButton.dataset.youtubeFeedId);
      return;
    }

    if (refreshButton) {
      event.preventDefault();
      loadYoutubeAccountFeeds();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadYoutubeAccountFeeds);
  } else {
    loadYoutubeAccountFeeds();
  }
})();

/* --- YouTube Account Lists --- */

;(() => {
  if (window.__julesYoutubeAccountListsInstalled) {
    return;
  }

  window.__julesYoutubeAccountListsInstalled = true;

  function ensureYoutubeAccountUi() {
    const playlistCard = document.querySelector('#playlist-card');
    const playlistInfo = document.querySelector('#playlist-info');

    if (!playlistCard || !playlistInfo) {
      return null;
    }

    let wrapper = document.querySelector('#youtube-account-lists');

    if (wrapper) {
      return wrapper;
    }

    wrapper = document.createElement('section');
    wrapper.id = 'youtube-account-lists';
    wrapper.className = 'youtube-account-lists';

    wrapper.innerHTML = `
      <div class="youtube-account-heading">
        <div>
          <p class="mini-label">YouTube Login</p>
          <h3>Meine YouTube-Listen</h3>
        </div>
        <button id="youtube-account-refresh-btn" class="ghost-button" type="button">Aktualisieren</button>
      </div>

      <p id="youtube-account-status" class="empty-note">
        Lädt deine YouTube-Listen über Firefox-Cookies …
      </p>

      <div id="youtube-account-feed-list" class="youtube-account-feed-list"></div>
    `;

    playlistInfo.insertAdjacentElement('afterend', wrapper);
    return wrapper;
  }

  function setYoutubeAccountStatus(text) {
    const status = document.querySelector('#youtube-account-status');

    if (status) {
      status.textContent = text || '';
    }
  }

  function renderYoutubeAccountFeeds(feeds) {
    const wrapper = ensureYoutubeAccountUi();

    if (!wrapper) {
      return;
    }

    const list = wrapper.querySelector('#youtube-account-feed-list');
    list.innerHTML = '';

    if (!Array.isArray(feeds) || !feeds.length) {
      setYoutubeAccountStatus('Keine YouTube-Listen gefunden.');
      return;
    }

    setYoutubeAccountStatus('Wähle eine YouTube-Liste aus.');

    for (const feed of feeds) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'youtube-account-feed-button';
      button.dataset.youtubeFeedId = feed.id;

      button.innerHTML = `
        <strong>${escapeHtml(feed.title || 'YouTube-Liste')}</strong>
        <span>${escapeHtml(feed.description || '')}</span>
      `;

      list.appendChild(button);
    }
  }

  async function loadYoutubeAccountFeeds() {
    ensureYoutubeAccountUi();
    setYoutubeAccountStatus('YouTube-Listen werden geladen …');

    try {
      const response = await fetch('/api/youtube/account-feeds');
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      renderYoutubeAccountFeeds(data.feeds || []);
    } catch (error) {
      setYoutubeAccountStatus(`YouTube-Listen konnten nicht geladen werden: ${error.message}`);
    }
  }

  async function loadYoutubeAccountFeedPreview(feedId) {
    const playlistInfo = document.querySelector('#playlist-info');
    const playlistActions = document.querySelector('#playlist-actions');
    const playlistResults = document.querySelector('#playlist-results');

    if (playlistInfo) {
      playlistInfo.textContent = 'YouTube-Liste wird geladen …';
    }

    if (playlistActions) {
      playlistActions.hidden = true;
    }

    if (playlistResults) {
      playlistResults.innerHTML = '';
    }

    try {
      const response = await fetch('/api/youtube/account-feed/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          feed_id: feedId,
          limit: 20,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      if (typeof window.renderPlaylistPreview !== 'function') {
        throw new Error('Playlist-Anzeige fehlt im Frontend.');
      }

      window.renderPlaylistPreview(data.playlist, data.tracks || []);

      const playlistInput = document.querySelector('#playlist-url-input');
      if (playlistInput) {
        playlistInput.value = '';
      }

      setYoutubeAccountStatus('YouTube-Liste geladen.');
    } catch (error) {
      if (playlistInfo) {
        playlistInfo.textContent = `YouTube-Liste konnte nicht geladen werden: ${error.message}`;
      }

      setYoutubeAccountStatus('Fehler beim Laden der YouTube-Liste.');
    }
  }

  document.addEventListener('click', (event) => {
    const feedButton = event.target.closest('[data-youtube-feed-id]');
    const refreshButton = event.target.closest('#youtube-account-refresh-btn');

    if (feedButton) {
      event.preventDefault();
      loadYoutubeAccountFeedPreview(feedButton.dataset.youtubeFeedId);
      return;
    }

    if (refreshButton) {
      event.preventDefault();
      loadYoutubeAccountFeeds();
    }
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadYoutubeAccountFeeds);
  } else {
    loadYoutubeAccountFeeds();
  }
})();


// JulesTube voice search v1
document.addEventListener("DOMContentLoaded", () => {
  const voiceButton = document.getElementById("voice-search-btn");
  const searchInput = document.getElementById("search-input");
  const searchForm = document.getElementById("search-form");

  if (!voiceButton || !searchInput || !searchForm) {
    console.warn("JulesTube: Elemente für Sprachsuche fehlen.");
    return;
  }

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    voiceButton.addEventListener("click", () => {
      alert(
        "Dieser Browser unterstützt die direkte Spracherkennung nicht. " +
        "Bitte Chrome auf Android verwenden."
      );
    });
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "de-AT";
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;

  voiceButton.addEventListener("click", () => {
    try {
      recognition.start();
    } catch (error) {
      console.warn("Spracherkennung läuft möglicherweise bereits:", error);
    }
  });

  recognition.addEventListener("start", () => {
    voiceButton.classList.add("is-listening");
    voiceButton.title = "Ich höre zu …";
  });

  recognition.addEventListener("result", (event) => {
    const spokenText =
      event.results?.[0]?.[0]?.transcript?.trim() || "";

    if (!spokenText) {
      return;
    }

    searchInput.value = spokenText;
    searchInput.dispatchEvent(new Event("input", { bubbles: true }));

    if (typeof searchForm.requestSubmit === "function") {
      searchForm.requestSubmit();
    } else {
      searchForm.dispatchEvent(
        new Event("submit", {
          bubbles: true,
          cancelable: true
        })
      );
    }
  });

  recognition.addEventListener("end", () => {
    voiceButton.classList.remove("is-listening");
    voiceButton.title = "Spracheingabe starten";
  });

  recognition.addEventListener("error", (event) => {
    voiceButton.classList.remove("is-listening");
    voiceButton.title = "Spracheingabe starten";
    console.warn("Spracherkennung:", event.error);
  });
});

// JulesTube Sprachsuche: sichtbare Diagnose
document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("voice-search-btn");
  const input = document.getElementById("search-input");
  const form = document.getElementById("search-form");

  if (!button || !input || !form) {
    return;
  }

  let status = document.getElementById("voice-search-status");

  if (!status) {
    status = document.createElement("p");
    status.id = "voice-search-status";
    status.setAttribute("aria-live", "polite");
    form.insertAdjacentElement("afterend", status);
  }

  const Recognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  function showStatus(text, error = false) {
    status.textContent = text;
    status.classList.toggle("voice-error", error);
  }

  if (!window.isSecureContext) {
    showStatus(
      "Sprachsuche benötigt HTTPS. Die aktuelle HTTP-Adresse darf das Mikrofon nicht verwenden.",
      true
    );
  }

  if (!Recognition) {
    showStatus(
      "Dieser Browser unterstützt die direkte Sprachsuche nicht. Bitte Chrome auf Android verwenden.",
      true
    );
    return;
  }

  const recognition = new Recognition();

  recognition.lang = "de-AT";
  recognition.interimResults = false;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;

  button.onclick = async () => {
    if (!window.isSecureContext) {
      showStatus(
        "Mikrofon blockiert: JulesTube läuft noch über HTTP statt HTTPS.",
        true
      );
      return;
    }

    try {
      button.classList.add("is-listening");
      showStatus("Ich höre zu …");
      recognition.start();
    } catch (error) {
      button.classList.remove("is-listening");
      showStatus(`Sprachsuche konnte nicht starten: ${error.message}`, true);
    }
  };

  recognition.onresult = (event) => {
    const spokenText =
      event.results?.[0]?.[0]?.transcript?.trim() || "";

    if (!spokenText) {
      showStatus("Ich konnte leider nichts verstehen.", true);
      return;
    }

    input.value = spokenText;
    input.dispatchEvent(new Event("input", { bubbles: true }));
    showStatus(`Erkannt: „${spokenText}“`);

    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
    }
  };

  recognition.onerror = (event) => {
    button.classList.remove("is-listening");

    const messages = {
      "not-allowed": "Mikrofonzugriff wurde blockiert oder nicht erlaubt.",
      "service-not-allowed": "Der Spracherkennungsdienst wurde blockiert.",
      "audio-capture": "Auf das Mikrofon konnte nicht zugegriffen werden.",
      "no-speech": "Es wurde keine Sprache erkannt.",
      network: "Der Spracherkennungsdienst ist nicht erreichbar."
    };

    showStatus(
      messages[event.error] || `Sprachfehler: ${event.error}`,
      true
    );
  };

  recognition.onend = () => {
    button.classList.remove("is-listening");
  };
});


// JulesTube: persönliche YouTube-Playlists
(() => {
  const FEATURE_MARKER = 'julestube-my-youtube-playlists';

  function createPlaylistSection() {
    if (document.getElementById(FEATURE_MARKER)) {
      return document.getElementById(FEATURE_MARKER);
    }

    const playlistCard = document.querySelector('#playlist-card');

    if (!playlistCard) {
      return null;
    }

    const section = document.createElement('section');
    section.id = FEATURE_MARKER;
    section.className = 'youtube-my-playlists';

    section.innerHTML = `
      <div class="section-heading">
        <div>
          <p class="mini-label">Dein Account</p>
          <h2>Meine YouTube-Playlists</h2>
        </div>

        <button
          id="youtube-my-playlists-refresh"
          class="ghost-button"
          type="button"
        >
          Aktualisieren
        </button>
      </div>

      <p
        id="youtube-my-playlists-status"
        class="empty-note"
        aria-live="polite"
      >
        Playlists werden geladen …
      </p>

      <div
        id="youtube-my-playlists-list"
        class="youtube-my-playlists-list"
      ></div>
    `;

    playlistCard.appendChild(section);
    return section;
  }

  function setStatus(message) {
    const status = document.querySelector(
      '#youtube-my-playlists-status'
    );

    if (status) {
      status.textContent = message;
    }
  }

  function renderPlaylists(playlists) {
    const list = document.querySelector(
      '#youtube-my-playlists-list'
    );

    if (!list) {
      return;
    }

    list.innerHTML = '';

    if (!Array.isArray(playlists) || playlists.length === 0) {
      setStatus('Keine YouTube-Playlists gefunden.');
      return;
    }

    setStatus(`${playlists.length} Playlists gefunden`);

    playlists.forEach((playlist) => {
      const card = document.createElement('article');
      card.className = 'youtube-playlist-card';

      const thumbnail = playlist.thumbnail
        ? `
          <img
            class="youtube-playlist-thumbnail"
            src="${playlist.thumbnail}"
            alt=""
            loading="lazy"
          >
        `
        : `
          <div class="youtube-playlist-thumbnail is-empty">
            ▶
          </div>
        `;

      const count = Number(playlist.count || 0);

      card.innerHTML = `
        ${thumbnail}

        <div class="youtube-playlist-card-content">
          <strong>${playlist.title || 'Unbenannte Playlist'}</strong>
          <span>${count} Videos</span>

          <button
            class="ghost-button youtube-playlist-open"
            type="button"
            data-youtube-playlist-id="${playlist.id || ''}"
            data-youtube-playlist-title="${encodeURIComponent(
              playlist.title || 'YouTube Playlist'
            )}"
          >
            Öffnen
          </button>
        </div>
      `;

      list.appendChild(card);
    });
  }

  async function loadMyPlaylists() {
    createPlaylistSection();
    setStatus('Playlists werden geladen …');

    try {
      const response = await fetch(
        '/api/youtube/my-playlists?limit=100',
        {
          cache: 'no-store',
        }
      );

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error(
            'Bitte zuerst oben rechts mit YouTube anmelden.'
          );
        }

        throw new Error(
          data.error || `HTTP ${response.status}`
        );
      }

      renderPlaylists(data.playlists || []);
    } catch (error) {
      console.error(
        'YouTube-Playlists konnten nicht geladen werden:',
        error
      );

      setStatus(
        `Playlists konnten nicht geladen werden: ${error.message}`
      );
    }
  }

  async function openPlaylist(button) {
    const playlistId = button.dataset.youtubePlaylistId;
    const playlistTitle = decodeURIComponent(
      button.dataset.youtubePlaylistTitle || 'YouTube Playlist'
    );

    if (!playlistId) {
      return;
    }

    button.disabled = true;
    button.textContent = 'Lädt …';
    setStatus(`„${playlistTitle}“ wird geöffnet …`);

    try {
      const response = await fetch(
        `/api/youtube/my-playlist/${encodeURIComponent(
          playlistId
        )}?limit=500`,
        {
          cache: 'no-store',
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || `HTTP ${response.status}`
        );
      }

      if (typeof window.renderPlaylistPreview !== 'function') {
        throw new Error(
          'Die Playlist-Vorschau ist im Frontend nicht verfügbar.'
        );
      }

      window.renderPlaylistPreview(
        {
          id: playlistId,
          title: playlistTitle,
          channel: 'Dein YouTube-Account',
          count: data.count || 0,
          source_url: '',
        },
        data.tracks || []
      );

      setStatus(
        `„${playlistTitle}“ mit ${data.count || 0} Videos geladen`
      );

      const playlistCard = document.querySelector('#playlist-card');

      if (playlistCard) {
        playlistCard.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }
    } catch (error) {
      console.error(
        'YouTube-Playlist konnte nicht geöffnet werden:',
        error
      );

      setStatus(
        `Playlist konnte nicht geöffnet werden: ${error.message}`
      );
    } finally {
      button.disabled = false;
      button.textContent = 'Öffnen';
    }
  }

  document.addEventListener('click', (event) => {
    const refreshButton = event.target.closest(
      '#youtube-my-playlists-refresh'
    );

    if (refreshButton) {
      loadMyPlaylists();
      return;
    }

    const openButton = event.target.closest(
      '[data-youtube-playlist-id]'
    );

    if (openButton) {
      openPlaylist(openButton);
    }
  });

  document.addEventListener('DOMContentLoaded', () => {
    createPlaylistSection();
    loadMyPlaylists();
  });
})();


// JulesTube: YouTube-Profil und Konto-Menü
(() => {
  function createAccountMenu() {
    const signInLink =
      document.getElementById('youtube-signin') ||
      document.querySelector('.signin');

    if (!signInLink) {
      return null;
    }

    let wrapper = document.getElementById(
      'youtube-account-menu'
    );

    if (wrapper) {
      return wrapper;
    }

    wrapper = document.createElement('div');
    wrapper.id = 'youtube-account-menu';
    wrapper.className = 'youtube-account-menu';

    signInLink.parentNode.insertBefore(
      wrapper,
      signInLink
    );

    wrapper.appendChild(signInLink);

    const dropdown = document.createElement('div');
    dropdown.id = 'youtube-account-dropdown';
    dropdown.className = 'youtube-account-dropdown';
    dropdown.hidden = true;

    dropdown.innerHTML = `
      <div class="youtube-account-summary">
        <img
          id="youtube-account-dropdown-avatar"
          class="youtube-account-dropdown-avatar"
          alt=""
          hidden
        >

        <div>
          <span class="mini-label">YouTube</span>
          <strong id="youtube-account-dropdown-name">
            Nicht angemeldet
          </strong>
        </div>
      </div>

      <button
        id="youtube-account-playlists"
        class="youtube-account-menu-item"
        type="button"
      >
        Meine Playlists
      </button>

      <a
        class="youtube-account-menu-item"
        href="/auth/youtube/logout"
      >
        Abmelden
      </a>
    `;

    wrapper.appendChild(dropdown);

    return wrapper;
  }

  function showSignedOut(link, dropdown) {
    link.href = '/auth/youtube/login';
    link.classList.remove('is-signed-in');
    link.innerHTML = '<span>Sign in</span>';

    if (dropdown) {
      dropdown.hidden = true;
    }
  }

  function showSignedIn(link, dropdown, data) {
    const channelName =
      data.channel_title || 'YouTube';

    const avatar = data.thumbnail
      ? `
        <img
          class="youtube-account-avatar"
          src="${data.thumbnail}"
          alt=""
        >
      `
      : `
        <span class="youtube-account-avatar is-empty">
          ▶
        </span>
      `;

    link.href = '#youtube-account-menu';
    link.classList.add('is-signed-in');
    link.setAttribute('aria-haspopup', 'true');
    link.setAttribute('aria-expanded', 'false');

    link.innerHTML = `
      ${avatar}
      <span class="youtube-account-name">
        ${channelName}
      </span>
      <span
        class="youtube-account-chevron"
        aria-hidden="true"
      >
        ▾
      </span>
    `;

    const dropdownName = document.getElementById(
      'youtube-account-dropdown-name'
    );
    const dropdownAvatar = document.getElementById(
      'youtube-account-dropdown-avatar'
    );

    if (dropdownName) {
      dropdownName.textContent = channelName;
    }

    if (dropdownAvatar && data.thumbnail) {
      dropdownAvatar.src = data.thumbnail;
      dropdownAvatar.hidden = false;
    }

    dropdown.hidden = true;
  }

  async function loadYoutubeAccountProfile() {
    const wrapper = createAccountMenu();

    if (!wrapper) {
      return;
    }

    const link =
      document.getElementById('youtube-signin') ||
      wrapper.querySelector('.signin');

    const dropdown = document.getElementById(
      'youtube-account-dropdown'
    );

    if (!link || !dropdown) {
      return;
    }

    try {
      const response = await fetch(
        '/api/youtube/account/status',
        {
          cache: 'no-store',
        }
      );

      const data = await response.json();

      if (!response.ok || !data.signed_in) {
        showSignedOut(link, dropdown);
        return;
      }

      showSignedIn(link, dropdown, data);
    } catch (error) {
      console.warn(
        'YouTube-Kontoprofil konnte nicht geladen werden:',
        error
      );

      showSignedOut(link, dropdown);
    }
  }

  document.addEventListener('click', (event) => {
    const wrapper = document.getElementById(
      'youtube-account-menu'
    );
    const link = document.getElementById(
      'youtube-signin'
    );
    const dropdown = document.getElementById(
      'youtube-account-dropdown'
    );

    if (!wrapper || !link || !dropdown) {
      return;
    }

    if (
      event.target.closest('#youtube-signin') &&
      link.classList.contains('is-signed-in')
    ) {
      event.preventDefault();

      dropdown.hidden = !dropdown.hidden;

      link.setAttribute(
        'aria-expanded',
        dropdown.hidden ? 'false' : 'true'
      );

      return;
    }

    const playlistsButton = event.target.closest(
      '#youtube-account-playlists'
    );

    if (playlistsButton) {
      dropdown.hidden = true;

      const playlistSection = document.getElementById(
        'julestube-my-youtube-playlists'
      );

      if (playlistSection) {
        playlistSection.scrollIntoView({
          behavior: 'smooth',
          block: 'start',
        });
      }

      return;
    }

    if (!wrapper.contains(event.target)) {
      dropdown.hidden = true;
      link.setAttribute('aria-expanded', 'false');
    }
  });

  document.addEventListener(
    'keydown',
    (event) => {
      if (event.key !== 'Escape') {
        return;
      }

      const dropdown = document.getElementById(
        'youtube-account-dropdown'
      );
      const link = document.getElementById(
        'youtube-signin'
      );

      if (dropdown) {
        dropdown.hidden = true;
      }

      if (link) {
        link.setAttribute('aria-expanded', 'false');
      }
    }
  );

  document.addEventListener(
    'DOMContentLoaded',
    loadYoutubeAccountProfile
  );
})();


// JulesTube: Abend exportieren
(() => {
  const SECTION_ID = 'history-export-card';

  function localDateString(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');

    return `${year}-${month}-${day}`;
  }

  function yesterdayString() {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    return localDateString(date);
  }

  function createExportCard() {
    if (document.getElementById(SECTION_ID)) {
      return document.getElementById(SECTION_ID);
    }

    const historyPanel = document.querySelector('.history-panel');

    if (!historyPanel) {
      console.warn(
        'JulesTube: History-Panel für Export nicht gefunden.'
      );
      return null;
    }

    const card = document.createElement('section');
    card.id = SECTION_ID;
    card.className = 'history-export-card';

    card.innerHTML = `
      <div class="section-heading history-export-heading">
        <div>
          <p class="mini-label">Dein Sofa-Soundtrack</p>
          <h2>Abend exportieren</h2>
        </div>
      </div>

      <p class="history-export-description">
        Wähle einen Tag und lade die komplette Hörhistorie
        als CSV oder JSON herunter.
      </p>

      <div class="history-export-controls">
        <label class="history-export-date-field">
          <span>Datum</span>
          <input
            id="history-export-date"
            type="date"
            value="${yesterdayString()}"
          >
        </label>

        <button
          id="history-export-yesterday"
          class="ghost-button"
          type="button"
        >
          Gestern
        </button>
      </div>

      <p
        id="history-export-status"
        class="history-export-status"
        aria-live="polite"
      >
        Datum auswählen, um den Abend zu prüfen.
      </p>

      <div class="history-export-actions">
        <a
          id="history-export-csv"
          class="ghost-button history-export-download"
          href="#"
          download
        >
          CSV herunterladen
        </a>

        <a
          id="history-export-json"
          class="ghost-button history-export-download"
          href="#"
          download
        >
          JSON herunterladen
        </a>
      </div>
    `;

    historyPanel.insertAdjacentElement('afterend', card);
    return card;
  }

  function selectedDate() {
    return document.querySelector('#history-export-date')?.value || '';
  }

  function updateDownloadLinks(dateValue) {
    const csvLink = document.querySelector('#history-export-csv');
    const jsonLink = document.querySelector('#history-export-json');

    if (!csvLink || !jsonLink || !dateValue) {
      return;
    }

    const encodedDate = encodeURIComponent(dateValue);

    csvLink.href =
      `/api/history/export.csv?date=${encodedDate}`;

    jsonLink.href =
      `/api/history/export.json?date=${encodedDate}`;

    csvLink.download =
      `julestube-abend-${dateValue}.csv`;

    jsonLink.download =
      `julestube-abend-${dateValue}.json`;
  }

  async function loadExportSummary() {
    const dateValue = selectedDate();
    const status = document.querySelector(
      '#history-export-status'
    );

    if (!status || !dateValue) {
      return;
    }

    updateDownloadLinks(dateValue);
    status.textContent = 'Abend wird geprüft …';

    try {
      const response = await fetch(
        `/api/history/day?date=${encodeURIComponent(dateValue)}`,
        {
          cache: 'no-store',
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.error || `HTTP ${response.status}`
        );
      }

      const count = Number(data.count || 0);

      if (count === 0) {
        status.textContent =
          `Für den ${dateValue} wurden keine Songs gefunden.`;
        return;
      }

      status.textContent =
        `${count} ${count === 1 ? 'Song' : 'Songs'} ` +
        `für den ${dateValue} gefunden.`;
    } catch (error) {
      console.error(
        'History-Zusammenfassung konnte nicht geladen werden:',
        error
      );

      status.textContent =
        `Export konnte nicht vorbereitet werden: ${error.message}`;
    }
  }

  document.addEventListener('change', (event) => {
    if (event.target.matches('#history-export-date')) {
      loadExportSummary();
    }
  });

  document.addEventListener('click', (event) => {
    const yesterdayButton = event.target.closest(
      '#history-export-yesterday'
    );

    if (!yesterdayButton) {
      return;
    }

    const input = document.querySelector(
      '#history-export-date'
    );

    if (!input) {
      return;
    }

    input.value = yesterdayString();
    loadExportSummary();
  });

  document.addEventListener('DOMContentLoaded', () => {
    createExportCard();
    loadExportSummary();
  });
})();


// Link von "Abend exportieren" zum Sofa-Soundtrack
document.addEventListener("DOMContentLoaded", () => {
  const actions = document.querySelector(
    ".history-export-actions"
  );

  const dateInput = document.querySelector(
    "#history-export-date"
  );

  if (!actions || !dateInput) {
    return;
  }

  let link = document.getElementById(
    "history-open-soundtrack"
  );

  if (!link) {
    link = document.createElement("a");
    link.id = "history-open-soundtrack";
    link.className =
      "ghost-button history-export-download";
    link.textContent = "Sofa-Soundtrack öffnen";
    actions.prepend(link);
  }

  function updateLink() {
    link.href =
      `/soundtrack?date=${encodeURIComponent(dateInput.value)}`;
  }

  dateInput.addEventListener("change", updateLink);
  updateLink();
});
