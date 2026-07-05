<template>
  <div class="sentiment-page">

    <!-- ── Hero ── -->
    <div class="page-hero">
      <div>
        <h1 class="page-title">Sentiment Pulse</h1>
        <p class="tagline">Real-time social media sentiment from Reddit and Twitter/X — what fans are saying during WC 2026 matches.</p>
      </div>
      <div class="source-badges" v-if="stats">
        <span class="src-badge" :class="stats.reddit_configured ? 'live' : 'off'">
          <span class="src-dot" />
          Reddit {{ stats.reddit_configured ? 'Live' : 'Not configured' }}
        </span>
        <span class="src-badge" :class="stats.twitter_configured ? 'live' : 'off'">
          <span class="src-dot" />
          Twitter/X {{ stats.twitter_configured ? 'Live' : 'Optional' }}
        </span>
      </div>
    </div>

    <!-- ── Setup notice if Reddit not configured ── -->
    <div class="setup-card card" v-if="stats && !stats.reddit_configured">
      <p class="setup-title">⚙️ Reddit API not configured</p>
      <p class="setup-desc">
        Add your Reddit credentials to <code>backend/.env</code> to enable live sentiment collection.
        Follow the instructions in <code>.env.example</code> — takes about 2 minutes.
      </p>
      <ol class="setup-steps">
        <li>Go to <strong>reddit.com/prefs/apps</strong> → create a "script" app</li>
        <li>Copy <code>client_id</code> and <code>client_secret</code></li>
        <li>Paste them into <code>backend/.env</code></li>
        <li>Restart the backend</li>
      </ol>
    </div>

    <!-- ── Controls ── -->
    <div class="card controls-card">
      <p class="eyebrow">Select a match</p>
      <div class="controls-row">
        <input
          v-model="matchSearch"
          list="match-list"
          placeholder="Search a match (e.g. Brazil vs Scotland)…"
          class="match-input"
          @change="onMatchSelect"
        />
        <datalist id="match-list">
          <option v-for="m in availableMatches" :key="m" :value="m" />
        </datalist>

        <div class="source-toggle">
          <button class="src-toggle-btn" :class="{ active: sources.includes('reddit') }"
            @click="toggleSource('reddit')">Reddit</button>
          <button class="src-toggle-btn" :class="{ active: sources.includes('twitter') }"
            @click="toggleSource('twitter')">Twitter/X</button>
        </div>

        <button class="btn-refresh" :disabled="!selectedMatch || refreshing" @click="refresh">
          <span v-if="refreshing" class="spinner" />
          <span v-else>↻ Fetch sentiment</span>
        </button>
      </div>
      <p class="last-updated" v-if="lastRefreshed">Last fetched: {{ lastRefreshed }}</p>
    </div>

    <!-- ── Pulse stats ── -->
    <div class="stats-row" v-if="stats && stats.total > 0">
      <div class="pulse-card pos">
        <div class="pulse-val">{{ positivePercent }}%</div>
        <div class="pulse-label">😊 Positive</div>
        <div class="pulse-count">{{ stats.positive }} posts</div>
      </div>
      <div class="pulse-card neu">
        <div class="pulse-val">{{ neutralPercent }}%</div>
        <div class="pulse-label">😐 Neutral</div>
        <div class="pulse-count">{{ stats.neutral }} posts</div>
      </div>
      <div class="pulse-card neg">
        <div class="pulse-val">{{ negativePercent }}%</div>
        <div class="pulse-label">😤 Negative</div>
        <div class="pulse-count">{{ stats.negative }} posts</div>
      </div>
      <div class="pulse-card avg">
        <div class="pulse-val" :style="{ color: scoreColor(stats.avg_score) }">
          {{ stats.avg_score > 0 ? '+' : '' }}{{ stats.avg_score.toFixed(2) }}
        </div>
        <div class="pulse-label">Avg sentiment score</div>
        <div class="pulse-count">−1.0 = max negative · +1.0 = max positive</div>
      </div>
    </div>

    <!-- ── Sentiment bar ── -->
    <div class="sentiment-bar-wrap card" v-if="stats && stats.total > 0">
      <p class="eyebrow" style="margin-bottom:0.75rem">Sentiment distribution</p>
      <div class="sentiment-bar">
        <div class="bar-seg pos" :style="{ width: positivePercent + '%' }" :title="`${positivePercent}% positive`" />
        <div class="bar-seg neu" :style="{ width: neutralPercent  + '%' }" :title="`${neutralPercent}% neutral`" />
        <div class="bar-seg neg" :style="{ width: negativePercent + '%' }" :title="`${negativePercent}% negative`" />
      </div>
      <div class="bar-legend">
        <span><span class="leg-dot pos" />Positive {{ positivePercent }}%</span>
        <span><span class="leg-dot neu" />Neutral {{ neutralPercent }}%</span>
        <span><span class="leg-dot neg" />Negative {{ negativePercent }}%</span>
        <span class="total-count">{{ stats.total }} total posts</span>
      </div>
    </div>

    <!-- ── Trend chart ── -->
    <div class="card" v-if="trend.length > 0">
      <p class="eyebrow" style="margin-bottom:1rem">Hourly trend (last 24h)</p>
      <div style="height:220px;position:relative">
        <canvas ref="trendCanvas" />
      </div>
    </div>

    <!-- ── Feed ── -->
    <div class="card feed-card" v-if="feed.length > 0">
      <div class="feed-header">
        <p class="eyebrow">Live feed</p>
        <div class="feed-filters">
          <button class="feed-filter" :class="{ active: feedFilter === 'all' }"    @click="feedFilter = 'all'">All</button>
          <button class="feed-filter" :class="{ active: feedFilter === 'POSITIVE' }" @click="feedFilter = 'POSITIVE'">😊</button>
          <button class="feed-filter" :class="{ active: feedFilter === 'NEUTRAL' }"  @click="feedFilter = 'NEUTRAL'">😐</button>
          <button class="feed-filter" :class="{ active: feedFilter === 'NEGATIVE' }" @click="feedFilter = 'NEGATIVE'">😤</button>
        </div>
      </div>

      <div class="feed-list">
        <div v-for="item in filteredFeed" :key="item.id" class="feed-item" :class="item.label.toLowerCase()">
          <div class="feed-meta">
            <span class="feed-source" :class="item.source">{{ item.source }}</span>
            <span class="feed-label" :class="item.label.toLowerCase()">
              {{ item.label === 'POSITIVE' ? '😊' : item.label === 'NEGATIVE' ? '😤' : '😐' }}
              {{ item.label }}
            </span>
            <span class="feed-score">{{ item.score > 0 ? '+' : '' }}{{ item.score }}</span>
          </div>
          <p class="feed-text">{{ item.text }}</p>
          <div class="feed-footer">
            <span class="feed-author">u/{{ item.author }}</span>
            <a v-if="item.url" :href="item.url" target="_blank" class="feed-link">View post ↗</a>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Empty state ── -->
    <div class="empty-state card" v-else-if="!refreshing && selectedMatch">
      <p class="empty-icon">📡</p>
      <p class="empty-title">No posts collected yet</p>
      <p class="empty-desc">Click "Fetch sentiment" to collect posts about <strong>{{ selectedMatch }}</strong> from Reddit and Twitter.</p>
    </div>

    <div class="empty-state card" v-else-if="!selectedMatch">
      <p class="empty-icon">🔍</p>
      <p class="empty-title">Select a match to begin</p>
      <p class="empty-desc">Choose a WC 2026 match above to start tracking what fans are saying in real time.</p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip } from 'chart.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Filler, Tooltip)

