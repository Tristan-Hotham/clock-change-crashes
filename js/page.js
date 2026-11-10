/* Do the clocks kill? Local authority districts (2023) on a plain MapLibre base map (OpenFreeMap Positron), coloured by the
 * change in reported injury collisions in the week after each clock change against the same weekdays three weeks either side
 * (2009 to 2025), or by collisions per 100,000 people a year (2015 to 2025); plus an hour-by-day chart.
 * Data: DfT STATS19 (Open Government Licence v3.0). Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => Number(n).toLocaleString('en-GB');
  const pc = v => (v >= 1 ? '+' : '') + ((v - 1) * 100).toFixed(1) + '%';
  const DIV = ['#2F6A9E', '#9DB8CF', '#EDE6D3', '#E3A48F', '#B4442E'];
  const SEQ = ['#FBEAE2', '#E9B49E', '#C8644A', '#8E2D1C', '#5A160B'];
  let map = null, G = null, mode = 'a';
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => { ct.classList.toggle('folded', f); document.getElementById('ctToggle').setAttribute('aria-expanded', !f); };
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function colorExpr() {
    if (mode === 'p') return ['interpolate', ['linear'], ['get', 'per100k'], 100, SEQ[0], 180, SEQ[1], 260, SEQ[2], 360, SEQ[3], 500, SEQ[4]];
    const k = mode === 'a' ? 'a_rr' : 's_rr';
    return ['case', ['==', ['get', k], null], '#DDD', ['interpolate', ['linear'], ['get', k], 0.8, DIV[0], 0.9, DIV[1], 1, DIV[2], 1.1, DIV[3], 1.2, DIV[4]]];
  }
  function sigFilter() {
    if (mode === 'p') return ['==', ['get', 'code'], ''];
    const p = mode === 'a' ? 'a_' : 's_';
    return ['any', ['>', ['coalesce', ['get', p + 'lo'], 0], 1], ['<', ['coalesce', ['get', p + 'hi'], 2], 1]];
  }
  function key() {
    const t = document.getElementById('keyTitle'), b = document.getElementById('keyBar'), e = document.getElementById('keyEnds'), s = document.getElementById('keySub'), g = document.getElementById('keySig');
    if (mode === 'p') { t.textContent = 'Collisions per head'; b.style.background = `linear-gradient(90deg,${SEQ.join(',')})`; e.innerHTML = '<span>100</span><span>260</span><span>500+</span>'; s.textContent = 'reported injury collisions per 100,000 people a year, 2015 to 2025'; g.parentNode.style.display = 'none'; }
    else { t.textContent = mode === 'a' ? 'Week after the clocks go back' : 'Week after the clocks go forward'; b.style.background = `linear-gradient(90deg,${DIV.join(',')})`; e.innerHTML = '<span>-20%</span><span>0</span><span>+20%</span>'; s.textContent = 'vs the same weekdays, three weeks either side'; g.parentNode.style.display = ''; }
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
  }
  function refresh() { map.setPaintProperty('dist', 'fill-color', colorExpr()); map.setFilter('sig', sigFilter()); key(); }
  function row(p, s, lab) {
    const r = p[s + '_rr'];
    if (r == null) return `<tr><td>${lab}</td><td>no data</td></tr>`;
    return `<tr><td>${lab}</td><td><b>${pc(r)}</b> (95% interval ${pc(p[s + '_lo'])} to ${pc(p[s + '_hi'])}); ${fmt(p[s + '_O'])} collisions in the change weeks</td></tr>`;
  }
  function popup(p, ll) {
    let h = `<b class="t">${esc(p.name)}</b><table>`;
    h += row(p, 'a', 'Clocks back') + row(p, 's', 'Clocks forward');
    h += `<tr><td>Per head</td><td><b>${p.per100k.toFixed(0)}</b> collisions per 100,000 people a year (2015 to 2025)</td></tr></table>`;
    h += '<p class="nt">Week after each change against the same weekdays one to three weeks either side, 2009 to 2025 (16 autumn and 15 spring changes; 2020 and spring 2021 left out). Most districts are within chance of zero. Source: DfT STATS19 (OGL v3.0); population mid-2020 via mySociety.</p>';
    new maplibregl.Popup({ maxWidth: '340px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function bbox(f) {
    let b = [180, 90, -180, -90];
    (f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates).forEach(p => p[0].forEach(c => { b = [Math.min(b[0], c[0]), Math.min(b[1], c[1]), Math.max(b[2], c[0]), Math.max(b[3], c[1])]; }));
    return [[b[0], b[1]], [b[2], b[3]]];
  }
  function setup() {
    G.features.forEach((f, i) => { f.id = i; });
    map.addSource('d', { type: 'geojson', data: G });
    const lbl = map.getStyle().layers.find(l => l.type === 'symbol');
    map.addLayer({ id: 'dist', type: 'fill', source: 'd', paint: { 'fill-color': colorExpr(), 'fill-opacity': ['case', ['boolean', ['feature-state', 'hover'], false], 0.95, 0.78] } }, lbl && lbl.id);
    map.addLayer({ id: 'lines', type: 'line', source: 'd', paint: { 'line-color': '#8C7B5A', 'line-width': ['interpolate', ['linear'], ['zoom'], 4, 0.2, 9, 1.2], 'line-opacity': 0.8 } }, lbl && lbl.id);
    map.addLayer({ id: 'sig', type: 'line', source: 'd', filter: sigFilter(), paint: { 'line-color': '#2B2119', 'line-width': ['interpolate', ['linear'], ['zoom'], 4, 1.2, 9, 2.6] } });
    map.addLayer({ id: 'sel', type: 'line', source: 'd', filter: ['==', ['get', 'code'], ''], paint: { 'line-color': '#B4442E', 'line-width': 3 } });
    let hov = null;
    map.on('click', 'dist', e => { const f = e.features[0]; map.setFilter('sel', ['==', ['get', 'code'], f.properties.code]); popup(f.properties, e.lngLat); });
    map.on('mousemove', 'dist', e => { map.getCanvas().style.cursor = 'pointer'; if (hov !== null) map.setFeatureState({ source: 'd', id: hov }, { hover: false }); hov = e.features[0].id; map.setFeatureState({ source: 'd', id: hov }, { hover: true }); });
    map.on('mouseleave', 'dist', () => { map.getCanvas().style.cursor = ''; if (hov !== null) map.setFeatureState({ source: 'd', id: hov }, { hover: false }); hov = null; });
    const tog = (box, ids) => document.getElementById(box).addEventListener('change', e => ids.forEach(id => map.setLayoutProperty(id, 'visibility', e.target.checked ? 'visible' : 'none')));
    tog('lyD', ['dist']); tog('lyX', ['sig']); tog('lyO', ['lines']);
    tog('lyL', map.getStyle().layers.filter(l => l.type === 'symbol').map(l => l.id));
    const idx = G.features.map(f => ({ k: norm(f.properties.name), t: f.properties.name, f }));
    const q = document.getElementById('q'), sug = document.getElementById('sug');
    let hits = [], cur = -1;
    function go(h) {
      sug.style.display = 'none'; q.value = h.t; const b = bbox(h.f); map.fitBounds(b, { padding: small ? 30 : 80, maxZoom: 11 });
      map.setFilter('sel', ['==', ['get', 'code'], h.f.properties.code]);
      map.once('moveend', () => popup(h.f.properties, [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2]));
    }
    q.addEventListener('input', () => {
      const v = norm(q.value.trim()); cur = -1;
      if (v.length < 2) { sug.style.display = 'none'; return; }
      hits = idx.filter(x => x.k.includes(v)).sort((a, b) => (b.k.startsWith(v) - a.k.startsWith(v)) || a.k.length - b.k.length).slice(0, 8);
      sug.innerHTML = hits.map((h, i) => `<li role="option" data-i="${i}">${esc(h.t)} <span>district</span></li>`).join('') || '<li>No match</li>';
      sug.style.display = 'block';
    });
    sug.addEventListener('click', e => { const li = e.target.closest('li[data-i]'); if (li) go(hits[+li.dataset.i]); });
    q.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); cur = Math.max(0, Math.min(hits.length - 1, cur + (e.key === 'ArrowDown' ? 1 : -1))); sug.querySelectorAll('li').forEach((l, i) => l.setAttribute('aria-selected', i === cur)); }
      if (e.key === 'Enter' && hits.length) go(hits[Math.max(cur, 0)]);
      if (e.key === 'Escape') sug.style.display = 'none';
    });
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
    key();
  }
  const lb = document.getElementById('lyrBtn'), lp = document.getElementById('lp');
  lb.addEventListener('click', () => { const o = !lp.classList.contains('open'); lp.classList.toggle('open', o); lb.setAttribute('aria-expanded', o); });

  // hour-by-day chart
  function heat(S, season) {
    const svg = document.getElementById('hdSvg'), tip = document.getElementById('hdTip');
    const g = S.grid[season], rels = g.rel, V = g.v;
    const L = 52, T = 22, W = 650, Hh = 420, cw = W / 24, ch = Hh / rels.length;
    const col = v => { const t = Math.max(-1, Math.min(1, (v - 1) / 0.3)); const a = t < 0 ? [47, 106, 158] : [180, 68, 46], z = [237, 230, 211]; const k = Math.abs(t); return `rgb(${a.map((x, i) => Math.round(z[i] + (x - z[i]) * k)).join(',')})`; };
    let h = '';
    rels.forEach((r, i) => V[i].forEach((v, hr) => { h += `<rect x="${L + hr * cw}" y="${T + i * ch}" width="${cw + 0.4}" height="${ch + 0.4}" fill="${col(v)}" data-r="${r}" data-h="${hr}" data-v="${v}"/>`; }));
    const i0 = rels.indexOf(0), i7 = rels.indexOf(7);
    h += `<rect x="${L}" y="${T + i0 * ch}" width="${W}" height="${(i7 - i0) * ch}" fill="none" stroke="#2B2119" stroke-width="2"/>`;
    for (let hr = 0; hr < 24; hr += 3) h += `<text x="${L + hr * cw + cw / 2}" y="${T - 6}" font-size="11" text-anchor="middle" fill="currentColor" font-family="IBM Plex Mono">${String(hr).padStart(2, '0')}:00</text>`;
    [-21, -14, -7, 0, 7, 14, 21].forEach(r => { const i = rels.indexOf(r); if (i >= 0) h += `<text x="${L - 6}" y="${T + i * ch + ch * 0.8}" font-size="11" text-anchor="end" fill="currentColor" font-family="IBM Plex Mono">${r > 0 ? '+' + r : r}</text>`; });
    h += `<text x="${L + W + 4}" y="${T + i0 * ch + 12}" font-size="11" fill="currentColor" font-family="IBM Plex Mono" transform="rotate(90 ${L + W + 4} ${T + i0 * ch + 12})">change week</text>`;
    svg.innerHTML = h;
    svg.onmousemove = svg.onclick = e => { const c = e.target.closest('rect[data-r]'); if (!c) return; const r = +c.dataset.r, v = +c.dataset.v; tip.textContent = `Day ${r > 0 ? '+' + r : r} from the change, ${String(c.dataset.h).padStart(2, '0')}:00 to ${String(c.dataset.h).padStart(2, '0')}:59: ${pc(v)} share of the day's collisions against the same hour in the comparison weeks (all ${season === 'autumn' ? 'autumn' : 'spring'} changes pooled).`; };
  }
  fetch('data/site.json').then(r => r.json()).then(S => {
    let s = 'autumn'; heat(S, s);
    document.querySelectorAll('#hd button[data-s]').forEach(b => b.addEventListener('click', () => { s = b.dataset.s; document.querySelectorAll('#hd button[data-s]').forEach(x => x.setAttribute('aria-pressed', x === b)); heat(S, s); }));
  });
  fetch('data/districts_map.geojson').then(r => r.json()).then(g => {
    G = g;
    map = new maplibregl.Map({ container: 'map', style: STYLE, bounds: [[-8.2, 49.8], [1.9, 60.9]], fitBoundsOptions: { padding: small ? 10 : 30 }, attributionControl: { compact: true }, minZoom: 3.5, maxZoom: 13 });
    window.__map = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.on('load', () => { document.getElementById('nojs').style.display = 'none'; setup(); });
  }).catch(() => { document.getElementById('nojs').textContent = 'The map data could not be loaded.'; });
})();
