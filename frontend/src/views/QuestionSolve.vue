<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import QuestionBody from '../components/QuestionBody.vue'
import CodeEditor from '../components/CodeEditor.vue'

const props = defineProps({ id: { type: String, required: true } })
const router = useRouter()

const question = ref(null)
const siblingIds = ref([])
const selected = ref(null)
const result = ref(null)
const submitting = ref(false)
const editableCode = ref('')

const currentIndex = computed(() => siblingIds.value.indexOf(props.id))
const prevId = computed(() =>
  currentIndex.value > 0 ? siblingIds.value[currentIndex.value - 1] : null
)
const nextId = computed(() =>
  currentIndex.value >= 0 && currentIndex.value < siblingIds.value.length - 1
    ? siblingIds.value[currentIndex.value + 1]
    : null
)

async function load() {
  question.value = null
  result.value = null
  selected.value = null
  const { data } = await api.get(`/api/questions/${props.id}`)
  question.value = data
  editableCode.value = data.코드 ?? ''

  if (siblingIds.value.length === 0) {
    const { data: list } = await api.get('/api/questions', { params: { exam_id: data.exam_id } })
    siblingIds.value = list.map((q) => q.id)
  }
}

watch(() => props.id, load, { immediate: true })

async function submit() {
  if (selected.value === null) return
  submitting.value = true
  const { data } = await api.post('/api/attempts', {
    question_id: props.id,
    selected: selected.value,
  })
  result.value = data
  submitting.value = false
}

function retry() {
  result.value = null
  selected.value = null
}

function goto(id) {
  if (id) router.push(`/questions/${id}`)
}
</script>

<template>
  <div v-if="question" class="solve">
    <div class="meta">
      <span>{{ question.내용영역 }}</span>
      <span class="sep">·</span>
      <span>{{ question.standard_id }}</span>
    </div>

    <QuestionBody :question="question" />

    <CodeEditor v-if="question.코드 && question.언어 === 'python'" v-model:code="editableCode" />

    <ul class="choices">
      <li v-for="(text, num) in question.선택지" :key="num">
        <label
          class="choice"
          :class="{
            selected: String(selected) === num && !result,
            correct: result && Number(num) === result.correct_answer,
            wrong: result && String(selected) === num && !result.is_correct,
          }"
        >
          <input
            type="radio"
            :name="question.id"
            :value="Number(num)"
            v-model="selected"
            :disabled="!!result"
          />
          <span class="num">{{ num }}</span>
          <span>{{ text }}</span>
        </label>
      </li>
    </ul>

    <div class="actions">
      <button v-if="!result" class="submit" :disabled="selected === null || submitting" @click="submit">
        제출
      </button>
      <button v-else class="retry" @click="retry">다시 풀기</button>
    </div>

    <div v-if="result" class="result-banner" :class="result.is_correct ? 'ok' : 'bad'">
      <strong>{{ result.is_correct ? '정답입니다!' : '오답입니다.' }}</strong>
      <span v-if="!result.is_correct">정답: {{ result.correct_answer }}번</span>
      <p v-if="result.해설" class="explain">{{ result.해설 }}</p>
    </div>

    <nav class="pager">
      <button :disabled="!prevId" @click="goto(prevId)">← 이전 문제</button>
      <span>{{ currentIndex + 1 }} / {{ siblingIds.length }}</span>
      <button :disabled="!nextId" @click="goto(nextId)">다음 문제 →</button>
    </nav>
  </div>
</template>

<style scoped>
.meta {
  font-size: 13px;
  color: var(--text-dim);
  margin-bottom: 8px;
}

.sep {
  margin: 0 6px;
}

.choices {
  list-style: none;
  padding: 0;
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.choice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  cursor: pointer;
}

.choice.selected {
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.choice.correct {
  border-color: var(--correct);
  background: var(--correct-bg);
}

.choice.wrong {
  border-color: var(--wrong);
  background: var(--wrong-bg);
}

.choice .num {
  font-weight: 600;
  color: var(--text-dim);
  min-width: 16px;
}

.actions {
  margin: 12px 0;
}

.submit,
.retry {
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 10px 22px;
  font-weight: 600;
  cursor: pointer;
}

.submit:disabled {
  opacity: 0.5;
  cursor: default;
}

.result-banner {
  border-radius: 8px;
  padding: 14px 16px;
  margin: 12px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.result-banner.ok {
  background: var(--correct-bg);
  color: var(--correct);
}

.result-banner.bad {
  background: var(--wrong-bg);
  color: var(--wrong);
}

.explain {
  color: var(--text);
  font-size: 14px;
}

.pager {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 24px;
  border-top: 1px solid var(--border);
  padding-top: 16px;
}

.pager button {
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 14px;
  cursor: pointer;
  color: var(--text);
}

.pager button:disabled {
  opacity: 0.4;
  cursor: default;
}

.pager span {
  color: var(--text-dim);
  font-size: 14px;
}
</style>
