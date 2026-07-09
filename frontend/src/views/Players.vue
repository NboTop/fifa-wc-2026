<template>
  <div class="players-page">

    <!-- ── Page header ── -->
    <div class="page-header">
      <div>
        <p class="label">Player intelligence</p>
        <h1 class="page-title">Squad Analysis</h1>
        <p class="page-desc">{{ totalPlayers.toLocaleString() }} outfield players across all 48 WC 2026 nations, clustered into 6 tactical archetypes using K-Means on FC 26 attribute data.</p>
      </div>
      <div class="model-tag">
        <span class="label">K-Means k=6</span>
        <span class="label" style="color:var(--pitch)">FC 26 Dataset</span>
      </div>
    </div>

    <!-- ── Archetype radar ── -->
    <section class="radar-section zone">
      <div class="radar-header">
        <div>
          <p class="label">Player archetypes</p>
          <p class="radar-sub">Clusters computed on normalised pace, shooting, passing, dribbling, defending, physic. Names are human-readable labels for cluster centroids — not hand-labelled.</p>
        </div>
        <button class="method-btn" @click="showMethod = !showMethod">
          {{ showMethod ? 'Hide' : 'Methodology' }}
        </button>
      </div>

      <div class="method-panel" v-if="showMethod">
        <p>Features standardised with <code>StandardScaler</code> → K-Means (k=6, n_init=20, random_state=42). Cluster count chosen by elbow method. Each centroid's top-2 Z-score attributes determine archetype name. Dataset filtered to WC 2026 nations, outfield only, overall ≥ 60.</p>
      </div>

      <div class="radar-canvas-wrap">
        <canvas ref="radarCanvas" />
      </div>

      <!-- Archetype pills — clickable filter -->
      <div class="arch-pills">
        <button
          v-for="(arch, i) in archetypes" :key="arch.name"
          class="arch-pill"
          :class="{ active: activeArch === arch.name }"
          @click="toggleArch(arch.name)"
          :style="activeArch === arch.name
            ? { background: COLORS[i] + '20', borderColor: COLORS[i], color: COLORS[i] }
            : {}"
        >
          <span class="arch-swatch" :style="{ background: COLORS[i] }"></span>
          <span class="arch-name">{{ arch.name }}</span>
          <span class="arch-n">{{ arch.count }}</span>
        </button>
      </div>

      <p class="arch-hint" v-if="activeArch">
        Filtering to <strong>{{ activeArch }}</strong> ·
        <button class="clear-arch" @click="activeArch = null">clear</button>
      </p>
    </section>

    <!-- ── Team explorer ── -->
    <section class="explorer-section">
      <div class="explorer-header">
        <p class="label">Team explorer</p>
        <input
          v-model="nationSearch"
          list="nations-datalist"
          placeholder="SEARCH A NATION…"
          class="nation-input"
          @change="onNationSelect"
        />
        <datalist id="nations-datalist">
          <option v-for="n in nations" :key="n" :value="n" />
        </datalist>
      </div>

      <div class="team-body" v-if="selectedNation && teamComp">

        <!-- Team headline -->
        <div class="team-headline">
          <h2 class="team-name">{{ selectedNation }}</h2>
          <div class="team-meta">
            <span class="label">{{ topPlayers.length }} players</span>
            <span class="dominant-tag" v-if="dominantArch">
              Primary: <strong>{{ dominantArch.name }}</strong> ({{ dominantArch.pct }}%)
            </span>
          </div>
        </div>

        <!-- Composition bars -->
        <div class="comp-grid">
          <div
            v-for="(val, cname) in sortedComp" :key="cname"
            class="comp-row"
            :class="{ dominant: dominantArch && cname === dominantArch.name }"
          >
            <span class="comp-name">{{ cname }}</span>
            <div class="comp-track">
              <div class="comp-fill"
                :style="{ width: val.pct + '%', background: archColor(cname) }"
              ></div>
            </div>
            <span class="comp-stat">{{ val.count }} <em>{{ val.pct }}%</em></span>
          </div>
        </div>

        <!-- Player cards -->
        <div class="players-grid-header">
          <p class="label">Top rated players
            <span v-if="activeArch"> · {{ activeArch }}</span>
          </p>
          <span class="label">{{ filteredPlayers.length }} shown</span>
        </div>

        <div class="players-grid" v-if="filteredPlayers.length">
          <div
            v-for="p in filteredPlayers" :key="p.short_name"
            class="player-card"
            :style="{ borderTopColor: archColor(p.cluster_name) }"
          >
            <div class="player-top">
              <span class="player-ovr" :style="{ color: ovrColor(p.overall) }">{{ p.overall }}</span>
              <div class="player-info">
                <span class="player-name">{{ p.short_name }}</span>
                <span class="player-pos">{{ primaryPos(p.player_positions) }}</span>
              </div>
            </div>
            <div class="player-arch"
              :style="{ color: archColor(p.cluster_name), borderColor: archColor(p.cluster_name) + '40' }">
              {{ p.cluster_name }}
            </div>
            <div class="player-attrs">
              <div v-for="s in statKeys" :key="s.key" class="attr">
                <span class="attr-v" :style="{ color: attrColor(p[s.key]) }">{{ p[s.key] }}</span>
                <span class="attr-k">{{ s.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="empty-arch" v-else>
          No {{ activeArch }} players in {{ selectedNation }} ·
          <button class="clear-arch" @click="activeArch = null">clear filter</button>
        </div>

      </div>

      <div class="empty-nation" v-else-if="!selectedNation">
        <p class="label">Type a nation name above to explore their squad</p>
      </div>
    </section>
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

const COLORS = ['#00A651','#F5C518','#E8162B','#1ABCFE','#F5A623','#A259FF']

const statKeys = [
  { key: 'pace',      label: 'PAC' },
  { key: 'shooting',  label: 'SHO' },
  { key: 'passing',   label: 'PAS' },
  { key: 'dribbling', label: 'DRI' },
  { key: 'defending', label: 'DEF' },
  { key: 'physic',    label: 'PHY' },
]

const radarCanvas     = ref(null)
const nations         = ref([])
const clusterProfiles = ref({})
const nationSearch    = ref('')
const selectedNation  = ref('')
const teamComp        = ref(null)
const topPlayers      = ref([])
const activeArch      = ref(null)
const showMethod      = ref(false)
let chart = null

const archetypes   = computed(() => Object.entries(clusterProfiles.value).map(([name, d]) => ({ name, ...d })))
const totalPlayers = computed(() => archetypes.value.reduce((s, a) => s + (a.count || 0), 0))

function archColor(name) {
  const i = archetypes.value.findIndex(a => a.name === name)
  return COLORS[i % COLORS.length] ?? '#5A6E60'
}
function ovrColor(v) {
  if (v >= 88) return '#F5C518'
  if (v >= 82) return '#00A651'
  if (v >= 74) return '#F0F2EE'
  return '#5A6E60'
}
function attrColor(v) {
  if (v >= 85) return '#F5C518'
  if (v >= 75) return '#00A651'
  return '#A8B4A4'
}
function primaryPos(pos) { return pos ? pos.split(',')[0].trim() : '—' }
function toggleArch(name) { activeArch.value = activeArch.value === name ? null : name }
function onNationSelect() {
  const m = nations.value.find(n => n.toLowerCase() === nationSearch.value.toLowerCase())
  selectedNation.value = m || nationSearch.value
}

const sortedComp = computed(() => {
  if (!teamComp.value) return {}
  return Object.fromEntries(Object.entries(teamComp.value).sort((a, b) => b[1].pct - a[1].pct))
})
const dominantArch = computed(() => {
  if (!teamComp.value) return null
  const entries = Object.entries(teamComp.value)
  if (!entries.length) return null
  const top = entries.reduce((b, c) => c[1].pct > b[1].pct ? c : b)
  return { name: top[0], pct: top[1].pct }
})
const filteredPlayers = computed(() => {
  if (!activeArch.value) return topPlayers.value
  return topPlayers.value.filter(p => p.cluster_name === activeArch.value)
})

function buildRadar() {
  if (chart) { chart.destroy(); chart = null }
  if (!radarCanvas.value || !archetypes.value.length) return
  const keys = ['pace','shooting','passing','dribbling','defending','physic']
  chart = new Chart(radarCanvas.value, {
    type: 'radar',
    data: {
      labels: ['Pace','Shooting','Passing','Dribbling','Defending','Physic'],
      datasets: archetypes.value.map((a, i) => ({
        label: a.name,
        data: keys.map(k => a[k] || 0),
        borderColor: COLORS[i],
        backgroundColor: COLORS[i] + '14',
        borderWidth: 1.5,
        pointBackgroundColor: COLORS[i],
        pointRadius: 2.5,
      })),
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        r: {
          min: 30, max: 85,
          ticks: { color: '#5A6E60', backdropColor: 'transparent', font: { size: 9, family: 'JetBrains Mono' } },
          grid: { color: 'rgba(255,255,255,0.05)' },
          angleLines: { color: 'rgba(255,255,255,0.05)' },
          pointLabels: { color: '#A8B4A4', font: { size: 11, weight: '500', family: 'Inter' } },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#111A14',
          borderColor: '#1C2E22',
          borderWidth: 1,
          titleColor: '#F0F2EE',
          bodyColor: '#A8B4A4',
          titleFont: { family: 'Bebas Neue', size: 14, letterSpacing: '0.06em' },
        },
      },
    },
  })
}

watch(selectedNation, async (nation) => {
  if (!nation) { teamComp.value = null; topPlayers.value = []; return }
  try {
    const [comp, players] = await Promise.all([
      axios.get(`/api/v1/team-composition/${encodeURIComponent(nation)}`),
      axios.get(`/api/v1/players/${encodeURIComponent(nation)}`),
    ])
    teamComp.value   = comp.data
    topPlayers.value = players.data
  } catch (e) { console.error(e) }
})

onMounted(async () => {
  const [n, c] = await Promise.all([
    axios.get('/api/v1/nations'),
    axios.get('/api/v1/clusters'),
  ])
  nations.value       = n.data
  clusterProfiles.value = c.data
  buildRadar()
})

onBeforeUnmount(() => { if (chart) chart.destroy() })
</script>

<style scoped>
.players-page { display: flex; flex-direction: column; gap: 2.5rem; animation: rise 0.4s ease; }

/* Header */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1.5rem; flex-wrap: wrap; }
.page-title  { font-family: var(--display); font-size: 3rem; letter-spacing: 0.04em; color: var(--chalk); margin: 0.25rem 0 0.5rem; line-height: 1; }
.page-desc   { font-size: 0.8rem; color: var(--chalk-3); max-width: 520px; line-height: 1.55; }
.model-tag   { display: flex; flex-direction: column; gap: 4px; align-items: flex-end; padding-top: 0.5rem; }

