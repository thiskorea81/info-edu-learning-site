<script setup>
import { useRouter, RouterLink, RouterView } from 'vue-router'
import { authState, isLoggedIn, isTeacher, isAdmin, logout } from './auth'

const router = useRouter()

async function doLogout() {
  await logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header v-if="isLoggedIn()" class="topbar">
    <div class="topbar-row">
      <RouterLink to="/" class="brand">정보ON</RouterLink>
      <div class="user-box">
        <span class="user-name">{{ authState.user?.name }}({{ authState.user?.login_id }}){{ isTeacher() ? (isAdmin() ? ' 관리자' : ' 교사') : '' }}</span>
        <RouterLink to="/change-password" class="change-pw-btn">비밀번호 변경</RouterLink>
        <button class="logout-btn" @click="doLogout">로그아웃</button>
      </div>
    </div>
    <nav>
      <RouterLink to="/materials" active-class="active">학습자료</RouterLink>
      <RouterLink to="/" exact-active-class="active">평가</RouterLink>
      <RouterLink v-if="!isTeacher()" to="/assignments" active-class="active">과제</RouterLink>
      <RouterLink v-else :to="{ name: 'teacher-assignments' }" active-class="active">과제</RouterLink>
      <RouterLink to="/problems" active-class="active">코딩테스트</RouterLink>
      <RouterLink v-if="!isTeacher()" to="/wrong-notes" active-class="active">오답노트</RouterLink>
      <RouterLink v-if="!isTeacher()" to="/stats" active-class="active">통계</RouterLink>
      <RouterLink v-if="isTeacher()" to="/add-question" active-class="active">문제 등록</RouterLink>
      <RouterLink v-if="isTeacher()" to="/teacher" active-class="active">교사용 관리</RouterLink>
    </nav>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.topbar {
  display: flex;
  flex-direction: column;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border);
  gap: 10px;
}

.topbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  font-weight: 700;
  font-size: 18px;
  text-decoration: none;
  color: var(--text-h);
  white-space: nowrap;
}

nav {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

nav a {
  text-decoration: none;
  color: var(--text-dim);
  font-size: 15px;
  padding: 4px 2px;
  border-bottom: 2px solid transparent;
}

nav a.active {
  color: var(--text-h);
  border-bottom-color: var(--accent);
}

.user-box {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.user-name {
  font-size: 13px;
  color: var(--text-dim);
}

.change-pw-btn,
.logout-btn {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: none;
  color: var(--text-dim);
  font-size: 13px;
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
}

.change-pw-btn:hover,
.logout-btn:hover {
  color: var(--text-h);
  border-color: var(--accent-border);
}

main {
  flex: 1;
  padding: 24px;
}
</style>
