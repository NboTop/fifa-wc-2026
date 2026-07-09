<template>
  <div class="sentiment-page">

    <!-- ── Page header ── -->
    <div class="page-header">
      <div>
        <p class="label">Sentiment pulse</p>
        <h1 class="page-title">Fan Reaction</h1>
        <p class="page-desc">Real-time posts from Reddit analysed with VADER — purpose-built for social media text. Updated on demand.</p>
      </div>
      <div class="src-status">
        <div class="src-row">
          <span class="src-dot" :class="stats?.reddit_configured ? 'live' : 'off'"></span>
          <span class="label">Reddit {{ stats?.reddit_configured ? 'CONNECTED' : 'OFFLINE' }}</span>
        </div>
        <div class="src-row">
          <span class="src-dot" :class="stats?.twitter_configured ? 'live' : 'off'"></span>
          <span class="label">Twitter/X {{ stats?.twitter_configured ? 'CONNECTED' : 'OPTIONAL' }}</span>
        </div>
      </div>
    </div>

    <!-- ── Controls ── -->
    <section class="controls-section zone">
      <div class="controls-row">
        <div class="match-field">
          <p class="label" style="margin-bottom:5px">Match or topic</p>
          <input
            v-model="matchSearch"
            list="match-datalist"
            placeholder="e.g. Brazil vs Norway"
            class="match-input"
            @change="onMatchSelect"
          />
          <datalist id="match-datalist">
            <option v-for="m in availableMatches" :key="m" :value="m" />
          </datalist>
        </div>

        <div class="source-toggles">
          <p class="label" style="margin-bottom:5px">Sources</p>
          <div class="toggle-row">
            <button class="src-toggle"
              :class="{ active: sources.includes('reddit') }"
              @click="toggleSrc('reddit')">Reddit</button>
            <button class="src-toggle"
              :class="{ active: sources.includes('twitter') }"
              @click="toggleSrc('twitter')">Twitter/X</button>
          </div>
        </div>

        <div class="fetch-col">
          <p class="label" style="margin-bottom:5px">
            <span v-if="lastFetched">Last: {{ lastFetched }}</span>
            <span v-else>Ready</span>
          </p>
          <button class="btn-fetch"
            :disabled="!selectedMatch || refreshing"
            @click="refresh">
            <span v-if="refreshing" class="loading-dot"></span>
            <span v-else>↻ FETCH</span>
          </button>
        </div>
      </div>
    </section>

    <!-- ── Pulse stats ── -->
    <div class="pulse-row" v-if="stats && stats.total > 0">
      <div class="pulse-card">
        <div class="pulse-val pitch">{{ positivePercent }}%</div>
        <div class="label">Positive</div>
        <div class="pulse-count">{{ stats.positive }} posts</div>
      </div>
      <div class="pulse-card">
        <div class="pulse-val muted">{{ neutralPercent }}%</div>
        <div class="label">Neutral</div>
        <div class="pulse-count">{{ stats.neutral }} posts</div>
      </div>
      <div class="pulse-card">
        <div class="pulse-val foul">{{ negativePercent }}%</div>
        <div class="label">Negative</div>
        <div class="pulse-count">{{ stats.negative }} posts</div>
      </div>
      <div class="pulse-card score-card">
        <div class="pulse-val" :style="{ color: scoreColor(stats.avg_score) }">
          {{ stats.avg_score > 0 ? '+' : '' }}{{ stats.avg_score.toFixed(2) }}
        </div>
        <div class="label">Avg VADER score</div>
        <div class="pulse-count">−1.0 → +1.0 scale</div>
      </div>
    </div>

    <!-- ── Sentiment bar ── -->
    <div class="sent-bar-wrap" v-if="stats && stats.total > 0">
      <div class="sent-bar">
        <div class="sent-seg" style="background:var(--pitch)"
          :style="{ width: positivePercent + '%' }" :title="`${positivePercent}% positive`"></div>
        <div class="sent-seg" style="background:var(--chalk-3)"
          :style="{ width: neutralPercent + '%' }" :title="`${neutralPercent}% neutral`"></div>
        <div class="sent-seg" style="background:var(--foul)"
          :style="{ width: negativePercent + '%' }" :title="`${negativePercent}% negative`"></div>
      </div>
      <div class="sent-legend">
        <span><span class="leg pitch"></span>Positive {{ positivePercent }}%</span>
        <span><span class="leg muted-leg"></span>Neutral {{ neutralPercent }}%</span>
        <span><span class="leg foul"></span>Negative {{ negativePercent }}%</span>
        <span class="total-posts">{{ stats.total }} total posts</span>
      </div>
    </div>

    <!-- ── Trend chart ── -->
    <section class="chart-section zone" v-if="trend.length > 0">
      <p class="label" style="margin-bottom:1rem">Hourly trend (last 24h)</p>
      <div style="height:200px;position:relative">
        <canvas ref="trendCanvas" />
      </div>
    </section>

    <!-- ── Feed ── -->
    <section class="feed-section" v-if="feed.length > 0">
      <div class="feed-head">
        <p class="label">Live feed</p>
        <div class="feed-filters">
          <button class="feed-filter" :class="{ active: feedFilter === 'all' }"    @click="feedFilter = 'all'">ALL</button>
          <button class="feed-filter pitch-f" :class="{ active: feedFilter === 'POSITIVE' }" @click="feedFilter = 'POSITIVE'">POS</button>
          <button class="feed-filter muted-f" :class="{ active: feedFilter === 'NEUTRAL' }"  @click="feedFilter = 'NEUTRAL'">NEU</button>
          <button class="feed-filter foul-f"  :class="{ active: feedFilter === 'NEGATIVE' }" @click="feedFilter = 'NEGATIVE'">NEG</button>
        </div>
      </div>

      <div class="feed-list">
        <div v-for="item in filteredFeed" :key="item.id"
          class="feed-item"
          :class="item.label.toLowerCase()">
          <div class="feed-top">
            <span class="src-chip" :class="item.source">{{ item.source }}</span>
            <span class="sent-chip" :class="item.label.toLowerCase()">
              {{ item.label === 'POSITIVE' ? '↑' : item.label === 'NEGATIVE' ? '↓' : '—' }}
              {{ item.label }}
            </span>
            <span class="vader-score">{{ item.score > 0 ? '+' : '' }}{{ item.score }}</span>
            <a v-if="item.url" :href="item.url" target="_blank" class="post-link">↗</a>
          </div>
          <p class="feed-text">{{ item.text }}</p>
          <span class="feed-author">{{ item.source === 'reddit' ? 'u/' : '@' }}{{ item.author }}</span>
        </div>
      </div>
    </section>

    <!-- ── Empty states ── -->
    <div class="empty-state" v-else-if="!refreshing && selectedMatch">
      <p class="empty-icon">📡</p>
      <p class="empty-title">No posts collected yet</p>
      <p class="empty-sub">Click FETCH to collect posts about <strong>{{ selectedMatch }}</strong></p>
    </div>
    <div class="empty-state" v-else-if="!selectedMatch">
      <p class="empty-icon">⚽</p>
      <p class="empty-title">Select a match above</p>
      <p class="empty-sub">Choose any WC 2026 match or type a topic to start tracking fan sentiment</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip } from 'chart.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip)

