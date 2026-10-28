// AutoCRO tracking layer: GA4-shaped events to dataLayer, gtag (if configured) and the
// simulator's capture hook (window.__acCapture) when present.
(function () {
  window.dataLayer = window.dataLayer || [];
  function cid() {
    let id = localStorage.getItem('ac_cid');
    if (!id) { id = Math.random().toString(36).slice(2) + Date.now().toString(36); localStorage.setItem('ac_cid', id); }
    return id;
  }
  function sid() {
    let id = sessionStorage.getItem('ac_sid');
    if (!id) { id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6); sessionStorage.setItem('ac_sid', id); }
    return id;
  }
  const device = () => (window.innerWidth < 768 ? 'mobile' : 'desktop');
  let gtagReady = false;

  const T = {
    clientId: cid,
    device,
    experiments: {}, // expId -> variantId (set by experiments.js)
    initGA4(measurementId) {
      if (!measurementId || gtagReady) return;
      const s = document.createElement('script');
      s.async = true; s.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
      document.head.appendChild(s);
      window.gtag = function () { window.dataLayer.push(arguments); };
      gtag('js', new Date());
      gtag('config', measurementId, { send_page_view: false, client_id: cid() });
      gtagReady = true;
    },
    track(name, params = {}) {
      const exp = Object.entries(T.experiments).map(([e, v]) => e + ':' + v).join('|');
      const ev = Object.assign({
        event: name, ts: Date.now(), client_id: cid(), session_id: sid(),
        device_category: device(), page_location: location.hash || '#/', experiments: exp
      }, params);
      window.dataLayer.push(ev);
      if (gtagReady) {
        const p = Object.assign({}, params, { device_category: device(), ac_experiments: exp });
        if (name === 'page_view') { p.page_location = location.href; p.page_title = document.title + ' | ' + (params.page_type || ''); }
        gtag('event', name, p);
      }
      if (typeof window.__acCapture === 'function') { try { window.__acCapture(ev); } catch (e) {} }
    }
  };
  window.AC = window.AC || {};
  window.AC.tracking = T;
})();
