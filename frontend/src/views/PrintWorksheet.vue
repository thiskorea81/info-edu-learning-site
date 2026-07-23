<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'
import { parsePipeTable } from '../utils/markdownTable'

const props = defineProps({
  subject: { type: String, required: true },
  unit: { type: String, required: true },
})

const loading = ref(true)
const standards = ref([]) // [{standard_id, 성취기준명, question_count}]
const materialsById = reactive({}) // standard_id -> material | null
const questionsById = reactive({}) // standard_id -> question[] (교사용 전체 필드 포함)

const mode = ref('student') // 'student' | 'teacher'
const printType = ref('full') // 'full' | 'summary' | 'questions'
const includeAdvanced = ref(false)
const includeSolvingSpace = ref(true)
const selected = ref(new Set())

onMounted(async () => {
  const { data: subjects } = await api.get('/api/subjects')
  const subj = subjects.find((s) => s.교과 === props.subject)
  const unitObj = subj?.units.find((u) => u.단원 === props.unit)
  standards.value = unitObj?.standards ?? []
  selected.value = new Set(standards.value.map((s) => s.standard_id))

  await Promise.all(
    standards.value.map(async (s) => {
      const [matResult, listResult] = await Promise.allSettled([
        api.get(`/api/materials/${s.standard_id}`),
        api.get('/api/questions', { params: { standard_id: s.standard_id } }),
      ])
      materialsById[s.standard_id] = matResult.status === 'fulfilled' ? matResult.value.data : null

      const baseList = listResult.status === 'fulfilled' ? listResult.value.data : []
      // 정답·해설은 교사 전용 단건 조회에서만 내려오므로 문항마다 개별 요청으로 채운다.
      const detailed = await Promise.all(
        baseList.map((q) =>
          api
            .get(`/api/questions/${q.id}/teacher-view`)
            .then((r) => r.data)
            .catch(() => q)
        )
      )
      questionsById[s.standard_id] = detailed
    })
  )
  loading.value = false
})

const includedStandards = computed(() => standards.value.filter((s) => selected.value.has(s.standard_id)))

function visibleSections(material) {
  if (!material) return []
  return includeAdvanced.value ? material.sections : material.sections.filter((sec) => !sec.advanced)
}

function sectionTable(s) {
  return parsePipeTable(s.표)
}

// content 안에서 {{용어}} 빈칸이 포함된 문장/줄만 뽑아 핵심정리용 목록으로 만든다.
function extractClozeSentences(content) {
  if (!content) return []
  const lines = content.split('\n')
  const sentences = []
  for (const line of lines) {
    const parts = line.split(/(?<=[.?!])\s+(?=\S)/)
    for (const part of parts) {
      const t = part.trim()
      if (t.includes('{{')) sentences.push(t)
    }
  }
  return sentences
}

// 성취기준의 학습자료를 소제목 단위로 묶어, 빈칸이 있는 문장만 남긴 핵심정리 목록을 만든다.
function summaryGroups(material) {
  if (!material) return []
  return visibleSections(material)
    .map((s) => ({ heading: s.heading, sentences: extractClozeSentences(s.content) }))
    .filter((g) => g.sentences.length > 0)
}

