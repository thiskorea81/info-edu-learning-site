<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const categories = ref([])
const loading = ref(true)

onMounted(async () => {
  const { data } = await api.get('/api/problems/categories/textbook')
  categories.value = data
  loading.value = false
})
</script>

<template>
  <RouterLink to="/problems" class="back">← 코딩테스트</RouterLink>
  <h1>교과서문제</h1>
  <p class="hint">성취기준별로 묶인 코딩테스트 문제입니다.</p>

  <p v-if="loading">불러오는 중…</p>
  <div v-else class="grid">
    <RouterLink
      v-for="c in categories"
      :key="c.key"
      :to="{ name: 'problem-category', params: { categoryKey: c.key } }"
      class="card"
    >
      <h2>{{ c.label }}</h2>
      <p v-if="c.성취기준명" class="std-name">{{ c.성취기준명 }}</p>
      <p class="meta">{{ c.count }}문제</p>
    </RouterLink>
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
  margin-bottom: 6px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.meta {
  font-size: 13px;
  color: var(--text-dim);
}
</style>
