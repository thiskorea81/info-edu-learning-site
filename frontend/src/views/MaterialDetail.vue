<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import CodeEditor from '../components/CodeEditor.vue'
import { parsePipeTable } from '../utils/markdownTable'
import { isAdmin, isTeacher } from '../auth'

// 코드가 길어지는 응용 과목은 타이핑 대신 복사해서 실습할 수 있도록 허용한다.
const COPY_ALLOWED_SUBJECTS = ['인공지능 기초', '디지털 논리회로', '데이터 과학']

const props = defineProps({
  standardId: { type: String, required: true },
})

const material = ref(null)
const loading = ref(true)
const practiceCode = reactive({})

const panelOpen = ref(false)
const activeIndex = ref(null)
const hasProblems = ref(false)
const hasQuestions = ref(false)

const allSubjects = ref([])
const materialsById = ref(new Map())

async function loadMaterial(id) {
  loading.value = true
  const { data } = await api.get(`/api/materials/${id}`)
  material.value = data
  Object.keys(practiceCode).forEach((k) => delete practiceCode[k])
  data.sections.forEach((s, i) => {
    if (s.code) practiceCode[i] = ''
  })
  const first = data.sections.findIndex((s) => s.code)
  activeIndex.value = first !== -1 ? first : null
  loading.value = false

  const [{ data: problems }, { data: questions }] = await Promise.all([
    api.get('/api/problems', { params: { standard_id: id } }),
    api.get('/api/questions', { params: { standard_id: id, include_similar: true } }),
  ])
  hasProblems.value = problems.length > 0
  hasQuestions.value = questions.length > 0
}

onMounted(async () => {
  const [{ data: subjects }, { data: mats }] = await Promise.all([
    api.get('/api/subjects'),
    api.get('/api/materials'),
  ])
  allSubjects.value = subjects
  materialsById.value = new Map(mats.map((m) => [m.standard_id, m]))

  await loadMaterial(props.standardId)
})

watch(
  () => props.standardId,
  (id) => {
    panelOpen.value = false
    loadMaterial(id)
  }
)

// 현재 성취기준이 속한 과목·단원 (뒤로 가기 링크와 이전/다음 목록 계산에 함께 사용)
const currentLocation = computed(() => {
  for (const subject of allSubjects.value) {
    const unit = subject.units.find((u) =>
      u.standards.some((s) => s.standard_id === props.standardId)
    )
    if (unit) return { subject, unit }
  }
  return null
})

// 같은 "과목" 안에서 실제 학습자료가 있는 성취기준을, 단원 경계를 넘어 전부 순서대로 이어붙인 목록
const subjectStandards = computed(() => {
  const subject = currentLocation.value?.subject
  if (!subject) return []
  return subject.units
    .flatMap((unit) => unit.standards)
    .filter((s) => materialsById.value.has(s.standard_id))
})

const currentIndex = computed(() =>
  subjectStandards.value.findIndex((s) => s.standard_id === props.standardId)
)

const canCopyCode = computed(
  () =>
    isTeacher() ||
    isAdmin() ||
    COPY_ALLOWED_SUBJECTS.includes(currentLocation.value?.subject?.교과)
)
const copiedIndex = ref(null)

const prevMaterial = computed(() => {
  const i = currentIndex.value
  if (i <= 0) return null
  return materialsById.value.get(subjectStandards.value[i - 1].standard_id)
})

const nextMaterial = computed(() => {
  const i = currentIndex.value
  if (i === -1 || i >= subjectStandards.value.length - 1) return null
  return materialsById.value.get(subjectStandards.value[i + 1].standard_id)
})

const codeSections = computed(() =>
  (material.value?.sections ?? [])
    .map((s, i) => ({ i, heading: s.heading }))
    .filter((s) => material.value.sections[s.i].code)
)

function openPractice(i) {
  activeIndex.value = i
  panelOpen.value = true
}

function clearPractice(i) {
  practiceCode[i] = ''
}

function blockCopy(e) {
  if (!canCopyCode.value) e.preventDefault()
}

function blockContextMenu(e) {
  if (!canCopyCode.value) e.preventDefault()
}

async function copyCode(i, code) {
  try {
    await navigator.clipboard.writeText(code)
  } catch {
    const textarea = document.createElement('textarea')
    textarea.value = code
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
  }
  copiedIndex.value = i
  setTimeout(() => {
    if (copiedIndex.value === i) copiedIndex.value = null
  }, 1500)
}

function sectionTable(s) {
  return parsePipeTable(s.표)
}
</script>

