// AutoCRO experiment engine: sticky hash-based assignment, feature overrides, exposure events.
(function () {
  function hash(str) { // FNV-1a 32-bit
    let h = 0x811c9dc5;
    for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193); }
    return (h >>> 0);
  }
  const E = {
    assignments: {}, // expId -> {variant, exposure_route, exposed}
    async load() {
      const bust = '?v=' + Date.now();
      const [cfg, reg] = await Promise.all([
        fetch('config/site-config.json' + bust).then(r => r.json()),
        fetch('config/experiments.json' + bust).then(r => r.json())
      ]);
      const T = window.AC.tracking;
      const cid = T.clientId();
      const dev = T.device();
      const features = Object.assign({}, cfg.features, (cfg.device_features || {})[dev] || {});
      let css = cfg.css || '';
      // Preview mode: ?ac_preview=EXP003:B_compact_gallery shows one variant (any status), other tests off, no GA4.
      const pv = new URLSearchParams(location.search).get('ac_preview');
      if (pv) {
        const [pe, pvar] = pv.split(':');
        const exp = (reg.experiments || []).find(e => e.id === pe);
        const v = exp && exp.variants.find(x => x.id === pvar);
        if (exp && v) {
          Object.assign(features, v.id === exp.variants[0].id ? (exp.control_features || {}) : (v.features || {}));
          if (v.css) css += '\n' + v.css;
          T.preview = true;
          const bar = document.createElement('div');
          bar.style.cssText = 'background:#fab219;color:#0b0b0b;text-align:center;font:600 13px system-ui;padding:6px';
          bar.textContent = 'AutoCRO preview: ' + exp.id + ' · ' + v.id + ' (' + exp.name + ') — not tracked';
          document.addEventListener('DOMContentLoaded', () => document.body.prepend(bar));
          if (document.body) document.body.prepend(bar);
        }
        if (css) { const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st); }
        return { cfg, features };
      }
      for (const exp of reg.experiments || []) {
        if (exp.status !== 'running') continue;
        if (exp.targeting && exp.targeting.device && exp.targeting.device !== 'all' && exp.targeting.device !== dev) continue;
        const bucket = hash(cid + ':' + exp.id) % 10000 / 100; // 0..100
        if (bucket >= (exp.traffic_allocation ?? 100)) continue;
        const b2 = hash(exp.id + ':' + cid) % 10000 / 100;
        let acc = 0, chosen = exp.variants[exp.variants.length - 1];
        for (const v of exp.variants) { acc += v.weight; if (b2 < acc) { chosen = v; break; } }
        Object.assign(features, chosen.features || {});
        if (chosen.css) css += '\n' + chosen.css;
        E.assignments[exp.id] = { variant: chosen.id, exposure_route: exp.exposure_route || '', exposed: false };
        T.experiments[exp.id] = chosen.id;
      }
      if (css) { const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st); }
      return { cfg, features };
    },
    // Called on each route render; fires experiment_impression once per experiment per session.
    expose(route) {
      for (const [id, a] of Object.entries(E.assignments)) {
        if (a.exposed) continue;
        const key = 'ac_exp_' + id;
        if (sessionStorage.getItem(key)) { a.exposed = true; continue; }
        if (!a.exposure_route || route.startsWith(a.exposure_route)) {
          a.exposed = true; sessionStorage.setItem(key, '1');
          window.AC.tracking.track('experiment_impression', { experiment_id: id, variant_id: a.variant });
        }
      }
    }
  };
  window.AC = window.AC || {};
  window.AC.experiments = E;
})();
