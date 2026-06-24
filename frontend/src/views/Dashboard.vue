<template>
  <div class="dashboard">

    <!-- ── Hero ── -->
    <div class="hero-section">
      <div>
        <div class="live-badge">🔴 Live · WC 2026</div>
        <h1 class="page-title">Match Intelligence</h1>
        <p class="tagline">AI-powered outcome predictions for every 2026 World Cup match, trained on 32,000+ international fixtures since 1990.</p>
      </div>
      <div class="model-pill" v-if="lastUpdated">
        <span class="model-version">Model v1.0 · RF + XGBoost ensemble</span>
        <span class="model-date">Updated {{ lastUpdated }}</span>
      </div>
    </div>

    <!-- ── Primary KPI ── -->
    <div class="kpi-hero card" v-if="accuracy">
      <div class="kpi-primary">
        <svg viewBox="0 0 120 120" class="acc-ring">
          <circle cx="60" cy="60" r="52" fill="none" stroke="#1e1e32" stroke-width="10"/>
          <circle cx="60" cy="60" r="52" fill="none"
            :stroke="accuracy.accuracy >= 70 ? 'var(--green)' : accuracy.accuracy >= 55 ? 'var(--gold)' : 'var(--coral)'"
            stroke-width="10" stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="dashOffset"
            transform="rotate(-90 60 60)"
            style="transition: stroke-dashoffset 1s ease"
          />
          <text x="60" y="54" text-anchor="middle" fill="var(--gold-l)" font-size="22" font-weight="900" font-family="Inter">
            {{ accuracy.accuracy }}%
          </text>
          <text x="60" y="72" text-anchor="middle" fill="#6b6b88" font-size="8.5" font-family="JetBrains Mono">
            ACCURACY
          </text>
        </svg>
        <div class="kpi-primary-text">
          <p class="eyebrow">Tournament accuracy</p>
          <h2 class="kpi-headline">{{ accuracy.correct }} from {{ accuracy.played }} correct</h2>
          <p class="kpi-note">Both wrong predictions were goalless draws — statistically the hardest outcome to predict. No model consistently predicts a goalkeeper saving 15 shots.</p>
        </div>
      </div>
      <div class="kpi-row">
        <div class="kpi-stat">
          <span class="kpi-val">{{ accuracy.total_predictions }}</span>
          <span class="kpi-lab">Total</span>
        </div>
        <div class="kpi-stat">
          <span class="kpi-val">{{ accuracy.played }}</span>
          <span class="kpi-lab">Played</span>
        </div>
        <div class="kpi-stat">
          <span class="kpi-val" style="color:var(--green)">{{ accuracy.correct }}</span>
          <span class="kpi-lab">Correct</span>
        </div>
        <div class="kpi-stat">
          <span class="kpi-val" style="color:var(--coral)">{{ accuracy.played - accuracy.correct }}</span>
          <span class="kpi-lab">Wrong</span>
        </div>
        <div class="kpi-stat">
          <span class="kpi-val" style="color:var(--muted)">{{ accuracy.total_predictions - accuracy.played }}</span>
          <span class="kpi-lab">Pending</span>
        </div>
      </div>
    </div>

    <!-- ── Model Insights ── -->
    <div class="card" v-if="playedPredictions.length > 0">
      <p class="eyebrow" style="margin-bottom:1rem">Model insights</p>
      <div class="insights-grid">
        <!-- Accuracy by confidence -->
        <div class="insight-block">
          <p class="insight-title">Accuracy by confidence bucket</p>
          <div class="bucket-list">
            <div v-for="b in confidenceBuckets" :key="b.label" class="bucket-row">
              <span class="bucket-label">{{ b.label }}</span>
              <div class="bucket-bar-track">
                <div class="bucket-bar" :style="{ width: b.pct + '%', background: b.color }"/>
              </div>
              <span class="bucket-stat">{{ b.correct }}/{{ b.total }} ({{ b.pct }}%)</span>
            </div>
          </div>
          <p class="insight-note">High-confidence calls (≥70%) are most reliable. Treat anything below 55% as a coin flip.</p>
        </div>
        <!-- Failure modes -->
        <div class="insight-block">
          <p class="insight-title">Known failure modes</p>
          <div class="failure-list">
            <div class="failure-item">
              <span class="failure-icon">⚖️</span>
              <div>
                <p class="failure-label">Goalless draws</p>
                <p class="failure-desc">Model trained on match statistics cannot predict exceptional individual goalkeeper performances. Both incorrect predictions were 0-0 results.</p>
              </div>
            </div>
            <div class="failure-item">
              <span class="failure-icon">📉</span>
              <div>
                <p class="failure-label">Low-confidence calls</p>
                <p class="failure-desc">When no team exceeds 55% win probability, outcomes are genuinely uncertain. The model is well-calibrated in these cases — low confidence reflects real uncertainty.</p>
              </div>
            </div>
            <div class="failure-item">
              <span class="failure-icon">🆕</span>
              <div>
                <p class="failure-label">Debutant nations</p>
                <p class="failure-desc">Teams with limited international history (Curaçao, Cabo Verde) have sparse form data, making their predictions less reliable.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Predictor ── -->
    <div class="card predictor-card">
      <p class="eyebrow">Live predictor</p>
      <p class="pred-desc">Enter any two WC 2026 nations. The model calculates win/draw/loss probabilities using recent international form, head-to-head history, FIFA rankings, and scoring patterns.</p>

      <div class="pred-form">
        <div class="input-wrap">
          <input v-model="teamA" list="nations-list" placeholder="Team A" class="team-input"
            :class="{ error: teamAError }" @keydown.enter="predict" @blur="validateTeam('a')" />
          <span class="input-error" v-if="teamAError">Not a recognised WC 2026 nation</span>
        </div>
        <span class="vs-badge">VS</span>
        <div class="input-wrap">
          <input v-model="teamB" list="nations-list" placeholder="Team B" class="team-input"
            :class="{ error: teamBError }" @keydown.enter="predict" @blur="validateTeam('b')" />
          <span class="input-error" v-if="teamBError">Not a recognised WC 2026 nation</span>
        </div>
        <datalist id="nations-list">
          <option v-for="n in nations" :key="n" :value="n" />
        </datalist>
        <button class="btn-predict" :disabled="!canPredict || predicting" @click="predict">
          <span v-if="predicting" class="spinner" />
          <span v-else>Predict →</span>
        </button>
      </div>

      <p class="responsible-ai">⚠️ These are probability estimates, not guarantees. The model simulates thousands of historical outcomes to produce each figure. Football is inherently unpredictable.</p>

      <div class="pred-result" v-if="predResult">
        <div class="pred-bars">
          <div class="pred-bar-row">
            <span class="bar-label">{{ predResult.team_a }}</span>
            <div class="bar-track">
              <div class="bar-fill gold" :style="{ width: predResult.team_a_win + '%' }"/>
            </div>
            <span class="bar-pct">{{ predResult.team_a_win }}%</span>
          </div>
          <div class="pred-bar-row">
            <span class="bar-label">Draw</span>
            <div class="bar-track">
              <div class="bar-fill muted" :style="{ width: predResult.draw + '%' }"/>
            </div>
            <span class="bar-pct">{{ predResult.draw }}%</span>
          </div>
          <div class="pred-bar-row">
            <span class="bar-label">{{ predResult.team_b }}</span>
            <div class="bar-track">
              <div class="bar-fill purple" :style="{ width: predResult.team_b_win + '%' }"/>
            </div>
            <span class="bar-pct">{{ predResult.team_b_win }}%</span>
          </div>
        </div>
        <div class="pred-verdict">
          <span class="verdict-label">Predicted:</span>
          <strong>{{ predResult.predicted }}</strong>
          <span class="conf-badge" :class="confClass(predResult.confidence)">
            {{ predResult.confidence }}% confidence
          </span>
          <span v-if="predResult.draw_risk" class="draw-badge">⚖️ Draw risk</span>
        </div>
      </div>
    </div>

    <!-- ── Predictions Table ── -->
    <div class="card">
      <div class="table-header">
        <p class="eyebrow">All predictions</p>
        <div class="table-controls">
          <!-- Filter -->
          <div class="filter-tabs">
            <button v-for="f in filters" :key="f.val"
              class="filter-tab" :class="{ active: activeFilter === f.val }"
              @click="activeFilter = f.val">
              {{ f.label }}
              <span class="filter-count">{{ f.count }}</span>
            </button>
          </div>
          <!-- Sort -->
          <select v-model="sortBy" class="sort-select">
            <option value="default">Default order</option>
            <option value="confidence_desc">Confidence ↓</option>
            <option value="confidence_asc">Confidence ↑</option>
            <option value="group">Group</option>
          </select>
        </div>
      </div>

      <div v-if="loading" style="text-align:center;padding:2rem;color:var(--muted)">
        <span class="spinner"/> Loading…
      </div>

      <table class="pred-table" v-else>
        <thead>
          <tr>
            <th>Match</th>
            <th>Group</th>
            <th>Predicted</th>
            <th style="text-align:right">Confidence</th>
            <th style="text-align:right">Result</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filteredPredictions" :key="p.team_a + p.team_b"
            :class="[rowClass(p), isHighConfWrong(p) ? 'high-conf-wrong' : '']">
            <td class="match-cell">
              {{ p.team_a }} <span class="vs">vs</span> {{ p.team_b }}
              <span v-if="isHighConfWrong(p)" class="hcw-badge" title="High-confidence wrong prediction">⚡</span>
            </td>
            <td class="group-cell">{{ p.stage }}</td>
            <td>
              <span class="pred-pill">{{ p.predicted }}</span>
            </td>
            <td style="text-align:right">
              <div class="conf-cell">
                <div class="mini-bar" :style="{ width: Math.min(p.confidence, 100) + '%', background: confColor(p.confidence) }"/>
                <span class="mini-pct">{{ p.confidence }}%</span>
              </div>
            </td>
            <td style="text-align:right">
              <span v-if="!p.actual_result" class="status pending">⏳ Pending</span>
              <span v-else-if="isCorrect(p)" class="status correct">✅ {{ p.actual_result }}</span>
              <span v-else class="status wrong">❌ {{ p.actual_result }}</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="table-footer" v-if="!loading">
        Showing {{ filteredPredictions.length }} of {{ predictions.length }} predictions
        <span v-if="activeFilter !== 'all'"> · <button class="clear-filter" @click="activeFilter = 'all'">Clear filter</button></span>
      </p>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const accuracy    = ref(null)
