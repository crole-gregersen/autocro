// Fjeldspor demo shop. Rendering is driven by `F` (features) = site-config features + experiment overrides.
// CONTRACT: elements carrying data-ac="..." are interaction hooks used by the shopper simulator.
// Variants may restyle/move them, but must keep the hooks.
(async function () {
  const T = window.AC.tracking, E = window.AC.experiments;
  const { cfg, features: F } = await E.load();
  T.initGA4(cfg.ga4_measurement_id);
  const CAT = await fetch('data/products.json?v=' + Date.now()).then(r => r.json());
  const P = Object.fromEntries(CAT.products.map(p => [p.id, p]));
  const SHIP = CAT.shipping;
  const app = document.getElementById('app');
  const eur = n => '€' + n.toFixed(2);
  const sized = p => p.category === 'jackets' || p.category === 'footwear';
  const item = (p, extra = {}) => Object.assign({ item_id: p.id, item_name: p.name, item_category: p.category, price: p.price }, extra);

  // ---- cart ----
  const cart = {
    get() { return JSON.parse(sessionStorage.getItem('ac_cart') || '[]'); },
    set(c) { sessionStorage.setItem('ac_cart', JSON.stringify(c)); document.getElementById('cartCount').textContent = c.reduce((a, l) => a + l.qty, 0); },
    add(id, size) { const c = cart.get(); const l = c.find(x => x.id === id && x.size === size); l ? l.qty++ : c.push({ id, size, qty: 1 }); cart.set(c); },
    remove(i) { const c = cart.get(); c.splice(i, 1); cart.set(c); },
    subtotal() { return cart.get().reduce((a, l) => a + P[l.id].price * l.qty, 0); },
    items() { return cart.get().map(l => item(P[l.id], { quantity: l.qty, item_variant: l.size || '' })); }
  };
  const shipping = sub => (sub >= SHIP.free_over || sub === 0 ? 0 : SHIP.flat);
  cart.set(cart.get());

  const img = (p, cls = 'img', i = 0, eager = false) => {
    const im = (p.images || [])[i % Math.max((p.images || []).length, 1)];
    return im
      ? `<div class="${cls} photo ${im.kind || ''}"${im.bg ? ` style="background:${im.bg}"` : ''}><img src="${im.src}" alt="${im.alt}" ${eager ? 'fetchpriority="high"' : 'loading="lazy"'} decoding="async"></div>`
      : `<div class="${cls}" style="background:linear-gradient(160deg,${p.color},#111c18)"></div>`;
  };
  const stars = p => `<div class="rating">★ ${p.rating} (${p.reviews} reviews)</div>`;
  const btnClass = { dark: 'btn-dark', green: 'btn-green', orange: 'btn-orange' }[F.atc_button_color] || 'btn-dark';
  const shipMsg = sub => sub >= SHIP.free_over ? 'You qualify for free shipping.'
    : `Shipping ${eur(SHIP.flat)} — free shipping on orders over ${eur(SHIP.free_over)}.`;

  function promo() {
    const el = document.getElementById('promoBar');
    if (!F.free_shipping_bar) { el.innerHTML = ''; return; }
    const sub = cart.subtotal(), left = SHIP.free_over - sub;
    el.innerHTML = `<div class="fsbar">${left > 0 ? `Free shipping on orders over ${eur(SHIP.free_over)} — you're ${eur(left)} away` : 'You qualify for free shipping!'}</div>`;
  }

  function popup() {
    if (!F.newsletter_popup || sessionStorage.getItem('ac_popup')) return;
    sessionStorage.setItem('ac_popup', '1');
    setTimeout(() => {
      document.getElementById('overlay').innerHTML = `<div class="modal-bg"><div class="modal"><h3>Get 10% off your first order</h3>
        <p>Sign up for our newsletter.</p><input placeholder="Email" style="width:100%;padding:8px">
        <p><button class="btn btn-dark" data-ac="popup-signup">Sign up</button> <button class="btn btn-light" data-ac="popup-close">No thanks</button></p></div></div>`;
      T.track('popup_shown', { popup: 'newsletter' });
    }, 300);
  }
  document.getElementById('overlay').addEventListener('click', e => {
    const a = e.target.dataset.ac;
    if (a === 'popup-close' || a === 'popup-signup') {
      T.track(a === 'popup-close' ? 'popup_closed' : 'newsletter_signup', { popup: 'newsletter' });
      document.getElementById('overlay').innerHTML = '';
    }
  });

  // ---- views ----
  function home() {
    T.track('page_view', { page_type: 'home' });
    app.innerHTML = `<section class="hero${CAT.hero_image ? ' has-photo' : ''}">${CAT.hero_image ? `<img class="hero-bg" src="${CAT.hero_image.src}" alt="${CAT.hero_image.alt}" fetchpriority="high">` : ''}<div class="hero-copy"><h1>Gear for the long way round</h1><p>Jackets, boots and packs tested in Nordic weather.</p>
      <a class="btn btn-light" href="#/c/jackets" data-ac="hero-cta">${F.home_hero_cta}</a></div></section>
      <div class="cat-tiles">${CAT.categories.map(c => `<a class="cat-tile" data-ac="cat-tile" href="#/c/${c}">${c}</a>`).join('')}</div>
      <h2 style="margin-top:32px">Popular right now</h2>${grid(CAT.products.slice().sort((a, b) => b.reviews - a.reviews).slice(0, 6), 'home_popular')}`;
    T.track('view_item_list', { item_list_id: 'home_popular', items: CAT.products.slice(0, 6).map(p => item(p)) });
  }
  function grid(list, listId) {
    return `<div class="grid">${list.map((p, i) => `<a class="card" data-ac="product-card" data-id="${p.id}" data-list="${listId}" data-index="${i}" href="#/p/${p.id}">
      ${img(p)}<div class="info"><div class="name">${p.name}</div><div class="price">${eur(p.price)}</div>${F.plp_show_ratings ? stars(p) : ''}</div></a>`).join('')}</div>`;
  }
  function plp(cat) {
    const list = CAT.products.filter(p => p.category === cat);
    T.track('page_view', { page_type: 'plp' });
    const ci = (CAT.category_images || {})[cat];
    app.innerHTML = `${ci ? `<div class="cat-banner"><img src="${ci.src}" alt="${ci.alt}" fetchpriority="high"></div>` : ''}<h1 style="text-transform:capitalize">${cat}</h1><p>${list.length} products</p>${grid(list, 'plp_' + cat)}`;
    T.track('view_item_list', { item_list_id: 'plp_' + cat, items: list.map(p => item(p)) });
  }
  function search(q) {
    const ql = q.toLowerCase();
    const list = CAT.products.filter(p => (p.name + ' ' + p.category).toLowerCase().includes(ql));
    T.track('page_view', { page_type: 'search' });
    T.track('view_search_results', { search_term: q, results: list.length });
    app.innerHTML = `<h1>Search: “${q}”</h1>${list.length ? grid(list, 'search') : '<p data-ac="no-results">No products found.</p>'}`;
  }
  let selSize = null;
  function pdp(id) {
    const p = P[id]; if (!p) return home();
    selSize = null;
    T.track('page_view', { page_type: 'pdp' });
    T.track('view_item', { currency: 'EUR', value: p.price, items: [item(p)] });
    const sizes = p.category === 'footwear' ? ['40', '41', '42', '43', '44', '45'] : ['XS', 'S', 'M', 'L', 'XL'];
    const atc = `<button class="btn ${btnClass} btn-block" data-ac="add-to-cart">${F.atc_button_text}</button>`;
    const galleryCount = F.pdp_gallery_layout === 'tall' ? 3 : 1;
    app.innerHTML = `<div class="pdp"><div class="gallery ${F.pdp_gallery_layout}">${Array.from({ length: galleryCount }, (_, i) => img(p, 'img', i, i === 0)).join('')}</div>
      <div class="buy"><h1>${p.name}</h1>${F.pdp_show_reviews ? stars(p) : ''}<div class="price">${eur(p.price)}</div>
      <p>${F.pdp_long_desc && p.long_desc ? p.long_desc.split(/(?<=\.)\s/)[0] : p.desc}</p>
      ${sized(p) ? `<div class="size-row">${sizes.map(s => `<button data-ac="size" data-size="${s}">${s}</button>`).join('')}</div>` : ''}
      <div id="atcMsg"></div>${atc}
      ${F.pdp_usps && CAT.usps ? `<ul class="usps" data-ac="usps">${CAT.usps.map(u => `<li><span aria-hidden="true">✓</span> ${u}</li>`).join('')}</ul>` : ''}
      ${F.pdp_long_desc && p.long_desc ? `<div class="pdp-details"><h2>About this product</h2><p>${p.long_desc}</p></div>` : ''}
      ${F.pdp_specs && p.specs ? `<div class="pdp-details"><h2>Specifications</h2><dl class="specs">${p.specs.map(s => `<dt>${s.label}</dt><dd>${s.value}</dd>`).join('')}</dl></div>` : ''}
      ${F.pdp_shipping_info ? `<div class="note" data-ac="shipping-note">${shipMsg(cart.subtotal() + p.price)}</div>` : ''}
      ${F.pdp_show_reviews ? `<div class="reviews"><strong>What customers say</strong><p>“Exactly as described, kept me dry on a 3-day trek.” — Verified buyer</p></div>` : ''}
      </div></div>
      ${F.sticky_atc_mobile && T.device() === 'mobile' ? `<div class="sticky-atc"><button class="btn ${btnClass} btn-block" data-ac="add-to-cart">${F.atc_button_text} — ${eur(p.price)}</button></div>` : ''}`;
    app.querySelectorAll('[data-ac=size]').forEach(b => b.onclick = () => {
      app.querySelectorAll('[data-ac=size]').forEach(x => x.classList.remove('sel')); b.classList.add('sel'); selSize = b.dataset.size;
      T.track('select_size', { item_id: p.id, size: selSize });
    });
    app.querySelectorAll('[data-ac=add-to-cart]').forEach(b => b.onclick = () => {
      if (sized(p) && !selSize) { document.getElementById('atcMsg').innerHTML = '<p style="color:#b00020">Please select a size.</p>'; T.track('atc_error', { reason: 'no_size' }); return; }
      cart.add(p.id, selSize); promo();
      T.track('add_to_cart', { currency: 'EUR', value: p.price, items: [item(p, { quantity: 1, item_variant: selSize || '' })] });
      document.getElementById('atcMsg').innerHTML = `<p class="note" data-ac="atc-confirm">Added to your bag. <a href="#/cart" data-ac="go-cart">View bag</a></p>`;
    });
  }
  function cartView() {
    const c = cart.get(), sub = cart.subtotal();
    T.track('page_view', { page_type: 'cart' });
    T.track('view_cart', { currency: 'EUR', value: sub, items: cart.items() });
    if (!c.length) { app.innerHTML = '<h1>Your bag</h1><p>Your bag is empty.</p><a class="btn btn-dark" href="#/">Continue shopping</a>'; return; }
    app.innerHTML = `<h1>Your bag</h1>${c.map((l, i) => `<div class="cart-line"><span>${P[l.id].name}${l.size ? ' — ' + l.size : ''} × ${l.qty}</span>
      <span>${eur(P[l.id].price * l.qty)} <button data-ac="remove" data-i="${i}">Remove</button></span></div>`).join('')}
      <div class="totals"><div><span>Subtotal</span><span>${eur(sub)}</span></div>
      ${F.cart_shipping_info ? `<div data-ac="cart-shipping"><span>Shipping</span><span>${shipping(sub) ? eur(shipping(sub)) : 'Free'}</span></div><div class="note">${shipMsg(sub)}</div>
      <div><strong>Total</strong><strong>${eur(sub + shipping(sub))}</strong></div>` : '<div style="color:#777;font-size:13px"><span>Shipping calculated at checkout</span></div>'}</div>
      <p><a class="btn ${btnClass} btn-block" href="#/checkout" data-ac="checkout">Go to checkout</a></p>`;
    app.querySelectorAll('[data-ac=remove]').forEach(b => b.onclick = () => {
      const l = c[+b.dataset.i]; T.track('remove_from_cart', { items: [item(P[l.id], { quantity: l.qty })] }); cart.remove(+b.dataset.i); promo(); cartView();
    });
  }
  function checkout() {
    const sub = cart.subtotal(); if (!sub) return cartView();
    const ship = shipping(sub);
    T.track('page_view', { page_type: 'checkout' });
    T.track('begin_checkout', { currency: 'EUR', value: sub, items: cart.items() });
    const acct = F.checkout_guest
      ? `<h2>1. Contact</h2><label>Email<input data-ac="email" type="email"></label><p style="font-size:13px">Checking out as guest — you can create an account after your order.</p>`
      : `<h2>1. Create your account</h2><p style="font-size:13px">An account is required to place an order.</p>
         <label>Email<input data-ac="email" type="email"></label><label>Password<input data-ac="password" type="password"></label>
         <label>Confirm password<input data-ac="password2" type="password"></label>`;
    app.innerHTML = `<h1>Checkout</h1><div class="checkout">
      <section id="s1">${acct}<p><button class="btn btn-dark" data-ac="step1">Continue</button></p></section>
      <section id="s2" class="locked"><h2>2. Delivery</h2><label>Full name<input data-ac="name"></label><label>Address<input data-ac="address"></label>
        <label>Postcode<input data-ac="zip"></label><label>City<input data-ac="city"></label><p><button class="btn btn-dark" data-ac="step2">Continue to payment</button></p></section>
      <section id="s3" class="locked"><h2>3. Payment</h2><label>Card number<input data-ac="card" placeholder="4111 1111 1111 1111"></label>
        <p><button class="btn btn-dark" data-ac="step3">Use this card</button></p></section>
      <section class="totals" data-ac="order-summary"><div><span>Subtotal</span><span>${eur(sub)}</span></div>
        <div data-ac="checkout-shipping"><span>Shipping</span><span>${ship ? eur(ship) : 'Free'}</span></div>
        <div><strong>Total</strong><strong>${eur(sub + ship)}</strong></div>
        <p><button class="btn ${btnClass} btn-block" data-ac="place-order" disabled>Place order</button></p></section></div>`;
    const unlock = id => document.getElementById(id).classList.remove('locked');
    app.querySelector('[data-ac=step1]').onclick = () => { T.track(F.checkout_guest ? 'checkout_contact' : 'sign_up', { method: F.checkout_guest ? 'guest' : 'account' }); unlock('s2'); };
    app.querySelector('[data-ac=step2]').onclick = () => { T.track('add_shipping_info', { currency: 'EUR', value: sub, shipping_tier: 'standard', items: cart.items() }); unlock('s3'); };
    app.querySelector('[data-ac=step3]').onclick = () => { T.track('add_payment_info', { currency: 'EUR', value: sub, payment_type: 'card', items: cart.items() }); app.querySelector('[data-ac=place-order]').disabled = false; };
    app.querySelector('[data-ac=place-order]').onclick = () => {
      const tid = 'T' + Date.now().toString(36).toUpperCase();
      T.track('purchase', { transaction_id: tid, currency: 'EUR', value: +(sub + ship).toFixed(2), shipping: ship, items: cart.items() });
      cart.set([]); promo(); location.hash = '#/confirm/' + tid;
    };
  }
  function confirm(tid) {
    T.track('page_view', { page_type: 'confirmation' });
    app.innerHTML = `<h1>Thank you!</h1><p data-ac="order-confirmed">Order ${tid} confirmed (demo — nothing will ship).</p><a class="btn btn-dark" href="#/">Back to shop</a>`;
  }

  // ---- router ----
  function route() {
    const h = location.hash.replace(/^#\/?/, '');
    const [r, arg] = h.split('/');
    E.expose(r || 'home');
    window.scrollTo(0, 0);
    if (r === 'c') plp(arg); else if (r === 'p') pdp(arg); else if (r === 'cart') cartView();
    else if (r === 'checkout') checkout(); else if (r === 'confirm') confirm(arg);
    else if (r === 'search') search(decodeURIComponent(arg || '')); else home();
    promo(); popup();
    document.body.dataset.route = r || 'home';
  }
  app.addEventListener('click', e => {
    const c = e.target.closest('[data-ac=product-card]');
    if (c) T.track('select_item', { item_list_id: c.dataset.list, index: +c.dataset.index, items: [item(P[c.dataset.id])] });
  });
  document.getElementById('searchForm').onsubmit = e => { e.preventDefault(); location.hash = '#/search/' + encodeURIComponent(document.getElementById('searchInput').value); };
  window.addEventListener('hashchange', route);
  T.track('session_start_ac', { landing: location.hash || '#/' });
  route();
  window.AC.ready = true;
})();
