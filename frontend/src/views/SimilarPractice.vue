<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const props = defineProps({
  standardId: { type: String, required: true },
})

const questions = ref([])
const standard = ref(null)
const loading = ref(true)

onMounted(async () => {
  const [{ data: qs }, { data: standards }] = await Promise.all([
    api.get('/api/questions', { params: { standard_id: props.standardId, include_similar: true } }),
    api.get('/api/standards'),
  ])
  questions.value = qs
  standard.value = standards.find((s) => s.standard_id === props.standardId) ?? null
  loading.value = false
})
</script>

<template>
  <RouterLink to="/wrong-notes" class="back">← 오답노트</RouterLink>
  <h1>비슷한 문제 연습</h1>
  <p v-if="standard" class="hint">[{{ standard.standard_id }}] {{ standard.성취기준명 }}</p>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="questions.length === 0" class="empty">이 성취기준에는 아직 문제가 없습니다.</p>

  <ul v-else class="list">
    <li v-for="(q, i) in questions" :key="q.id">
      <RouterLink :to="`/questions/${q.id}`" class="item">
        <span class="num">{{ i + 1 }}</span>
        <span class="stem">{{ q.문제 }}</span>
        <span v-if="q.코드" class="badge code">코드</span>
        <span v-if="q.유사문제" class="badge similar">유사</span>
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

.hint {
  color: var(--text-dim);
  margin-bottom: 20px;
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
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.badge.similar {
  color: var(--text-dim);
  border-color: var(--border);
  background: var(--bg-soft);
}
</style>
