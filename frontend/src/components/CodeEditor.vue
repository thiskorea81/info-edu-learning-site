<script setup>
import { ref } from 'vue'
import api from '../api'

const code = defineModel('code', { type: String, default: '' })

const props = defineProps({
  noPaste: { type: Boolean, default: false },
  placeholder: { type: String, default: '' },
})

const stdin = ref('')
const showStdin = ref(false)
const running = ref(false)
const result = ref(null)
const error = ref('')

const OPEN_TO_CLOSE = { '(': ')', '{': '}', '[': ']' }
const CLOSE_CHARS = new Set([')', '}', ']'])

function onKeydown(e) {
  if (e.ctrlKey || e.metaKey || e.altKey) return // 복사/붙여넣기/실행 취소 등 단축키는 그대로 둔다
  if (e.key === 'Tab') return onTab(e)
  if (e.key === 'Enter') return onEnter(e)
  if (e.key === 'Backspace') return onBackspace(e)
  if (OPEN_TO_CLOSE[e.key]) return onBracketOpen(e)
  if (CLOSE_CHARS.has(e.key)) return onBracketClose(e)
}

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

function onEnter(e) {
  e.preventDefault()
  const el = e.target
  const start = el.selectionStart
  const end = el.selectionEnd
  const before = code.value.slice(0, start)
  const after = code.value.slice(end)
  const lineStart = before.lastIndexOf('\n') + 1
  const currentLine = before.slice(lineStart)
  let indent = currentLine.match(/^[ \t]*/)[0]
  if (/:\s*$/.test(currentLine.trimEnd())) {
    indent += '  ' // 콜론으로 끝나면 2칸 추가 들여쓰기
  }
  const insertion = '\n' + indent
  code.value = before + insertion + after
  const newPos = start + insertion.length
  requestAnimationFrame(() => {
    el.selectionStart = el.selectionEnd = newPos
  })
}

function onBackspace(e) {
  const el = e.target
  const start = el.selectionStart
  const end = el.selectionEnd
  if (start !== end) return // 선택 영역이 있으면 기본 삭제 동작에 맡긴다
  const before = code.value.slice(0, start)
  const lineStart = before.lastIndexOf('\n') + 1
  const linePrefix = before.slice(lineStart)
  if (linePrefix.length === 0 || !/^ +$/.test(linePrefix)) return // 들여쓰기 공백만 있을 때만 개입
  e.preventDefault()
  const deleteCount = linePrefix.length % 2 === 0 ? 2 : 1
  const newStart = start - deleteCount
  code.value = code.value.slice(0, newStart) + code.value.slice(start)
  requestAnimationFrame(() => {
    el.selectionStart = el.selectionEnd = newStart
  })
}

function onBracketOpen(e) {
  e.preventDefault()
  const el = e.target
  const start = el.selectionStart
  const end = el.selectionEnd
  const open = e.key
  const close = OPEN_TO_CLOSE[open]
  if (start !== end) {
    const selected = code.value.slice(start, end)
    code.value = code.value.slice(0, start) + open + selected + close + code.value.slice(end)
    requestAnimationFrame(() => {
      el.selectionStart = start + 1
      el.selectionEnd = end + 1
    })
  } else {
    code.value = code.value.slice(0, start) + open + close + code.value.slice(start)
    requestAnimationFrame(() => {
      el.selectionStart = el.selectionEnd = start + 1
    })
  }
}

function onBracketClose(e) {
  const el = e.target
  const start = el.selectionStart
  const end = el.selectionEnd
  if (start === end && code.value[start] === e.key) {
    // 바로 다음 글자가 이미 같은 닫는 괄호면 새로 넣지 않고 커서만 넘어간다
    e.preventDefault()
    el.selectionStart = el.selectionEnd = start + 1
  }
}

function blockPaste(e) {
  if (props.noPaste) e.preventDefault()
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
      :placeholder="placeholder"
      @keydown="onKeydown"
      @paste="blockPaste"
      @drop="blockPaste"
    ></textarea>
    <p v-if="noPaste" class="no-paste-hint">✏️ 붙여넣기는 막혀 있어요 — 직접 입력해보세요.</p>

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

.no-paste-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: var(--text-dim);
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
