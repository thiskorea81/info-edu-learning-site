<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header class="topbar">
    <RouterLink to="/" class="brand">정보교육학습사이트</RouterLink>
    <nav>
      <RouterLink to="/" exact-active-class="active">교과서</RouterLink>
      <RouterLink to="/problems" active-class="active">코딩테스트</RouterLink>
      <RouterLink to="/materials" active-class="active">학습자료</RouterLink>
      <RouterLink to="/wrong-notes" active-class="active">오답노트</RouterLink>
      <RouterLink to="/stats" active-class="active">통계</RouterLink>
      <RouterLink to="/add-question" active-class="active">문제 등록</RouterLink>
    </nav>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border);
}

.brand {
  font-weight: 700;
  font-size: 18px;
  text-decoration: none;
  color: var(--text-h);
}

nav {
  display: flex;
  gap: 20px;
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

main {
  flex: 1;
  padding: 24px;
}
</style>
