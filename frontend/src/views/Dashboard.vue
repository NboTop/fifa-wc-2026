<template>
  <div class="dashboard">

    <!-- ── Scoreboard hero ── -->
    <section class="scoreboard-section">
      <div class="scoreboard-inner" v-if="accuracy">
        <div class="scoreboard-left">
          <p class="label" style="margin-bottom:0.5rem">Current tournament accuracy</p>
          <div class="scoreboard-display">
            <div class="score-num">{{ accuracy.accuracy }}</div>
            <div class="score-pct">%</div>
          </div>
          <div class="score-sub">
            <span>{{ accuracy.total_predictions }} predicted</span>
            <span class="score-dot">·</span>
            <span class="correct-val">{{ accuracy.correct }} correct</span>
            <span class="score-dot">·</span>
            <span class="wrong-val">{{ accuracy.played - accuracy.correct }} wrong</span>
          </div>
        </div>
        <div class="scoreboard-right">
          <div class="accuracy-bar-wrap">
            <div class="accuracy-bar">
              <div class="accuracy-fill" :style="{ width: accuracy.accuracy + '%' }"></div>
            </div>
            <div class="accuracy-labels">
              <span class="label">0%</span>
              <span class="label">Random: 33%</span>
              <span class="label">100%</span>
            </div>
          </div>
          <div class="kpi-row">
            <div class="kpi">
              <div class="kpi-n">{{ accuracy.played }}</div>
              <div class="label">Played</div>
            </div>
            <div class="kpi">
              <div class="kpi-n goal">{{ accuracy.correct }}</div>
              <div class="label">Correct</div>
            </div>
            <div class="kpi">
              <div class="kpi-n foul">{{ accuracy.played - accuracy.correct }}</div>
              <div class="label">Wrong</div>
            </div>
            <div class="kpi">
              <div class="kpi-n muted">{{ accuracy.total_predictions - accuracy.played }}</div>
              <div class="label">Pending</div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="scoreboard-placeholder">
        <div class="score-num muted">- - . -</div>
      </div>
    </section>

    <!-- ── VS Predictor ── -->
    <section class="predictor-section zone">
      <div class="predictor-header">
        <p class="label">Match predictor</p>
        <p class="predictor-desc">Enter two WC 2026 nations to generate a probability breakdown using Elo ratings, recent form, and head-to-head data.</p>
      </div>

      <div class="vs-arena">
        <div class="team-slot" :class="{ filled: teamA }">
          <p class="label slot-label">Home side</p>
          <input
            v-model="teamA"
            list="nations-list"
            placeholder="SELECT TEAM"
            class="team-input"
            @keydown.enter="predict"
          />
        </div>

        <div class="vs-center">
          <div class="vs-text">VS</div>
          <button class="btn-predict" :disabled="!teamA || !teamB || predicting" @click="predict">
            <span v-if="predicting" class="loading-dot"></span>
            <span v-else>ANALYSE</span>
          </button>
        </div>

        <div class="team-slot right" :class="{ filled: teamB }">
          <p class="label slot-label">Away side</p>
          <input
            v-model="teamB"
            list="nations-list"
            placeholder="SELECT TEAM"
            class="team-input"
            @keydown.enter="predict"
          />
        </div>

        <datalist id="nations-list">
          <option v-for="n in nations" :key="n" :value="n" />
        </datalist>
      </div>

      <div class="pred-result" v-if="predResult">
        <div class="prob-bars">
          <div class="prob-row">
            <span class="prob-team">{{ predResult.team_a }}</span>
            <div class="prob-track">
              <div class="prob-fill home" :style="{ width: predResult.team_a_win + '%' }"></div>
            </div>
            <span class="prob-pct">{{ predResult.team_a_win }}%</span>
          </div>
          <div class="prob-row">
            <span class="prob-team draw">DRAW</span>
            <div class="prob-track">
              <div class="prob-fill draw" :style="{ width: predResult.draw + '%' }"></div>
            </div>
            <span class="prob-pct">{{ predResult.draw }}%</span>
          </div>
          <div class="prob-row">
            <span class="prob-team">{{ predResult.team_b }}</span>
            <div class="prob-track">
              <div class="prob-fill away" :style="{ width: predResult.team_b_win + '%' }"></div>
            </div>
            <span class="prob-pct">{{ predResult.team_b_win }}%</span>
          </div>
        </div>

        <div class="verdict-row">
          <span class="verdict-label">PREDICTED WINNER</span>
          <span class="verdict-winner" :class="{ 'draw-result': predResult.predicted === 'Draw' }">
            {{ predResult.predicted.toUpperCase() }}
          </span>
          <span class="verdict-conf" :class="confClass(predResult.confidence)">
            {{ predResult.confidence }}% confidence
          </span>
          <span class="draw-warn" v-if="predResult.draw_risk">⚖ draw risk</span>
        </div>

        <p class="responsible-note">Probability estimates only. Football is unpredictable — this model has been wrong 28.6% of the time across 56 tracked predictions.</p>
      </div>
    </section>

    <!-- ── Predictions board ── -->
    <section class="board-section">
      <div class="board-header">
        <p class="label">Results board</p>
        <div class="board-controls">
          <div class="filter-group">
            <button v-for="f in filters" :key="f.val"
              class="filter-btn" :class="{ active: activeFilter === f.val }"
              @click="activeFilter = f.val">
              {{ f.label }}
              <span class="filter-n">{{ f.count }}</span>
            </button>
          </div>
          <select v-model="sortBy" class="sort-sel">
            <option value="default">Default</option>
            <option value="conf_desc">Conf ↓</option>
            <option value="conf_asc">Conf ↑</option>
            <option value="stage">Stage</option>
          </select>
        </div>
      </div>

      <div class="board-loading" v-if="loading">
        <span class="loading-dot"></span> Loading predictions…
      </div>

      <table class="board-table" v-else>
        <thead>
          <tr>
            <th>Match</th>
            <th>Stage</th>
            <th>Prediction</th>
            <th class="right">Confidence</th>
            <th class="right">Result</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in filteredPredictions" :key="p.team_a + p.team_b"
            :class="[rowClass(p), isHighConfWrong(p) ? 'hcw' : '']">
            <td class="match-td">
              <span class="team-a">{{ p.team_a }}</span>
              <span class="vs-chip">VS</span>
              <span class="team-b">{{ p.team_b }}</span>
              <span v-if="isHighConfWrong(p)" class="hcw-flag" title="High-confidence wrong prediction">⚡</span>
            </td>
            <td class="stage-td">{{ p.stage }}</td>
            <td>
              <span class="pred-chip">{{ p.predicted }}</span>
            </td>
            <td class="right">
              <div class="conf-bar-wrap">
                <div class="conf-bar">
                  <div class="conf-fill" :style="{ width: p.confidence + '%', background: confColor(p.confidence) }"></div>
                </div>
                <span class="conf-n">{{ p.confidence }}%</span>
              </div>
            </td>
            <td class="right">
              <span v-if="!p.actual_result" class="result-chip pending">⏳ TBD</span>
              <span v-else-if="isCorrect(p)" class="result-chip correct">✓ {{ p.actual_result }}</span>
              <span v-else class="result-chip wrong">✗ {{ p.actual_result }}</span>
            </td>
          </tr>
        </tbody>
      </table>

      <p class="board-footer" v-if="!loading">
        {{ filteredPredictions.length }} of {{ predictions.length }} predictions
        <button v-if="activeFilter !== 'all'" class="clear-filter" @click="activeFilter = 'all'">
          clear filter
        </button>
      </p>
    </section>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const accuracy     = ref(null)
