<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const assignments = ref([])
const loading = ref(true)

const STATUS_LABEL = {
  not_submitted: '미제출',
  draft: '임시저장',
  submitted: '제출완료',
  graded: '채점완료',
}

onMounted(async () => {
  const { data } = await api.get('/api/assignments')
  assignments.value = data
  loading.value = false
})

function formatDue(due) {
  if (!due) return '기한 없음'
  return new Date(due).toLocaleString('ko-KR', { month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function isOverdue(due, status) {
  return !!due && new Date(due) < new Date() && (status === 'not_submitted' || status === 'draft')
}
</script>

<template>
  <h1>과제</h1>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="!assignments.length" class="empty">받은 과제가 없습니다.</p>
  <ul v-else class="list">
    <li v-for="a in assignments" :key="a.id">
      <RouterLink :to="`/assignments/${a.id}`" class="item">
        <div class="item-main">
          <span class="subject-tag">{{ a.subject_name }}</span>
          <span class="title">{{ a.title }}</span>
        </div>
        <div class="item-meta">
          <span class="due" :class="{ overdue: isOverdue(a.due_at, a.my_status) }">
            {{ formatDue(a.due_at) }}
          </span>
          <span class="status-badge" :class="a.my_status">
            {{ STATUS_LABEL[a.my_status] }}<template v-if="a.my_status === 'graded'"> ({{ a.my_score }}점)</template>
          </span>
        </div>
      </RouterLink>
    </li>
  </ul>
</template>

<style scoped>
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
  justify-content: space-between;
  gap: 14px;
  padding: 14px 4px;
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  color: var(--text);
  flex-wrap: wrap;
}

.item:hover {
  background: var(--bg-soft);
}

.item-main {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.subject-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--text-dim);
  white-space: nowrap;
}

.title {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.due {
  font-size: 12px;
  color: var(--text-dim);
}

.due.overdue {
  color: var(--wrong);
  font-weight: 600;
}

.status-badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--text-dim);
}

.status-badge.submitted {
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.status-badge.graded {
  color: #16a34a;
  border-color: #16a34a;
  background: rgba(22, 163, 74, 0.1);
  font-weight: 600;
}

.status-badge.not_submitted {
  color: var(--wrong);
  border-color: var(--wrong);
}
</style>
