<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const subjects = ref([])
const loading = ref(true)

onMounted(async () => {
  const { data } = await api.get('/api/subjects')
  subjects.value = data
  loading.value = false
})
</script>

<template>
  <h1>평가 - 과목 선택</h1>
  <p class="hint">기출문제를 풀며 이해도를 평가해보세요. 결과는 오답노트와 통계에 반영됩니다.</p>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="!subjects.length" class="empty">수강 중인 과목이 없습니다. 선생님께 문의해 주세요.</p>
  <div v-else class="grid">
    <RouterLink
      v-for="s in subjects"
      :key="s.교과"
      :to="{ name: 'subject-units', params: { subject: s.교과 } }"
      class="card"
    >
      <h2>{{ s.교과 }}</h2>
      <p class="meta">{{ s.units.length }}개 단원 · 문제 {{ s.question_count }}개</p>
    </RouterLink>
  </div>
</template>

<style scoped>
.hint {
  color: var(--text-dim);
  margin-bottom: 20px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}

.card {
  display: block;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.15s, background 0.15s;
}

.card:hover {
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.card h2 {
  margin-bottom: 6px;
}

.meta {
  font-size: 13px;
  color: var(--text-dim);
}

.empty {
  color: var(--text-dim);
  font-size: 13px;
}
</style>