const predictions  = ref([])
const nations      = ref([])
const loading      = ref(true)
const teamA        = ref('')
const teamB        = ref('')
const predicting   = ref(false)
const predResult   = ref(null)
const activeFilter = ref('all')
const sortBy       = ref('default')

const filters = computed(() => [
  { val: 'all',     label: 'All',     count: predictions.value.length },
  { val: 'pending', label: 'Pending', count: predictions.value.filter(p => !p.actual_result).length },
  { val: 'correct', label: 'Correct', count: predictions.value.filter(p => isCorrect(p)).length },
  { val: 'wrong',   label: 'Wrong',   count: predictions.value.filter(p => p.actual_result && !isCorrect(p)).length },
])

const filteredPredictions = computed(() => {
  let list = [...predictions.value]
  if (activeFilter.value === 'pending') list = list.filter(p => !p.actual_result)
  else if (activeFilter.value === 'correct') list = list.filter(p => isCorrect(p))
  else if (activeFilter.value === 'wrong') list = list.filter(p => p.actual_result && !isCorrect(p))
  if (sortBy.value === 'conf_desc') list.sort((a, b) => b.confidence - a.confidence)
  else if (sortBy.value === 'conf_asc') list.sort((a, b) => a.confidence - b.confidence)
  else if (sortBy.value === 'stage') list.sort((a, b) => (a.stage || '').localeCompare(b.stage || ''))
  return list
})

