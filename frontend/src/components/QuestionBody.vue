<script setup>
import { computed } from 'vue'
import { parsePipeTable } from '../utils/markdownTable'

const props = defineProps({
  question: { type: Object, required: true },
})

const table = computed(() => parsePipeTable(props.question.표))
</script>

<template>
  <div class="body">
    <p class="stem">{{ question.문제 }}</p>

    <table v-if="table">
      <thead>
        <tr>
          <th v-for="(h, i) in table.headers" :key="i">{{ h }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, ri) in table.rows" :key="ri">
          <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
        </tr>
      </tbody>
    </table>

    <img v-if="question.이미지" :src="question.이미지" class="question-image" alt="문제 이미지" />

    <pre v-if="question.코드" class="code-block"><code>{{ question.코드 }}</code></pre>
    <div v-if="question.실행결과" class="run-result-label">
      실행 결과:
      <pre class="code-block inline"><code>{{ question.실행결과 }}</code></pre>
    </div>
  </div>
</template>

<style scoped>
.stem {
  font-size: 17px;
  color: var(--text-h);
  margin-bottom: 4px;
  white-space: pre-wrap;
}

.code-block {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px 14px;
  overflow-x: auto;
  font-size: 14px;
  margin: 10px 0;
}

.question-image {
  max-width: 100%;
  border-radius: 6px;
  margin: 10px 0;
}

.run-result-label {
  font-size: 14px;
  color: var(--text-dim);
}
</style>
