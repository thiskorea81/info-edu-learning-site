<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const props = defineProps({
  subject: { type: String, required: true },
})

const all = ref([])
const loading = ref(true)

const items = computed(() => all.value.filter((t) => t.교과 === props.subject))

async function load() {
  loading.value = true
  const { data } = await api.get('/api/textbooks')
  all.value = data
  loading.value = false
}

onMounted(load)
watch(() => props.subject, load)

function fileUrl(파일명) {
  const encoded = 파일명
    .split('/')
    .map((seg) => encodeURIComponent(seg))
    .join('/')
  return `/textbook-files/${encoded}`
}
</script>

<template>
  <RouterLink :to="{ name: 'textbooks' }" class="back"> ← 교과서 </RouterLink>
  <h1>{{ subject }}</h1>

  <p v-if="loading">불러오는 중…</p>
  <p v-else-if="!items.length" class="empty">이 과목에는 등록된 교과서가 없습니다.</p>
  <ul v-else class="list">
    <li v-for="t in items" :key="t.파일명">
      <span class="unit-name">{{ t.단원 }}</span>
      <span class="size">{{ t.size_mb }}MB</span>
      <a :href="fileUrl(t.파일명)" target="_blank" rel="noopener" class="view-btn">보기</a>
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

.size {
  font-size: 12px;
  color: var(--text-dim);
  white-space: nowrap;
}

.view-btn {
  padding: 6px 16px;
  border-radius: 8px;
  background: var(--accent);
  color: #ffffff;
  font-weight: 600;
  font-size: 13px;
  text-decoration: none;
  white-space: nowrap;
}

.view-btn:hover {
  opacity: 0.9;
}
</style>
