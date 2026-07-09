<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const props = defineProps({
  categoryKey: { type: String, required: true },
})

const category = ref(null)
const problems = ref([])
const loading = ref(true)

async function load() {
  loading.value = true
  const [{ data: cats }, { data: probs }] = await Promise.all([
    api.get('/api/problems/categories'),
    api.get('/api/problems', { params: { category: props.categoryKey } }),
  ])
  category.value = cats.find((c) => c.key === props.categoryKey) ?? null
  problems.value = probs
  loading.value = false
}

onMounted(load)

const isDaily = computed(() => props.categoryKey === 'daily')
const isStandardCategory = computed(
  () => props.categoryKey !== 'basic' && props.categoryKey !== 'daily'
)

// group daily problems by year-month, newest month first, newest problem first within month
const monthGroups = computed(() => {
  if (!isDaily.value) return []
  const groups = new Map()
  for (const p of problems.value) {
    const date = (p.source || '').replace('daily_', '')
    const month = date.slice(0, 7) || '기타'
    if (!groups.has(month)) groups.set(month, [])
    groups.get(month).push({ ...p, date })
  }
  return [...groups.entries()]
    .sort((a, b) => (a[0] < b[0] ? 1 : -1))
    .map(([month, items]) => ({
      month,
      items: items.sort((a, b) => (a.date < b.date ? 1 : -1)),
    }))
})

function difficultyClass(letter) {
  if (letter === 'A') return 'easy'
  if (letter === 'B') return 'medium'
  return 'hard'
}
</script>

<template>
  <RouterLink to="/problems" class="back">← 코딩테스트</RouterLink>
  <h1>{{ category?.label ?? '' }}</h1>
  <p v-if="category?.성취기준명" class="hint">{{ category.성취기준명 }}</p>
  <RouterLink v-if="isStandardCategory" :to="`/materials/${categoryKey}`" class="theory-link">
    📖 이론 보기
  </RouterLink>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="problems.length === 0" class="empty">문제가 없습니다.</p>

  <ul v-else-if="!isDaily" class="list">
    <li v-for="p in problems" :key="p.id">
      <RouterLink :to="`/problems/${p.id}`" class="item">
        <span class="letter" :class="difficultyClass(p.letter)">{{ p.letter }}</span>
        <span class="title">{{ p.title }}</span>
        <span class="badge" :class="difficultyClass(p.letter)">{{ p.difficulty }}</span>
      </RouterLink>
    </li>
  </ul>

  <details v-else v-for="g in monthGroups" :key="g.month" class="month-group" open>
    <summary>
      <span>{{ g.month }}</span>
      <span class="month-count">{{ g.items.length }}문제</span>
    </summary>
    <ul class="list">
      <li v-for="p in g.items" :key="p.id">
        <RouterLink :to="`/problems/${p.id}`" class="item">
          <span class="letter" :class="difficultyClass(p.letter)">{{ p.letter }}</span>
          <span class="title">{{ p.title }}</span>
          <span class="date">{{ p.date }}</span>
          <span class="badge" :class="difficultyClass(p.letter)">{{ p.difficulty }}</span>
        </RouterLink>
      </li>
    </ul>
  </details>
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
  font-size: 14px;
  margin-bottom: 20px;
}

.empty {
  color: var(--text-dim);
}

.theory-link {
  display: inline-block;
  margin-bottom: 20px;
  padding: 8px 16px;
  border: 1px solid var(--accent-border);
  background: var(--accent-bg);
  color: var(--accent);
  border-radius: 8px;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.month-group {
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 10px;
  overflow: hidden;
}

.month-group summary {
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

.month-group summary::-webkit-details-marker {
  display: none;
}

.month-count {
  font-size: 12px;
  color: var(--text-dim);
  font-weight: 400;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  border-top: 1px solid var(--border);
}

.month-group .list {
  border-top: none;
}

.item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  text-decoration: none;
  color: var(--text);
}

.month-group .item {
  border-top: 1px solid var(--border);
}

.list > li:first-child .item {
  border-top: none;
}

.item:hover {
  background: var(--bg-soft);
}

.letter {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 13px;
  flex-shrink: 0;
}

.letter.easy {
  color: var(--correct);
  background: var(--correct-bg);
}

.letter.medium {
  color: var(--accent);
  background: var(--accent-bg);
}

.letter.hard {
  color: var(--wrong);
  background: var(--wrong-bg);
}

.title {
  flex: 1;
  font-weight: 500;
  color: var(--text-h);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.date {
  font-size: 12px;
  color: var(--text-dim);
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