/* Radar */
.radar-section { padding: 1.75rem; }
.radar-header  { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; gap: 1rem; }
.radar-sub     { font-size: 0.75rem; color: var(--chalk-3); margin-top: 0.3rem; max-width: 520px; line-height: 1.5; }
.method-btn {
  background: none; border: 1px solid var(--border); color: var(--chalk-3);
  font-family: var(--mono); font-size: 10px; letter-spacing: 0.08em;
  padding: 4px 10px; cursor: pointer; white-space: nowrap;
  transition: border-color 0.15s, color 0.15s;
}
.method-btn:hover { border-color: var(--pitch); color: var(--pitch); }

.method-panel {
  background: var(--turf); border: 1px solid var(--border);
  padding: 1rem; margin-bottom: 1.25rem; font-size: 0.75rem;
  color: var(--chalk-3); line-height: 1.6;
}
.method-panel code { background: var(--border); padding: 1px 5px; font-family: var(--mono); font-size: 0.7rem; }

.radar-canvas-wrap { height: 320px; position: relative; margin-bottom: 1.25rem; }

.arch-pills { display: flex; flex-wrap: wrap; gap: 6px; padding-top: 1.25rem; border-top: 1px solid var(--border); }
.arch-pill {
  display: flex; align-items: center; gap: 7px;
  background: none; border: 1px solid var(--border); color: var(--chalk-3);
  font-family: var(--mono); font-size: 10px; letter-spacing: 0.06em;
  padding: 4px 10px; cursor: pointer; transition: all 0.15s;
}
.arch-pill:hover { border-color: var(--chalk-3); color: var(--chalk); }
.arch-swatch { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.arch-n { opacity: 0.5; font-size: 9px; }

.arch-hint { font-family: var(--mono); font-size: 10px; color: var(--chalk-3); margin-top: 0.5rem; }
.clear-arch { background: none; border: none; color: var(--pitch); cursor: pointer; font-family: var(--mono); font-size: 10px; text-decoration: underline; }

/* Explorer */
.explorer-section { }
.explorer-header { display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.75rem; flex-wrap: wrap; }

.nation-input {
  background: transparent; border: none;
  border-bottom: 2px solid var(--border);
  color: var(--chalk); font-family: var(--display);
  font-size: 1.5rem; letter-spacing: 0.06em;
  padding: 4px 0; width: 280px;
  text-transform: uppercase; transition: border-color 0.2s;
}
.nation-input::placeholder { color: var(--chalk-3); font-size: 1.1rem; }
.nation-input:focus { outline: none; border-bottom-color: var(--pitch); }

/* Team */
.team-headline { display: flex; align-items: baseline; gap: 1.25rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.team-name { font-family: var(--display); font-size: 2.5rem; letter-spacing: 0.04em; color: var(--chalk); line-height: 1; }
.team-meta { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.dominant-tag { font-family: var(--mono); font-size: 10px; color: var(--pitch); letter-spacing: 0.06em; }

/* Composition bars */
.comp-grid { display: flex; flex-direction: column; gap: 8px; margin-bottom: 2rem; }
.comp-row  { display: grid; grid-template-columns: 180px 1fr 90px; align-items: center; gap: 12px; }
.comp-name { font-size: 0.75rem; color: var(--chalk-3); }
.comp-row.dominant .comp-name { color: var(--chalk); font-weight: 600; }
.comp-track { height: 4px; background: var(--border); }
.comp-fill  { height: 100%; transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1); }
.comp-stat  { font-family: var(--mono); font-size: 0.68rem; color: var(--chalk-3); text-align: right; }
.comp-stat em { font-style: normal; color: var(--chalk-2); margin-left: 4px; }

/* Players grid */
.players-grid-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.875rem;
}

.players-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
}