<template>
  <RouterLink
    v-if="currentLocation"
    :to="{
      name: 'material-unit-standards',
      params: { subject: currentLocation.subject.교과, unit: currentLocation.unit.단원 },
    }"
    class="back"
  >
    ← {{ currentLocation.unit.단원 }}
  </RouterLink>
  <RouterLink v-else to="/materials" class="back">← 학습자료</RouterLink>

  <p v-if="loading">불러오는 중…</p>
  <template v-else-if="material">
    <nav class="material-nav">
      <RouterLink
        v-if="prevMaterial"
        :to="`/materials/${prevMaterial.standard_id}`"
        class="nav-link prev"
      >
        <span class="nav-arrow">←</span>
        <span class="nav-text">
          <span class="nav-label">이전 학습자료</span>
          <span class="nav-title">{{ prevMaterial.title }}</span>
        </span>
      </RouterLink>
      <span v-else class="nav-link disabled">
        <span class="nav-arrow">←</span>
        <span class="nav-text"><span class="nav-label">이전 학습자료</span></span>
      </span>

      <RouterLink
        v-if="nextMaterial"
        :to="`/materials/${nextMaterial.standard_id}`"
        class="nav-link next"
      >
        <span class="nav-text">
          <span class="nav-label">다음 학습자료</span>
          <span class="nav-title">{{ nextMaterial.title }}</span>
        </span>
        <span class="nav-arrow">→</span>
      </RouterLink>
      <span v-else class="nav-link disabled next">
        <span class="nav-text"><span class="nav-label">다음 학습자료</span></span>
        <span class="nav-arrow">→</span>
      </span>
    </nav>

    <h1>{{ material.title }}</h1>
    <p class="std-name">[{{ material.standard_id }}] {{ material.성취기준명 }}</p>

    <template v-for="(s, i) in material.sections" :key="i">
      <div v-if="s.advanced && !material.sections[i - 1]?.advanced" class="advanced-divider">
        <span>🔍 심화 학습</span>
      </div>
      <section class="section" :class="{ advanced: s.advanced }">
        <h2>
          {{ s.heading }}
          <span v-if="s.advanced" class="advanced-badge">심화</span>
        </h2>
        <p class="content">{{ s.content }}</p>
        <table v-if="sectionTable(s)" class="section-table">
          <thead>
            <tr>
              <th v-for="(h, hi) in sectionTable(s).headers" :key="hi">{{ h }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, ri) in sectionTable(s).rows" :key="ri">
              <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
        <div v-if="s.image" class="diagram" v-html="s.image"></div>
        <div v-if="s.code" class="code-block-wrap">
          <div class="col-label-row">
            <span class="col-label">📖 예제 코드{{ canCopyCode ? '' : ' (읽기 전용)' }}</span>
            <div class="code-actions">
              <button v-if="canCopyCode" class="copy-btn" @click="copyCode(i, s.code)">
                {{ copiedIndex === i ? '✅ 복사됨' : '📋 코드 복사' }}
              </button>
              <button class="try-btn" @click="openPractice(i)">✏️ 직접 타이핑해보기</button>
            </div>
          </div>
          <pre
            class="code-block"
            :class="{ readonly: !canCopyCode }"
            @copy="blockCopy"
            @contextmenu="blockContextMenu"
          ><code>{{ s.code }}</code></pre>
        </div>
      </section>
    </template>

    <div class="cta-row">
      <RouterLink
        v-if="hasProblems"
        :to="`/problems/category/${material.standard_id}`"
        class="practice-link"
      >
        관련 코딩테스트 문제 풀기 →
      </RouterLink>
      <RouterLink v-if="hasQuestions" :to="`/practice/${material.standard_id}`" class="practice-link">
        관련 평가 문제 풀기 →
      </RouterLink>
    </div>

    <nav class="material-nav bottom">
      <RouterLink
        v-if="prevMaterial"
        :to="`/materials/${prevMaterial.standard_id}`"
        class="nav-link prev"
      >
        <span class="nav-arrow">←</span>
        <span class="nav-text">
          <span class="nav-label">이전 학습자료</span>
          <span class="nav-title">{{ prevMaterial.title }}</span>
        </span>
      </RouterLink>
      <span v-else class="nav-link disabled">
        <span class="nav-arrow">←</span>
        <span class="nav-text"><span class="nav-label">이전 학습자료</span></span>
      </span>

      <RouterLink
        v-if="nextMaterial"
        :to="`/materials/${nextMaterial.standard_id}`"
        class="nav-link next"
      >
        <span class="nav-text">
          <span class="nav-label">다음 학습자료</span>
          <span class="nav-title">{{ nextMaterial.title }}</span>
        </span>
        <span class="nav-arrow">→</span>
      </RouterLink>
      <span v-else class="nav-link disabled next">
        <span class="nav-text"><span class="nav-label">다음 학습자료</span></span>
        <span class="nav-arrow">→</span>
      </span>
    </nav>

    <button
      v-if="codeSections.length && !panelOpen"
      class="fab"
      @click="panelOpen = true"
    >
      ✏️ 직접 타이핑해보기
    </button>

    <div v-if="panelOpen" class="panel-backdrop" @click="panelOpen = false"></div>
    <aside v-if="panelOpen" class="practice-panel">
      <div class="panel-header">
        <select v-model.number="activeIndex" class="panel-select">
          <option v-for="cs in codeSections" :key="cs.i" :value="cs.i">{{ cs.heading }}</option>
        </select>
        <button class="panel-close" @click="panelOpen = false">✕</button>
      </div>
      <div v-if="activeIndex !== null" class="panel-body">
        <div class="col-label-row">
          <span class="col-label">✏️ 직접 타이핑해보기</span>
          <button v-if="practiceCode[activeIndex]" class="clear-btn" @click="clearPractice(activeIndex)">지우기</button>
        </div>
        <CodeEditor
          v-model:code="practiceCode[activeIndex]"
          :no-paste="!canCopyCode"
          placeholder="왼쪽 본문의 예제 코드를 보고 한 줄씩 직접 입력해보세요"
        />
      </div>
    </aside>
  </template>