const stats         = ref(null)
const feed          = ref([])
const trend         = ref([])
const matchSearch   = ref('')
const selectedMatch = ref('')
const sources       = ref(['reddit'])
const refreshing    = ref(false)
const feedFilter    = ref('all')
const lastFetched   = ref('')
const trendCanvas   = ref(null)
const availableMatches = ref([])
let trendChart = null
let autoTimer  = null

const positivePercent = computed(() => stats.value?.total ? Math.round(stats.value.positive / stats.value.total * 100) : 0)
const neutralPercent  = computed(() => stats.value?.total ? Math.round(stats.value.neutral  / stats.value.total * 100) : 0)
const negativePercent = computed(() => stats.value?.total ? Math.round(stats.value.negative / stats.value.total * 100) : 0)
const filteredFeed    = computed(() => feedFilter.value === 'all' ? feed.value : feed.value.filter(i => i.label === feedFilter.value))

function scoreColor(s) {
  if (s > 0.1)  return 'var(--pitch)'
  if (s < -0.1) return 'var(--foul)'
  return 'var(--chalk-3)'
}
function toggleSrc(s) {
  if (sources.value.includes(s)) { if (sources.value.length > 1) sources.value = sources.value.filter(x => x !== s) }
  else sources.value.push(s)
}
function onMatchSelect() {
  const m = availableMatches.value.find(x => x.toLowerCase() === matchSearch.value.toLowerCase())
  selectedMatch.value = m || matchSearch.value
}

async function refresh() {
  if (!selectedMatch.value || refreshing.value) return
  refreshing.value = true
  try {
    await axios.post('/api/v1/sentiment/refresh', null, {
      params: { match_tag: selectedMatch.value, sources: sources.value.join(',') }
    })
    await loadData()
    lastFetched.value = new Date().toLocaleTimeString()
  } catch { alert('Refresh failed — check backend is running') }
  finally { refreshing.value = false }
}

