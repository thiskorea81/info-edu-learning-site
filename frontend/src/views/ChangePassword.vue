<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { changePassword, mustChangePassword } from '../auth'

const router = useRouter()

const forced = mustChangePassword()

const newPassword = ref('')
const confirmPassword = ref('')
const error = ref('')
const done = ref(false)
const loading = ref(false)

async function submit() {
  if (!/^\d{4}$/.test(newPassword.value)) {
    error.value = '비밀번호는 숫자 4자리로 입력해 주세요.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    error.value = '비밀번호가 서로 일치하지 않습니다.'
    return
  }
  error.value = ''
  loading.value = true
  try {
    await changePassword(newPassword.value)
    done.value = true
    setTimeout(() => router.replace('/'), 800)
  } catch (e) {
    error.value = e.response?.data?.detail || '비밀번호 변경에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="wrap">
    <form class="card" @submit.prevent="submit">
      <h1>비밀번호 변경</h1>
      <p v-if="forced" class="hint">최초 로그인이거나 초기화된 계정입니다. 계속하려면 비밀번호를 변경해 주세요.</p>
      <p v-else class="hint">새 비밀번호를 입력해 주세요.</p>

      <label>
        새 비밀번호 (숫자 4자리)
        <input
          v-model="newPassword"
          type="password"
          inputmode="numeric"
          maxlength="4"
          autocomplete="new-password"
          placeholder="예: 5678"
        />
      </label>
      <label>
        새 비밀번호 확인
        <input
          v-model="confirmPassword"
          type="password"
          inputmode="numeric"
          maxlength="4"
          autocomplete="new-password"
          placeholder="다시 입력"
        />
      </label>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="done" class="success">변경되었습니다. 이동 중…</p>

      <button type="submit" :disabled="loading">{{ loading ? '변경 중…' : '변경하기' }}</button>
    </form>
  </div>
</template>

<style scoped>
.wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px);
}

.card {
  width: 100%;
  max-width: 340px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 28px;
}

.card h1 {
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

.success {
  color: var(--correct, #16a34a);
  font-size: 13px;
}
</style>
