import { reactive } from 'vue'
import api from './api'

function loadUser() {
  const raw = localStorage.getItem('user')
  return raw ? JSON.parse(raw) : null
}

export const authState = reactive({
  token: localStorage.getItem('token'),
  user: loadUser(),
})

export function isLoggedIn() {
  return !!authState.token
}

export function isTeacher() {
  return authState.user?.role === 'teacher'
}

export async function login(name, number) {
  const { data } = await api.post('/api/auth/login', { name, number })
  authState.token = data.token
  authState.user = data.user
  localStorage.setItem('token', data.token)
  localStorage.setItem('user', JSON.stringify(data.user))
}

export async function logout() {
  try {
    await api.post('/api/auth/logout')
  } catch {
    // 네트워크 오류 등으로 서버 로그아웃이 실패해도 클라이언트 상태는 정리한다.
  }
  authState.token = null
  authState.user = null
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}
