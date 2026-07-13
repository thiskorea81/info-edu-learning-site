<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { login } from '../auth'

const router = useRouter()
const route = useRoute()

const name = ref('')
const number = ref('')
const error = ref('')
const loading = ref(false)

async function submit() {
  if (!name.value.trim() || !number.value.trim()) {
    error.value = '이름과 번호를 모두 입력해 주세요.'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await login(name.value.trim(), number.value.trim())
    const redirect = route.query.redirect || '/'
    router.replace(redirect)
  } catch (e) {
    error.value = e.response?.data?.detail || '로그인에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-wrap">
    <form class="login-card" @submit.prevent="submit">
      <h1>정보교육학습사이트</h1>
      <p class="hint">이름과 번호를 입력해 로그인하세요.</p>

      <label>
        이름
        <input v-model="name" type="text" autocomplete="name" placeholder="예: 김민준" />
      </label>
      <label>
        번호
        <input v-model="number" type="text" inputmode="numeric" placeholder="예: 1" />
      </label>

      <p v-if="error" class="error">{{ error }}</p>

      <button type="submit" :disabled="loading">{{ loading ? '로그인 중…' : '로그인' }}</button>
    </form>
  </div>
</template>

<style scoped>
.login-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px);
}

.login-card {
  width: 100%;
  max-width: 340px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 28px;
}

.login-card h1 {
  font-size: 18px;
  text-align: center;
}

.hint {
  color: var(--text-dim);
  font-size: 13px;
  text-align: center;
  margin-bottom: 4px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: var(--text-dim);
}

input {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
  color: var(--text-h);
  font-size: 14px;
}

button {
  margin-top: 6px;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: #ffffff;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

button:disabled {
  opacity: 0.6;
  cursor: default;
}

.error {
  color: var(--wrong);
  font-size: 13px;
}
</style>