function isSvgMarkup(image) {
  return image?.trim().startsWith('<svg')
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

// content 안의 {{용어}}를 학생용은 빈칸으로, 교사용은 하이라이트로 렌더링한다.
function renderContent(text) {
  if (!text) return ''
  const parts = text.split(/\{\{(.+?)\}\}/g)
  return parts
    .map((part, i) => {
      if (i % 2 === 0) return escapeHtml(part)
      const term = escapeHtml(part)
      if (mode.value === 'teacher') {
        return `<mark class="cloze-highlight">${term}</mark>`
      }
      return `<span class="cloze-blank" style="min-width:${Math.max(part.length, 2)}ch"></span>`
    })
    .join('')
}

const printTypeLabel = computed(() => {
  if (printType.value === 'summary') return '핵심정리 빈칸 채우기'
  if (printType.value === 'questions') return '문제만'
  return null
})

function toggleAll(checked) {
  selected.value = checked ? new Set(standards.value.map((s) => s.standard_id)) : new Set()
}

function toggleOne(id) {
  const next = new Set(selected.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selected.value = next
}

function doPrint() {
  window.print()
}
</script>

<template>
  <div class="no-print">
    <RouterLink :to="{ name: 'unit-questions', params: { subject, unit } }" class="back">
      ← {{ unit }}
    </RouterLink>
    <h1>인쇄용 학습지</h1>
    <p v-if="loading">자료를 불러오는 중…</p>

    <div v-else class="toolbar">
      <div class="toolbar-row">
        <span class="toolbar-label">버전</span>
        <label><input type="radio" value="student" v-model="mode" /> 학생용 (정답·해설 별도 수록)</label>
        <label><input type="radio" value="teacher" v-model="mode" /> 교사용 (정답·해설 문항 아래 표시)</label>
      </div>
      <div class="toolbar-row">
        <span class="toolbar-label">구성</span>
        <label><input type="radio" value="full" v-model="printType" /> 전체 (학습자료 + 평가문항)</label>
        <label><input type="radio" value="summary" v-model="printType" /> 핵심정리 빈칸 채우기 (성취기준별 1장)</label>
        <label><input type="radio" value="questions" v-model="printType" /> 문제만 출력</label>
      </div>
      <div class="toolbar-row">
        <label><input type="checkbox" v-model="includeAdvanced" /> 심화 학습 내용 포함</label>
        <label><input type="checkbox" v-model="includeSolvingSpace" /> 풀이 공간 포함</label>
      </div>
      <div class="toolbar-row standards-picker">
        <span class="toolbar-label">포함할 성취기준</span>
        <label><input type="checkbox" :checked="selected.size === standards.length" @change="toggleAll($event.target.checked)" /> 전체</label>
        <label v-for="s in standards" :key="s.standard_id">
          <input
            type="checkbox"
            :checked="selected.has(s.standard_id)"
            @change="toggleOne(s.standard_id)"
          />
          [{{ s.standard_id }}]
        </label>
      </div>
      <button class="print-btn" @click="doPrint">🖨️ 인쇄하기</button>
    </div>
  </div>

  <div v-if="!loading" class="worksheet">
    <header class="worksheet-header">
      <h1>{{ subject }} — {{ unit }}</h1>
      <p class="mode-tag">
        {{ mode === 'teacher' ? '[교사용]' : '[학생용]' }}<template v-if="printTypeLabel"> · [{{ printTypeLabel }}]</template>
      </p>
      <p v-if="printType !== 'questions'" class="cloze-note">
        {{
          mode === 'teacher'
            ? '노란색으로 표시된 부분이 학생용 학습지에서는 빈칸으로 제시됩니다.'
            : '밑줄 친 빈칸에 알맞은 핵심 용어를 채워 넣으며 학습하세요.'
        }}
      </p>
      <div v-if="mode === 'student'" class="name-fields">
        <span>학번: ______________</span>
        <span>이름: ______________</span>
        <span>날짜: ______________</span>
      </div>
    </header>

    <section v-for="std in includedStandards" :key="std.standard_id" class="standard-block">
      <h2>[{{ std.standard_id }}] {{ materialsById[std.standard_id]?.title ?? std.성취기준명 }}</h2>
      <p class="std-desc">{{ std.성취기준명 }}</p>

      <template v-if="printType === 'summary'">
        <div v-if="summaryGroups(materialsById[std.standard_id]).length" class="summary">
          <template v-for="(g, gi) in summaryGroups(materialsById[std.standard_id])" :key="gi">
            <h3>{{ g.heading }}</h3>
            <ul class="summary-list">
              <li v-for="(sentence, si) in g.sentences" :key="si" v-html="renderContent(sentence)"></li>
            </ul>
          </template>
        </div>
        <p v-else class="no-material">(이 성취기준에는 핵심정리로 뽑을 학습자료가 아직 없습니다.)</p>
      </template>

      <template v-if="printType === 'full'">
        <div v-if="materialsById[std.standard_id]" class="material">
          <template v-for="(s, i) in visibleSections(materialsById[std.standard_id])" :key="i">
            <h3>{{ s.heading }}</h3>
            <p class="content" v-html="renderContent(s.content)"></p>
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
            <pre v-if="s.code" class="code-block"><code>{{ s.code }}</code></pre>
          </template>
        </div>
        <p v-else class="no-material">(이 성취기준에는 아직 학습자료가 없습니다.)</p>
      </template>

      <div
        v-if="printType !== 'summary' && questionsById[std.standard_id]?.length"
        class="questions"
        :class="{ 'page-split': printType === 'full' && materialsById[std.standard_id] }"
      >
        <div v-for="(q, qi) in questionsById[std.standard_id]" :key="q.id" class="question-block">
          <p class="q-stem"><span class="q-num">{{ qi + 1 }}.</span> {{ q.문제 }}</p>

          <table v-if="parsePipeTable(q.표)" class="section-table">
            <thead>
              <tr>
                <th v-for="(h, hi) in parsePipeTable(q.표).headers" :key="hi">{{ h }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in parsePipeTable(q.표).rows" :key="ri">
                <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="q.이미지 && isSvgMarkup(q.이미지)" class="diagram" v-html="q.이미지"></div>
          <img v-else-if="q.이미지" :src="q.이미지" class="q-image" alt="문제 이미지" />
          <pre v-if="q.코드" class="code-block"><code>{{ q.코드 }}</code></pre>

          <ol class="choices">
            <li v-for="(text, num) in q.선택지" :key="num">{{ text }}</li>
          </ol>

          <div v-if="includeSolvingSpace" class="solving-space">
            <span class="solving-label">풀이</span>
          </div>

          <div v-if="mode === 'teacher'" class="answer-box">
            <strong>정답: {{ q.정답 }}번</strong>
            <p v-if="q.해설">{{ q.해설 }}</p>
          </div>
        </div>
      </div>
    </section>

    <section v-if="mode === 'student' && printType !== 'summary'" class="answer-key">
      <h2>정답 및 해설</h2>
      <div v-for="std in includedStandards" :key="std.standard_id" class="answer-key-block">
        <h3>[{{ std.standard_id }}] {{ materialsById[std.standard_id]?.title ?? std.성취기준명 }}</h3>
        <table class="section-table">
          <thead>
            <tr>
              <th>번호</th>
              <th>정답</th>
              <th>해설</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(q, qi) in questionsById[std.standard_id]" :key="q.id">
              <td>{{ qi + 1 }}</td>
              <td>{{ q.정답 }}번</td>
              <td>{{ q.해설 }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.back {
  display: inline-block;
  color: var(--text-dim);
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 12px;
}

.toolbar {
  margin: 16px 0 24px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-soft);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toolbar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  font-size: 14px;
}

.toolbar-label {
  font-weight: 600;
  color: var(--text-dim);
  font-size: 13px;
}

.standards-picker label {
  font-family: var(--mono);
  font-size: 13px;
}

.print-btn {
  align-self: flex-start;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 22px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

/* ---- 인쇄물 본문: 화면/인쇄 모두 흰 종이 위 검은 글씨로 고정(다크 모드 영향 안 받도록) ---- */
.worksheet {
  background: #ffffff;
  color: #18181b;
  padding: 24px;
  border: 1px solid var(--border);
  border-radius: 10px;
  max-width: 860px;
}

.worksheet-header {
  border-bottom: 2px solid #18181b;
  padding-bottom: 12px;
  margin-bottom: 20px;
}

.worksheet-header h1 {
  color: #18181b;
  font-size: 22px;
  margin: 0 0 4px;
}

.mode-tag {
  font-weight: 700;
  color: #18181b;
  margin: 0 0 10px;
}

.name-fields {
  display: flex;
  gap: 28px;
  font-size: 14px;
  color: #18181b;
}

.cloze-note {
  font-size: 12px;
  color: #52525b;
  margin: 0 0 10px;
}

.standard-block {
  margin-bottom: 36px;
}

.standard-block h2 {
  color: #18181b;
  font-size: 18px;
  border-bottom: 1px solid #d4d4d8;
  padding-bottom: 6px;
}

.std-desc {
  color: #52525b;
  font-size: 13px;
  margin-bottom: 14px;
}

.material h3 {
  color: #18181b;
  font-size: 15px;
  font-weight: 400;
  margin: 16px 0 6px;
  break-after: avoid-page;
  page-break-after: avoid;
}

.content {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 14px;
  margin: 0 0 8px;
}

.content :deep(.cloze-blank),
.summary-list :deep(.cloze-blank) {
  display: inline-block;
  border-bottom: 1.5px solid #18181b;
  min-height: 1em;
  vertical-align: baseline;
  margin: 0 2px;
}

.content :deep(mark.cloze-highlight),
.summary-list :deep(mark.cloze-highlight) {
  background: #fef08a;
  color: #18181b;
  padding: 0 3px;
  border-radius: 2px;
  font-weight: 700;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

.summary h3 {
  color: #18181b;
  font-size: 15px;
  font-weight: 400;
  margin: 14px 0 4px;
  break-after: avoid-page;
  page-break-after: avoid;
}

.summary-list {
  margin: 0 0 6px;
  padding-left: 20px;
  font-size: 14px;
  line-height: 1.9;
}

.summary-list li {
  break-inside: avoid;
}

.section-table {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
  font-size: 13px;
}

.section-table th,
.section-table td {
  border: 1px solid #a1a1aa;
  padding: 6px 8px;
  text-align: left;
}

.diagram {
  margin: 10px 0;
  overflow-x: auto;
}

.diagram :deep(svg) {
  display: block;
  max-width: 100%;
  height: auto;
}

.code-block {
  background: #f4f4f5;
  border: 1px solid #d4d4d8;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 13px;
  overflow-x: auto;
  margin: 8px 0;
}

.no-material {
  color: #a1a1aa;
  font-size: 13px;
  font-style: italic;
}

.question-block {
  margin: 18px 0;
  break-inside: avoid;
}

.q-stem {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 6px;
  white-space: pre-wrap;
}

.q-num {
  margin-right: 4px;
}

.q-image {
  max-width: 100%;
  margin: 8px 0;
}

.choices {
  list-style: decimal;
  margin: 6px 0 6px 22px;
  padding: 0;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.solving-space {
  position: relative;
  margin: 10px 0 4px;
  min-height: 80px;
  border: 1px dashed #a1a1aa;
  border-radius: 4px;
}

.solving-label {
  position: absolute;
  top: 4px;
  left: 8px;
  font-size: 11px;
  color: #a1a1aa;
}

.answer-box {
  margin-top: 8px;
  padding: 8px 12px;
  border-left: 3px solid #dc2626;
  background: #fef2f2;
  color: #b91c1c;
  font-size: 13px;
}

.answer-box p {
  margin: 4px 0 0;
  color: #b91c1c;
}

.answer-key {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 2px solid #18181b;
  break-before: page;
}

.answer-key h2 {
  color: #18181b;
}

.answer-key-block {
  margin-bottom: 20px;
}

.answer-key-block h3 {
  font-size: 14px;
  color: #18181b;
}

@media print {
  .no-print {
    display: none !important;
  }

  .worksheet {
    border: none;
    border-radius: 0;
    max-width: none;
    padding: 0;
  }

  .standard-block {
    break-before: page;
  }

  .standard-block:first-of-type {
    break-before: auto;
  }

  /* 학습자료 내용과 평가문항은 항상 페이지를 분리한다 */
  .questions.page-split {
    break-before: page;
  }
}
</style>
