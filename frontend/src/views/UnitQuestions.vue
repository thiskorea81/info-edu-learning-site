<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const props = defineProps({
  subject: { type: String, required: true },
  unit: { type: String, required: true },
})

const questions = ref([])
const wrongIds = ref(new Set())
const loading = ref(true)

async function load() {
  loading.value = true
  const [{ data: qs }, { data: wrong }] = await Promise.all([
    api.get('/api/questions', { params: { 교과: props.subject, 단원: props.unit } }),
    api.get('/api/attempts/wrong'),
  ])
  questions.value = qs
  wrongIds.value = new Set(wrong.map((w) => w.question.id))
  loading.value = false
}

onMounted(load)
watch(() => [props.subject, props.unit], load)
</script>

<template>
  <RouterLink :to="{ name: 'subject-units', params: { subject } }" class="back">
    ← {{ subject }}
  </RouterLink>
  <h1>{{ unit }}</h1>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="questions.length === 0" class="empty">이 단원에는 아직 문제가 없습니다.</p>

  <ul v-else class="list">
    <li v-for="(q, i) in questions" :key="q.id">
      <RouterLink :to="`/questions/${q.id}`" class="item">
        <span class="num">{{ i + 1 }}</span>
        <span class="stem">{{ q.문제 }}</span>
        <span v-if="q.코드" class="badge code">코드</span>
        <span v-if="wrongIds.has(q.id)" class="badge wrong">오답</span>
      </RouterLink>
    </li>
  </ul>
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

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  border-top: 1px solid var(--border);
}

.item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  color: var(--text);
}

.item:hover {
  background: var(--bg-soft);
}

.num {
  color: var(--text-dim);
  font-size: 13px;
  min-width: 24px;
}

.stem {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--text-dim);
}

.badge.code {
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.badge.wrong {
  color: var(--wrong);
  border-color: var(--wrong);
  background: var(--wrong-bg);
}
</style>
