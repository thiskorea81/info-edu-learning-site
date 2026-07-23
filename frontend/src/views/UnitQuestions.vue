<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import { isTeacher } from '../auth'

const props = defineProps({
  subject: { type: String, required: true },
  unit: { type: String, required: true },
})

const questions = ref([])
const wrongIds = ref(new Set())
const itemStats = ref({})
const studentCount = ref(0)
const loading = ref(true)

async function load() {
  loading.value = true
  if (isTeacher()) {
    const [{ data: qs }, { data: statsData }] = await Promise.all([
      api.get('/api/questions', {
        params: { 교과: props.subject, 단원: props.unit, include_similar: true },
      }),
      api.get('/api/questions/stats', { params: { 교과: props.subject, 단원: props.unit } }),
    ])
    questions.value = qs
    itemStats.value = statsData.items
    studentCount.value = statsData.student_count
  } else {
    const [{ data: qs }, { data: wrong }] = await Promise.all([
      api.get('/api/questions', { params: { 교과: props.subject, 단원: props.unit } }),
      api.get('/api/attempts/wrong'),
    ])
    questions.value = qs
    wrongIds.value = new Set(wrong.map((w) => w.question.id))
  }
  loading.value = false
}

onMounted(load)
watch(() => [props.subject, props.unit], load)
</script>

<template>
  <RouterLink :to="{ name: 'subject-units', params: { subject } }" class="back">
    ← {{ subject }}
  </RouterLink>
  <div class="title-row">
    <h1>{{ unit }}</h1>
    <RouterLink
      v-if="isTeacher()"
      :to="{ name: 'print-worksheet', params: { subject, unit } }"
      class="print-link"
    >
      🖨️ 인쇄용 학습지
    </RouterLink>
  </div>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="questions.length === 0" class="empty">이 단원에는 아직 문제가 없습니다.</p>

  <ul v-else class="list">
    <li v-for="(q, i) in questions" :key="q.id">
      <RouterLink
        :to="{ path: `/questions/${q.id}`, query: { scope: 'unit', subject, unit } }"
        class="item"
      >
        <span class="num">{{ i + 1 }}</span>
        <span class="stem">{{ q.문제 }}</span>
        <span v-if="q.기출" class="badge exam">기출</span>
        <span v-if="q.AI생성" class="badge ai">AI</span>
        <span v-if="q.유사문제" class="badge similar">유사</span>
        <span v-if="q.검증" class="badge verified">검증</span>
        <span v-if="q.코드" class="badge code">코드</span>
        <template v-if="isTeacher()">
          <span v-if="itemStats[q.id]?.accuracy !== null" class="badge stat" :class="`grade-${itemStats[q.id].grade}`">
            {{ itemStats[q.id].correct }}/{{ itemStats[q.id].attempted }} ({{ itemStats[q.id].accuracy }}%)
          </span>
          <span v-else class="badge stat not-attempted">미응시</span>
          <span v-if="itemStats[q.id]?.needs_attention" class="badge attention">중점 지도 필요</span>
        </template>
        <span v-else-if="wrongIds.has(q.id)" class="badge wrong">오답</span>
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

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.title-row h1 {
  margin: 0;
}

.print-link {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 8px;
  border: 1px solid var(--accent-border);
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
}

.print-link:hover {
  background: var(--accent);
  color: #ffffff;
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

.badge.exam {
  color: #7c3aed;
  border-color: #7c3aed;
  background: rgba(124, 58, 237, 0.1);
  font-weight: 600;
}

.badge.ai {
  color: #0891b2;
  border-color: #0891b2;
  background: rgba(8, 145, 178, 0.1);
}

.badge.verified {
  color: #16a34a;
  border-color: #16a34a;
  background: rgba(22, 163, 74, 0.1);
  font-weight: 600;
}

.badge.similar {
  color: var(--text-dim);
  border-color: var(--border);
  background: var(--bg-soft);
}

.badge.wrong {
  color: var(--wrong);
  border-color: var(--wrong);
  background: var(--wrong-bg);
}

.badge.stat {
  font-family: var(--mono);
  white-space: nowrap;
}

.badge.stat.not-attempted {
  color: var(--text-dim);
}

.badge.stat.grade-A,
.badge.stat.grade-B {
  color: #16a34a;
  border-color: #16a34a;
}

.badge.stat.grade-C {
  color: #ca8a04;
  border-color: #ca8a04;
}

.badge.stat.grade-D,
.badge.stat.grade-E {
  color: var(--wrong);
  border-color: var(--wrong);
}

.badge.attention {
  color: var(--wrong);
  border-color: var(--wrong);
  background: var(--wrong-bg);
  font-weight: 600;
}
</style>
