<script setup>
import { ref, watch } from 'vue'
import api from '../api'

const props = defineProps({ id: { type: String, required: true } })

const problem = ref(null)
const code = ref('')
const submissions = ref([])

const sampleRunning = ref(null) // index of sample currently running
const sampleResults = ref({}) // index -> { actual, stderr, match }

const submitting = ref(false)
const submitResult = ref(null)
const submitError = ref('')

async function load() {
  problem.value = null
  submitResult.value = null
  sampleResults.value = {}
  const { data } = await api.get(`/api/problems/${props.id}`)
  problem.value = data
  code.value = ''
  await loadSubmissions()
}

async function loadSubmissions() {
  const { data } = await api.get(`/api/problems/${props.id}/submissions`)
  submissions.value = data
}

watch(() => props.id, load, { immediate: true })

function onTab(e) {
  e.preventDefault()
  const el = e.target
  const start = el.selectionStart
  const end = el.selectionEnd
  code.value = code.value.slice(0, start) + '    ' + code.value.slice(end)
  requestAnimationFrame(() => {
    el.selectionStart = el.selectionEnd = start + 4
  })
}

async function runSample(index, sample) {
  sampleRunning.value = index
  try {
    const { data } = await api.post('/api/run-code', { code: code.value, stdin: sample.input })
    const actual = data.stdout
    const match = actual.trim() === sample.output.trim()
    sampleResults.value = { ...sampleResults.value, [index]: { ...data, match } }
  } finally {
    sampleRunning.value = null
  }
}

async function submit() {
  submitting.value = true
  submitError.value = ''
  submitResult.value = null
  try {
    const { data } = await api.post(`/api/problems/${props.id}/submit`, { code: code.value })
    submitResult.value = data
    await loadSubmissions()
  } catch (e) {
    submitError.value = e?.response?.data?.detail ?? '제출에 실패했습니다.'
  } finally {
    submitting.value = false
  }
}

function loadSubmissionCode(sub) {
  code.value = sub.code
}

function verdictLabel(v) {
  return { AC: '정답', WA: '오답', RE: '런타임 에러', TLE: '시간 초과' }[v] ?? v
}
</script>

<template>
  <div v-if="problem" class="solve">
    <div class="header">
      <span class="letter" :class="problem.difficulty === '쉬움' ? 'easy' : problem.difficulty === '보통' ? 'medium' : 'hard'">
        {{ problem.letter }}
      </span>
      <h1>{{ problem.title }}</h1>
      <span class="badge" :class="problem.difficulty === '쉬움' ? 'easy' : problem.difficulty === '보통' ? 'medium' : 'hard'">
        {{ problem.difficulty }}
      </span>
    </div>

    <p class="statement">{{ problem.statement }}</p>

    <div class="spec">
      <div><strong>제약조건</strong><br />{{ problem.constraints }}</div>
      <div><strong>입력</strong><br />{{ problem.input_format }}</div>
      <div><strong>출력</strong><br />{{ problem.output_format }}</div>
      <div><strong>시간 제한</strong><br />{{ problem.time_limit_ms }}ms</div>
    </div>

    <h2>예제</h2>
    <div v-for="(sample, i) in problem.samples" :key="i" class="sample">
      <div class="sample-io">
        <div>
          <span class="label">입력</span>
          <pre>{{ sample.input }}</pre>
        </div>
        <div>
          <span class="label">출력</span>
          <pre>{{ sample.output }}</pre>
        </div>
      </div>
      <p v-if="sample.explanation" class="explain">{{ sample.explanation }}</p>
      <button class="sample-run" :disabled="sampleRunning === i" @click="runSample(i, sample)">
        {{ sampleRunning === i ? '실행 중…' : '이 예제로 실행' }}
      </button>
      <div v-if="sampleResults[i]" class="sample-result" :class="{ ok: sampleResults[i].match, bad: !sampleResults[i].match }">
        <span class="label">내 출력</span>
        <pre>{{ sampleResults[i].stdout || '(없음)' }}</pre>
        <pre v-if="sampleResults[i].stderr" class="stderr">{{ sampleResults[i].stderr }}</pre>
        <strong>{{ sampleResults[i].match ? '일치' : '불일치' }}</strong>
      </div>
    </div>

    <div class="help-section">
      <details v-if="problem.힌트" class="help-block">
        <summary>💡 힌트 보기</summary>
        <p class="help-text">{{ problem.힌트 }}</p>
      </details>
      <details v-if="problem.해설" class="help-block">
        <summary>📝 해설 보기</summary>
        <p class="help-text">{{ problem.해설 }}</p>
      </details>
      <details v-if="problem.정답_코드" class="help-block">
        <summary>✅ 모범 답안 보기</summary>
        <p v-if="problem.시간복잡도" class="complexity"><strong>시간복잡도</strong> {{ problem.시간복잡도 }}</p>
        <pre class="code-block"><code>{{ problem.정답_코드 }}</code></pre>
      </details>
    </div>

    <h2>코드 작성</h2>
    <textarea
      v-model="code"
      class="code-input"
      spellcheck="false"
      rows="14"
      placeholder="여기에 파이썬 코드를 작성하세요"
      @keydown.tab="onTab"
    ></textarea>

    <div class="actions">
      <button class="submit" :disabled="submitting || !code" @click="submit">
        {{ submitting ? '채점 중…' : '제출' }}
      </button>
    </div>

    <p v-if="submitError" class="error">{{ submitError }}</p>

    <div v-if="submitResult" class="result" :class="submitResult.verdict === 'AC' ? 'ok' : 'bad'">
      <strong>{{ verdictLabel(submitResult.verdict) }}</strong>
      <span>{{ submitResult.passed_count }} / {{ submitResult.total_count }} 통과</span>

      <div class="cases-scroll">
        <table class="cases">
          <thead>
            <tr>
              <th>#</th>
              <th>결과</th>
              <th>입력</th>
              <th>기대 출력</th>
              <th>내 출력</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in submitResult.cases" :key="c.index" :class="c.verdict === 'AC' ? 'ok' : 'bad'">
              <td>{{ c.index }}</td>
              <td>{{ verdictLabel(c.verdict) }}</td>
              <td><pre>{{ c.input }}</pre></td>
              <td><pre>{{ c.expected }}</pre></td>
              <td>
                <pre>{{ c.actual }}</pre>
                <pre v-if="c.stderr" class="stderr">{{ c.stderr }}</pre>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <h2 v-if="submissions.length">제출 기록</h2>
    <ul v-if="submissions.length" class="submissions">
      <li v-for="s in submissions" :key="s.id">
        <span class="badge" :class="s.verdict === 'AC' ? 'easy' : 'wrong'">{{ verdictLabel(s.verdict) }}</span>
        <span>{{ s.passed_count }}/{{ s.total_count }}</span>
        <span class="time">{{ new Date(s.created_at).toLocaleString() }}</span>
        <button class="load-code" @click="loadSubmissionCode(s)">코드 불러오기</button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.statement {
  white-space: pre-wrap;
  margin: 12px 0;
}

