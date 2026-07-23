<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import { isTeacher } from '../auth'
import RichEditor from '../components/RichEditor.vue'
import { useAutosave } from '../composables/useAutosave'

const props = defineProps({
  subject: { type: String, required: true },
  unit: { type: String, required: true },
})

const allSubjects = ref([])
const materials = ref([])
const unitReport = ref(null)
const loading = ref(true)

const matchedAssignment = ref(null)
const submission = ref(null)
const content = ref({ type: 'doc', content: [{ type: 'paragraph' }] })
const submissionLoading = ref(false)
const saving = ref(false)
const submitting = ref(false)
const message = ref('')

const locked = computed(
  () => submission.value?.status === 'submitted' || submission.value?.status === 'graded'
)

const autosave = useAutosave(
  () => content.value,
  async () => {
    const { data } = await api.put(
      `/api/assignments/${matchedAssignment.value.id}/submission`,
      { content: content.value }
    )
    submission.value = data
    message.value = `자동 저장됨 · ${new Date().toLocaleTimeString('ko-KR')}`
  }
)

const materialsById = computed(() => new Map(materials.value.map((m) => [m.standard_id, m])))
const currentUnit = computed(() => {
  const subject = allSubjects.value.find((s) => s.교과 === props.subject)
  return subject?.units.find((u) => u.단원 === props.unit)
})

const reportAssignmentQuery = computed(() => {
  if (!unitReport.value) return null
  const questions = (unitReport.value.탐구질문 || [])
    .map((q, i) => `${i + 1}. ${q}`)
    .join('\n')
  const description = [
    unitReport.value.안내,
    questions ? `[탐구 질문]\n${questions}` : '',
    unitReport.value.제출형식 ? `[제출 형식]\n${unitReport.value.제출형식}` : '',
  ]
    .filter(Boolean)
    .join('\n\n')
  return {
    subject: props.subject,
    title: unitReport.value.제목,
    description,
    단원: props.unit,
  }
})

async function load() {
  autosave.stop()
  loading.value = true
  matchedAssignment.value = null
  submission.value = null
  content.value = { type: 'doc', content: [{ type: 'paragraph' }] }

  const [{ data: subjects }, { data: mats }, { data: reports }] = await Promise.all([
    api.get('/api/subjects'),
    api.get('/api/materials'),
    api.get('/api/unit-reports', { params: { 교과: props.subject, 단원: props.unit } }),
  ])
  allSubjects.value = subjects
  materials.value = mats
  unitReport.value = reports[0] ?? null
  loading.value = false

  const { data: myAssignments } = await api.get('/api/assignments')
  const match = myAssignments.find(
    (a) => a.subject_name === props.subject && a.단원 === props.unit
  )
  if (match) {
    matchedAssignment.value = match
    if (!isTeacher()) {
      submissionLoading.value = true
      const { data: sub } = await api.get(`/api/assignments/${match.id}/submission`)
      submission.value = sub
      content.value = sub.content
      submissionLoading.value = false
      if (!locked.value) autosave.start()
    }
  } else {
    autosave.stop()
  }
}

onMounted(load)
watch(() => [props.subject, props.unit], load)

async function saveDraft() {
  saving.value = true
  message.value = ''
  try {
    const { data } = await api.put(
      `/api/assignments/${matchedAssignment.value.id}/submission`,
      { content: content.value }
    )
    submission.value = data
    autosave.markSaved()
    message.value = '임시저장되었습니다.'
  } finally {
    saving.value = false
  }
}

