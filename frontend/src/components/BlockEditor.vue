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

const BLOCK_LABEL = { text: '텍스트', table: '표', code: '코드', image: '이미지' }

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

function autoResize(el) {
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
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
        <span class="block-type">{{ BLOCK_LABEL[block.type] }}</span>
        <button type="button" :disabled="i === 0" @click="moveBlock(i, -1)">↑</button>
        <button type="button" :disabled="i === blocks.length - 1" @click="moveBlock(i, 1)">↓</button>
        <button type="button" class="remove" @click="removeBlock(i)">삭제</button>
      </div>

      <!-- 텍스트: 박스 없이 본문처럼 흐르는 문단 -->
      <template v-if="block.type === 'text'">
        <textarea
          v-if="!readonly"
          :ref="(el) => autoResize(el)"
          :value="block.value"
          rows="1"
          class="prose-input"
          placeholder="내용을 입력하세요…"
          @input="
            updateBlockValue(i, $event.target.value);
            autoResize($event.target)
          "
        ></textarea>
        <p v-else class="text-block">{{ block.value }}</p>
      </template>

      <!-- 표 -->
      <template v-else-if="block.type === 'table'">
        <div class="embed">
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
        </div>
      </template>

      <!-- 코드 -->
      <template v-else-if="block.type === 'code'">
        <div class="embed">
          <CodeEditor
            v-if="!readonly"
            :code="block.value"
            @update:code="updateBlockValue(i, $event)"
            placeholder="코드를 입력하세요"
          />
          <pre v-else class="code-block"><code>{{ block.value }}</code></pre>
        </div>
      </template>

      <!-- 이미지 -->
      <template v-else-if="block.type === 'image'">
        <div class="embed">
          <template v-if="!readonly">
            <label class="file-label">
              <input
                type="file"
                accept="image/png,image/jpeg,image/gif,image/webp"
                @change="onImageSelected(i, $event)"
              />
              {{ block.value ? '이미지 바꾸기' : '이미지 선택' }}
            </label>
            <p v-if="uploadingIndex === i" class="hint">업로드 중…</p>
          </template>
          <img v-if="block.value" :src="block.value" class="preview-image" alt="첨부 이미지" />
        </div>
      </template>
    </div>

    <p v-if="uploadError" class="error">{{ uploadError }}</p>

    <div v-if="!readonly" class="add-bar">
      <span class="add-label">추가</span>
      <button type="button" @click="addBlock('text')">텍스트</button>
      <button type="button" @click="addBlock('table')">표</button>
      <button type="button" @click="addBlock('code')">코드</button>
      <button type="button" @click="addBlock('image')">이미지</button>
    </div>

    <p v-if="!blocks.length && readonly" class="empty">작성된 내용이 없습니다.</p>
  </div>
</template>

<style scoped>
.block-editor {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.block {
  position: relative;
}

.block-toolbar {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  opacity: 0;
  transition: opacity 0.15s;
}

.block:hover .block-toolbar,
.block:focus-within .block-toolbar {
  opacity: 1;
}

.block-type {
  font-size: 11px;
  color: var(--text-dim);
  font-weight: 600;
  margin-right: auto;
}

.block-toolbar button {
  padding: 2px 7px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: none;
  color: var(--text-dim);
  font-size: 11px;
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

/* 텍스트: 테두리 없이 본문처럼 */
.prose-input {
  width: 100%;
  border: none;
  background: transparent;
  color: var(--text-h);
  font-size: 16px;
  line-height: 1.8;
  font-family: inherit;
  resize: none;
  overflow: hidden;
  padding: 0;
  box-sizing: border-box;
}

.prose-input:focus {
  outline: none;
}

.text-block {
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 16px;
}

/* 표/코드/이미지: 굵은 박스 대신 왼쪽 강조선으로 가볍게 구분 */
.embed {
  border-left: 3px solid var(--border);
  padding: 4px 0 4px 14px;
}

textarea.mono {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
  color: var(--text-h);
  font-family: var(--mono);
  font-size: 13px;
  resize: vertical;
  box-sizing: border-box;
}

.hint {
  font-size: 12px;
  color: var(--text-dim);
  margin-top: 6px;
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

.file-label {
  display: inline-block;
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 13px;
  color: var(--text);
  cursor: pointer;
}

.file-label input {
  display: none;
}

.preview-image {
  display: block;
  max-width: 100%;
  border-radius: 6px;
  margin-top: 10px;
}

.add-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.add-label {
  font-size: 12px;
  color: var(--text-dim);
  margin-right: 4px;
}

.add-bar button {
  padding: 5px 12px;
  border: 1px dashed var(--border);
  border-radius: 999px;
  background: none;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
}

.add-bar button:hover {
  border-style: solid;
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
