<script setup>
import { onMounted, ref } from 'vue'
import api from '../api'

const stats = ref(null)

onMounted(async () => {
  const { data } = await api.get('/api/stats')
  stats.value = data
})
</script>

<template>
  <h1>내 학습 통계</h1>

  <div v-if="stats" class="kpi-row">
    <div class="kpi">
      <span class="value">{{ stats.total_questions }}</span>
      <span class="label">전체 문제</span>
    </div>
    <div class="kpi">
      <span class="value">{{ stats.solved }}</span>
      <span class="label">푼 문제</span>
    </div>
    <div class="kpi">
      <span class="value">{{ stats.correct }}</span>
      <span class="label">정답</span>
    </div>
    <div class="kpi">
      <span class="value">{{ stats.accuracy }}%</span>
      <span class="label">정답률</span>
    </div>
  </div>

  <h2 v-if="stats">성취기준별 성취도</h2>
  <table v-if="stats && stats.by_standard.length">
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
      <tr v-for="row in stats.by_standard" :key="row.standard_id">
        <td class="std-id">{{ row.standard_id }}</td>
        <td>{{ row.단원 }}</td>
        <td class="acc-cell">
          <template v-if="row.solved">
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: row.accuracy + '%' }"></div>
            </div>
            <span class="acc-text">{{ row.correct }}/{{ row.solved }} ({{ row.accuracy }}%)</span>
          </template>
          <span v-else class="not-attempted">미응시</span>
        </td>
        <td class="acc-cell">
          <template v-if="row.practice_attempted">
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: row.practice_accuracy + '%' }"></div>
            </div>
            <span class="acc-text">
              {{ row.practice_correct }}/{{ row.practice_attempted }} ({{ row.practice_accuracy }}%)
            </span>
          </template>
          <span v-else class="not-attempted">미응시</span>
        </td>
        <td class="grade-cell">
          <span v-if="row.grade" class="grade-badge" :class="`grade-${row.grade}`">{{ row.grade }}</span>
          <span v-else class="not-attempted">-</span>
        </td>
      </tr>
    </tbody>
  </table>
  <p v-else-if="stats" class="empty">아직 푼 문제가 없습니다.</p>
</template>

<style scoped>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}

.kpi {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi .value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-h);
}

.kpi .label {
  font-size: 13px;
  color: var(--text-dim);
}

.std-id {
  font-family: var(--mono);
  font-size: 13px;
  white-space: nowrap;
}

.acc-cell {
  min-width: 220px;
}

.bar-track {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: var(--bg-soft);
  border: 1px solid var(--border);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 999px;
}

.acc-text {
  font-size: 12px;
  color: var(--text-dim);
  display: block;
  margin-top: 4px;
}

.not-attempted {
  font-size: 12px;
  color: var(--text-dim);
}

.grade-cell {
  text-align: center;
}

.grade-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 14px;
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
}
</style>
