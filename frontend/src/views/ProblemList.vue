<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const groups = ref([])
const loading = ref(true)

onMounted(async () => {
  const { data } = await api.get('/api/problems/groups/by-standard')
  groups.value = data
  loading.value = false
})

function difficultyClass(d) {
  if (d === '쉬움') return 'easy'
  if (d === '어려움') return 'hard'
  return 'medium'
}
</script>

<template>
  <h1>코딩테스트</h1>
  <p class="hint">AtCoder Beginner Contest 스타일의 알고리즘 문제를 직접 풀고 제출해보세요.</p>

  <p v-if="loading">불러오는 중…</p>

  <details v-for="g in groups" :key="g.standard_id ?? 'etc'" class="group" open>
    <summary>
      <span class="group-title">{{ g.standard_id ? `[${g.standard_id}] ${g.성취기준명}` : '기본 예제' }}</span>
      <span class="group-count">{{ g.problems.length }}문제</span>
    </summary>
    <ul class="list">
      <li v-for="p in g.problems" :key="p.id">
        <RouterLink :to="`/problems/${p.id}`" class="item">
          <span class="title">{{ p.title }}</span>
          <span class="badge" :class="difficultyClass(p.difficulty)">{{ p.difficulty }}</span>
        </RouterLink>
      </li>
    </ul>
  </details>
</template>

<style scoped>
.hint {
  color: var(--text-dim);
  margin-bottom: 20px;
}

.group {
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 10px;
  overflow: hidden;
}

.group summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  cursor: pointer;
  background: var(--bg-soft);
  font-weight: 600;
  color: var(--text-h);
  list-style: none;
}

.group summary::-webkit-details-marker {
  display: none;
}

.group-title {
  font-size: 14px;
}

.group-count {
  font-size: 12px;
  color: var(--text-dim);
  font-weight: 400;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  text-decoration: none;
  color: var(--text);
}

.item:hover {
  background: var(--bg-soft);
}

.title {
  font-weight: 500;
  color: var(--text-h);
}

.badge {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
}

.badge.easy {
  color: var(--correct);
  border-color: var(--correct);
  background: var(--correct-bg);
}

.badge.medium {
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.badge.hard {
  color: var(--wrong);
  border-color: var(--wrong);
  background: var(--wrong-bg);
}
</style>
