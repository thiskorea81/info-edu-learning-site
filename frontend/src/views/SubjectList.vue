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
  <h1>교과서 선택</h1>
  <p class="hint">공부할 교과서를 선택하면 단원별로 문제를 풀 수 있습니다.</p>

  <p v-if="loading">불러오는 중…</p>
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
</style>