async function submitFinal() {
  if (!confirm('제출하면 더 이상 수정할 수 없습니다. 제출할까요?')) return
  submitting.value = true
  message.value = ''
  try {
    const { data } = await api.put(
      `/api/assignments/${matchedAssignment.value.id}/submission`,
      { content: content.value },
      { params: { submit: true } }
    )
    submission.value = data
    autosave.stop()
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <RouterLink :to="{ name: 'material-subject-units', params: { subject } }" class="back">
    ← {{ subject }}
  </RouterLink>
  <div class="title-row">
    <h1>{{ unit }}</h1>
    <RouterLink
      v-if="isTeacher()"
      :to="{ name: 'print-worksheet', params: { subject, unit } }"
      class="print-link"
    >
      🖨️ 인쇄용 학습지
    </RouterLink>
  </div>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="!currentUnit" class="empty">단원 정보를 찾을 수 없습니다.</p>

  <div v-else class="grid">
    <template v-for="s in currentUnit.standards" :key="s.standard_id">
      <RouterLink
        v-if="materialsById.has(s.standard_id)"
        :to="`/materials/${s.standard_id}`"
        class="card"
      >
        <h2>{{ materialsById.get(s.standard_id).title }}</h2>
        <p class="std-name">[{{ s.standard_id }}] {{ s.성취기준명 }}</p>
      </RouterLink>
      <div v-else class="card disabled">
        <h2>{{ s.성취기준명 }}</h2>
        <p class="std-name">[{{ s.standard_id }}] 준비 중</p>
      </div>
    </template>
  </div>

  <section v-if="unitReport" class="report-box">
    <div class="report-head">
      <h2>📋 심화 탐구 보고서 — {{ unitReport.제목 }}</h2>
      <RouterLink
        v-if="isTeacher() && !matchedAssignment"
        :to="{ name: 'teacher-assignments', query: reportAssignmentQuery }"
        class="assign-btn"
      >
        이 보고서를 과제로 내기
      </RouterLink>
      <RouterLink
        v-else-if="isTeacher() && matchedAssignment"
        :to="{ name: 'teacher-assignments', query: { subject } }"
        class="assign-btn done"
      >
        과제로 등록됨 · 제출 현황 보기
      </RouterLink>
    </div>
    <p class="report-content">{{ unitReport.안내 }}</p>
    <p class="report-label">탐구 질문</p>
    <ol class="report-questions">
      <li v-for="(q, i) in unitReport.탐구질문" :key="i">{{ q }}</li>
    </ol>
    <p class="report-format"><strong>제출 형식</strong> {{ unitReport.제출형식 }}</p>
  </section>

  <section v-if="!isTeacher() && matchedAssignment" class="submit-box">
    <h2>내 보고서 작성</h2>
    <p v-if="submissionLoading">불러오는 중…</p>
    <template v-else-if="submission">
      <div v-if="submission.status === 'graded'" class="grade-box">
        <strong>{{ submission.score }}점</strong>
        <p v-if="submission.feedback">{{ submission.feedback }}</p>
      </div>
      <p v-else-if="submission.status === 'submitted'" class="submitted-note">
        제출 완료 · {{ new Date(submission.submitted_at).toLocaleString('ko-KR') }} (채점 대기 중)
      </p>

      <RichEditor v-model="content" :readonly="locked" />

      <div v-if="!locked" class="actions">
        <button class="save-btn" :disabled="saving" @click="saveDraft">
          {{ saving ? '저장 중…' : '임시저장' }}
        </button>
        <button class="submit-btn" :disabled="submitting" @click="submitFinal">
          {{ submitting ? '제출 중…' : '제출하기' }}
        </button>
      </div>
      <p v-if="message" class="message">{{ message }}</p>
    </template>
  </section>
</template>

<style scoped>
.back {
  display: inline-block;
  color: var(--text-dim);
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 12px;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.title-row h1 {
  margin: 0;
}

.print-link {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--accent-border);
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.print-link:hover {
  background: var(--accent);
  color: #ffffff;
}

.empty {
  color: var(--text-dim);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}

.card {
  display: block;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 18px;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s, background 0.15s;
}

.card:hover {
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.card.disabled {
  opacity: 0.5;
  cursor: default;
}

.card.disabled:hover {
  border-color: var(--border);
  background: none;
}

.card h2 {
  font-size: 16px;
  margin-bottom: 6px;
}

.std-name {
  font-size: 13px;
  color: var(--text-dim);
}

.report-box {
  margin-top: 32px;
  padding: 20px;
  border: 1px solid var(--accent-border);
  border-radius: 12px;
  background: var(--accent-bg);
}

.report-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.report-box h2 {
  font-size: 16px;
  margin-bottom: 0;
}

.assign-btn {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--accent-border);
  background: var(--bg);
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.assign-btn:hover {
  background: var(--accent);
  color: #ffffff;
}

.assign-btn.done {
  color: #16a34a;
  border-color: #16a34a;
}

.assign-btn.done:hover {
  background: #16a34a;
  color: #ffffff;
}

.report-content {
  white-space: pre-wrap;
  line-height: 1.7;
  margin-bottom: 12px;
}

.report-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dim);
  margin-bottom: 4px;
}

.report-questions {
  margin: 0 0 14px;
  padding-left: 20px;
  line-height: 1.8;
}

.report-format {
  font-size: 13px;
  color: var(--text-dim);
  line-height: 1.6;
}

.submit-box {
  margin-top: 24px;
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: 12px;
}

.submit-box h2 {
  font-size: 16px;
  margin-bottom: 16px;
}

.grade-box {
  border: 1px solid #16a34a;
  background: rgba(22, 163, 74, 0.08);
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 20px;
}

.grade-box strong {
  font-size: 18px;
  color: #16a34a;
}

.submitted-note {
  color: var(--accent);
  font-size: 13px;
  margin-bottom: 16px;
}

.actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
}

.save-btn,
.submit-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.save-btn {
  border: 1px solid var(--border);
  background: none;
  color: var(--text);
}

.submit-btn {
  border: none;
  background: var(--accent);
  color: white;
}

.save-btn:disabled,
.submit-btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.message {
  margin-top: 10px;
  font-size: 13px;
  color: var(--text-dim);
}
</style>