const stats        = ref(null)
const feed         = ref([])
const trend        = ref([])
const matchSearch  = ref('')
const selectedMatch = ref('')
const sources      = ref(['reddit'])
const refreshing   = ref(false)
const feedFilter   = ref('all')
const lastRefreshed = ref('')
const trendCanvas  = ref(null)
let trendChart     = null
let autoTimer      = null

// WC 2026 matches for the datalist
const availableMatches = ref([])

const positivePercent = computed(() => {
  if (!stats.value || stats.value.total === 0) return 0
  return Math.round(stats.value.positive / stats.value.total * 100)
})
const neutralPercent = computed(() => {
  if (!stats.value || stats.value.total === 0) return 0
  return Math.round(stats.value.neutral / stats.value.total * 100)
})
const negativePercent = computed(() => {
  if (!stats.value || stats.value.total === 0) return 0
  return Math.round(stats.value.negative / stats.value.total * 100)
})

const filteredFeed = computed(() => {
  if (feedFilter.value === 'all') return feed.value
  return feed.value.filter(i => i.label === feedFilter.value)
})

function scoreColor(score) {
  if (score > 0.1) return 'var(--green)'
  if (score < -0.1) return 'var(--coral)'
  return 'var(--muted)'
}

function toggleSource(src) {
  if (sources.value.includes(src)) {
    if (sources.value.length > 1) sources.value = sources.value.filter(s => s !== src)
  } else {
    sources.value.push(src)
  }
}