.spec {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  font-size: 14px;
  margin-bottom: 20px;
}

.sample {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
}

.sample-io {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.label {
  display: block;
  font-size: 12px;
  color: var(--text-dim);
  margin-bottom: 2px;
}

pre {
  background: var(--code-bg);
  border-radius: 6px;
  padding: 8px 10px;
  margin: 0;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
}

.explain {
  font-size: 13px;
  color: var(--text-dim);
  margin: 8px 0 0;
}

.sample-run {
  margin-top: 10px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 12px;
  cursor: pointer;
  color: var(--text);
}

.sample-result {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--border);
}

.sample-result.ok strong {
  color: var(--correct);
}

.sample-result.bad strong {
  color: var(--wrong);
}

.help-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 16px 0;
}

.help-block {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 4px 14px;
}

.help-block summary {
  padding: 10px 0;
  cursor: pointer;
  font-weight: 600;
  color: var(--text-h);
  font-size: 14px;
}

.help-block .help-text {
  font-size: 14px;
  line-height: 1.6;
  padding-bottom: 12px;
  white-space: pre-wrap;
}

.help-block .complexity {
  font-size: 13px;
  color: var(--text-dim);
  margin: 0 0 8px;
}

.help-block .code-block {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 14px;
  overflow-x: auto;
  font-size: 13px;
  margin: 0 0 12px;
}

.code-input {
  width: 100%;
  font-family: var(--mono);
  font-size: 14px;
  background: var(--code-bg);
  color: var(--text-h);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  resize: vertical;
  box-sizing: border-box;
  margin-top: 8px;
}

.actions {
  margin: 12px 0;
}

.submit {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 10px 22px;
  font-weight: 600;
  cursor: pointer;
}

.submit:disabled {
  opacity: 0.5;
  cursor: default;
}

.error {
  color: var(--wrong);
}

.result {
  border-radius: 8px;
  padding: 14px 16px;
  margin: 16px 0;
}

.result.ok {
  background: var(--correct-bg);
}

.result.bad {
  background: var(--wrong-bg);
}

.result.ok strong {
  color: var(--correct);
}

.result.bad strong {
  color: var(--wrong);
}

.result span {
  margin-left: 10px;
  font-size: 14px;
  color: var(--text);
}

.cases-scroll {
  overflow-x: auto;
  margin-top: 12px;
}

table.cases {
  font-size: 13px;
  min-width: 640px;
}

table.cases th,
table.cases td {
  vertical-align: top;
}

table.cases tr.ok td:nth-child(2) {
  color: var(--correct);
}

table.cases tr.bad td:nth-child(2) {
  color: var(--wrong);
}

.stderr {
  color: var(--wrong);
  margin-top: 4px;
}

.submissions {
  list-style: none;
  padding: 0;
}

.submissions li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
  font-size: 14px;
}

.submissions .time {
  color: var(--text-dim);
  font-size: 12px;
}

.load-code {
  margin-left: auto;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 10px;
  cursor: pointer;
  color: var(--text-dim);
  font-size: 12px;
}

.letter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  font-weight: 700;
  font-size: 16px;
  flex-shrink: 0;
}

.letter.easy {
  color: var(--correct);
  background: var(--correct-bg);
}

.letter.medium {
  color: var(--accent);
  background: var(--accent-bg);
}

.letter.hard {
  color: var(--wrong);
  background: var(--wrong-bg);
}

.badge {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
}

.badge.easy {
  color: var(--correct);
  border-color: var(--correct);
  background: var(--correct-bg);
}

.badge.medium {
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.badge.hard {
  color: var(--wrong);
  border-color: var(--wrong);
  background: var(--wrong-bg);
}

.badge.wrong {
  color: var(--wrong);
  border-color: var(--wrong);
  background: var(--wrong-bg);
}
</style>
