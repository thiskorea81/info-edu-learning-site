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
  <h1>학습자료</h1>
  <p class="hint">교과서처럼 개념을 차근차근 설명합니다. 과목을 선택해 단원별로 살펴보세요.</p>

  <p v-if="loading">불러오는 중…</p>
  <div v-else class="grid">
    <RouterLink
      v-for="s in subjects"
      :key="s.교과"
      :to="{ name: 'material-subject-units', params: { subject: s.교과 } }"
      class="card"
    >
      <h2>{{ s.교과 }}</h2>
      <p class="meta">{{ s.units.length }}개 단원</p>
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