function onMatchSelect() {
  const match = availableMatches.value.find(
    m => m.toLowerCase() === matchSearch.value.toLowerCase()
  )
  if (match) selectedMatch.value = match
  else selectedMatch.value = matchSearch.value  // allow free-text too
}

async function refresh() {
  if (!selectedMatch.value || refreshing.value) return
  refreshing.value = true
  try {
    await axios.post('/api/v1/sentiment/refresh', null, {
      params: { match_tag: selectedMatch.value, sources: sources.value.join(',') }
    })
    await loadData()
    lastRefreshed.value = new Date().toLocaleTimeString()
  } catch (e) {
    alert('Refresh failed — is the backend running?')
  } finally {
    refreshing.value = false
  }
}

async function loadData() {
  const [statsRes, feedRes, trendRes] = await Promise.all([
    axios.get('/api/v1/sentiment/stats',  { params: { match_tag: selectedMatch.value || undefined } }),
    axios.get('/api/v1/sentiment/feed',   { params: { match_tag: selectedMatch.value || undefined, limit: 40 } }),
    axios.get('/api/v1/sentiment/trend',  { params: { match_tag: selectedMatch.value || undefined } }),
  ])
  stats.value = statsRes.data
  feed.value  = feedRes.data
  trend.value = trendRes.data

  // Populate available matches from DB tags + predictions
  if (statsRes.data.match_tags?.length) {
    availableMatches.value = [...new Set([...availableMatches.value, ...statsRes.data.match_tags])]
  }

  buildTrendChart()
}

