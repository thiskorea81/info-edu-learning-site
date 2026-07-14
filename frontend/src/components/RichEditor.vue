<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import { Table } from '@tiptap/extension-table'
import TableRow from '@tiptap/extension-table-row'
import TableHeader from '@tiptap/extension-table-header'
import TableCell from '@tiptap/extension-table-cell'
import Placeholder from '@tiptap/extension-placeholder'
import api from '../api'

const content = defineModel({
  type: Object,
  default: () => ({ type: 'doc', content: [{ type: 'paragraph' }] }),
})

const EMPTY_DOC = { type: 'doc', content: [{ type: 'paragraph' }] }

const props = defineProps({
  readonly: { type: Boolean, default: false },
})

function isEmptyDoc(doc) {
  if (!doc || !Array.isArray(doc.content)) return true
  return doc.content.every((node) => !node.content || node.content.length === 0)
}

const uploading = ref(false)
const uploadError = ref('')

const editor = useEditor({
  content: content.value?.type ? content.value : EMPTY_DOC,
  editable: !props.readonly,
  extensions: [
    StarterKit,
    Image,
    Table.configure({ resizable: false }),
    TableRow,
    TableHeader,
    TableCell,
    Placeholder.configure({ placeholder: '내용을 입력하세요…' }),
  ],
  onUpdate: ({ editor: ed }) => {
    content.value = ed.getJSON()
  },
})

watch(
  () => content.value,
  (next) => {
    if (!editor.value) return
    const current = JSON.stringify(editor.value.getJSON())
    if (current !== JSON.stringify(next)) {
      editor.value.commands.setContent(next?.type ? next : EMPTY_DOC, { emitUpdate: false })
    }
  }
)

watch(
  () => props.readonly,
  (next) => {
    editor.value?.setEditable(!next)
  }
)

onBeforeUnmount(() => {
  editor.value?.destroy()
})

const showEmpty = computed(() => props.readonly && isEmptyDoc(content.value))

function insertTable() {
  editor.value?.chain().focus().insertTable({ rows: 2, cols: 2, withHeaderRow: true }).run()
}

function insertImage() {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/png,image/jpeg,image/gif,image/webp'
  input.onchange = async () => {
    const file = input.files?.[0]
    if (!file) return
    uploadError.value = ''
    uploading.value = true
    try {
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post('/api/uploads', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      editor.value?.chain().focus().setImage({ src: data.url }).run()
    } catch (e) {
      uploadError.value = e.response?.data?.detail || '이미지 업로드에 실패했습니다.'
    } finally {
      uploading.value = false
    }
  }
  input.click()
}
</script>

<template>
  <div class="rich-editor">
    <div v-if="!readonly && editor" class="toolbar">
      <button
        type="button"
        :class="{ active: editor.isActive('bold') }"
        @click="editor.chain().focus().toggleBold().run()"
      >
        <b>B</b>
      </button>
      <button
        type="button"
        :class="{ active: editor.isActive('italic') }"
        @click="editor.chain().focus().toggleItalic().run()"
      >
        <i>I</i>
      </button>
      <button
        type="button"
        :class="{ active: editor.isActive('heading', { level: 2 }) }"
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
      >
        제목
      </button>
      <button
        type="button"
        :class="{ active: editor.isActive('bulletList') }"
        @click="editor.chain().focus().toggleBulletList().run()"
      >
        목록
      </button>
      <span class="sep"></span>
      <button type="button" @click="insertTable">표</button>
      <button
        type="button"
        :class="{ active: editor.isActive('codeBlock') }"
        @click="editor.chain().focus().toggleCodeBlock().run()"
      >
        코드
      </button>
      <button type="button" :disabled="uploading" @click="insertImage">
        {{ uploading ? '업로드 중…' : '이미지' }}
      </button>
      <template v-if="editor.isActive('table')">
        <span class="sep"></span>
        <button type="button" @click="editor.chain().focus().addRowAfter().run()">행 추가</button>
        <button type="button" @click="editor.chain().focus().deleteRow().run()">행 삭제</button>
        <button type="button" @click="editor.chain().focus().addColumnAfter().run()">열 추가</button>
        <button type="button" @click="editor.chain().focus().deleteColumn().run()">열 삭제</button>
        <button type="button" class="danger" @click="editor.chain().focus().deleteTable().run()">
          표 삭제
        </button>
      </template>
    </div>

    <p v-if="uploadError" class="error">{{ uploadError }}</p>

    <p v-if="showEmpty" class="empty">작성된 내용이 없습니다.</p>
    <EditorContent v-else :editor="editor" class="editor-content" :class="{ readonly }" />
  </div>
</template>

<style scoped>
.rich-editor {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.toolbar button {
  padding: 5px 10px;
  border: 1px solid transparent;
  border-radius: 6px;
  background: none;
  color: var(--text-dim);
  font-size: 13px;
  cursor: pointer;
}

.toolbar button:hover {
  background: var(--bg-soft);
  color: var(--text);
}

.toolbar button.active {
  border-color: var(--accent-border);
  background: var(--accent-bg);
  color: var(--accent);
}

.toolbar button.danger {
  color: var(--wrong);
}

.toolbar button:disabled {
  opacity: 0.6;
  cursor: default;
}

.sep {
  width: 1px;
  height: 18px;
  background: var(--border);
  margin: 0 4px;
}

.error {
  color: var(--wrong);
  font-size: 13px;
}

.empty {
  color: var(--text-dim);
  font-size: 13px;
}

.editor-content :deep(.ProseMirror) {
  min-height: 160px;
  font-size: 16px;
  line-height: 1.8;
  outline: none;
}

.editor-content.readonly :deep(.ProseMirror) {
  min-height: 0;
}

.editor-content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--text-dim);
  pointer-events: none;
  height: 0;
}

.editor-content :deep(.ProseMirror h2) {
  font-size: 20px;
  font-weight: 700;
  margin: 18px 0 8px;
}

.editor-content :deep(.ProseMirror ul) {
  padding-left: 22px;
  margin: 10px 0;
}

.editor-content :deep(.ProseMirror pre) {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  font-family: var(--mono);
  font-size: 13px;
  overflow-x: auto;
  margin: 14px 0;
}

.editor-content :deep(.ProseMirror pre code) {
  background: none;
  padding: 0;
}

.editor-content :deep(.ProseMirror img) {
  max-width: 100%;
  border-radius: 6px;
  margin: 10px 0;
}

.editor-content :deep(.ProseMirror table) {
  border-collapse: collapse;
  width: 100%;
  margin: 14px 0;
  font-size: 14px;
}

.editor-content :deep(.ProseMirror th),
.editor-content :deep(.ProseMirror td) {
  border: 1px solid var(--border);
  padding: 6px 10px;
  text-align: left;
  vertical-align: top;
}

.editor-content :deep(.ProseMirror th) {
  background: var(--bg-soft);
  font-weight: 600;
}

.editor-content :deep(.ProseMirror p) {
  margin: 10px 0;
}
</style>
