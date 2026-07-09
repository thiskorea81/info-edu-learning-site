<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import QuestionBody from '../components/QuestionBody.vue'

const items = ref([])
const loading = ref(true)
const deleting = ref(null)

onMounted(load)

async function load() {
  loading.value = true
  const { data } = await api.get('/api/attempts/wrong')
  items.value = data
  loading.value = false
}

async function removeNote(questionId) {
  deleting.value = questionId
  try {
    await api.delete(`/api/attempts/wrong/${questionId}`)
    items.value = items.value.filter((item) => item.question.id !== questionId)
  } finally {
    deleting.value = null
  }
}
</script>

<template>
  <h1>오답노트</h1>
  <p class="hint">한 번이라도 틀린 문제는 다시 맞혀도 목록에 남습니다. 복습이 끝났다면 직접 삭제하세요.</p>
  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="items.length === 0" class="empty">아직 틀린 문제가 없습니다.</p>

  <div v-for="item in items" :key="item.question.id" class="card">
    <QuestionBody :question="item.question" />
    <p class="answer-line">
      내가 선택: <strong class="wrong">{{ item.selected }}번</strong>
      {{ item.question.선택지[item.selected] }}
    </p>
    <p class="answer-line">
      정답: <strong class="correct">{{ item.question.정답 }}번</strong>
      {{ item.question.선택지[item.question.정답] }}
    </p>
    <p v-if="item.question.해설" class="explain">{{ item.question.해설 }}</p>

    <div class="actions">
      <RouterLink :to="`/questions/${item.question.id}`" class="action-link">다시 풀기 →</RouterLink>
      <RouterLink :to="`/practice/${item.question.standard_id}`" class="action-link accent">
        비슷한 문제 풀기 →
      </RouterLink>
      <button
        class="delete-btn"
        :disabled="deleting === item.question.id"
        @click="removeNote(item.question.id)"
      >
        {{ deleting === item.question.id ? '삭제 중…' : '오답노트에서 삭제' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.hint {
  color: var(--text-dim);
  font-size: 14px;
  margin-bottom: 20px;
}

.empty {
  color: var(--text-dim);
}

.card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
}

.answer-line {
  font-size: 14px;
  margin: 4px 0;
}

.answer-line .wrong {
  color: var(--wrong);
}

.answer-line .correct {
  color: var(--correct);
}

.explain {
  font-size: 14px;
  color: var(--text-dim);
  margin-top: 6px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.action-link {
  color: var(--text-dim);
  text-decoration: none;
  font-size: 14px;
}

.action-link.accent {
  color: var(--accent);
}

.delete-btn {
  margin-left: auto;
  background: transparent;
  border: 1px solid var(--wrong);
  color: var(--wrong);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
}

.delete-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
</style>
