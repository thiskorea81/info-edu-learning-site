<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const props = defineProps({
  subject: { type: String, required: true },
  unit: { type: String, required: true },
})

const allSubjects = ref([])
const materials = ref([])
const unitReport = ref(null)
const loading = ref(true)

const materialsById = computed(() => new Map(materials.value.map((m) => [m.standard_id, m])))
const currentUnit = computed(() => {
  const subject = allSubjects.value.find((s) => s.교과 === props.subject)
  return subject?.units.find((u) => u.단원 === props.unit)
})

async function load() {
  loading.value = true
  const [{ data: subjects }, { data: mats }, { data: reports }] = await Promise.all([
    api.get('/api/subjects'),
    api.get('/api/materials'),
    api.get('/api/unit-reports', { params: { 교과: props.subject, 단원: props.unit } }),
  ])
  allSubjects.value = subjects
  materials.value = mats
  unitReport.value = reports[0] ?? null
  loading.value = false
}

onMounted(load)
watch(() => [props.subject, props.unit], load)
</script>

<template>
  <RouterLink :to="{ name: 'material-subject-units', params: { subject } }" class="back">
    ← {{ subject }}
  </RouterLink>
  <h1>{{ unit }}</h1>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="!currentUnit" class="empty">단원 정보를 찾을 수 없습니다.</p>

  <div v-else class="grid">
    <template v-for="s in currentUnit.standards" :key="s.standard_id">
      <RouterLink
        v-if="materialsById.has(s.standard_id)"
        :to="`/materials/${s.standard_id}`"
        class="card"
      >
        <h2>{{ materialsById.get(s.standard_id).title }}</h2>
        <p class="std-name">[{{ s.standard_id }}] {{ s.성취기준명 }}</p>
      </RouterLink>
      <div v-else class="card disabled">
        <h2>{{ s.성취기준명 }}</h2>
        <p class="std-name">[{{ s.standard_id }}] 준비 중</p>
      </div>
    </template>
  </div>

  <section v-if="unitReport" class="report-box">
    <h2>📋 심화 탐구 보고서 — {{ unitReport.제목 }}</h2>
    <p class="report-content">{{ unitReport.안내 }}</p>
    <p class="report-label">탐구 질문</p>
    <ol class="report-questions">
      <li v-for="(q, i) in unitReport.탐구질문" :key="i">{{ q }}</li>
    </ol>
    <p class="report-format"><strong>제출 형식</strong> {{ unitReport.제출형식 }}</p>
  </section>
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
  cursor: default;
}

.card.disabled:hover {
  border-color: var(--border);
  background: none;
}

.card h2 {
  font-size: 16px;
  margin-bottom: 6px;
}

.std-name {
  font-size: 13px;
  color: var(--text-dim);
}

.report-box {
  margin-top: 32px;
  padding: 20px;
  border: 1px solid var(--accent-border);
  border-radius: 12px;
  background: var(--accent-bg);
}

.report-box h2 {
  font-size: 16px;
  margin-bottom: 10px;
}

.report-content {
  white-space: pre-wrap;
  line-height: 1.7;
  margin-bottom: 12px;
}

.report-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-dim);
  margin-bottom: 4px;
}

.report-questions {
  margin: 0 0 14px;
  padding-left: 20px;
  line-height: 1.8;
}

.report-format {
  font-size: 13px;
  color: var(--text-dim);
  line-height: 1.6;
}
</style>
