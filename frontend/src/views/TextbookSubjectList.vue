<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const subjects = ref([])
const loading = ref(true)

onMounted(async () => {
  const [{ data: mySubjects }, { data: textbooks }] = await Promise.all([
    api.get('/api/subjects'),
    api.get('/api/textbooks'),
  ])
  const allowedNames = new Set(mySubjects.map((s) => s.교과))
  const counts = new Map()
  for (const t of textbooks) {
    if (!allowedNames.has(t.교과)) continue
    counts.set(t.교과, (counts.get(t.교과) || 0) + 1)
  }
  subjects.value = [...counts.entries()].map(([name, count]) => ({ name, count }))
  loading.value = false
})
</script>

<template>
  <h1>교과서</h1>
  <p class="hint">교과서 PDF를 바로 볼 수 있습니다.</p>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="!subjects.length" class="empty">등록된 교과서가 없습니다.</p>
  <div v-else class="grid">
    <RouterLink
      v-for="s in subjects"
      :key="s.name"
      :to="{ name: 'textbook-list', params: { subject: s.name } }"
      class="card"
    >
      <h2>{{ s.name }}</h2>
      <p class="meta">{{ s.count }}개 단원</p>
    </RouterLink>
  </div>
</template>

<style scoped>
.hint {
  color: var(--text-dim);
  margin-bottom: 20px;
}

.empty {
  color: var(--text-dim);
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
