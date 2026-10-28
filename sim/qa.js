// QA: render each running experiment variant and report what a shopper perceives (no sealed data used).
const { chromium } = require('playwright'); const perceive = require('./perceive');
const BASE = process.argv[2] || 'http://localhost:8787';
const shots = process.argv[3] || '/tmp/qa';
(async () => {
  const b = await chromium.launch(); require('fs').mkdirSync(shots, { recursive: true });
  const reg = require('../site/config/experiments.json');
  for (const exp of reg.experiments.filter(e => e.status === 'running')) {
    const found = {};
    const route = { p: '/#/p/P001', cart: '/#/cart', checkout: '/#/checkout', c: '/#/c/jackets', home: '/#/' }[exp.exposure_route] || '/#/';
    const dev = exp.targeting.device === 'desktop' ? 'desktop' : 'mobile';
    for (let i = 0; i < 60 && Object.keys(found).length < exp.variants.length; i++) {
      const ctx = await b.newContext(dev === 'mobile' ? { viewport: { width: 390, height: 844 }, isMobile: true } : { viewport: { width: 1366, height: 800 } });
      const pg = await ctx.newPage();
      await pg.addInitScript(c => { localStorage.setItem('ac_cid', c); sessionStorage.setItem('ac_cart', JSON.stringify([{ id: 'P019', size: null, qty: 1 }])); }, 'qa' + i);
      await pg.goto(BASE + route); await pg.waitForFunction(() => window.AC && window.AC.ready);
      const v = await pg.evaluate(id => window.AC.tracking.experiments[id], exp.id);
      if (v && !found[v]) { found[v] = await pg.evaluate(perceive); await pg.screenshot({ path: `${shots}/${exp.id}-${v}.png` }); }
      await ctx.close();
    }
    for (const [v, p] of Object.entries(found)) console.log(exp.id, v, JSON.stringify({ atcAboveFold: p.atcAboveFold, shippingKnownCost: p.shippingKnownCost, threshold: p.freeShippingThresholdSeen, accountRequired: p.accountRequired, checkoutShipping: p.checkoutShipping, cartShipping: p.cartShipping }));
  }
  await b.close();
})();