</template>

<style scoped>
.back {
  display: inline-block;
  color: var(--text-dim);
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 12px;
}

.std-name {
  color: var(--text-dim);
  font-size: 14px;
  margin-bottom: 24px;
}

.material-nav {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.material-nav.bottom {
  margin-top: 32px;
  margin-bottom: 0;
}

.nav-link {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: 10px;
  text-decoration: none;
  color: var(--text);
  min-width: 0;
  transition: border-color 0.15s, background 0.15s;
}

.nav-link.next {
  justify-content: flex-end;
  text-align: right;
}

.nav-link:not(.disabled):hover {
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.nav-link.disabled {
  opacity: 0.4;
  cursor: default;
}

.nav-arrow {
  flex-shrink: 0;
  font-size: 16px;
  color: var(--text-dim);
}

.nav-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.nav-label {
  font-size: 11px;
  color: var(--text-dim);
}

.nav-title {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.section {
  margin-bottom: 28px;
}

.section h2 {
  font-size: 18px;
  font-weight: 400;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section.advanced {
  border-left: 3px solid var(--accent-border);
  padding-left: 16px;
}

.advanced-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 999px;
  color: var(--accent);
  border: 1px solid var(--accent-border);
  background: var(--accent-bg);
  vertical-align: middle;
}

.advanced-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 32px 0 20px;
  font-size: 13px;
  font-weight: 700;
  color: var(--accent);
}

.advanced-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--accent-border);
}

.content {
  white-space: pre-wrap;
  line-height: 1.7;
  margin-bottom: 10px;
}

.diagram {
  margin: 12px 0;
  overflow-x: auto;
}

.diagram :deep(svg) {
  display: block;
  max-width: 100%;
  height: auto;
}

.code-block-wrap {
  margin: 12px 0;
}

.col-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.col-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-dim);
}

.code-actions {
  display: flex;
  gap: 8px;
}

.try-btn,
.copy-btn {
  background: var(--accent-bg);
  border: 1px solid var(--accent-border);
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 6px;
}

.try-btn:hover,
.copy-btn:hover {
  background: var(--accent-border);
}

.clear-btn {
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
  padding: 0 0 6px;
}

.clear-btn:hover {
  color: var(--wrong);
  text-decoration: underline;
}

.code-block {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin: 0;
  overflow-x: auto;
  font-size: 14px;
  line-height: 1.5;
  box-sizing: border-box;
}

.code-block.readonly {
  user-select: none;
  -webkit-user-select: none;
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.practice-link {
  display: inline-block;
  margin-top: 12px;
  padding: 12px 20px;
  background: var(--accent);
  color: white;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
}

.fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 40;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 999px;
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
}

.fab:hover {
  filter: brightness(1.08);
}

.panel-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.25);
  z-index: 45;
}

.practice-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 420px;
  max-width: 92vw;
  background: var(--bg);
  border-left: 1px solid var(--border);
  box-shadow: -8px 0 24px rgba(0, 0, 0, 0.2);
  z-index: 46;
  display: flex;
  flex-direction: column;
  padding: 16px;
  box-sizing: border-box;
  overflow-y: auto;
  animation: slide-in 0.18s ease-out;
}

@keyframes slide-in {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

@media (max-width: 560px) {
  .practice-panel {
    width: 100vw;
    max-width: 100vw;
  }
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
}

.panel-select {
  flex: 1;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 6px;
  border: 1px solid var(--border);
  background: var(--bg-soft);
  color: var(--text-h);
  font-size: 13px;
}

.panel-close {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  width: 32px;
  height: 32px;
  cursor: pointer;
  color: var(--text-dim);
  font-size: 14px;
  flex-shrink: 0;
}

.panel-close:hover {
  color: var(--wrong);
}

.panel-body {
  flex: 1;
}
</style>
