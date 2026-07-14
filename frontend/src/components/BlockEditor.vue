<script setup>
import { ref } from 'vue'
import api from '../api'
import { parsePipeTable } from '../utils/markdownTable'
import CodeEditor from './CodeEditor.vue'

const blocks = defineModel({ type: Array, default: () => [] })

defineProps({
  readonly: { type: Boolean, default: false },
})

const uploadingIndex = ref(null)
const uploadError = ref('')

function addBlock(type) {
  blocks.value = [...blocks.value, { type, value: '', language: type === 'code' ? 'python' : null }]
}

function removeBlock(i) {
  blocks.value = blocks.value.filter((_, idx) => idx !== i)
}

function moveBlock(i, dir) {
  const j = i + dir
  if (j < 0 || j >= blocks.value.length) return
  const next = [...blocks.value]
  ;[next[i], next[j]] = [next[j], next[i]]
  blocks.value = next
}

function updateBlockValue(i, value) {
  const next = [...blocks.value]
  next[i] = { ...next[i], value }
  blocks.value = next
}

async function onImageSelected(i, event) {
  const file = event.target.files?.[0]
  if (!file) return
  uploadError.value = ''
  uploadingIndex.value = i
  try {
    const form = new FormData()
    form.append('file', file)
    const { data } = await api.post('/api/uploads', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    updateBlockValue(i, data.url)
  } catch (e) {
    uploadError.value = e.response?.data?.detail || '이미지 업로드에 실패했습니다.'
  } finally {
    uploadingIndex.value = null
    event.target.value = ''
  }
}
</script>

<template>
  <div class="block-editor">
    <div v-for="(block, i) in blocks" :key="i" class="block" :class="`block-${block.type}`">
      <div v-if="!readonly" class="block-toolbar">
        <span class="block-type">{{
          { text: '텍스트', table: '표', code: '코드', image: '이미지' }[block.type]
        }}</span>
        <button type="button" :disabled="i === 0" @click="moveBlock(i, -1)">↑</button>
        <button type="button" :disabled="i === blocks.length - 1" @click="moveBlock(i, 1)">↓</button>
        <button type="button" class="remove" @click="removeBlock(i)">삭제</button>
      </div>

      <!-- 텍스트 -->
      <template v-if="block.type === 'text'">
        <textarea
          v-if="!readonly"
          :value="block.value"
          rows="4"
          placeholder="내용을 입력하세요"
          @input="updateBlockValue(i, $event.target.value)"
        ></textarea>
        <p v-else class="text-block">{{ block.value }}</p>
      </template>

      <!-- 표 -->
      <template v-else-if="block.type === 'table'">
        <template v-if="!readonly">
          <textarea
            :value="block.value"
            rows="3"
            placeholder="| 열1 | 열2 |&#10;| :--- | :--- |&#10;| 값1 | 값2 |"
            class="mono"
            @input="updateBlockValue(i, $event.target.value)"
          ></textarea>
          <p class="hint">파이프(|)로 구분한 표 형식으로 입력하세요. 첫 줄은 제목, 둘째 줄은 구분선입니다.</p>
        </template>
        <table v-if="parsePipeTable(block.value)" class="preview-table">
          <thead>
            <tr>
              <th v-for="(h, hi) in parsePipeTable(block.value).headers" :key="hi">{{ h }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, ri) in parsePipeTable(block.value).rows" :key="ri">
              <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
            </tr>
          </tbody>
        </table>
      </template>

      <!-- 코드 -->
      <template v-else-if="block.type === 'code'">
        <CodeEditor
          v-if="!readonly"
          :code="block.value"
          @update:code="updateBlockValue(i, $event)"
          placeholder="코드를 입력하세요"
        />
        <pre v-else class="code-block"><code>{{ block.value }}</code></pre>
      </template>

      <!-- 이미지 -->
      <template v-else-if="block.type === 'image'">
        <template v-if="!readonly">
          <input type="file" accept="image/png,image/jpeg,image/gif,image/webp" @change="onImageSelected(i, $event)" />
          <p v-if="uploadingIndex === i" class="hint">업로드 중…</p>
        </template>
        <img v-if="block.value" :src="block.value" class="preview-image" alt="첨부 이미지" />
      </template>
    </div>

    <p v-if="uploadError" class="error">{{ uploadError }}</p>

    <div v-if="!readonly" class="add-buttons">
      <button type="button" @click="addBlock('text')">+ 텍스트</button>
      <button type="button" @click="addBlock('table')">+ 표</button>
      <button type="button" @click="addBlock('code')">+ 코드</button>
      <button type="button" @click="addBlock('image')">+ 이미지</button>
    </div>

    <p v-if="!blocks.length && readonly" class="empty">작성된 내용이 없습니다.</p>
  </div>
</template>

<style scoped>
.block-editor {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.block {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
}

.block-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.block-type {
  font-size: 11px;
  color: var(--text-dim);
  font-weight: 600;
  margin-right: auto;
}

.block-toolbar button {
  padding: 3px 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: none;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
}

.block-toolbar button:disabled {
  opacity: 0.4;
  cursor: default;
}

.block-toolbar button.remove {
  color: var(--wrong);
  border-color: var(--wrong);
}

textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
  color: var(--text-h);
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
}

textarea.mono {
  font-family: var(--mono);
  font-size: 13px;
}

.hint {
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 6px;
}

.text-block {
  white-space: pre-wrap;
  line-height: 1.6;
}

.preview-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  font-size: 13px;
}

.preview-table th,
.preview-table td {
  border: 1px solid var(--border);
  padding: 6px 10px;
  text-align: left;
}

.preview-table th {
  background: var(--bg-soft);
}

.code-block {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
  overflow-x: auto;
  margin: 0;
}

.preview-image {
  max-width: 100%;
  border-radius: 6px;
  margin-top: 8px;
}

.add-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.add-buttons button {
  padding: 8px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: none;
  color: var(--text);
  font-size: 13px;
  cursor: pointer;
}

.add-buttons button:hover {
  border-color: var(--accent-border);
  color: var(--accent);
}

.error {
  color: var(--wrong);
  font-size: 13px;
}

.empty {
  color: var(--text-dim);
  font-size: 13px;
}
</style>
