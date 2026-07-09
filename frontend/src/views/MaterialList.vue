<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const materials = ref([])
const loading = ref(true)

onMounted(async () => {
  const { data } = await api.get('/api/materials')
  materials.value = data
  loading.value = false
})
</script>

<template>
  <h1>학습자료</h1>
  <p class="hint">알고리즘과 프로그래밍의 핵심 개념을 교과서처럼 차근차근 읽고, 실제 코드로 확인해보세요.</p>

  <p v-if="loading">불러오는 중…</p>
  <div v-else class="grid">
    <RouterLink
      v-for="m in materials"
      :key="m.standard_id"
      :to="`/materials/${m.standard_id}`"
      class="card"
    >
      <h2>{{ m.title }}</h2>
      <p class="std-name">[{{ m.standard_id }}] {{ m.성취기준명 }}</p>
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

.card h2 {
  font-size: 16px;
  margin-bottom: 6px;
}

.std-name {
  font-size: 13px;
  color: var(--text-dim);
}
</style>
