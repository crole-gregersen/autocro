// What a shopper can perceive on the rendered page (runs in the browser).
// Deliberately implementation-agnostic: text, visibility and geometry, not feature flags.
module.exports = function perceive() {
  const vh = window.innerHeight, vw = window.innerWidth;
  const footer = document.querySelector('footer');
  const text = (document.body.innerText || '').replace(footer ? footer.innerText : '', '');
  const visible = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const inView = el => { const r = el.getBoundingClientRect(); return visible(el) && r.top >= 0 && r.bottom <= vh; };
  const atcs = [...document.querySelectorAll('[data-ac=add-to-cart]')];
  const center = document.elementFromPoint(vw / 2, vh / 2);
  const overlayBlocking = !!center && !center.closest('main, header, #promoBar, footer') && center !== document.body && center !== document.documentElement;
  const route = document.body.dataset.route || '';
  const money = s => { if (!s) return null; if (/free/i.test(s)) return 0; const m = s.match(/€\s?(\d+(?:\.\d+)?)/); return m ? +m[1] : null; };
  const sumEl = document.querySelector('[data-ac=order-summary]');
  const shipLine = sumEl ? [...sumEl.querySelectorAll('div')].find(d => /shipping/i.test(d.innerText)) : null;
  // shipping cost knowledge outside checkout
  const shipText = route === 'checkout' ? '' : text;
  const thresholdSeen = /free shipping[^.\n]*over\s*€/i.test(shipText) || /€\s?\d+(\.\d+)?\s*away/i.test(shipText);
  const knownCost = /shipping[^\n]{0,40}€\s?\d/i.test(shipText) || /€\s?\d[^\n]{0,20}shipping/i.test(shipText) || thresholdSeen || /qualify for free shipping/i.test(shipText);
  const cartShip = (() => { if (route !== 'cart') return null; const line = [...document.querySelectorAll('main div')].find(d => /^\s*shipping/i.test(d.innerText) && /€|free/i.test(d.innerText)); return line ? money(line.innerText) : null; })();
  return {
    route,
    atcAboveFold: atcs.some(inView),
    socialProof: /★|\b\d+\s+reviews?\b|\brated\s+\d/i.test(text),
    overlayBlocking,
    shippingKnownCost: knownCost,
    freeShippingThresholdSeen: thresholdSeen,
    cartShipping: cartShip,
    accountRequired: [...document.querySelectorAll('input[type=password]')].some(visible),
    checkoutShipping: shipLine ? money(shipLine.innerText) : null,
    cartCount: +(document.getElementById('cartCount') || {}).textContent || 0,
  };
};