.player-card {
  background: var(--void);
  border-top: 2px solid transparent;
  padding: 1rem;
  display: flex; flex-direction: column; gap: 8px;
  transition: background 0.15s;
}
.player-card:hover { background: var(--surface); }

.player-top   { display: flex; align-items: flex-start; gap: 10px; }
.player-ovr   { font-family: var(--display); font-size: 2rem; letter-spacing: 0.02em; line-height: 1; flex-shrink: 0; }
.player-info  { display: flex; flex-direction: column; gap: 2px; padding-top: 3px; }
.player-name  { font-size: 0.85rem; font-weight: 600; color: var(--chalk); }
.player-pos   { font-family: var(--mono); font-size: 0.62rem; color: var(--chalk-3); letter-spacing: 0.06em; }

.player-arch {
  font-family: var(--mono); font-size: 0.62rem; letter-spacing: 0.06em;
  padding: 2px 6px; border: 1px solid; display: inline-block; align-self: flex-start;
}

.player-attrs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; }
.attr         { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.attr-v       { font-family: var(--mono); font-size: 0.78rem; font-weight: 600; }
.attr-k       { font-family: var(--mono); font-size: 0.56rem; color: var(--chalk-3); letter-spacing: 0.06em; }

.empty-arch, .empty-nation {
  padding: 3rem;
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--chalk-3);
  letter-spacing: 0.06em;
  text-align: center;
}
</style>
