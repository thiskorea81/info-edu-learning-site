<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const standards = ref([])
const standardId = ref('')
const 문제 = ref('')
const hasCode = ref(false)
const 코드 = ref('')
const hasTable = ref(false)
const 표 = ref('')
const 이미지 = ref('')
const 선택지 = ref(['', '', '', '', ''])
const 정답 = ref(1)
const 해설 = ref('')

const submitting = ref(false)
const submitError = ref('')
const createdQuestion = ref(null)

const selectedStandard = computed(() => standards.value.find((s) => s.standard_id === standardId.value))

onMounted(async () => {
  const { data } = await api.get('/api/standards')
  standards.value = data
})

function resetForm() {
  문제.value = ''
  hasCode.value = false
  코드.value = ''
  hasTable.value = false
  표.value = ''
  이미지.value = ''
  선택지.value = ['', '', '', '', '']
  정답.value = 1
  해설.value = ''
}

async function submitSingle() {
  submitError.value = ''
  createdQuestion.value = null
  submitting.value = true
  try {
    const { data } = await api.post('/api/questions', {
      standard_id: standardId.value,
      문제: 문제.value,
      코드: hasCode.value ? 코드.value : null,
      표: hasTable.value ? 표.value : null,
      이미지: 이미지.value || null,
      선택지: 선택지.value,
      정답: Number(정답.value),
      해설: 해설.value,
    })
    createdQuestion.value = data
    resetForm()
  } catch (e) {
    submitError.value = e?.response?.data?.detail ?? '문제 등록에 실패했습니다.'
  } finally {
    submitting.value = false
  }
}

// bulk upload
const bulkFile = ref(null)
const bulkUploading = ref(false)
const bulkError = ref('')
const bulkResult = ref(null)

function onFileChange(e) {
  bulkFile.value = e.target.files[0] ?? null
}

