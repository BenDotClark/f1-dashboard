// static/js/main.js

// 1. DOM References & Team Colors
const tableBody    = document.querySelector('#results-table tbody');
const yearSelect   = document.getElementById('year-select');
const raceSelect   = document.getElementById('race-select');
const sessionSelect = document.getElementById('session-select');
const loadingEl = document.getElementById('loading-indicator');
const errorEl   = document.getElementById('error-message');

// Mapping of constructor names to hex colors
const teamColors = {
  'Mercedes':      '#00D7B6',
  'Red Bull Racing':'#4781D7',
  'Ferrari':       '#ED1131',
  'McLaren':       '#F47600',
  'Alpine':        '#00A1E8',
  'Racing Bulls':  '#6C98FF',
  'Aston Martin':  '#229971',
  'Williams':      '#1868DB',
  'Kick Sauber':   '#01C00E',
  'Haas':          '#9C9FA2'
};

// 2. Utility functions
function showLoading() {
  errorEl.classList.add('hidden');
  loadingEl.classList.remove('hidden');
  document.getElementById('main-content')
          .setAttribute('aria-busy','true');
  setControlsEnabled(false);
}
function hideLoading() {
  loadingEl.classList.add('hidden');
  document.getElementById('main-content')
          .setAttribute('aria-busy','false');
  setControlsEnabled(true);
}
function showError(msg) {
  errorEl.textContent = msg;
  errorEl.classList.remove('hidden');
}

// disable/enable all controls while loading
function setControlsEnabled(enabled) {
  [yearSelect, raceSelect, sessionSelect].forEach(el => el.disabled = !enabled);
}

// A wrapper around fetch() to show spinner + error banner automatically
async function safeFetch(url, opts) {
  showLoading();
  try {
    const res = await fetch(url, opts);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return await res.json();
  } catch (e) {
    console.error('Fetch error:', e);
    showError('Oops! Something went wrong. Please try again.');
    throw e;    // so callers stop further processing
  } finally {
    hideLoading();
  }
}

// 3. Populate Year & Race dropdowns
async function initControls(season) {
  yearSelect.innerHTML = '';
  raceSelect.innerHTML = '';

  yearSelect.append(new Option(season, season));

  // now use safeFetch
  const { races } = await safeFetch(`/api/calendar/${season}`);
  races.forEach(r => {
    raceSelect.append(new Option(`${r.round} – ${r.raceName}`, r.round));
  });
  sessionSelect.value = 'R';
}

// 4. Render Table Rows
function renderTable(results) {
  errorEl.classList.add('hidden');   // clear old errors
  tableBody.innerHTML = '';

  if (results.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 3;                         // one cell across all 3 columns
    td.textContent = 'No results for this session.';
    td.style.textAlign = 'center';
    tr.appendChild(td);
    tableBody.appendChild(tr);
    return;
  }

  results.forEach(res => {
    const tr = document.createElement('tr');
    tr.style.setProperty('--team-color', teamColors[res.constructor] || '#ccc');
    tr.classList.add('team-row');

    // Position cell
    const tdPos = document.createElement('td');
    tdPos.textContent = res.position;
    tr.appendChild(tdPos);

    // Driver + coloured bar
    const tdDriver = document.createElement('td');
    const bar = document.createElement('span');
    bar.classList.add('team-bar');
    tdDriver.append(bar, document.createTextNode(res.driver));
    tr.appendChild(tdDriver);

    // Time / Gap cell
    const tdTime = document.createElement('td');
    let txt = res.time || res.gap || '';
    tdTime.textContent = txt;
    tr.appendChild(tdTime);

    tableBody.appendChild(tr);
  });
}

// 5. Fetch & render for a given year/round/session
async function fetchAndRenderResults() {
  try {
    const yr = yearSelect.value;
    const rd = raceSelect.value;
    const ss = sessionSelect.value;
    const { results } = await safeFetch(
      `/api/season/${yr}/results/${rd}?session=${ss}`
    );
    renderTable(results);
  } catch (_) {
    // error banner already shown
  }
}

// 6. Load latest on page load (and when year changes)
async function loadLatest() {
  try {
    // Determine the current year
    const year = new Date().getFullYear();
    await initControls(year);

    // Fetch latest results
    const data = await safeFetch('/api/latest');

    // Automatically set the race/session dropdown to the fetched round/session
    raceSelect.value   = data.round;
    sessionSelect.value = data.session;
    renderTable(data.results);
  } catch(_){ /* error already shown by safeFetch */ }

}

// 7. Wire up events
window.addEventListener('DOMContentLoaded', () => {
  loadLatest();
  yearSelect   .addEventListener('change', loadLatest);
  raceSelect   .addEventListener('change', fetchAndRenderResults);
  sessionSelect.addEventListener('change', fetchAndRenderResults);
});