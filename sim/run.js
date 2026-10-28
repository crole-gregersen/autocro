#!/usr/bin/env node
// AutoCRO traffic simulator. Usage:
//   node sim/run.js --base http://localhost:8787 --sessions 1000 --concurrency 8 --seed 1 --run R001
// Writes events to data/events/<run>.jsonl (visible to analysis) and
// sim/sealed/truth/<run>.jsonl (persona ground truth — analysis must not read).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const M = require('./sealed/model');
const perceiveFn = require('./perceive');

const args = Object.fromEntries(process.argv.slice(2).reduce((a, x, i, arr) => (x.startsWith('--') && a.push([x.slice(2), arr[i + 1]]), a), []));
const BASE = args.base || 'http://localhost:8787';
const N = +(args.sessions || 200), C = +(args.concurrency || 8), SEED = +(args.seed || 1);
const RUN = args.run || 'R' + Date.now();
const ROOT = path.resolve(__dirname, '..');
fs.mkdirSync(path.join(ROOT, 'data/events'), { recursive: true });
fs.mkdirSync(path.join(__dirname, 'sealed/truth'), { recursive: true });
const evOut = fs.createWriteStream(path.join(ROOT, 'data/events', RUN + '.jsonl'), { flags: 'a' });
const truthOut = fs.createWriteStream(path.join(__dirname, 'sealed/truth', RUN + '.jsonl'), { flags: 'a' });

function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const UA = {
  mobile: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1',
  desktop: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
};
const CATS = ['jackets', 'footwear', 'backpacks', 'accessories'];
const gaAudit = [];
const DWELL = +(args['dwell-ms'] || 0);
const SEARCH_TERMS = ['jacket', 'boot', 'pack', 'socks', 'rain', 'gloves', 'tent', 'merino'];

