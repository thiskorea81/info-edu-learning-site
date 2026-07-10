<script setup>
import { onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import CodeEditor from '../components/CodeEditor.vue'

const props = defineProps({
  standardId: { type: String, required: true },
})

const material = ref(null)
const loading = ref(true)
const practiceCode = reactive({})

onMounted(async () => {
  const { data } = await api.get(`/api/materials/${props.standardId}`)
  material.value = data
  data.sections.forEach((s, i) => {
    if (s.code) practiceCode[i] = ''
  })
  loading.value = false
})

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
        <div v-if="s.code" class="code-pair">
          <div class="code-col">
            <span class="col-label">📖 예제 코드 (읽기 전용)</span>
            <pre class="code-block readonly" @copy="blockCopy" @contextmenu.prevent><code>{{ s.code }}</code></pre>
          </div>
          <div class="code-col">
            <div class="col-label-row">
              <span class="col-label">✏️ 직접 타이핑해보기</span>
              <button v-if="practiceCode[i]" class="clear-btn" @click="clearPractice(i)">지우기</button>
            </div>
            <CodeEditor
              v-model:code="practiceCode[i]"
              no-paste
              placeholder="왼쪽 예제 코드를 보고 한 줄씩 직접 입력해보세요"
            />
          </div>
        </div>
      </section>
    </template>

    <RouterLink :to="`/problems/category/${material.standard_id}`" class="practice-link">
      관련 코딩테스트 문제 풀기 →
    </RouterLink>
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

.code-pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin: 12px 0;
}

@media (max-width: 720px) {
  .code-pair {
    grid-template-columns: 1fr;
  }
}

.code-col {
  min-width: 0;
}

.col-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.col-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-dim);
  margin-bottom: 6px;
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
  height: 100%;
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
</style>
