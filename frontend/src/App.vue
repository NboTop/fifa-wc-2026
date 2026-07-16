<template>
  <div id="app">

    <!-- Live ticker -->
    <div class="ticker-bar">
      <span class="ticker-live">● LIVE</span>
      <div class="ticker-clip">
        <div class="ticker-scroll">
          <span class="ticker-item">WC 2026</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">MODEL ACCURACY <strong>71.0%</strong></span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">44 CORRECT FROM 62</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">RF + XGBOOST + ELO RATINGS</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">9,952 PLAYERS CLUSTERED</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">QUARTERFINALS IN PROGRESS</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">WC 2026</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">MODEL ACCURACY <strong>71.0%</strong></span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">44 CORRECT FROM 62</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">RF + XGBOOST + ELO RATINGS</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">9,952 PLAYERS CLUSTERED</span>
          <span class="ticker-sep">·</span>
          <span class="ticker-item">QUARTERFINALS IN PROGRESS</span>
          <span class="ticker-sep">·</span>
        </div>
      </div>
    </div>

    <!-- Main nav -->
    <nav class="navbar">
      <RouterLink to="/" class="brand">
        <span class="brand-badge">WC</span>
        <span class="brand-year">2026</span>
        <span class="brand-sub">Intelligence</span>
      </RouterLink>
      <div class="nav-links">
        <RouterLink to="/">Predictions</RouterLink>
        <RouterLink to="/players">Players</RouterLink>
        <RouterLink to="/sentiment">
          <span class="nav-live-dot"></span>
          Sentiment
        </RouterLink>
      </div>
    </nav>

    <main><RouterView /></main>
  </div>
</template>

<style>
/* ── Reset ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Design tokens: Stadium Broadcast ── */
:root {
  /* The stadium at night — not pure black, faint turf undertone */
  --void:    #060A08;
  --turf:    #0C1410;
  --surface: #111A14;
  --line:    #1C2E22;
  --border:  #243328;

  /* FIFA pitch green — the ONE chromatic accent */
  --pitch:   #00A651;
  --pitch-d: #007A3D;
  --pitch-l: rgba(0, 166, 81, 0.12);

  /* Text */
  --chalk:   #F0F2EE;
  --chalk-2: #A8B4A4;
  --chalk-3: #5A6E60;

  /* Results */
  --goal:    #F5C518;  /* correct — warm amber like goal flash */
  --foul:    #E8162B;  /* wrong — broadcast red */
  --goal-bg: rgba(245, 197, 24, 0.10);
  --foul-bg: rgba(232, 22, 43, 0.10);

  /* Typography */
  --display: 'Bebas Neue', 'Arial Narrow', sans-serif;
  --body:    'Inter', system-ui, sans-serif;
  --mono:    'JetBrains Mono', monospace;

  --r: 4px;
}

/* ── Base ── */
html { scroll-behavior: smooth; }

body {
  font-family: var(--body);
  background: var(--void);
  color: var(--chalk);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  font-feature-settings: 'kern' 1;
}

#app { display: flex; flex-direction: column; min-height: 100vh; }

/* ── Ticker bar ── */
.ticker-bar {
  height: 28px;
  background: var(--pitch);
  display: flex;
  align-items: center;
  padding-left: 1.25rem;
  overflow: hidden;
  gap: 0;
}

.ticker-live {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  color: var(--void);
  letter-spacing: 0.1em;
  white-space: nowrap;
  flex-shrink: 0;
  padding-right: 1rem;
  margin-right: 0.5rem;
  border-right: 1px solid rgba(0,0,0,0.2);
  background: var(--pitch);
  position: relative;
  z-index: 2;
}

.ticker-clip {
  flex: 1;
  overflow: hidden;
  height: 100%;
  display: flex;
  align-items: center;
  position: relative;
}

.ticker-scroll {
  display: flex;
  align-items: center;
  gap: 1rem;
  white-space: nowrap;
  flex-shrink: 0;
  animation: ticker 40s linear infinite;
}

.ticker-item { font-family: var(--mono); font-size: 10px; color: var(--void); letter-spacing: 0.06em; }
.ticker-item strong { font-weight: 700; }
.ticker-sep { color: rgba(0,0,0,0.3); font-size: 10px; }


@keyframes ticker {
  0%   { transform: translateX(50%); }
  100% { transform: translateX(-50%); }
}

/* ── Navbar ── */
.navbar {
  height: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 2rem;
  background: var(--void);
  border-bottom: 1px solid var(--pitch);
  position: sticky;
  top: 0;
  z-index: 100;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
}

.brand-badge {
  font-family: var(--display);
  font-size: 1.1rem;
  color: var(--void);
  background: var(--pitch);
  padding: 1px 6px;
  letter-spacing: 0.05em;
  line-height: 1.4;
}

.brand-year {
  font-family: var(--display);
  font-size: 1.5rem;
  color: var(--pitch);
  letter-spacing: 0.03em;
  line-height: 1;
}

.brand-sub {
  font-size: 0.7rem;
  color: var(--chalk-3);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 500;
  padding-top: 2px;
  border-left: 1px solid var(--border);
  padding-left: 8px;
}

.nav-links { display: flex; gap: 2px; }

.nav-links a {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--chalk-3);
  text-decoration: none;
  padding: 6px 14px;
  border-radius: var(--r);
  display: flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0.04em;
  transition: color 0.15s, background 0.15s;
}

.nav-links a:hover { color: var(--chalk); background: var(--surface); }

.nav-links a.router-link-active {
  color: var(--pitch);
  background: var(--pitch-l);
}

.nav-live-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--pitch);
  animation: pulse-dot 2s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

/* ── Main ── */
main {
  flex: 1;
  max-width: 1080px;
  width: 100%;
  margin: 0 auto;
  padding: 3rem 2rem;
}

/* ── Shared utilities ── */
.label {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--chalk-3);
}

.zone {
  background: var(--surface);
  border: 1px solid var(--border);
}

/* ── Animations ── */
@keyframes rise {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes spin { to { transform: rotate(360deg); } }
@keyframes bar-fill {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
}
</style>