const predictions = ref([])
const nations     = ref([])
const loading     = ref(true)
const teamA       = ref('')
const teamB       = ref('')
const teamAError  = ref(false)
const teamBError  = ref(false)
const predicting  = ref(false)
const predResult  = ref(null)
const activeFilter = ref('all')
const sortBy      = ref('default')
const lastUpdated = ref('')

const circumference = 2 * Math.PI * 52
const dashOffset    = computed(() => {
  if (!accuracy.value) return circumference
  return circumference * (1 - accuracy.value.accuracy / 100)
})

const playedPredictions = computed(() =>
  predictions.value.filter(p => p.actual_result)
)

// Confidence buckets for model insights
const confidenceBuckets = computed(() => {
  const played = playedPredictions.value
  const buckets = [
    { label: 'High (≥70%)',    min: 70,  max: 100, color: 'var(--green)' },
    { label: 'Medium (55–70%)',min: 55,  max: 70,  color: 'var(--gold)'  },
    { label: 'Low (<55%)',     min: 0,   max: 55,  color: 'var(--muted)' },
  ]
  return buckets.map(b => {
    const sub   = played.filter(p => p.confidence >= b.min && p.confidence < b.max)
    const correct = sub.filter(p => isCorrect(p)).length
    const total   = sub.length
    return { ...b, correct, total, pct: total ? Math.round(correct / total * 100) : 0 }
  })
})

