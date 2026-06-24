<template>
  <div id="app">
    <nav class="navbar">
      <RouterLink to="/" class="brand">
        <span class="trophy">🏆</span>
        <span>WC 2026 Intelligence</span>
      </RouterLink>
      <div class="nav-links">
        <RouterLink to="/">Dashboard</RouterLink>
        <RouterLink to="/players">Players</RouterLink>
      </div>
    </nav>
    <main><RouterView /></main>
  </div>
</template>

<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:       #07070f;
  --surface:  #10101a;
  --surface2: #181826;
  --border:   #1e1e32;
  --gold:     #c9a84c;
  --gold-l:   #f0d080;
  --gold-dim: rgba(201,168,76,0.12);
  --purple:   #7b61ff;
  --green:    #0acf83;
  --coral:    #ff7262;
  --blue:     #1abcfe;
  --text:     #e8e8f0;
  --muted:    #6b6b88;
  --font:     'Inter', system-ui, sans-serif;
  --mono:     'JetBrains Mono', monospace;
  --r:        10px;
}

body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

#app { display: flex; flex-direction: column; min-height: 100vh; }

/* Navbar */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 2rem;
  height: 58px;
  background: rgba(7,7,15,0.92);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  font-size: 1rem;
  font-weight: 800;
  color: var(--gold-l);
  letter-spacing: -0.02em;
}

.trophy { font-size: 1.2rem; }

.nav-links { display: flex; gap: 4px; }

.nav-links a {
  color: var(--muted);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 99px;
  transition: background 0.15s, color 0.15s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background: var(--gold-dim);
  color: var(--gold-l);
}

main {
  flex: 1;
  max-width: 1100px;
  margin: 0 auto;
  padding: 2.5rem 2rem;
  width: 100%;
}

/* Shared */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: 1.5rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 900;
  letter-spacing: -0.04em;
  color: var(--gold-l);
  margin-bottom: 2rem;
}

.eyebrow {
  font-family: var(--mono);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--muted);
  margin-bottom: 0.5rem;
}

.spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.2);
  border-top-color: var(--gold);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

@keyframes rise {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
