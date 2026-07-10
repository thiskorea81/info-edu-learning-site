<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import CodeEditor from '../components/CodeEditor.vue'

const props = defineProps({
  standardId: { type: String, required: true },
})

const material = ref(null)
const loading = ref(true)
const practiceCode = reactive({})

const panelOpen = ref(false)
const activeIndex = ref(null)

onMounted(async () => {
  const { data } = await api.get(`/api/materials/${props.standardId}`)
  material.value = data
  data.sections.forEach((s, i) => {
    if (s.code) practiceCode[i] = ''
  })
  const first = data.sections.findIndex((s) => s.code)
  if (first !== -1) activeIndex.value = first
  loading.value = false
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
  e.preventDefault()
}
</script>

<template>
  <RouterLink to="/materials" class="back">← 학습자료</RouterLink>

  <p v-if="loading">불러오는 중…</p>
  <template v-else-if="material">
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
        <div v-if="s.image" class="diagram" v-html="s.image"></div>
        <div v-if="s.code" class="code-block-wrap">
          <div class="col-label-row">
            <span class="col-label">📖 예제 코드 (읽기 전용)</span>
            <button class="try-btn" @click="openPractice(i)">✏️ 직접 타이핑해보기</button>
          </div>
          <pre class="code-block readonly" @copy="blockCopy" @contextmenu.prevent><code>{{ s.code }}</code></pre>
        </div>
      </section>
    </template>

    <RouterLink :to="`/problems/category/${material.standard_id}`" class="practice-link">
      관련 코딩테스트 문제 풀기 →
    </RouterLink>

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
          no-paste
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

.section {
  margin-bottom: 28px;
}

.section h2 {
  font-size: 18px;
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

.try-btn {
  background: var(--accent-bg);
  border: 1px solid var(--accent-border);
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 6px;
}

.try-btn:hover {
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

.code-block.readonly {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin: 0;
  overflow-x: auto;
  font-size: 14px;
  line-height: 1.5;
  box-sizing: border-box;
  user-select: none;
  -webkit-user-select: none;
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