function buildTrendChart() {
  if (trendChart) { trendChart.destroy(); trendChart = null }
  if (!trendCanvas.value || trend.value.length === 0) return

  trendChart = new Chart(trendCanvas.value, {
    type: 'line',
    data: {
      labels: trend.value.map(t => t.hour),
      datasets: [
        { label: 'Positive', data: trend.value.map(t => t.positive), borderColor: '#0acf83', backgroundColor: 'rgba(10,207,131,0.07)', fill: true, tension: 0.4, borderWidth: 2 },
        { label: 'Negative', data: trend.value.map(t => t.negative), borderColor: '#ff7262', backgroundColor: 'rgba(255,114,98,0.07)',  fill: true, tension: 0.4, borderWidth: 2 },
        { label: 'Neutral',  data: trend.value.map(t => t.neutral),  borderColor: '#f5a623', backgroundColor: 'rgba(245,166,35,0.07)', fill: true, tension: 0.4, borderWidth: 2 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#6b6b88', font: { size: 11 }, boxWidth: 10 } },
        tooltip: { backgroundColor: '#10101a', borderColor: '#1e1e32', borderWidth: 1, titleColor: '#e8e8f0', bodyColor: '#6b6b88' },
      },
      scales: {
        x: { ticks: { color: '#6b6b88', font: { size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
        y: { ticks: { color: '#6b6b88', font: { size: 10 }, stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.04)' }, min: 0 },
      },
    },
  })
}

// Load predictions list for match suggestions
async function loadMatchList() {
  try {
    const { data } = await axios.get('/api/v1/predictions')
    const matches = data.map(p => `${p.team_a} vs ${p.team_b}`)
    availableMatches.value = [...new Set(matches)]
  } catch {}
}

onMounted(async () => {
  await Promise.all([loadData(), loadMatchList()])
  // Auto-refresh every 5 minutes if a match is selected
  autoTimer = setInterval(() => {
    if (selectedMatch.value) loadData()
  }, 5 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (autoTimer) clearInterval(autoTimer)
  if (trendChart) trendChart.destroy()
})
</script>

<style scoped>
.sentiment-page { display: flex; flex-direction: column; gap: 1.5rem; animation: rise 0.3s ease; }

/* Hero */
.page-hero { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
.tagline   { font-size: 0.875rem; color: var(--muted); max-width: 520px; line-height: 1.5; margin-top: 0.35rem; }

.source-badges { display: flex; gap: 0.5rem; align-items: flex-start; flex-wrap: wrap; }
.src-badge {
  display: flex; align-items: center; gap: 6px;
  font-family: var(--mono); font-size: 0.68rem; font-weight: 600;
  padding: 4px 10px; border-radius: 99px; border: 1px solid;
}
.src-badge.live { background: rgba(10,207,131,0.1); color: var(--green); border-color: rgba(10,207,131,0.3); }
.src-badge.off  { background: rgba(107,107,136,0.1); color: var(--muted); border-color: var(--border); }
.src-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

/* Setup card */
.setup-card { border-left: 3px solid var(--gold); }
.setup-title { font-weight: 700; margin-bottom: 0.5rem; }
.setup-desc  { font-size: 0.82rem; color: var(--muted); margin-bottom: 0.75rem; line-height: 1.55; }
.setup-steps { font-size: 0.78rem; color: var(--muted); padding-left: 1.25rem; display: flex; flex-direction: column; gap: 4px; }
.setup-steps code { background: var(--surface2); padding: 1px 5px; border-radius: 4px; font-family: var(--mono); font-size: 0.72rem; }

/* Controls */
.controls-row {
  display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.75rem;
}
.match-input {
  flex: 1; min-width: 200px;
  background: var(--surface2); border: 1.5px solid var(--border);
  color: var(--text); padding: 0.6rem 1rem; border-radius: var(--r);
  font-family: var(--font); font-size: 0.875rem; transition: border-color 0.2s;
}
.match-input:focus { outline: none; border-color: var(--gold); }

.source-toggle { display: flex; gap: 4px; }
.src-toggle-btn {
  background: none; border: 1px solid var(--border); color: var(--muted);
  padding: 6px 12px; border-radius: 99px; font-size: 0.75rem;
  font-family: var(--font); cursor: pointer; transition: all 0.15s;
}
.src-toggle-btn.active { background: var(--gold-dim); color: var(--gold); border-color: var(--gold); }

.btn-refresh {
  background: var(--gold); color: #07070f; border: none;
  padding: 0.6rem 1.25rem; border-radius: var(--r);
  font-weight: 700; font-size: 0.875rem; cursor: pointer;
  font-family: var(--font); display: flex; align-items: center; gap: 6px;
  white-space: nowrap; transition: opacity 0.15s;
}
.btn-refresh:hover:not(:disabled) { opacity: 0.85; }
.btn-refresh:disabled { opacity: 0.4; cursor: not-allowed; }

.last-updated { font-family: var(--mono); font-size: 0.68rem; color: var(--muted); margin-top: 0.5rem; }

/* Pulse stats */
.stats-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.875rem; }
.pulse-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--r); padding: 1.25rem; text-align: center;
  border-top: 3px solid transparent;
}
.pulse-card.pos { border-top-color: var(--green); }
.pulse-card.neu { border-top-color: var(--neu); }
.pulse-card.neg { border-top-color: var(--coral); }
.pulse-card.avg { border-top-color: var(--blue); }
.pulse-val   { font-size: 2rem; font-weight: 900; letter-spacing: -0.04em; }
.pulse-label { font-size: 0.8rem; color: var(--muted); margin: 4px 0; }
.pulse-count { font-family: var(--mono); font-size: 0.65rem; color: var(--muted); }

/* Sentiment bar */
.sentiment-bar {
  height: 12px; border-radius: 99px; overflow: hidden;
  display: flex; gap: 2px; margin-bottom: 0.75rem;
}
.bar-seg { height: 100%; border-radius: 99px; transition: width 0.8s ease; }
.bar-seg.pos { background: var(--green); }
.bar-seg.neu { background: var(--neu); }
.bar-seg.neg { background: var(--coral); }
.bar-legend  { display: flex; gap: 1.25rem; font-size: 0.75rem; color: var(--muted); flex-wrap: wrap; align-items: center; }
.leg-dot     { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.leg-dot.pos { background: var(--green); }
.leg-dot.neu { background: var(--neu); }
.leg-dot.neg { background: var(--coral); }
.total-count { margin-left: auto; font-family: var(--mono); font-size: 0.68rem; }

/* Feed */
.feed-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.feed-filters { display: flex; gap: 4px; }
.feed-filter {
  background: none; border: 1px solid var(--border); color: var(--muted);
  padding: 3px 10px; border-radius: 99px; font-size: 0.72rem;
  cursor: pointer; font-family: var(--font); transition: all 0.15s;
}
.feed-filter.active { background: var(--gold-dim); color: var(--gold); border-color: var(--gold); }

.feed-list  { display: flex; flex-direction: column; gap: 0.75rem; }
.feed-item  {
  background: var(--surface2); border: 1px solid var(--border);
  border-left: 3px solid transparent; border-radius: var(--r); padding: 1rem;
}
.feed-item.positive { border-left-color: var(--green); }
.feed-item.negative { border-left-color: var(--coral); }
.feed-item.neutral  { border-left-color: var(--neu); }

.feed-meta   { display: flex; align-items: center; gap: 8px; margin-bottom: 0.5rem; flex-wrap: wrap; }
.feed-source { font-family: var(--mono); font-size: 0.65rem; padding: 2px 7px; border-radius: 4px; font-weight: 600; }
.feed-source.reddit  { background: rgba(255,69,0,0.12); color: #ff4500; }
.feed-source.twitter { background: rgba(26,188,254,0.12); color: var(--blue); }
.feed-label  { font-family: var(--mono); font-size: 0.68rem; font-weight: 600; }
.feed-label.positive { color: var(--green); }
.feed-label.negative { color: var(--coral); }
.feed-label.neutral  { color: var(--neu); }
.feed-score  { font-family: var(--mono); font-size: 0.65rem; color: var(--muted); margin-left: auto; }
.feed-text   { font-size: 0.85rem; color: var(--muted); line-height: 1.55; margin-bottom: 0.5rem; }
.feed-footer { display: flex; justify-content: space-between; }
.feed-author { font-family: var(--mono); font-size: 0.65rem; color: var(--muted); }
.feed-link   { font-family: var(--mono); font-size: 0.65rem; color: var(--gold); text-decoration: none; }
.feed-link:hover { text-decoration: underline; }

/* Empty state */
.empty-state { text-align: center; padding: 3rem; }
.empty-icon  { font-size: 2.5rem; margin-bottom: 0.75rem; }
.empty-title { font-weight: 700; margin-bottom: 0.5rem; }
.empty-desc  { font-size: 0.85rem; color: var(--muted); line-height: 1.55; }
</style>