function isCorrect(p) { return String(p.correct).toLowerCase() === 'true' }
function rowClass(p) {
  if (!p.actual_result) return 'row-pending'
  return isCorrect(p) ? 'row-correct' : 'row-wrong'
}
function isHighConfWrong(p) { return p.actual_result && !isCorrect(p) && p.confidence >= 65 }
function confColor(c) {
  if (c >= 70) return 'var(--pitch)'
  if (c >= 55) return 'var(--goal)'
  return 'var(--chalk-3)'
}
function confClass(c) {
  if (c >= 70) return 'conf-hi'
  if (c >= 55) return 'conf-mid'
  return 'conf-lo'
}

async function predict() {
  if (!teamA.value || !teamB.value || predicting.value) return
  predicting.value = true
  predResult.value = null
  try {
    const { data } = await axios.post('/api/v1/predict', { team_a: teamA.value, team_b: teamB.value })
    predResult.value = data
  } catch { alert('Prediction failed — is the backend running?') }
  finally { predicting.value = false }
}

onMounted(async () => {
  try {
    const [accRes, predRes, natRes] = await Promise.all([
      axios.get('/api/v1/accuracy'),
      axios.get('/api/v1/predictions'),
      axios.get('/api/v1/nations'),
    ])
    accuracy.value   = accRes.data
    predictions.value = predRes.data
    nations.value    = natRes.data
  } finally { loading.value = false }
})
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 0; animation: rise 0.4s ease; }

/* ── Scoreboard hero ── */
.scoreboard-section {
  padding: 3rem 0 2.5rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2.5rem;
}

.scoreboard-inner {
  display: flex;
  align-items: flex-start;
  gap: 4rem;
  flex-wrap: wrap;
}

.scoreboard-left { flex-shrink: 0; }

.scoreboard-display {
  display: flex;
  align-items: flex-start;
  gap: 0.25rem;
  line-height: 1;
  margin: 0.5rem 0 0.75rem;
  position: relative;
}

/* The scanline signature element */
.scoreboard-display::after {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent 0px,
    transparent 3px,
    rgba(0,0,0,0.10) 3px,
    rgba(0,0,0,0.10) 4px
  );
  pointer-events: none;
}

.score-num {
  font-family: var(--display);
  font-size: clamp(5rem, 12vw, 9rem);
  color: var(--chalk);
  letter-spacing: 0.02em;
}

.score-num.muted { color: var(--chalk-3); }

.score-pct {
  font-family: var(--display);
  font-size: clamp(2rem, 5vw, 4rem);
  color: var(--pitch);
  padding-top: 0.6rem;
  letter-spacing: 0.02em;
}

.score-sub {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.78rem;
  color: var(--chalk-3);
  font-family: var(--mono);
}

.score-dot { opacity: 0.4; }
.correct-val { color: var(--goal); }
.wrong-val   { color: var(--foul); }

.scoreboard-right { flex: 1; min-width: 260px; padding-top: 0.75rem; }

