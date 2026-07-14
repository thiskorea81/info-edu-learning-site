<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import RichEditor from '../components/RichEditor.vue'

const props = defineProps({ id: { type: String, required: true } })

const assignment = ref(null)
const submission = ref(null)
const content = ref({ type: 'doc', content: [{ type: 'paragraph' }] })
const loading = ref(true)
const saving = ref(false)
const submitting = ref(false)
const message = ref('')

const locked = computed(
  () => submission.value?.status === 'submitted' || submission.value?.status === 'graded'
)

async function load() {
  loading.value = true
  const [{ data: a }, { data: s }] = await Promise.all([
    api.get(`/api/assignments/${props.id}`),
    api.get(`/api/assignments/${props.id}/submission`),
  ])
  assignment.value = a
  submission.value = s
  content.value = s.content
  loading.value = false
}

onMounted(load)

async function saveDraft() {
  saving.value = true
  message.value = ''
  try {
    const { data } = await api.put(`/api/assignments/${props.id}/submission`, { content: content.value })
    submission.value = data
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
      `/api/assignments/${props.id}/submission`,
      { content: content.value },
      { params: { submit: true } }
    )
    submission.value = data
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <p v-if="loading">불러오는 중…</p>
  <div v-else-if="assignment">
    <RouterLink to="/assignments" class="back">← 과제 목록</RouterLink>
    <h1>{{ assignment.title }}</h1>
    <p class="meta">
      {{ assignment.subject_name }}<span v-if="assignment.단원"> · {{ assignment.단원 }}</span>
    </p>
    <p class="due">
      제출 기한:
      {{ assignment.due_at ? new Date(assignment.due_at).toLocaleString('ko-KR') : '없음' }}
    </p>
    <p class="description">{{ assignment.description }}</p>

    <div v-if="submission.status === 'graded'" class="grade-box">
      <strong>{{ submission.score }}점</strong>
      <p v-if="submission.feedback">{{ submission.feedback }}</p>
    </div>
    <p v-else-if="submission.status === 'submitted'" class="submitted-note">
      제출 완료 · {{ new Date(submission.submitted_at).toLocaleString('ko-KR') }}
      (채점 대기 중)
    </p>

    <h2>내 제출물</h2>
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
  </div>
</template>

<style scoped>
.back {
  display: inline-block;
  color: var(--text-dim);
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 12px;
}

.meta {
  color: var(--text-dim);
  font-size: 13px;
  margin-bottom: 4px;
}

.due {
  color: var(--text-dim);
  font-size: 13px;
  margin-bottom: 14px;
}

.description {
  white-space: pre-wrap;
  line-height: 1.7;
  margin-bottom: 20px;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
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

h2 {
  font-size: 16px;
  margin-bottom: 12px;
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
