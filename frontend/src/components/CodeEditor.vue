<script setup>
import { ref } from 'vue'
import api from '../api'

const code = defineModel('code', { type: String, default: '' })

const stdin = ref('')
const showStdin = ref(false)
const running = ref(false)
const result = ref(null)
const error = ref('')

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

async function run() {
  running.value = true
  error.value = ''
  result.value = null
  try {
    const { data } = await api.post('/api/run-code', { code: code.value, stdin: stdin.value })
    result.value = data
  } catch (e) {
    error.value = e?.response?.data?.detail ?? '코드를 실행하지 못했습니다.'
  } finally {
    running.value = false
  }
}
</script>

<template>
  <div class="editor">
    <textarea
      v-model="code"
      class="code-input"
      spellcheck="false"
      rows="8"
      @keydown.tab="onTab"
    ></textarea>

    <div class="toolbar">
      <button class="run-btn" :disabled="running" @click="run">
        {{ running ? '실행 중…' : '▶ 코드 실행' }}
      </button>
      <button class="stdin-toggle" @click="showStdin = !showStdin">
        {{ showStdin ? '입력값 숨기기' : '입력값(stdin) 추가' }}
      </button>
    </div>

    <textarea
      v-if="showStdin"
      v-model="stdin"
      class="stdin-input"
      placeholder="input()에 전달할 값을 줄 단위로 입력하세요"
      rows="2"
    ></textarea>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="result" class="result">
      <div class="result-row">
        <span class="result-label">stdout</span>
        <pre class="output">{{ result.stdout || '(없음)' }}</pre>
      </div>
      <div v-if="result.stderr" class="result-row">
        <span class="result-label err">stderr</span>
        <pre class="output err">{{ result.stderr }}</pre>
      </div>
      <p v-if="result.timed_out" class="timeout">⚠ 실행 시간이 초과되었습니다.</p>
    </div>
  </div>
</template>

<style scoped>
.editor {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  background: var(--bg-soft);
  margin: 10px 0;
}

.code-input,
.stdin-input {
  width: 100%;
  font-family: var(--mono);
  font-size: 14px;
  background: var(--code-bg);
  color: var(--text-h);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  resize: vertical;
  box-sizing: border-box;
}

.stdin-input {
  margin-top: 8px;
}

.toolbar {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.run-btn {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  cursor: pointer;
  font-weight: 600;
}

.run-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.stdin-toggle {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 14px;
  cursor: pointer;
  color: var(--text-dim);
}

.error {
  color: var(--wrong);
  font-size: 14px;
}

.result {
  margin-top: 10px;
}

.result-row {
  margin-bottom: 6px;
}

.result-label {
  display: block;
  font-size: 12px;
  color: var(--text-dim);
  margin-bottom: 2px;
}

.result-label.err {
  color: var(--wrong);
}

.output {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.output.err {
  color: var(--wrong);
}

.timeout {
  color: var(--wrong);
  font-size: 13px;
}
</style>