.accuracy-bar-wrap { margin-bottom: 1.75rem; }
.accuracy-bar {
  height: 6px;
  background: var(--border);
  position: relative;
  margin-bottom: 0.4rem;
  overflow: hidden;
}
.accuracy-fill {
  height: 100%;
  background: var(--pitch);
  transition: width 1.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.accuracy-labels {
  display: flex;
  justify-content: space-between;
}

.kpi-row { display: flex; gap: 2.5rem; }
.kpi { display: flex; flex-direction: column; gap: 3px; }
.kpi-n {
  font-family: var(--display);
  font-size: 2.5rem;
  color: var(--chalk);
  letter-spacing: 0.02em;
  line-height: 1;
}
.kpi-n.goal  { color: var(--goal); }
.kpi-n.foul  { color: var(--foul); }
.kpi-n.muted { color: var(--chalk-3); }

/* ── Predictor ── */
.predictor-section {
  padding: 2rem;
  margin-bottom: 2.5rem;
}

.predictor-header { margin-bottom: 1.75rem; }
.predictor-desc {
  font-size: 0.8rem;
  color: var(--chalk-3);
  margin-top: 0.35rem;
  max-width: 520px;
  line-height: 1.5;
}

.vs-arena {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 1.5rem;
  align-items: center;
  margin-bottom: 1.5rem;
}

.team-slot { display: flex; flex-direction: column; gap: 6px; }
.team-slot.right { text-align: right; align-items: flex-end; }
.slot-label { transition: color 0.2s; }
.team-slot.filled .slot-label { color: var(--pitch); }

.team-input {
  background: transparent;
  border: none;
  border-bottom: 2px solid var(--border);
  color: var(--chalk);
  font-family: var(--display);
  font-size: 2rem;
  letter-spacing: 0.04em;
  width: 100%;
  padding: 4px 0;
  transition: border-color 0.2s;
  text-transform: uppercase;
}

.team-input::placeholder {
  color: var(--chalk-3);
  font-size: 1.4rem;
}

.team-input:focus {
  outline: none;
  border-bottom-color: var(--pitch);
}

.team-slot.right .team-input { text-align: right; }

.vs-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.vs-text {
  font-family: var(--display);
  font-size: 2.5rem;
  color: var(--pitch);
  letter-spacing: 0.1em;
  line-height: 1;
}

.btn-predict {
  background: var(--pitch);
  color: var(--void);
  border: none;
  font-family: var(--display);
  font-size: 1rem;
  letter-spacing: 0.1em;
  padding: 8px 20px;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
  white-space: nowrap;
}
.btn-predict:hover:not(:disabled) { background: var(--chalk); transform: translateY(-1px); }
.btn-predict:disabled { opacity: 0.35; cursor: not-allowed; }

/* Probability bars */
.pred-result {
  border-top: 1px solid var(--border);
  padding-top: 1.5rem;
  animation: rise 0.3s ease;
}

.prob-bars { display: flex; flex-direction: column; gap: 10px; margin-bottom: 1.25rem; }
.prob-row  { display: grid; grid-template-columns: 140px 1fr 52px; align-items: center; gap: 12px; }

.prob-team {
  font-family: var(--display);
  font-size: 1rem;
  letter-spacing: 0.04em;
  color: var(--chalk-2);
  text-transform: uppercase;
}
.prob-team.draw { color: var(--chalk-3); font-family: var(--mono); font-size: 0.72rem; letter-spacing: 0.1em; }

.prob-track {
  height: 8px;
  background: var(--border);
  position: relative;
  overflow: hidden;
}
.prob-fill {
  height: 100%;
  transition: width 0.9s cubic-bezier(0.16, 1, 0.3, 1);
}
.prob-fill.home { background: var(--pitch); }
.prob-fill.draw { background: var(--chalk-3); }
.prob-fill.away { background: var(--goal); }

.prob-pct {
  font-family: var(--mono);
  font-size: 0.78rem;
  color: var(--chalk-3);
  text-align: right;
}

.verdict-row {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}
.verdict-label {
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.12em;
  color: var(--chalk-3);
}
.verdict-winner {
  font-family: var(--display);
  font-size: 1.5rem;
  color: var(--chalk);
  letter-spacing: 0.06em;
}
.verdict-winner.draw-result { color: var(--chalk-2); }
.verdict-conf {
  font-family: var(--mono);
  font-size: 0.72rem;
  padding: 2px 8px;
  border: 1px solid;
}
.verdict-conf.conf-hi  { border-color: var(--pitch);    color: var(--pitch); }
.verdict-conf.conf-mid { border-color: var(--goal);     color: var(--goal); }
.verdict-conf.conf-lo  { border-color: var(--chalk-3);  color: var(--chalk-3); }
.draw-warn {
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--goal);
  letter-spacing: 0.06em;
  border: 1px solid rgba(245,197,24,0.3);
  padding: 2px 7px;
}

