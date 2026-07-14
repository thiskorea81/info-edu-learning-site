<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const props = defineProps({
  subject: { type: String, required: true },
})

const all = ref([])
const loading = ref(true)
const openingKey = ref(null)
const error = ref('')

const items = computed(() => all.value.filter((t) => t.교과 === props.subject))

async function load() {
  loading.value = true
  const { data } = await api.get('/api/textbooks')
  all.value = data
  loading.value = false
}

onMounted(load)
watch(() => props.subject, load)

function encodedPath(파일명) {
  return 파일명
    .split('/')
    .map((seg) => encodeURIComponent(seg))
    .join('/')
}

function openPublic(t) {
  window.open(`/textbook-files/${encodedPath(t.파일명)}`, '_blank', 'noopener')
}

async function openTeacherOnly(t) {
  error.value = ''
  openingKey.value = t.파일명
  try {
    const { data } = await api.get(`/api/textbooks/teacher-file/${encodedPath(t.파일명)}`, {
      responseType: 'blob',
    })
    const blobUrl = URL.createObjectURL(data)
    window.open(blobUrl, '_blank', 'noopener')
  } catch (e) {
    error.value = e.response?.data?.detail || 'PDF를 여는 데 실패했습니다.'
  } finally {
    openingKey.value = null
  }
}

function open(t) {
  if (t.teacher_only) {
    openTeacherOnly(t)
  } else {
    openPublic(t)
  }
}
</script>

<template>
  <RouterLink :to="{ name: 'textbooks' }" class="back"> ← 교과서 </RouterLink>
  <h1>{{ subject }}</h1>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="!items.length" class="empty">이 과목에는 등록된 교과서가 없습니다.</p>
  <p v-if="error" class="error">{{ error }}</p>
  <ul v-else-if="items.length" class="list">
    <li v-for="t in items" :key="t.파일명">
      <span class="unit-name">
        {{ t.단원 }}
        <span v-if="t.teacher_only" class="teacher-badge">교사용</span>
      </span>
      <span class="size">{{ t.size_mb }}MB</span>
      <button class="view-btn" :disabled="openingKey === t.파일명" @click="open(t)">
        {{ openingKey === t.파일명 ? '여는 중…' : '보기' }}
      </button>
    </li>
  </ul>
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

.error {
  color: var(--wrong);
  font-size: 13px;
}

.list {
  list-style: none;
  padding: 0;
  margin: 0;
  border-top: 1px solid var(--border);
}

.list li {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 4px;
  border-bottom: 1px solid var(--border);
}

.unit-name {
  flex: 1;
}

.teacher-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid #dc2626;
  color: #dc2626;
  font-size: 11px;
  font-weight: 600;
}

.size {
  font-size: 12px;
  color: var(--text-dim);
  white-space: nowrap;
}

.view-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: #ffffff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.view-btn:hover {
  opacity: 0.9;
}

.view-btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