// Table filters
const filters = computed(() => [
  { val: 'all',     label: 'All',     count: predictions.value.length },
  { val: 'pending', label: 'Pending', count: predictions.value.filter(p => !p.actual_result).length },
  { val: 'correct', label: '✅ Correct', count: predictions.value.filter(p => isCorrect(p)).length },
  { val: 'wrong',   label: '❌ Wrong',   count: predictions.value.filter(p => p.actual_result && !isCorrect(p)).length },
])

const filteredPredictions = computed(() => {
  let list = [...predictions.value]

  if (activeFilter.value === 'pending') list = list.filter(p => !p.actual_result)
  else if (activeFilter.value === 'correct') list = list.filter(p => isCorrect(p))
  else if (activeFilter.value === 'wrong') list = list.filter(p => p.actual_result && !isCorrect(p))

  if (sortBy.value === 'confidence_desc') list.sort((a, b) => b.confidence - a.confidence)
  else if (sortBy.value === 'confidence_asc') list.sort((a, b) => a.confidence - b.confidence)
  else if (sortBy.value === 'group') list.sort((a, b) => (a.stage || '').localeCompare(b.stage || ''))

  return list
})

const canPredict = computed(() => teamA.value.trim() && teamB.value.trim() && !teamAError.value && !teamBError.value)