.responsible-note {
  font-size: 0.72rem;
  color: var(--chalk-3);
  border-left: 2px solid var(--border);
  padding-left: 0.75rem;
  line-height: 1.5;
  max-width: 540px;
}

/* ── Results board ── */
.board-section { }

.board-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.board-controls { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }

.filter-group { display: flex; gap: 2px; }
.filter-btn {
  background: none;
  border: 1px solid var(--border);
  color: var(--chalk-3);
  padding: 4px 10px;
  font-family: var(--mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
  transition: all 0.15s;
}
.filter-btn:hover { border-color: var(--chalk-3); color: var(--chalk); }
.filter-btn.active { background: var(--pitch-l); border-color: var(--pitch); color: var(--pitch); }
.filter-n { opacity: 0.6; font-size: 9px; }

.sort-sel {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--chalk-3);
  font-family: var(--mono);
  font-size: 10px;
  padding: 4px 8px;
  cursor: pointer;
  letter-spacing: 0.06em;
}

.board-loading {
  padding: 3rem;
  text-align: center;
  color: var(--chalk-3);
  font-family: var(--mono);
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

/* Departure-board style table */
.board-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

.board-table thead tr {
  border-bottom: 1px solid var(--pitch);
}

.board-table th {
  font-family: var(--mono);
  font-size: 9px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--chalk-3);
  padding: 0 0.75rem 0.625rem;
  text-align: left;
  font-weight: 400;
}
.board-table th.right { text-align: right; }

.board-table td {
  padding: 0.625rem 0.75rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.board-table tr { transition: background 0.1s; }
.board-table tr:hover td { background: var(--surface); }

.row-correct { border-left: 2px solid var(--pitch); }
.row-wrong   { border-left: 2px solid var(--foul); }
.row-pending { border-left: 2px solid transparent; }
.hcw td:first-child { background: rgba(232,22,43,0.04); }

.match-td { display: flex; align-items: center; gap: 8px; }
.team-a, .team-b { font-weight: 500; color: var(--chalk); }
.vs-chip {
  font-family: var(--mono);
  font-size: 9px;
  color: var(--chalk-3);
  letter-spacing: 0.08em;
  padding: 1px 4px;
  border: 1px solid var(--border);
}
.hcw-flag { font-size: 0.7rem; opacity: 0.7; cursor: help; }

.stage-td {
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--chalk-3);
  letter-spacing: 0.04em;
}

.pred-chip {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.04em;
  color: var(--pitch);
  background: var(--pitch-l);
  padding: 2px 6px;
  border: 1px solid rgba(0,166,81,0.2);
}

.conf-bar-wrap { display: flex; align-items: center; gap: 6px; justify-content: flex-end; }
.conf-bar      { width: 60px; height: 3px; background: var(--border); }
.conf-fill     { height: 100%; transition: width 0.6s ease; }
.conf-n {
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--chalk-3);
  min-width: 34px;
  text-align: right;
}

.result-chip {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.03em;
  padding: 2px 7px;
  white-space: nowrap;
}
.result-chip.pending { color: var(--chalk-3); border: 1px solid var(--border); }
.result-chip.correct { color: var(--goal); background: var(--goal-bg); border: 1px solid rgba(245,197,24,0.2); }
.result-chip.wrong   { color: var(--foul); background: var(--foul-bg); border: 1px solid rgba(232,22,43,0.2); }

.board-footer {
  padding-top: 0.875rem;
  text-align: right;
  font-family: var(--mono);
  font-size: 0.68rem;
  color: var(--chalk-3);
}
.clear-filter {
  background: none;
  border: none;
  color: var(--pitch);
  cursor: pointer;
  font-family: var(--mono);
  font-size: 0.68rem;
  margin-left: 0.5rem;
  text-decoration: underline;
}

/* Loading dot */
.loading-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border: 2px solid rgba(255,255,255,0.2);
  border-top-color: var(--chalk);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
</style>