async function session(browser, idx) {
  const rng = mulberry32(SEED * 100003 + idx);
  const pick = arr => arr[Math.floor(rng() * arr.length)];
  const persona = M.samplePersona(rng);
  const ctx = await browser.newContext(persona.device === 'mobile'
    ? { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, userAgent: UA.mobile }
    : { viewport: { width: 1366, height: 800 }, userAgent: UA.desktop });
  const page = await ctx.newPage();
  let sid = null;
  if (args['ga-audit']) {
    page.on('request', req => {
      const u = req.url(); if (!/google-analytics\.com\/(g|[a-z0-9-]+)\/collect|\/g\/collect/.test(u)) return;
      const lines = [u.split('?')[1] || '', ...((req.postData() || '').split('\n'))];
      const evs = lines.map(l => new URLSearchParams(l).get('en')).filter(Boolean);
      req.response().then(res => gaAudit.push({ evs, status: res ? res.status() : 'none', bytes: (req.postData() || '').length + u.length })).catch(e => gaAudit.push({ evs, status: 'failed:' + e.message.slice(0, 40) }));
    });
    page.on('requestfailed', req => { if (/collect/.test(req.url())) gaAudit.push({ evs: ['?'], status: 'requestfailed:' + (req.failure() || {}).errorText }); });
  }
  await page.exposeFunction('__acCapture', ev => { sid = ev.session_id; evOut.write(JSON.stringify(Object.assign({ run_id: RUN }, ev)) + '\n'); });
  const seen = { shippingKnownCost: false, freeShippingThresholdSeen: false, socialProofPlp: false };
  const outcome = { purchased: false, exit: null };
  const obs = {};
  const look = async () => {
    if (DWELL) await page.waitForTimeout(Math.round(DWELL * (0.4 + 1.2 * rng())));  // human-like time on page
    const p = await page.evaluate(perceiveFn);
    seen.shippingKnownCost ||= p.shippingKnownCost; seen.freeShippingThresholdSeen ||= p.freeShippingThresholdSeen;
    if (p.route === 'c' && p.socialProof) seen.socialProofPlp = true;
    return p;
  };
  const go = async (sel, route) => { await page.click(sel, { timeout: 4000 }); await page.waitForFunction(r => document.body.dataset.route === r, route, { timeout: 4000 }); };
  const nav = async h => { await page.evaluate(x => { location.hash = x.slice(1); }, h); };
  const closePopup = async () => {
    const btn = await page.$('[data-ac=popup-close]');
    if (btn) await page.click(rng() < 0.07 ? '[data-ac=popup-signup]' : '[data-ac=popup-close]');
  };
  const pdpFlow = async () => {
    const p = await look();
    obs.pdpAtcAboveFold = p.atcAboveFold; obs.pdpSocialProof = p.socialProof;
    const prod = await page.evaluate(() => { const n = document.querySelector('.pdp h1'); const pr = document.querySelector('.pdp .price'); return { name: n && n.innerText, price: pr ? +pr.innerText.replace(/[^\d.]/g, '') : 0 }; });
    const sizes = await page.$$('[data-ac=size]');
    const want = rng() < M.pAddToCart(persona, { ...seen, atcAboveFold: p.atcAboveFold, socialProofPdp: p.socialProof }, prod);
    if (!want) return false;
    if (sizes.length) {
      if (rng() < 0.12) await page.click('[data-ac=add-to-cart] >> nth=0');
      await sizes[Math.floor(rng() * sizes.length)].click();
    }
    await page.click('[data-ac=add-to-cart] >> nth=0');
    await look();
    return true;
  };
  try {
    const entry = persona.entry;
    const url = entry === 'home' ? '/#/' : entry === 'plp' ? '/#/c/' + pick(CATS) : entry === 'pdp' ? '/#/p/P0' + String(1 + Math.floor(rng() * 24)).padStart(2, '0') : '/#/search/' + pick(SEARCH_TERMS);
    await page.goto(BASE + url);
    await page.waitForFunction(() => window.AC && window.AC.ready, null, { timeout: 8000 });
    await page.waitForTimeout(380); // allow late UI (e.g. popups) to render
    const first = await look();
    obs.overlayOnLanding = first.overlayBlocking;
    if (rng() < M.pBounce(persona, first)) { outcome.exit = 'bounce'; return; }
    await closePopup();
    if (M.pBrowseOnly && rng() < M.pBrowseOnly(persona)) {   // browse category pages only, then leave
      const k = 1 + Math.floor(rng() * 2);
      for (let i = 0; i < k; i++) { await nav('/#/c/' + pick(CATS)); await page.waitForFunction(() => document.body.dataset.route === 'c'); await look(); }
      outcome.exit = 'browse_only'; return;
    }
    const base = M.BASE[persona.intent];
    let pdps = 0, added = 0;
    let route = first.route;
    if (route === 'search') {
      if (await page.$('[data-ac=product-card]')) { /* results */ } else { await nav('/#/c/' + pick(CATS)); await page.waitForFunction(() => document.body.dataset.route === 'c'); }
    }
    if (route === 'home') {
      if (rng() < 0.55) await go(`[data-ac=cat-tile] >> nth=${Math.floor(rng() * 4)}`, 'c');
    }
    while (pdps < base.pdpViews) {
      if ((await look()).route !== 'p') {
        const cards = await page.$$('[data-ac=product-card]');
        if (!cards.length) break;
        await cards[Math.floor(rng() * cards.length)].click();
        await page.waitForFunction(() => document.body.dataset.route === 'p');
      }
      pdps++;
      const did = await pdpFlow();
      if (did) { added++; if (rng() < base.toCart) break; }
      if (rng() > base.browseMore) break;
      await nav('/#/c/' + pick(CATS)); await page.waitForFunction(() => document.body.dataset.route === 'c');
      await look();
    }
    if (!added) { outcome.exit = 'no_atc'; return; }
    await nav('/#/cart'); await page.waitForFunction(() => document.body.dataset.route === 'cart');
    let c = await look();
    // free-shipping top-up
    const sub = await page.evaluate(() => JSON.parse(sessionStorage.getItem('ac_cart') || '[]').length);
    const subtotal = await page.evaluate(() => { const d = [...document.querySelectorAll('.totals div')].find(x => /subtotal/i.test(x.innerText)); return d ? +d.innerText.replace(/[^\d.]/g, '') : 0; });
    if (sub && rng() < M.pTopUp(persona, seen, subtotal, 100)) {
      await nav('/#/c/accessories'); await page.waitForFunction(() => document.body.dataset.route === 'c');
      const cards = await page.$$('[data-ac=product-card]'); await cards[Math.floor(rng() * cards.length)].click();
      await page.waitForFunction(() => document.body.dataset.route === 'p');
      await page.click('[data-ac=add-to-cart] >> nth=0');
      await nav('/#/cart'); await page.waitForFunction(() => document.body.dataset.route === 'cart');
      c = await look();
    }
    if (rng() > M.pCartToCheckout(persona, { ...seen, cartShipping: c.cartShipping })) { outcome.exit = 'cart'; return; }
    await go('[data-ac=checkout]', 'checkout');
    const k = await look();
    obs.accountRequired = k.accountRequired; obs.checkoutShipping = k.checkoutShipping;
    const s = { ...seen, accountRequired: k.accountRequired, checkoutShipping: k.checkoutShipping };
    const fill = async (sel, v) => { const el = await page.$(`[data-ac=${sel}]`); if (el) await el.fill(v); };
    for (const step of [1, 2, 3, 4]) {
      if (rng() > M.pCheckoutStep(persona, s, step)) { outcome.exit = 'checkout_step_' + step; return; }
      if (step === 1) { await fill('email', 'demo@example.com'); await fill('password', 'Demo1234!'); await fill('password2', 'Demo1234!'); await page.click('[data-ac=step1]'); }
      if (step === 2) { await fill('name', 'Demo Shopper'); await fill('address', 'Fjeldvej 1'); await fill('zip', '8000'); await fill('city', 'Aarhus'); await page.click('[data-ac=step2]'); }
      if (step === 3) { await fill('card', '4111111111111111'); await page.click('[data-ac=step3]'); }
      if (step === 4) { await page.click('[data-ac=place-order]'); await page.waitForSelector('[data-ac=order-confirmed]', { timeout: 4000 }); outcome.purchased = true; outcome.exit = 'purchase'; }
    }
  } catch (e) {
    outcome.exit = 'error'; outcome.error = String(e.message).slice(0, 600);
    if (process.env.SIM_DEBUG_SHOTS) { try { await page.screenshot({ path: `${process.env.SIM_DEBUG_SHOTS}/err-${idx}.png` }); } catch (_) {} }
  } finally {
    // let gtag flush queued GA4 hits before the browser context is closed
    try { if (await page.evaluate(() => typeof window.gtag === 'function')) await page.waitForTimeout(3000); } catch (e) {}
    truthOut.write(JSON.stringify({ run_id: RUN, idx, session_id: sid, persona, outcome, seen: { ...seen, ...obs, overlay: undefined } }) + '\n');
    await ctx.close();
  }
}

(async () => {
  const t0 = Date.now();
  const browser = await chromium.launch();
  let next = 0, done = 0, errors = 0;
  async function worker() {
    while (next < N) { const i = next++; await session(browser, i); done++; if (done % 100 === 0) process.stderr.write(`  ${done}/${N}\n`); }
  }
  await Promise.all(Array.from({ length: C }, worker));
  await browser.close();
  await new Promise(r => evOut.end(r)); await new Promise(r => truthOut.end(r));
  if (args['ga-audit']) {
    const sent = {}, status = {}; let maxBytes = 0;
    for (const a of gaAudit) { for (const e of a.evs) sent[e] = (sent[e] || 0) + 1; status[a.status] = (status[a.status] || 0) + 1; maxBytes = Math.max(maxBytes, a.bytes || 0); }
    fs.mkdirSync(path.join(ROOT, 'reports'), { recursive: true });
    fs.writeFileSync(path.join(ROOT, 'reports', 'ga-audit-' + RUN + '.json'), JSON.stringify({ requests: gaAudit.length, events_sent: sent, statuses: status, max_request_bytes: maxBytes }, null, 1));
  }
  console.log(JSON.stringify({ run: RUN, sessions: N, seconds: Math.round((Date.now() - t0) / 1000) }));
})();