async function uploadBulk() {
  if (!bulkFile.value) return
  bulkError.value = ''
  bulkResult.value = null
  bulkUploading.value = true
  const form = new FormData()
  form.append('file', bulkFile.value)
  try {
    const { data } = await api.post('/api/questions/bulk', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    bulkResult.value = data
  } catch (e) {
    bulkError.value = e?.response?.data?.detail ?? '일괄 등록에 실패했습니다.'
  } finally {
    bulkUploading.value = false
  }
}

async function downloadTemplate() {
  const { data } = await api.get('/api/questions/template', { responseType: 'blob' })
  const url = URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'question_template.json'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <h1>문제 등록</h1>
  <p class="hint">교과서 문제 목록에 새 문제를 추가합니다. 하나씩 등록하거나, JSON 파일로 여러 문제를 한 번에 등록할 수 있습니다.</p>

  <section class="panel">
    <h2>문제 하나씩 등록</h2>

    <label class="field">
      <span>성취기준</span>
      <select v-model="standardId">
        <option value="" disabled>선택하세요</option>
        <option v-for="s in standards" :key="s.standard_id" :value="s.standard_id">
          [{{ s.standard_id }}] {{ s.교과}} · {{ s.단원 }} · {{ s.성취기준명 }}
        </option>
      </select>
    </label>
    <p v-if="selectedStandard" class="std-preview">{{ selectedStandard.성취기준명 }}</p>

    <label class="field">
      <span>문제</span>
      <textarea v-model="문제" rows="2" placeholder="문제 지문을 입력하세요"></textarea>
    </label>

    <label class="checkbox-field">
      <input type="checkbox" v-model="hasCode" />
      <span>코드 포함 (파이썬)</span>
    </label>
    <textarea
      v-if="hasCode"
      v-model="코드"
      class="code-area"
      rows="5"
      spellcheck="false"
      placeholder="print('hello')"
    ></textarea>

    <label class="checkbox-field">
      <input type="checkbox" v-model="hasTable" />
      <span>표 포함 (마크다운 형식)</span>
    </label>
    <textarea
      v-if="hasTable"
      v-model="표"
      class="code-area"
      rows="3"
      placeholder="| 설명 |&#10;| :--- |&#10;| 표에 들어갈 내용 |"
    ></textarea>

    <label class="field">
      <span>이미지 URL (선택)</span>
      <input v-model="이미지" type="text" placeholder="https://..." />
    </label>

    <fieldset class="choices-field">
      <legend>선택지 (정답 라디오로 표시)</legend>
      <div v-for="(c, i) in 선택지" :key="i" class="choice-row">
        <input type="radio" :value="i + 1" v-model="정답" />
        <span class="choice-num">{{ i + 1 }}</span>
        <input v-model="선택지[i]" type="text" :placeholder="`선택지 ${i + 1}`" />
      </div>
    </fieldset>

    <label class="field">
      <span>해설 (선택)</span>
      <textarea v-model="해설" rows="2"></textarea>
    </label>

    <button
      class="submit-btn"
      :disabled="submitting || !standardId || !문제 || 선택지.some((c) => !c)"
      @click="submitSingle"
    >
      {{ submitting ? '등록 중…' : '문제 등록' }}
    </button>

    <p v-if="submitError" class="error">{{ submitError }}</p>
    <div v-if="createdQuestion" class="success">
      문제가 등록되었습니다.
      <RouterLink :to="`/questions/${createdQuestion.id}`">바로 풀어보기 →</RouterLink>
    </div>
  </section>

  <section class="panel">
    <h2>JSON 파일 일괄 등록</h2>
    <p class="hint">
      아래 양식을 내려받아 형식에 맞춰 문제를 여러 개 채운 뒤 업로드하세요.
      <button class="link-btn" @click="downloadTemplate">양식 다운로드</button>
    </p>

    <div class="bulk-row">
      <input type="file" accept="application/json" @change="onFileChange" />
      <button class="submit-btn" :disabled="!bulkFile || bulkUploading" @click="uploadBulk">
        {{ bulkUploading ? '업로드 중…' : '일괄 등록' }}
      </button>
    </div>

    <p v-if="bulkError" class="error">{{ bulkError }}</p>

    <div v-if="bulkResult" class="bulk-result">
      <p>
        전체 {{ bulkResult.total }}개 중
        <strong class="correct">성공 {{ bulkResult.succeeded }}</strong> /
        <strong class="wrong">실패 {{ bulkResult.failed }}</strong>
      </p>
      <ul class="result-list">
        <li v-for="r in bulkResult.results" :key="r.index" :class="r.status">
          <span class="idx">#{{ r.index }}</span>
          <span v-if="r.status === 'ok'">{{ r.문제 }}</span>
          <span v-else class="reason">{{ r.reason }}</span>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.hint {
  color: var(--text-dim);
  margin-bottom: 20px;
  font-size: 14px;
}

.panel {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
}

.panel h2 {
  margin-bottom: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 14px;
  font-size: 14px;
}

.field select,
.field input[type='text'],
.field textarea {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  background: var(--bg);
  color: var(--text);
  font: inherit;
}

.std-preview {
  font-size: 13px;
  color: var(--text-dim);
  margin: -8px 0 14px;
}

.checkbox-field {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  margin-bottom: 8px;
  cursor: pointer;
}

.code-area {
  width: 100%;
  box-sizing: border-box;
  font-family: var(--mono);
  font-size: 13px;
  background: var(--code-bg);
  color: var(--text-h);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  margin-bottom: 14px;
}

.choices-field {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 14px;
}

.choices-field legend {
  font-size: 13px;
  color: var(--text-dim);
  padding: 0 6px;
}

.choice-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.choice-num {
  font-size: 13px;
  color: var(--text-dim);
  min-width: 14px;
}

.choice-row input[type='text'] {
  flex: 1;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 10px;
  background: var(--bg);
  color: var(--text);
  font: inherit;
}

.submit-btn {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 10px 20px;
  font-weight: 600;
  cursor: pointer;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.error {
  color: var(--wrong);
  font-size: 14px;
  margin-top: 10px;
  white-space: pre-wrap;
}

.success {
  margin-top: 12px;
  color: var(--correct);
  font-size: 14px;
}

.success a {
  color: var(--accent);
  margin-left: 8px;
}

.link-btn {
  background: none;
  border: none;
  color: var(--accent);
  text-decoration: underline;
  cursor: pointer;
  font-size: 14px;
  padding: 0;
}

.bulk-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.bulk-result {
  margin-top: 12px;
  font-size: 14px;
}

.bulk-result .correct {
  color: var(--correct);
}

.bulk-result .wrong {
  color: var(--wrong);
}

.result-list {
  list-style: none;
  padding: 0;
  margin-top: 8px;
}

.result-list li {
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
  font-size: 13px;
  display: flex;
  gap: 8px;
}

.result-list li.error .reason {
  color: var(--wrong);
}

.idx {
  color: var(--text-dim);
  min-width: 32px;
}
</style>
