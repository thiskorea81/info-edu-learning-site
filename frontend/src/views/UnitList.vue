<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const props = defineProps({ subject: { type: String, required: true } })

const allSubjects = ref([])
const loading = ref(true)

const current = computed(() => allSubjects.value.find((s) => s.교과 === props.subject))

onMounted(async () => {
  const { data } = await api.get('/api/subjects')
  allSubjects.value = data
  loading.value = false
})
</script>

<template>
  <RouterLink to="/" class="back">← 교과서 목록</RouterLink>
  <h1>{{ subject }}</h1>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="!current" class="empty">교과 정보를 찾을 수 없습니다.</p>

  <div v-else class="grid">
    <RouterLink
      v-for="u in current.units"
      :key="u.단원"
      :to="{ name: 'unit-questions', params: { subject, unit: u.단원 } }"
      class="card"
      :class="{ disabled: u.question_count === 0 }"
    >
      <h2>{{ u.단원 }}</h2>
      <p class="meta">
        성취기준 {{ u.standards.length }}개 · 문제 {{ u.question_count }}개
      </p>
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

.empty {
  color: var(--text-dim);
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

.card.disabled {
  opacity: 0.5;
}

.card h2 {
  font-size: 17px;
  margin-bottom: 6px;
}

.meta {
  font-size: 13px;
  color: var(--text-dim);
}
</style>