function isCorrect(p) { return String(p.correct).toLowerCase() === 'true' }
function rowClass(p) {
  if (!p.actual_result) return 'row-pending'
  return isCorrect(p) ? 'row-correct' : 'row-wrong'
}
function isHighConfWrong(p) { return p.actual_result && !isCorrect(p) && p.confidence >= 65 }

function confColor(conf) {
  if (conf >= 70) return 'var(--green)'
  if (conf >= 55) return 'var(--gold)'
  return 'var(--muted)'
}
function confClass(conf) {
  if (conf >= 70) return 'conf-high'
  if (conf >= 55) return 'conf-mid'
  return 'conf-low'
}

function validateTeam(side) {
  if (!nations.value.length) return
  const val = side === 'a' ? teamA.value : teamB.value
  const valid = !val || nations.value.includes(val)
  if (side === 'a') teamAError.value = !valid
  else teamBError.value = !valid
}

async function predict() {
  if (!canPredict.value) return
  predicting.value = true
  predResult.value = null
  try {
    const { data } = await axios.post('/api/v1/predict', {
      team_a: teamA.value, team_b: teamB.value,
    })
    predResult.value = data
  } catch {
    alert('Prediction failed — is the backend running?')
  } finally {
    predicting.value = false
  }
}

onMounted(async () => {
  try {
    const [accRes, predRes, natRes] = await Promise.all([
      axios.get('/api/v1/accuracy'),
      axios.get('/api/v1/predictions'),
      axios.get('/api/v1/nations'),
    ])
    accuracy.value    = accRes.data
    predictions.value = predRes.data
    nations.value     = natRes.data
    lastUpdated.value = new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 1.5rem; animation: rise 0.3s ease; }

/* Hero */
.hero-section { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; }
.live-badge {
  display: inline-block; font-family: var(--mono); font-size: 0.68rem; font-weight: 600;
  padding: 3px 10px; border-radius: 99px; background: rgba(255,80,80,0.12);
  color: #ff6060; border: 1px solid rgba(255,80,80,0.2); margin-bottom: 0.5rem;
}
.tagline { font-size: 0.875rem; color: var(--muted); max-width: 520px; line-height: 1.5; margin-top: 0.35rem; }
.model-pill {
  display: flex; flex-direction: column; align-items: flex-end; gap: 3px;
  background: var(--surface); border: 1px solid var(--border);
  padding: 8px 14px; border-radius: var(--r);
}
.model-version { font-family: var(--mono); font-size: 0.68rem; color: var(--gold); }
.model-date    { font-family: var(--mono); font-size: 0.62rem; color: var(--muted); }

/* KPI Hero */
.kpi-hero { }
.kpi-primary { display: flex; gap: 2rem; align-items: center; margin-bottom: 1.5rem; }
.acc-ring { width: 130px; height: 130px; flex-shrink: 0; }
.kpi-primary-text { flex: 1; }
.kpi-headline { font-size: 1.3rem; font-weight: 800; letter-spacing: -0.03em; margin: 0.25rem 0 0.5rem; }
.kpi-note { font-size: 0.8rem; color: var(--muted); line-height: 1.55; max-width: 440px; }
.kpi-row { display: flex; gap: 2rem; padding-top: 1.25rem; border-top: 1px solid var(--border); }
.kpi-stat { display: flex; flex-direction: column; gap: 2px; }
.kpi-val  { font-size: 1.75rem; font-weight: 800; letter-spacing: -0.04em; }
.kpi-lab  { font-family: var(--mono); font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); }

/* Model insights */
.insights-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
@media (max-width: 720px) { .insights-grid { grid-template-columns: 1fr; } }
.insight-title { font-size: 0.8rem; font-weight: 700; color: var(--text); margin-bottom: 0.875rem; }
.insight-note  { font-size: 0.72rem; color: var(--muted); margin-top: 0.75rem; line-height: 1.5; }

.bucket-list { display: flex; flex-direction: column; gap: 8px; }
.bucket-row  { display: grid; grid-template-columns: 120px 1fr 80px; align-items: center; gap: 8px; }
.bucket-label { font-size: 0.75rem; color: var(--muted); }
.bucket-bar-track { height: 5px; background: var(--border); border-radius: 99px; overflow: hidden; }
.bucket-bar   { height: 100%; border-radius: 99px; transition: width 0.8s ease; }
.bucket-stat  { font-family: var(--mono); font-size: 0.7rem; color: var(--muted); text-align: right; }

.failure-list { display: flex; flex-direction: column; gap: 0.875rem; }
.failure-item { display: flex; gap: 10px; align-items: flex-start; }
.failure-icon { font-size: 1rem; flex-shrink: 0; margin-top: 1px; }
.failure-label { font-size: 0.78rem; font-weight: 600; color: var(--text); margin-bottom: 2px; }
.failure-desc  { font-size: 0.72rem; color: var(--muted); line-height: 1.5; }

/* Predictor */
.predictor-card { }
.pred-desc { font-size: 0.8rem; color: var(--muted); margin: 0.35rem 0 1rem; line-height: 1.55; max-width: 600px; }
.pred-form { display: flex; align-items: flex-start; gap: 0.75rem; flex-wrap: wrap; }
.input-wrap { flex: 1; min-width: 150px; display: flex; flex-direction: column; gap: 4px; }
.team-input {
  width: 100%; background: var(--surface2); border: 1.5px solid var(--border);
  color: var(--text); padding: 0.6rem 1rem; border-radius: var(--r);
  font-family: var(--font); font-size: 0.9rem; transition: border-color 0.2s;
}
.team-input:focus { outline: none; border-color: var(--gold); }
.team-input.error { border-color: var(--coral); }
.input-error { font-size: 0.7rem; color: var(--coral); }
.vs-badge { font-family: var(--mono); font-size: 0.7rem; font-weight: 700; color: var(--muted); letter-spacing: 0.1em; padding-top: 0.65rem; }
.btn-predict {
  background: var(--gold); color: #07070f; border: none;
  padding: 0.6rem 1.4rem; border-radius: var(--r);
  font-weight: 700; font-size: 0.875rem; cursor: pointer;
  font-family: var(--font); white-space: nowrap;
  transition: opacity 0.15s, transform 0.15s;
  display: flex; align-items: center; gap: 6px; align-self: flex-start;
}
.btn-predict:hover:not(:disabled) { opacity: 0.88; transform: translateY(-1px); }
.btn-predict:disabled { opacity: 0.4; cursor: not-allowed; }

.responsible-ai {
  font-size: 0.72rem; color: var(--muted); margin-top: 0.875rem;
  padding: 0.5rem 0.875rem; background: rgba(255,255,255,0.03);
  border-left: 2px solid var(--border); border-radius: 0 4px 4px 0;
  line-height: 1.5;
}

.pred-result { margin-top: 1.25rem; padding-top: 1.25rem; border-top: 1px solid var(--border); }
.pred-bars { display: flex; flex-direction: column; gap: 8px; }
.pred-bar-row { display: grid; grid-template-columns: 120px 1fr 48px; align-items: center; gap: 10px; }
.bar-label { font-size: 0.82rem; color: var(--muted); font-weight: 500; }
.bar-track { height: 6px; background: var(--border); border-radius: 99px; overflow: hidden; }
.bar-fill  { height: 100%; border-radius: 99px; transition: width 0.8s cubic-bezier(0.34,1.56,0.64,1); }
.bar-fill.gold   { background: var(--gold); }
.bar-fill.purple { background: var(--purple); }
.bar-fill.muted  { background: var(--muted); }
.bar-pct { font-family: var(--mono); font-size: 0.72rem; color: var(--muted); text-align: right; }
.pred-verdict { display: flex; align-items: center; gap: 8px; margin-top: 1rem; font-size: 0.875rem; color: var(--muted); flex-wrap: wrap; }
.verdict-label { color: var(--muted); }
.pred-verdict strong { color: var(--gold-l); }
.conf-badge { font-family: var(--mono); font-size: 0.72rem; padding: 2px 8px; border-radius: 99px; }
.conf-badge.conf-high { background: rgba(10,207,131,0.12); color: var(--green); }
.conf-badge.conf-mid  { background: var(--gold-dim);         color: var(--gold);  }
.conf-badge.conf-low  { background: rgba(107,107,136,0.15);  color: var(--muted); }
.draw-badge { font-family: var(--mono); font-size: 0.72rem; padding: 2px 8px; border-radius: 99px; background: rgba(245,166,35,0.12); color: #f5a623; border: 1px solid rgba(245,166,35,0.2); }

/* Table */
.table-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
.table-controls { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }

.filter-tabs { display: flex; gap: 4px; }
.filter-tab {
  background: none; border: 1px solid var(--border); color: var(--muted);
  padding: 4px 10px; border-radius: 99px; font-size: 0.72rem; font-family: var(--font);
  cursor: pointer; display: flex; align-items: center; gap: 5px;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.filter-tab.active { background: var(--gold-dim); color: var(--gold); border-color: var(--gold); }
.filter-tab:hover:not(.active) { border-color: var(--muted); color: var(--text); }
.filter-count { font-family: var(--mono); font-size: 0.62rem; opacity: 0.7; }

.sort-select {
  background: var(--surface2); border: 1px solid var(--border); color: var(--muted);
  padding: 4px 8px; border-radius: var(--r); font-size: 0.75rem; font-family: var(--font);
  cursor: pointer;
}

.pred-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
.pred-table th {
  text-align: left; font-family: var(--mono); font-size: 9px;
  text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--muted); padding: 0 0.75rem 0.75rem;
  border-bottom: 1px solid var(--border);
}
.pred-table td { padding: 0.7rem 0.75rem; border-bottom: 1px solid rgba(255,255,255,0.03); vertical-align: middle; }
.pred-table tr { border-left: 3px solid transparent; transition: background 0.1s; }
.pred-table tr:hover td { background: rgba(255,255,255,0.02); }
.row-correct { border-left-color: var(--green) !important; }
.row-wrong   { border-left-color: var(--coral) !important; }
.row-pending { border-left-color: var(--border) !important; }
.high-conf-wrong { background: rgba(255,114,98,0.04) !important; }

.match-cell { font-weight: 500; display: flex; align-items: center; gap: 6px; }
.hcw-badge  { font-size: 0.7rem; title: cursor; }
.group-cell { font-family: var(--mono); font-size: 0.68rem; color: var(--muted); }
.vs         { font-size: 0.7rem; color: var(--muted); margin: 0 2px; }
.pred-pill  { font-family: var(--mono); font-size: 0.7rem; font-weight: 600; background: var(--surface2); color: var(--gold); padding: 2px 8px; border-radius: 4px; }

.conf-cell  { display: flex; align-items: center; gap: 8px; justify-content: flex-end; }
.mini-bar   { height: 4px; border-radius: 99px; min-width: 4px; max-width: 80px; transition: width 0.6s ease; }
.mini-pct   { font-family: var(--mono); font-size: 0.7rem; color: var(--muted); min-width: 38px; text-align: right; }

.status     { font-family: var(--mono); font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; white-space: nowrap; }
.status.pending { background: rgba(107,107,136,0.12); color: var(--muted); }
.status.correct { background: rgba(10,207,131,0.12); color: var(--green); }
.status.wrong   { background: rgba(255,114,98,0.12); color: var(--coral); }

.table-footer { font-size: 0.72rem; color: var(--muted); padding-top: 0.875rem; text-align: right; }
.clear-filter { background: none; border: none; color: var(--gold); cursor: pointer; font-size: 0.72rem; text-decoration: underline; }
</style>