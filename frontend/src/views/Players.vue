<template>
  <div class="players-page">

    <!-- ── Hero ── -->
    <div class="page-hero">
      <div>
        <h1 class="page-title">Player Intelligence</h1>
        <p class="tagline">9,952 outfield players from all 48 WC 2026 nations, clustered into 6 statistical archetypes using K-Means on normalised FIFA 26 attributes.</p>
      </div>
      <div class="model-pill">
        <span class="model-version">K-Means k=6 · FC 26 dataset</span>
        <span class="model-date">{{ totalPlayers.toLocaleString() }} players · 48 nations</span>
      </div>
    </div>

    <!-- ── Archetype Radar ── -->
    <div class="card">
      <div class="section-header">
        <div>
          <p class="eyebrow">Player archetypes</p>
          <p class="section-desc">Clusters computed on pace, shooting, passing, dribbling, defending, physic. Names are human-friendly labels for cluster centroids — not hand-labelled.</p>
        </div>
        <button class="info-btn" @click="showMethodology = !showMethodology">
          {{ showMethodology ? 'Hide' : 'How it works' }} ↗
        </button>
      </div>

      <!-- Methodology panel -->
      <div class="methodology-panel" v-if="showMethodology">
        <p class="method-text">
          <strong>Data:</strong> FC 26 player dataset (18,405 players). Filtered to WC 2026 nations, outfield only, overall ≥ 60. Final set: 9,952 players across 48 nations.<br><br>
          <strong>Features:</strong> pace, shooting, passing, dribbling, defending, physic — standardised with StandardScaler before clustering.<br><br>
          <strong>Algorithm:</strong> K-Means with k=6, n_init=20, random_state=42. Cluster count chosen by elbow method on within-cluster sum of squares.<br><br>
          <strong>Naming:</strong> Each cluster centroid's top-2 Z-score attributes determine the archetype name (e.g., high pace + high dribbling → "Pacey Dribbler").
        </p>
      </div>

      <!-- Radar -->
      <div class="radar-wrap">
        <canvas ref="radarCanvas" />
      </div>

      <!-- Archetype pills — clickable to filter -->
      <div class="archetype-pills">
        <button
          v-for="(arch, i) in archetypes" :key="arch.name"
          class="arch-pill"
          :class="{ active: activeArchetype === arch.name }"
          @click="toggleArchetype(arch.name)"
          :style="activeArchetype === arch.name ? { background: COLORS[i] + '22', borderColor: COLORS[i], color: COLORS[i] } : {}"
        >
          <span class="arch-dot" :style="{ background: COLORS[i] }"/>
          <span class="arch-name">{{ arch.name }}</span>
          <span class="arch-count">{{ arch.count }}</span>
        </button>
      </div>
      <p class="pill-hint" v-if="activeArchetype">
        Showing {{ activeArchetype }} — <button class="clear-btn" @click="activeArchetype = null">clear filter</button>
      </p>
    </div>

    <!-- ── Team Explorer ── -->
    <div class="card">
      <p class="eyebrow">Team explorer</p>
      <p class="section-desc" style="margin-bottom:1rem">Select a WC 2026 nation to see their squad archetype distribution and top-rated players.</p>

      <div class="nation-search-wrap">
        <input
          v-model="nationSearch"
          list="nations-datalist"
          placeholder="Search a WC 2026 nation…"
          class="nation-input"
          @change="onNationSelect"
        />
        <datalist id="nations-datalist">
          <option v-for="n in nations" :key="n" :value="n" />
        </datalist>
      </div>

      <!-- Team header -->
      <div v-if="selectedNation && teamComp" class="team-header">
        <div class="team-name-row">
          <h2 class="team-name">{{ selectedNation }}</h2>
          <span class="team-badge">{{ topPlayers.length }} players shown</span>
        </div>

        <!-- Dominant archetype callout -->
        <div class="dominant-callout" v-if="dominantArchetype">
          <span class="dominant-icon">⚽</span>
          <p>
            <strong>{{ dominantArchetype.name }}</strong> is this squad's primary profile at
            <strong>{{ dominantArchetype.pct }}%</strong> of eligible players.
          </p>
        </div>

        <!-- Composition bars -->
        <div class="comp-section">
          <p class="comp-title eyebrow">Squad archetype distribution</p>
          <div class="comp-bars">
            <div v-for="(val, cname) in sortedTeamComp" :key="cname" class="comp-row"
              :class="{ dominant: dominantArchetype && cname === dominantArchetype.name }">
              <span class="comp-name">{{ cname }}</span>
              <div class="bar-track">
                <div class="bar-fill"
                  :style="{ width: val.pct + '%', background: archColor(cname) }"
                />
              </div>
              <span class="comp-stat">
                <span class="comp-count">{{ val.count }}</span>
                <span class="comp-pct">{{ val.pct }}%</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Filter info -->
        <div class="player-list-header">
          <p class="comp-title eyebrow">
            Top rated players
            <span v-if="activeArchetype"> · {{ activeArchetype }}</span>
          </p>
          <span class="player-count">{{ filteredPlayers.length }} shown</span>
        </div>

        <!-- Player grid -->
        <div class="player-grid" v-if="filteredPlayers.length">
          <div v-for="p in filteredPlayers" :key="p.short_name" class="player-card"
            :style="{ borderTopColor: archColor(p.cluster_name) }">

            <!-- Rating badge -->
            <div class="player-ovr" :style="{ color: ovrColor(p.overall) }">{{ p.overall }}</div>

            <!-- Name + position -->
            <div class="player-info">
              <span class="player-name">{{ p.short_name }}</span>
              <span class="player-pos">{{ primaryPos(p.player_positions) }}</span>
            </div>

            <!-- Archetype tag -->
            <div class="player-archetype"
              :style="{ background: archColor(p.cluster_name) + '22', color: archColor(p.cluster_name) }">
              {{ p.cluster_name }}
            </div>

            <!-- Stats grid -->
            <div class="player-stats">
              <div class="stat-item" v-for="s in statKeys" :key="s.key">
                <span class="stat-val" :style="{ color: statColor(p[s.key]) }">{{ p[s.key] }}</span>
                <span class="stat-key">{{ s.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-state">
          No players found for "{{ activeArchetype }}" in {{ selectedNation }}.
          <button class="clear-btn" @click="activeArchetype = null">Clear filter</button>
        </div>
      </div>

      <div v-else-if="!selectedNation" class="empty-state">
        Search for a nation above to explore their squad
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import {
  Chart, RadarController, RadialLinearScale,
  PointElement, LineElement, Filler, Tooltip, Legend,
} from 'chart.js'

Chart.register(RadarController, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const COLORS = ['#c9a84c', '#7b61ff', '#0acf83', '#ff7262', '#1abcfe', '#f5a623']

const statKeys = [
  { key: 'pace',      label: 'PAC' },
  { key: 'shooting',  label: 'SHO' },
  { key: 'passing',   label: 'PAS' },
  { key: 'dribbling', label: 'DRI' },
  { key: 'defending', label: 'DEF' },
  { key: 'physic',    label: 'PHY' },
]

const radarCanvas      = ref(null)
const nations          = ref([])
const clusterProfiles  = ref({})
const nationSearch     = ref('')
const selectedNation   = ref('')
const teamComp         = ref(null)
const topPlayers       = ref([])
const activeArchetype  = ref(null)
const showMethodology  = ref(false)
let chart = null

const archetypes = computed(() =>
  Object.entries(clusterProfiles.value).map(([name, data]) => ({ name, ...data }))
)
const totalPlayers = computed(() =>
  archetypes.value.reduce((sum, a) => sum + (a.count || 0), 0)
)

function archColor(name) {
  const idx = archetypes.value.findIndex(a => a.name === name)
  return COLORS[idx % COLORS.length] ?? '#6b6b88'
}

function ovrColor(ovr) {
  if (ovr >= 88) return '#c9a84c'
  if (ovr >= 82) return '#0acf83'
  if (ovr >= 74) return '#1abcfe'
  return '#6b6b88'
}

function statColor(val) {
  if (val >= 85) return '#c9a84c'
  if (val >= 75) return '#0acf83'
  if (val >= 65) return '#e8e8f0'
  return '#6b6b88'
}

function primaryPos(pos) {
  return pos ? pos.split(',')[0].trim() : '—'
}

function toggleArchetype(name) {
  activeArchetype.value = activeArchetype.value === name ? null : name
}

// Sort team comp so dominant archetype is first
const sortedTeamComp = computed(() => {
  if (!teamComp.value) return {}
  return Object.fromEntries(
    Object.entries(teamComp.value).sort((a, b) => b[1].pct - a[1].pct)
  )
})

const dominantArchetype = computed(() => {
  if (!teamComp.value) return null
  const entries = Object.entries(teamComp.value)
  if (!entries.length) return null
  const top = entries.reduce((best, cur) => cur[1].pct > best[1].pct ? cur : best)
  return { name: top[0], pct: top[1].pct }
})

const filteredPlayers = computed(() => {
  if (!activeArchetype.value) return topPlayers.value
  return topPlayers.value.filter(p => p.cluster_name === activeArchetype.value)
})

function onNationSelect() {
  const match = nations.value.find(n => n.toLowerCase() === nationSearch.value.toLowerCase())
  if (match) selectedNation.value = match
}

function buildRadar() {
  if (chart) { chart.destroy(); chart = null }
  if (!radarCanvas.value || archetypes.value.length === 0) return
  const keys = ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic']
  const labels = ['Pace', 'Shooting', 'Passing', 'Dribbling', 'Defending', 'Physic']
  chart = new Chart(radarCanvas.value, {
    type: 'radar',
    data: {
      labels,
      datasets: archetypes.value.map((arch, i) => ({
        label: arch.name,
        data: keys.map(k => arch[k] || 0),
        borderColor: COLORS[i],
        backgroundColor: COLORS[i] + '18',
        borderWidth: 2,
        pointBackgroundColor: COLORS[i],
        pointRadius: 3,
      })),
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        r: {
          min: 30, max: 85,
          ticks:       { color: '#6b6b88', backdropColor: 'transparent', font: { size: 9 } },
          grid:        { color: 'rgba(255,255,255,0.05)' },
          angleLines:  { color: 'rgba(255,255,255,0.05)' },
          pointLabels: { color: '#e8e8f0', font: { size: 11, weight: '600' } },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#10101a', borderColor: '#1e1e32', borderWidth: 1,
          titleColor: '#e8e8f0', bodyColor: '#6b6b88', padding: 10,
        },
      },
    },
  })
}

watch(selectedNation, async (nation) => {
  if (!nation) { teamComp.value = null; topPlayers.value = []; return }
  try {
    const [compRes, playersRes] = await Promise.all([
      axios.get(`/api/v1/team-composition/${encodeURIComponent(nation)}`),
      axios.get(`/api/v1/players/${encodeURIComponent(nation)}`),
    ])
    teamComp.value   = compRes.data
    topPlayers.value = playersRes.data
  } catch (e) { console.error(e) }
})

onMounted(async () => {
  const [nRes, cRes] = await Promise.all([
    axios.get('/api/v1/nations'),
    axios.get('/api/v1/clusters'),
  ])
  nations.value       = nRes.data
  clusterProfiles.value = cRes.data
  buildRadar()
})

onBeforeUnmount(() => chart?.destroy())
</script>

<style scoped>
.players-page { display: flex; flex-direction: column; gap: 1.5rem; animation: rise 0.3s ease; }

/* Hero */
.page-hero { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
.tagline { font-size: 0.875rem; color: var(--muted); max-width: 560px; line-height: 1.5; margin-top: 0.35rem; }
.model-pill {
  display: flex; flex-direction: column; align-items: flex-end; gap: 3px;
  background: var(--surface); border: 1px solid var(--border);
  padding: 8px 14px; border-radius: var(--r); flex-shrink: 0;
}
.model-version { font-family: var(--mono); font-size: 0.68rem; color: var(--gold); }
.model-date    { font-family: var(--mono); font-size: 0.62rem; color: var(--muted); }

/* Section headers */
.section-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }
.section-desc   { font-size: 0.78rem; color: var(--muted); line-height: 1.55; }
.info-btn {
  background: none; border: 1px solid var(--border); color: var(--muted);
  padding: 4px 10px; border-radius: 99px; font-size: 0.72rem; font-family: var(--font);
  cursor: pointer; white-space: nowrap; flex-shrink: 0;
  transition: border-color 0.15s, color 0.15s;
}
.info-btn:hover { border-color: var(--gold); color: var(--gold); }

/* Methodology panel */
.methodology-panel {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--r); padding: 1rem 1.25rem; margin-bottom: 1rem;
}
.method-text { font-size: 0.78rem; color: var(--muted); line-height: 1.7; }

/* Radar */
.radar-wrap { height: 340px; position: relative; margin: 0.5rem 0 1.25rem; }

/* Archetype pills */
.archetype-pills { display: flex; flex-wrap: wrap; gap: 0.5rem; padding-top: 1.25rem; border-top: 1px solid var(--border); }
.arch-pill {
  display: flex; align-items: center; gap: 6px;
  background: none; border: 1px solid var(--border);
  padding: 4px 10px; border-radius: 99px; cursor: pointer;
  font-family: var(--font); font-size: 0.75rem; color: var(--muted);
  transition: all 0.15s;
}
.arch-pill:hover { border-color: var(--muted); color: var(--text); }
.arch-pill.active { font-weight: 600; }
.arch-dot  { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.arch-name { }
.arch-count { font-family: var(--mono); font-size: 0.65rem; opacity: 0.6; }

.pill-hint { font-size: 0.72rem; color: var(--muted); margin-top: 0.5rem; }
.clear-btn { background: none; border: none; color: var(--gold); cursor: pointer; font-size: 0.72rem; text-decoration: underline; font-family: var(--font); }

/* Nation input */
.nation-search-wrap { margin-bottom: 1.5rem; }
.nation-input {
  width: 100%; max-width: 320px;
  background: var(--surface2); border: 1.5px solid var(--border);
  color: var(--text); padding: 0.65rem 1rem; border-radius: var(--r);
  font-family: var(--font); font-size: 0.9rem;
  transition: border-color 0.2s;
}
.nation-input:focus { outline: none; border-color: var(--gold); }

/* Team header */
.team-header { }
.team-name-row { display: flex; align-items: center; gap: 0.875rem; margin-bottom: 0.875rem; }
.team-name  { font-size: 1.5rem; font-weight: 800; letter-spacing: -0.03em; color: var(--gold-l); }
.team-badge { font-family: var(--mono); font-size: 0.7rem; background: var(--gold-dim); color: var(--gold); padding: 2px 8px; border-radius: 99px; }

.dominant-callout {
  display: flex; align-items: center; gap: 10px;
  background: var(--surface2); border: 1px solid var(--border);
  border-left: 3px solid var(--gold); border-radius: var(--r);
  padding: 0.75rem 1rem; margin-bottom: 1.25rem;
  font-size: 0.82rem; color: var(--muted); line-height: 1.4;
}
.dominant-icon { font-size: 1rem; flex-shrink: 0; }
.dominant-callout strong { color: var(--text); }

/* Composition bars */
.comp-section { margin-bottom: 1.5rem; }
.comp-title   { margin-bottom: 0.75rem; }
.comp-bars    { display: flex; flex-direction: column; gap: 8px; }
.comp-row     { display: grid; grid-template-columns: 180px 1fr 90px; align-items: center; gap: 12px; padding: 4px 0; border-radius: 4px; transition: background 0.1s; }
.comp-row.dominant .comp-name { color: var(--gold-l); font-weight: 600; }
.comp-name    { font-size: 0.78rem; color: var(--muted); }
.bar-track    { height: 6px; background: var(--border); border-radius: 99px; overflow: hidden; }
.bar-fill     { height: 100%; border-radius: 99px; transition: width 0.8s cubic-bezier(0.34,1.56,0.64,1); }
.comp-stat    { display: flex; gap: 6px; justify-content: flex-end; align-items: baseline; }
.comp-count   { font-family: var(--mono); font-size: 0.72rem; color: var(--text); }
.comp-pct     { font-family: var(--mono); font-size: 0.65rem; color: var(--muted); }

/* Player list header */
.player-list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.875rem; }
.player-count { font-family: var(--mono); font-size: 0.7rem; color: var(--muted); }

/* Player grid */
.player-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.75rem;
}

.player-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-top: 3px solid transparent;
  border-radius: var(--r); padding: 0.875rem;
  display: flex; flex-direction: column; gap: 6px;
  transition: border-color 0.15s, transform 0.15s;
}
.player-card:hover { transform: translateY(-2px); border-color: rgba(255,255,255,0.12); }

.player-ovr   { font-size: 1.75rem; font-weight: 900; letter-spacing: -0.04em; line-height: 1; }

.player-info  { display: flex; justify-content: space-between; align-items: center; }
.player-name  { font-weight: 700; font-size: 0.875rem; color: var(--text); }
.player-pos   { font-family: var(--mono); font-size: 0.65rem; color: var(--muted); }

.player-archetype {
  display: inline-block; font-family: var(--mono); font-size: 0.65rem;
  padding: 2px 7px; border-radius: 4px; font-weight: 600;
  align-self: flex-start;
}

.player-stats {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 4px; margin-top: 4px;
  padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.05);
}
.stat-item  { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.stat-val   { font-family: var(--mono); font-size: 0.78rem; font-weight: 700; }
.stat-key   { font-family: var(--mono); font-size: 0.58rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }

.empty-state { text-align: center; padding: 3rem; color: var(--muted); font-size: 0.875rem; }
</style>