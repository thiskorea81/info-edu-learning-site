<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import api from '../api'

const props = defineProps({
  standardId: { type: String, required: true },
})

const material = ref(null)
const loading = ref(true)

onMounted(async () => {
  const { data } = await api.get(`/api/materials/${props.standardId}`)
  material.value = data
  loading.value = false
})
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
        <pre v-if="s.code" class="code-block"><code>{{ s.code }}</code></pre>
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

.code-block {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 14px 16px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
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
