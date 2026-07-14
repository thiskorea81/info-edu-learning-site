import { onUnmounted } from 'vue'

// 3초는 타이핑 중에도 계속 요청이 나가 너무 잦다고 판단해 10초로 잡았다.
// 변경된 내용이 있을 때만 저장을 시도한다.
const AUTOSAVE_INTERVAL_MS = 10000

export function useAutosave(getContent, saveFn) {
  let lastSaved = JSON.stringify(getContent())
  let timer = null

  async function tick() {
    const current = JSON.stringify(getContent())
    if (current === lastSaved) return
    try {
      await saveFn()
      lastSaved = current
    } catch {
      // 자동저장 실패는 조용히 넘어간다 — 다음 주기에 다시 시도하거나 사용자가 수동으로 저장할 수 있다.
    }
  }

  function start() {
    stop()
    lastSaved = JSON.stringify(getContent())
    timer = setInterval(tick, AUTOSAVE_INTERVAL_MS)
  }

  function stop() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  function markSaved() {
    lastSaved = JSON.stringify(getContent())
  }

  onUnmounted(stop)

  return { start, stop, markSaved }
}
