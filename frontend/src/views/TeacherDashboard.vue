<script setup>
import { onMounted, ref } from 'vue'
import api from '../api'

const roster = ref([])
const classStats = ref([])
const loading = ref(true)
const error = ref('')

const newName = ref('')
const newNumber = ref('')
const newRole = ref('student')
const adding = ref(false)

const detail = ref(null)
const detailLoading = ref(false)

async function loadAll() {
  loading.value = true
  try {
    const [{ data: rosterData }, { data: statsData }] = await Promise.all([
      api.get('/api/roster'),
      api.get('/api/stats/roster'),
    ])
    roster.value = rosterData
    classStats.value = statsData
  } finally {
    loading.value = false
  }
}

onMounted(loadAll)

async function addStudent() {
  if (!newName.value.trim() || !newNumber.value.trim()) {
    error.value = '이름과 번호를 모두 입력해 주세요.'
    return
  }
  error.value = ''
  adding.value = true
  try {
    await api.post('/api/roster', {
      name: newName.value.trim(),
      number: newNumber.value.trim(),
      role: newRole.value,
    })
    newName.value = ''
    newNumber.value = ''
    newRole.value = 'student'
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || '등록에 실패했습니다.'
  } finally {
    adding.value = false
  }
}

async function removeStudent(id) {
  if (!confirm('이 계정을 삭제할까요?')) return
  await api.delete(`/api/roster/${id}`)
  if (detail.value?.student?.id === id) detail.value = null
  await loadAll()
}

async function showDetail(id) {
  detailLoading.value = true
  try {
    const { data } = await api.get(`/api/stats/roster/${id}`)
    detail.value = data
  } finally {
    detailLoading.value = false
  }
}

function statFor(id) {
  return classStats.value.find((s) => s.id === id)
}
</script>

<template>
  <h1>교사용 관리</h1>

  <section class="panel">
    <h2>학생 등록</h2>
    <form class="add-form" @submit.prevent="addStudent">
      <input v-model="newName" type="text" placeholder="이름" />
      <input v-model="newNumber" type="text" placeholder="번호" />
      <select v-model="newRole">
        <option value="student">학생</option>
        <option value="teacher">교사</option>
      </select>
      <button type="submit" :disabled="adding">{{ adding ? '등록 중…' : '등록' }}</button>
    </form>
    <p v-if="error" class="error">{{ error }}</p>
  </section>

  <section class="panel">
    <h2>명단 및 성취도 ({{ roster.filter((r) => r.role === 'student').length }}명)</h2>
    <p v-if="loading">불러오는 중…</p>
    <table v-else-if="roster.length">
      <thead>
        <tr>
          <th>번호</th>
          <th>이름</th>
          <th>역할</th>
          <th>푼 문제</th>
          <th>정답률</th>
          <th>종합 등급</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in roster" :key="u.id">
          <td>{{ u.number }}</td>
          <td>{{ u.name }}</td>
          <td>
            <span class="role-badge" :class="u.role">{{ u.role === 'teacher' ? '교사' : '학생' }}</span>
          </td>
          <template v-if="u.role === 'student'">
            <td>{{ statFor(u.id)?.solved ?? 0 }}</td>
            <td>{{ statFor(u.id)?.accuracy ?? 0 }}%</td>
            <td>
              <span v-if="statFor(u.id)?.grade" class="grade-badge" :class="`grade-${statFor(u.id).grade}`">
                {{ statFor(u.id).grade }}
              </span>
              <span v-else class="not-attempted">-</span>
            </td>
          </template>
          <template v-else>
            <td colspan="3" class="not-attempted">-</td>
          </template>
          <td class="actions">
            <button v-if="u.role === 'student'" class="link-btn" @click="showDetail(u.id)">상세</button>
            <button class="link-btn danger" @click="removeStudent(u.id)">삭제</button>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">등록된 계정이 없습니다.</p>
  </section>

  <section v-if="detail" class="panel">
    <h2>{{ detail.student.name }}({{ detail.student.number }}) 상세 성취도</h2>
    <p v-if="detailLoading">불러오는 중…</p>
    <table v-else-if="detail.by_standard.length">
      <thead>
        <tr>
          <th>성취기준</th>
          <th>단원</th>
          <th>이론</th>
          <th>실습</th>
          <th>종합 등급</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in detail.by_standard" :key="row.standard_id">
          <td class="std-id">{{ row.standard_id }}</td>
          <td>{{ row.단원 }}</td>
          <td>
            <span v-if="row.solved">{{ row.correct }}/{{ row.solved }} ({{ row.accuracy }}%)</span>
            <span v-else class="not-attempted">미응시</span>
          </td>
          <td>
            <span v-if="row.practice_attempted">
              {{ row.practice_correct }}/{{ row.practice_attempted }} ({{ row.practice_accuracy }}%)
            </span>
            <span v-else class="not-attempted">미응시</span>
          </td>
          <td>
            <span v-if="row.grade" class="grade-badge" :class="`grade-${row.grade}`">{{ row.grade }}</span>
            <span v-else class="not-attempted">-</span>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">아직 푼 문제가 없습니다.</p>
  </section>
</template>

<style scoped>
.panel {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px;
  margin-bottom: 20px;
}

.panel h2 {
  font-size: 15px;
  margin-bottom: 14px;
}

.add-form {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.add-form input,
.add-form select {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
  color: var(--text-h);
  font-size: 13px;
}

.add-form input {
  width: 140px;
}

.add-form button {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: #ffffff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
}

.add-form button:disabled {
  opacity: 0.6;
}

.error {
  color: var(--wrong);
  font-size: 13px;
  margin-top: 8px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th,
td {
  text-align: left;
  padding: 8px 10px;
  border-top: 1px solid var(--border);
}

thead th {
  border-top: none;
  color: var(--text-dim);
  font-weight: 500;
}

.std-id {
  font-family: var(--mono);
  white-space: nowrap;
}

.role-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
}

.role-badge.teacher {
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.not-attempted {
  color: var(--text-dim);
  font-size: 12px;
}

.actions {
  white-space: nowrap;
}

.link-btn {
  background: none;
  border: none;
  color: var(--accent);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 6px;
}

.link-btn.danger {
  color: var(--wrong);
}

.grade-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 12px;
  color: #ffffff;
}

.grade-A {
  background: #16a34a;
}

.grade-B {
  background: #65a30d;
}

.grade-C {
  background: #ca8a04;
}

.grade-D {
  background: #ea580c;
}

.grade-E {
  background: #dc2626;
}

@media (prefers-color-scheme: dark) {
  .grade-badge {
    color: #0b0b0d;
  }

  .grade-A {
    background: #4ade80;
  }

  .grade-B {
    background: #a3e635;
  }

  .grade-C {
    background: #facc15;
  }

  .grade-D {
    background: #fb923c;
  }

  .grade-E {
    background: #f87171;
  }
}

.empty {
  color: var(--text-dim);
  font-size: 13px;
}
</style>
