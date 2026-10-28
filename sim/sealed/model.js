// ============================================================================
// SEALED GROUND-TRUTH BEHAVIOUR MODEL — the "real customers" of Fjeldspor.
// The analysis / ideation side of AutoCRO must NEVER read this file. It is only
// used by the traffic simulator and by the end-of-POC scoring script.
// Shoppers react to what they PERCEIVE on the rendered page (see perceive.js),
// never to experiment flags, so any implementation that fixes a real friction works.
// ============================================================================

function samplePersona(rng) {
  const r = rng();
  return {
    device: rng() < 0.62 ? 'mobile' : 'desktop',
    intent: r < 0.14 ? 'buyer' : r < 0.44 ? 'considerer' : 'browser',
    priceSensitive: rng() < 0.4,
    sceptical: rng() < 0.35,
    entry: (x => x < 0.65 ? 'home' : x < 0.85 ? 'plp' : x < 0.93 ? 'pdp' : 'search')(rng()),
  };
}

const BASE = {
  buyer: { atc: 0.62, browseMore: 0.35, toCart: 0.85, toCheckout: 0.9, pdpViews: 3 },
  considerer: { atc: 0.24, browseMore: 0.55, toCart: 0.7, toCheckout: 0.72, pdpViews: 4 },
  browser: { atc: 0.05, browseMore: 0.5, toCart: 0.5, toCheckout: 0.45, pdpViews: 3 },
};

// Probability of bouncing at landing / on a page.
function pBounce(persona, seen) {
  let p = persona.intent === 'browser' ? 0.32 : persona.intent === 'considerer' ? 0.14 : 0.04;
  if (seen.overlayBlocking) p += 0.12;                       // H5: intrusive popup
  return p;
}

// Probability of adding to cart on a PDP.
function pAddToCart(persona, seen, product) {
  let p = BASE[persona.intent].atc;
  if (persona.device === 'mobile' && !seen.atcAboveFold) p *= 0.62;   // H1: ATC below fold on mobile
  if (persona.sceptical && !seen.socialProofPdp) p *= 0.68;           // H2: no social proof
  if (persona.sceptical && seen.socialProofPlp) p *= 1.06;
  if (persona.priceSensitive && product.price > 150) p *= 0.72;
  if (persona.priceSensitive && seen.shippingKnownCost && !seen.freeShippingThresholdSeen) p *= 0.97;
  return Math.min(p, 0.95);
}

// Free-shipping threshold nudge: shopper below threshold adds another item.
function pTopUp(persona, seen, subtotal, threshold) {
  if (!seen.freeShippingThresholdSeen || subtotal >= threshold) return 0;
  const gap = threshold - subtotal;
  if (gap > 60) return 0.04;
  return persona.priceSensitive ? 0.3 : 0.14;                          // H4: threshold visibility lifts AOV
}

function pCartToCheckout(persona, seen) {
  let p = BASE[persona.intent].toCheckout;
  if (seen.shippingKnownCost && seen.cartShipping > 0 && persona.priceSensitive) p *= 0.94; // some leave early, honestly informed
  return p;
}

// Checkout step continuation probabilities.
function pCheckoutStep(persona, seen, step) {
  if (step === 1) {
    let p = 0.93;
    if (seen.accountRequired) p *= persona.intent === 'buyer' ? 0.82 : 0.66;   // H3: forced account creation
    return p;
  }
  if (step === 2) return 0.93;
  if (step === 3) return 0.95;
  // step 4 = place order, sees final total incl. shipping
  let p = 0.97;
  if (seen.checkoutShipping > 0 && !seen.shippingKnownCost) {                   // H6: shipping-cost surprise
    p *= persona.priceSensitive ? 0.55 : 0.88;
  }
  return p;
}

module.exports = { samplePersona, BASE, pBounce, pAddToCart, pTopUp, pCartToCheckout, pCheckoutStep };