async function loadData() {
  const [sr, fr, tr] = await Promise.all([
    axios.get('/api/v1/sentiment/stats',  { params: { match_tag: selectedMatch.value || undefined } }),
    axios.get('/api/v1/sentiment/feed',   { params: { match_tag: selectedMatch.value || undefined, limit: 40 } }),
    axios.get('/api/v1/sentiment/trend',  { params: { match_tag: selectedMatch.value || undefined } }),
  ])
  stats.value = sr.data
  feed.value  = fr.data
  trend.value = tr.data
  if (sr.data.match_tags?.length)
    availableMatches.value = [...new Set([...availableMatches.value, ...sr.data.match_tags])]
  buildTrend()
}

function buildTrend() {
  if (trendChart) { trendChart.destroy(); trendChart = null }
  if (!trendCanvas.value || !trend.value.length) return
  trendChart = new Chart(trendCanvas.value, {
    type: 'line',
    data: {
      labels: trend.value.map(t => t.hour),
      datasets: [
        { label: 'Positive', data: trend.value.map(t => t.positive), borderColor: '#00A651', backgroundColor: 'rgba(0,166,81,0.06)', fill: true, tension: 0.4, borderWidth: 1.5, pointRadius: 2 },
        { label: 'Negative', data: trend.value.map(t => t.negative), borderColor: '#E8162B', backgroundColor: 'rgba(232,22,43,0.06)', fill: true, tension: 0.4, borderWidth: 1.5, pointRadius: 2 },
        { label: 'Neutral',  data: trend.value.map(t => t.neutral),  borderColor: '#5A6E60', backgroundColor: 'rgba(90,110,96,0.06)', fill: true, tension: 0.4, borderWidth: 1.5, pointRadius: 2 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#5A6E60', font: { size: 10, family: 'JetBrains Mono' }, boxWidth: 8, padding: 16 } },
        tooltip: { backgroundColor: '#0C1410', borderColor: '#1C2E22', borderWidth: 1, titleColor: '#F0F2EE', bodyColor: '#5A6E60' },
      },
      scales: {
        x: { ticks: { color: '#5A6E60', font: { size: 9, family: 'JetBrains Mono' } }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#5A6E60', font: { size: 9 }, stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.04)' }, min: 0 },
      },
    },
  })
}

async function loadMatchList() {
  try {
    const { data } = await axios.get('/api/v1/predictions')
    availableMatches.value = [...new Set(data.map(p => `${p.team_a} vs ${p.team_b}`))]
  } catch {}
}

onMounted(async () => {
  await Promise.all([loadData(), loadMatchList()])
  autoTimer = setInterval(() => { if (selectedMatch.value) loadData() }, 5 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (autoTimer) clearInterval(autoTimer)
  if (trendChart) trendChart.destroy()
})
</script>

<style scoped>
.sentiment-page { display: flex; flex-direction: column; gap: 2rem; animation: rise 0.4s ease; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1.5rem; flex-wrap: wrap; }
.page-title  { font-family: var(--display); font-size: 3rem; letter-spacing: 0.04em; color: var(--chalk); margin: 0.25rem 0 0.5rem; line-height: 1; }
.page-desc   { font-size: 0.8rem; color: var(--chalk-3); max-width: 480px; line-height: 1.55; }

.src-status { display: flex; flex-direction: column; gap: 6px; padding-top: 0.5rem; }
.src-row    { display: flex; align-items: center; gap: 7px; }
.src-dot    { width: 7px; height: 7px; border-radius: 50%; }
.src-dot.live { background: var(--pitch); }
.src-dot.off  { background: var(--chalk-3); }

/* Controls */
.controls-section { padding: 1.5rem; }
.controls-row {
  display: flex; align-items: flex-end; gap: 2rem; flex-wrap: wrap;
}

.match-field { flex: 1; min-width: 200px; }
.match-input {
  width: 100%; background: transparent;
  border: none; border-bottom: 2px solid var(--border);
  color: var(--chalk); font-family: var(--body); font-size: 0.95rem;
  padding: 6px 0; transition: border-color 0.2s;
}
.match-input:focus { outline: none; border-bottom-color: var(--pitch); }
.match-input::placeholder { color: var(--chalk-3); }

.toggle-row { display: flex; gap: 2px; }
.src-toggle {
  background: none; border: 1px solid var(--border); color: var(--chalk-3);
  font-family: var(--mono); font-size: 10px; letter-spacing: 0.08em;
  padding: 5px 12px; cursor: pointer; transition: all 0.15s;
}
.src-toggle.active { background: var(--pitch-l); border-color: var(--pitch); color: var(--pitch); }

.btn-fetch {
  background: var(--pitch); color: var(--void); border: none;
  font-family: var(--display); font-size: 1rem; letter-spacing: 0.1em;
  padding: 7px 20px; cursor: pointer; white-space: nowrap;
  transition: background 0.15s, opacity 0.15s;
  display: flex; align-items: center; gap: 6px;
}
.btn-fetch:hover:not(:disabled) { background: var(--chalk); }
.btn-fetch:disabled { opacity: 0.35; cursor: not-allowed; }

/* Pulse stats */
.pulse-row {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 1px;
  background: var(--border); border: 1px solid var(--border);
}
.pulse-card {
  background: var(--void); padding: 1.25rem; display: flex; flex-direction: column; gap: 4px;
  transition: background 0.15s;
}
.pulse-card:hover { background: var(--surface); }
.score-card { border-left: 1px solid var(--border); }
.pulse-val  { font-family: var(--display); font-size: 2.5rem; letter-spacing: 0.02em; line-height: 1; }
.pulse-val.pitch { color: var(--pitch); }
.pulse-val.muted { color: var(--chalk-2); }
.pulse-val.foul  { color: var(--foul); }
.pulse-count { font-family: var(--mono); font-size: 0.62rem; color: var(--chalk-3); }

/* Sentiment bar */
.sent-bar-wrap { }
.sent-bar {
  height: 8px; display: flex; gap: 1px; margin-bottom: 0.5rem;
}
.sent-seg { height: 100%; transition: width 0.8s ease; }
.sent-legend {
  display: flex; gap: 1.25rem; font-family: var(--mono); font-size: 10px;
  color: var(--chalk-3); align-items: center; flex-wrap: wrap;
}
.leg { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.leg.pitch    { background: var(--pitch); }
.leg.muted-leg{ background: var(--chalk-3); }
.leg.foul     { background: var(--foul); }
.total-posts  { margin-left: auto; }

/* Chart */
.chart-section { padding: 1.25rem; }

/* Feed */
.feed-section { }
.feed-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.875rem; }
.feed-filters { display: flex; gap: 2px; }
.feed-filter {
  background: none; border: 1px solid var(--border); color: var(--chalk-3);
  font-family: var(--mono); font-size: 9px; letter-spacing: 0.1em;
  padding: 4px 9px; cursor: pointer; transition: all 0.15s;
}
.feed-filter.active { border-color: var(--chalk-3); color: var(--chalk); }
.feed-filter.active.pitch-f { border-color: var(--pitch); color: var(--pitch); background: var(--pitch-l); }
.feed-filter.active.foul-f  { border-color: var(--foul);  color: var(--foul);  background: rgba(232,22,43,0.08); }

.feed-list { display: flex; flex-direction: column; gap: 1px; background: var(--border); border: 1px solid var(--border); }

.feed-item {
  background: var(--void); padding: 1rem;
  border-left: 3px solid transparent;
  transition: background 0.1s;
}
.feed-item:hover     { background: var(--surface); }
.feed-item.positive  { border-left-color: var(--pitch); }
.feed-item.negative  { border-left-color: var(--foul); }
.feed-item.neutral   { border-left-color: var(--border); }

.feed-top { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.src-chip {
  font-family: var(--mono); font-size: 9px; letter-spacing: 0.08em;
  padding: 1px 6px; border: 1px solid;
}
.src-chip.reddit  { color: #FF4500; border-color: rgba(255,69,0,0.3); }
.src-chip.twitter { color: var(--chalk-2); border-color: var(--border); }

.sent-chip {
  font-family: var(--mono); font-size: 9px; letter-spacing: 0.08em; font-weight: 600;
}
.sent-chip.positive { color: var(--pitch); }
.sent-chip.negative { color: var(--foul); }
.sent-chip.neutral  { color: var(--chalk-3); }

.vader-score { font-family: var(--mono); font-size: 9px; color: var(--chalk-3); margin-left: auto; }
.post-link   { font-family: var(--mono); font-size: 9px; color: var(--chalk-3); text-decoration: none; }
.post-link:hover { color: var(--pitch); }

.feed-text   { font-size: 0.82rem; color: var(--chalk-2); line-height: 1.55; margin-bottom: 6px; }
.feed-author { font-family: var(--mono); font-size: 0.62rem; color: var(--chalk-3); }

/* Empty */
.empty-state { text-align: center; padding: 4rem 2rem; }
.empty-icon  { font-size: 2.5rem; margin-bottom: 0.75rem; }
.empty-title { font-family: var(--display); font-size: 1.5rem; letter-spacing: 0.06em; color: var(--chalk-2); margin-bottom: 0.5rem; }
.empty-sub   { font-size: 0.8rem; color: var(--chalk-3); line-height: 1.5; }

.loading-dot {
  display: inline-block; width: 12px; height: 12px;
  border: 2px solid rgba(255,255,255,0.2); border-top-color: var(--void);
  border-radius: 50%; animation: spin 0.6s linear infinite;
}
</style>
