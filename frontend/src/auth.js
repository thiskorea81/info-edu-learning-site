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

export function isAdmin() {
  return !!authState.user?.is_admin
}

export function mustChangePassword() {
  return !!authState.user?.must_change_password
}

function persist(user) {
  authState.user = user
  localStorage.setItem('user', JSON.stringify(user))
}

export async function login(loginId, password) {
  const { data } = await api.post('/api/auth/login', { login_id: loginId, password })
  authState.token = data.token
  localStorage.setItem('token', data.token)
  persist(data.user)
}

export async function changePassword(newPassword) {
  const { data } = await api.post('/api/auth/change-password', { new_password: newPassword })
  persist(data)
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
