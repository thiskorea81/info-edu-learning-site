<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import { isAdmin } from '../auth'
import RichEditor from '../components/RichEditor.vue'

const route = useRoute()
const tab = ref('roster')

// --- 명단 ---
const roster = ref([])
const includeArchived = ref(false)
const rosterLoading = ref(true)
const rosterError = ref('')

const newLoginId = ref('')
const newName = ref('')
const newRole = ref('student')
const newIsAdmin = ref(false)
const adding = ref(false)

const bulkText = ref('')
const bulkResult = ref(null)
const bulkAdding = ref(false)

const teachers = computed(() => roster.value.filter((r) => r.role === 'teacher'))

async function loadRoster() {
  rosterLoading.value = true
  try {
    const { data } = await api.get('/api/roster', {
      params: { include_archived: includeArchived.value },
    })
    roster.value = data
  } finally {
    rosterLoading.value = false
  }
}

async function addUser() {
  if (!newLoginId.value.trim() || !newName.value.trim()) {
    rosterError.value = '아이디와 이름을 모두 입력해 주세요.'
    return
  }
  rosterError.value = ''
  adding.value = true
  try {
    await api.post('/api/roster', {
      login_id: newLoginId.value.trim(),
      name: newName.value.trim(),
      role: newRole.value,
      is_admin: newRole.value === 'teacher' ? newIsAdmin.value : false,
    })
    newLoginId.value = ''
    newName.value = ''
    newRole.value = 'student'
    newIsAdmin.value = false
    await loadRoster()
  } catch (e) {
    rosterError.value = e.response?.data?.detail || '등록에 실패했습니다.'
  } finally {
    adding.value = false
  }
}

async function addBulk() {
  if (!bulkText.value.trim()) return
  bulkAdding.value = true
  try {
    const { data } = await api.post('/api/roster/bulk', { text: bulkText.value })
    bulkResult.value = data
    if (data.created > 0) bulkText.value = ''
    await loadRoster()
  } finally {
    bulkAdding.value = false
  }
}

async function resetPassword(u) {
  if (!confirm(`${u.name}(${u.login_id})의 비밀번호를 1234로 초기화할까요?`)) return
  await api.post(`/api/roster/${u.id}/reset-password`)
  await loadRoster()
}

async function toggleArchive(u) {
  await api.patch(`/api/roster/${u.id}/archive`, null, { params: { is_archived: !u.is_archived } })
  await loadRoster()
}

async function toggleAdmin(u) {
  await api.patch(`/api/roster/${u.id}/admin`, null, { params: { is_admin: !u.is_admin } })
  await loadRoster()
}

async function removeUser(u) {
  if (!confirm(`${u.name}(${u.login_id}) 계정을 완전히 삭제할까요? 수강 정보도 함께 삭제됩니다.`)) return
  await api.delete(`/api/roster/${u.id}`)
  await loadRoster()
  if (selectedSubject.value) await loadSubjectStudents(selectedSubject.value.id)
}

// --- 과목 ---
const subjects = ref([])
const subjectsLoading = ref(true)
const selectedSubject = ref(null)
const subjectStudents = ref([])
const enrollText = ref('')
const enrollResult = ref(null)
const enrolling = ref(false)

async function loadSubjects() {
  subjectsLoading.value = true
  try {
    const { data } = await api.get('/api/subject-admin')
    subjects.value = data
  } finally {
    subjectsLoading.value = false
  }
}

async function loadSubjectStudents(id) {
  const { data } = await api.get(`/api/subject-admin/${id}/students`)
  subjectStudents.value = data
}

async function selectSubject(s) {
  selectedSubject.value = s
  enrollResult.value = null
  enrollText.value = ''
  await loadSubjectStudents(s.id)
}

async function toggleSubjectArchive(s) {
  await api.patch(`/api/subject-admin/${s.id}/archive`, null, { params: { is_archived: !s.is_archived } })
  await loadSubjects()
  if (selectedSubject.value?.id === s.id) {
    selectedSubject.value = { ...selectedSubject.value, is_archived: !s.is_archived }
  }
}

async function reassignTeacher(s, teacherId) {
  if (!teacherId) return
  await api.patch(`/api/subject-admin/${s.id}/teacher`, null, { params: { teacher_id: teacherId } })
  await loadSubjects()
}

function parseLoginIds(text) {
  return text
    .split(/[\s,]+/)
    .map((v) => v.trim())
    .filter(Boolean)
}

async function enrollStudents() {
  const loginIds = parseLoginIds(enrollText.value)
  if (!loginIds.length || !selectedSubject.value) return
  enrolling.value = true
  try {
    const { data } = await api.post(`/api/subject-admin/${selectedSubject.value.id}/students`, {
      login_ids: loginIds,
    })
    enrollResult.value = data
    if (data.enrolled.length) enrollText.value = ''
    await loadSubjectStudents(selectedSubject.value.id)
    await loadSubjects()
  } finally {
    enrolling.value = false
  }
}

async function unenrollStudent(u) {
  if (!selectedSubject.value) return
  if (!confirm(`${u.name}(${u.login_id})을(를) 이 과목에서 제외할까요?`)) return
  await api.delete(`/api/subject-admin/${selectedSubject.value.id}/students/${u.id}`)
  await loadSubjectStudents(selectedSubject.value.id)
  await loadSubjects()
}

// --- 성취도 (과목별로 집계 — 한 학생이 여러 과목을 수강할 수 있으므로 섞지 않는다) ---
const statsSubject = ref(null)
const classSummary = ref(null)
const classSummaryLoading = ref(false)
const classStats = ref([])
const classStatsLoading = ref(false)
const statDetail = ref(null)
const statDetailLoading = ref(false)
const onlyBehind = ref(false)

const behindStandards = computed(() => {
  if (!classSummary.value) return []
  const rows = classSummary.value.by_standard
  return onlyBehind.value ? rows.filter((r) => r.solved_students === 0) : rows
})

const expandedStandard = ref(null)
const standardItems = ref(null)
const standardItemsLoading = ref(false)

async function toggleStandardItems(standardId) {
  if (expandedStandard.value === standardId) {
    expandedStandard.value = null
    return
  }
  expandedStandard.value = standardId
  standardItems.value = null
  standardItemsLoading.value = true
  try {
    const { data } = await api.get(
      `/api/subject-admin/${statsSubject.value.id}/stats-items/${encodeURIComponent(standardId)}`
    )
    standardItems.value = data
  } finally {
    standardItemsLoading.value = false
  }
}

async function selectStatsSubject(s) {
  statsSubject.value = s
  statDetail.value = null
  expandedStandard.value = null
  standardItems.value = null
  await Promise.all([loadClassSummary(), loadClassStats()])
}

async function loadClassSummary() {
  if (!statsSubject.value) return
  classSummaryLoading.value = true
  try {
    const { data } = await api.get(`/api/subject-admin/${statsSubject.value.id}/stats-summary`)
    classSummary.value = data
  } finally {
    classSummaryLoading.value = false
  }
}

async function loadClassStats() {
  if (!statsSubject.value) return
  classStatsLoading.value = true
  try {
    const { data } = await api.get(`/api/subject-admin/${statsSubject.value.id}/stats`)
    classStats.value = data
  } finally {
    classStatsLoading.value = false
  }
}

async function showStatDetail(id) {
  if (!statsSubject.value) return
  statDetailLoading.value = true
  try {
    const { data } = await api.get(`/api/subject-admin/${statsSubject.value.id}/stats/${id}`)
    statDetail.value = data
  } finally {
    statDetailLoading.value = false
  }
}

// --- 과제 ---
const assignmentsSubject = ref(null)
const assignments = ref([])
const assignmentsLoading = ref(false)
const showNewAssignmentForm = ref(false)
const newAssignmentTitle = ref('')
const newAssignmentDescription = ref('')
const newAssignmentUnit = ref('')
const newAssignmentDue = ref('')
const creatingAssignment = ref(false)

const selectedAssignment = ref(null)
const assignmentSubmissions = ref([])
const submissionsLoading = ref(false)
const selectedSubmission = ref(null)
const selectedSubmissionContent = ref({ type: 'doc', content: [{ type: 'paragraph' }] })
const gradeScore = ref(null)
const gradeFeedback = ref('')
const grading = ref(false)

const ASSIGNMENT_STATUS_LABEL = {
  not_submitted: '미제출',
  draft: '임시저장',
  submitted: '제출완료',
  graded: '채점완료',
}

async function selectAssignmentsSubject(s) {
  assignmentsSubject.value = s
  selectedAssignment.value = null
  await loadAssignments()
}

async function loadAssignments() {
  if (!assignmentsSubject.value) return
  assignmentsLoading.value = true
  try {
    const { data } = await api.get(`/api/subject-admin/${assignmentsSubject.value.id}/assignments`)
    assignments.value = data
  } finally {
    assignmentsLoading.value = false
  }
}

async function createAssignment() {
  if (!newAssignmentTitle.value.trim() || !newAssignmentDescription.value.trim()) return
  creatingAssignment.value = true
  try {
    await api.post(`/api/subject-admin/${assignmentsSubject.value.id}/assignments`, {
      title: newAssignmentTitle.value.trim(),
      description: newAssignmentDescription.value.trim(),
      단원: newAssignmentUnit.value.trim() || null,
      due_at: newAssignmentDue.value ? new Date(newAssignmentDue.value).toISOString() : null,
    })
    newAssignmentTitle.value = ''
    newAssignmentDescription.value = ''
    newAssignmentUnit.value = ''
    newAssignmentDue.value = ''
    showNewAssignmentForm.value = false
    await loadAssignments()
  } finally {
    creatingAssignment.value = false
  }
}

async function deleteAssignment(a) {
  if (!confirm(`"${a.title}" 과제를 삭제할까요? 제출물도 함께 삭제됩니다.`)) return
  await api.delete(`/api/subject-admin/${assignmentsSubject.value.id}/assignments/${a.id}`)
  if (selectedAssignment.value?.id === a.id) {
    selectedAssignment.value = null
    selectedSubmission.value = null
  }
  await loadAssignments()
}

async function selectAssignment(a) {
  selectedAssignment.value = a
  selectedSubmission.value = null
  await loadAssignmentSubmissions()
}

async function loadAssignmentSubmissions() {
  if (!selectedAssignment.value) return
  submissionsLoading.value = true
  try {
    const { data } = await api.get(
      `/api/subject-admin/${assignmentsSubject.value.id}/assignments/${selectedAssignment.value.id}/submissions`
    )
    assignmentSubmissions.value = data
  } finally {
    submissionsLoading.value = false
  }
}

function openSubmission(s) {
  selectedSubmission.value = s
  selectedSubmissionContent.value = s.content
  gradeScore.value = s.score
  gradeFeedback.value = s.feedback || ''
}

async function submitGrade() {
  grading.value = true
  try {
    const { data } = await api.patch(
      `/api/subject-admin/${assignmentsSubject.value.id}/assignments/${selectedAssignment.value.id}/submissions/${selectedSubmission.value.user_id}/grade`,
      { score: gradeScore.value, feedback: gradeFeedback.value }
    )
    selectedSubmission.value = data
    await loadAssignmentSubmissions()
  } finally {
    grading.value = false
  }
}

async function applyReportQuickCreate() {
  const { subject: subjectName, title, description, 단원: unit } = route.query
  if (!subjectName) return
  await loadSubjects()
  const match = subjects.value.find((s) => s.name === subjectName)
  if (!match) return
  tab.value = 'assignments'
  assignmentsSubject.value = match
  await loadAssignments()
  if (title) {
    newAssignmentTitle.value = String(title)
    newAssignmentDescription.value = String(description || '')
    newAssignmentUnit.value = String(unit || '')
    showNewAssignmentForm.value = true
  }
}

onMounted(async () => {
  loadRoster()
  loadSubjects()
  if (route.query.subject) {
    await applyReportQuickCreate()
  } else if (route.query.tab === 'assignments') {
    tab.value = 'assignments'
  }
})
</script>

<template>
  <h1>교사용 관리</h1>

  <div class="tabs">
    <button :class="{ active: tab === 'roster' }" @click="tab = 'roster'">명단 관리</button>
    <button :class="{ active: tab === 'subjects' }" @click="tab = 'subjects'">과목/수강 관리</button>
    <button :class="{ active: tab === 'stats' }" @click="tab = 'stats'">성취도</button>
    <button :class="{ active: tab === 'assignments' }" @click="tab = 'assignments'">과제</button>
  </div>

  <template v-if="tab === 'roster'">
    <section class="panel">
      <h2>계정 등록</h2>
      <form class="add-form" @submit.prevent="addUser">
        <input v-model="newLoginId" type="text" placeholder="학번/교사ID" />
        <input v-model="newName" type="text" placeholder="이름" />
        <select v-model="newRole">
          <option value="student">학생</option>
          <option value="teacher">교사</option>
        </select>
        <label v-if="newRole === 'teacher' && isAdmin()" class="admin-check">
          <input v-model="newIsAdmin" type="checkbox" /> 관리자 권한
        </label>
        <button type="submit" :disabled="adding">{{ adding ? '등록 중…' : '등록' }}</button>
      </form>
      <p class="hint">초기 비밀번호는 1234이며, 최초 로그인 시 변경이 강제됩니다. 교사 계정 생성은 관리자만 가능합니다.</p>
      <p v-if="rosterError" class="error">{{ rosterError }}</p>
    </section>

    <section class="panel">
      <h2>스프레드시트 붙여넣기로 학생 일괄 등록</h2>
      <p class="hint">한 줄에 "학번&#9;이름" 또는 "학번,이름" 형식으로 붙여넣으세요.</p>
      <textarea v-model="bulkText" rows="5" placeholder="30101&#9;김민준&#10;30102&#9;이서연"></textarea>
      <button class="bulk-btn" :disabled="bulkAdding" @click="addBulk">
        {{ bulkAdding ? '등록 중…' : '일괄 등록' }}
      </button>
      <div v-if="bulkResult" class="bulk-result">
        <p>총 {{ bulkResult.total }}건 · 등록 {{ bulkResult.created }}건 · 제외 {{ bulkResult.skipped }}건</p>
        <ul>
          <li
            v-for="(r, i) in bulkResult.results.filter((r) => r.status !== 'created')"
            :key="i"
            class="bulk-issue"
          >
            {{ r.line }} — {{ r.reason }}
          </li>
        </ul>
      </div>
    </section>

    <section class="panel">
      <div class="panel-head">
        <h2>명단 ({{ roster.filter((r) => r.role === 'student').length }}명)</h2>
        <label class="archive-toggle">
          <input v-model="includeArchived" type="checkbox" @change="loadRoster" /> 보관 계정 포함
        </label>
      </div>
      <p v-if="rosterLoading">불러오는 중…</p>
      <table v-else-if="roster.length">
        <thead>
          <tr>
            <th>아이디</th>
            <th>이름</th>
            <th>역할</th>
            <th>상태</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in roster" :key="u.id" :class="{ archived: u.is_archived }">
            <td>{{ u.login_id }}</td>
            <td>{{ u.name }}</td>
            <td>
              <span class="role-badge" :class="u.role">{{ u.role === 'teacher' ? '교사' : '학생' }}</span>
              <span v-if="u.is_admin" class="role-badge admin">관리자</span>
            </td>
            <td>
              <span v-if="u.is_archived" class="status-badge archived">보관됨</span>
              <span v-else-if="u.must_change_password" class="status-badge pending">비번 미변경</span>
              <span v-else class="status-badge ok">정상</span>
            </td>
            <td class="actions">
              <button class="link-btn" @click="resetPassword(u)">비번 초기화</button>
              <button class="link-btn" @click="toggleArchive(u)">
                {{ u.is_archived ? '보관 해제' : '보관' }}
              </button>
              <button v-if="isAdmin() && u.role === 'teacher'" class="link-btn" @click="toggleAdmin(u)">
                {{ u.is_admin ? '관리자 해제' : '관리자 지정' }}
              </button>
              <button class="link-btn danger" @click="removeUser(u)">삭제</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">등록된 계정이 없습니다.</p>
    </section>
  </template>

  <template v-else-if="tab === 'subjects'">
    <section class="panel">
      <h2>과목 목록</h2>
      <p v-if="subjectsLoading">불러오는 중…</p>
      <table v-else-if="subjects.length">
        <thead>
          <tr>
            <th>과목명</th>
            <th>담당 교사</th>
            <th>수강생</th>
            <th>상태</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in subjects"
            :key="s.id"
            :class="{ selected: selectedSubject?.id === s.id, archived: s.is_archived }"
          >
            <td>{{ s.name }}</td>
            <td>
              <select v-if="isAdmin()" :value="s.teacher_id" @change="reassignTeacher(s, $event.target.value)">
                <option v-for="t in teachers" :key="t.id" :value="t.id">{{ t.name }}</option>
              </select>
              <span v-else>{{ s.teacher_name }}</span>
            </td>
            <td>{{ s.student_count }}명</td>
            <td>
              <span v-if="s.is_archived" class="status-badge archived">보관됨</span>
              <span v-else class="status-badge ok">운영중</span>
            </td>
            <td class="actions">
              <button class="link-btn" @click="selectSubject(s)">수강생 관리</button>
              <button class="link-btn" @click="toggleSubjectArchive(s)">
                {{ s.is_archived ? '보관 해제' : '보관' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">등록된 과목이 없습니다.</p>
    </section>

    <section v-if="selectedSubject" class="panel">
      <h2>{{ selectedSubject.name }} — 수강생 관리</h2>

      <div class="enroll-form">
        <textarea
          v-model="enrollText"
          rows="2"
          placeholder="학번을 쉼표/공백/줄바꿈으로 구분해 입력 (예: 30101, 30102)"
        ></textarea>
        <button :disabled="enrolling" @click="enrollStudents">{{ enrolling ? '등록 중…' : '수강 등록' }}</button>
      </div>
      <p v-if="enrollResult" class="hint">
        등록 {{ enrollResult.enrolled.length }}명
        <span v-if="enrollResult.already_enrolled.length">· 이미 등록됨: {{ enrollResult.already_enrolled.join(', ') }}</span>
        <span v-if="enrollResult.not_found.length">· 존재하지 않는 학번: {{ enrollResult.not_found.join(', ') }}</span>
      </p>

      <table v-if="subjectStudents.length">
        <thead>
          <tr>
            <th>학번</th>
            <th>이름</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in subjectStudents" :key="u.id">
            <td>{{ u.login_id }}</td>
            <td>{{ u.name }}</td>
            <td class="actions">
              <button class="link-btn danger" @click="unenrollStudent(u)">제외</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">등록된 수강생이 없습니다.</p>
    </section>
  </template>

  <template v-else-if="tab === 'stats'">
    <section class="panel">
      <h2>과목 선택</h2>
      <p class="hint">한 학생이 여러 과목을 수강할 수 있어, 성취도는 과목별로 따로 집계합니다.</p>
      <div class="subject-picker">
        <button
          v-for="s in subjects"
          :key="s.id"
          class="subject-chip"
          :class="{ active: statsSubject?.id === s.id }"
          @click="selectStatsSubject(s)"
        >
          {{ s.name }}
        </button>
      </div>
    </section>

    <section v-if="statsSubject" class="panel">
      <h2>{{ statsSubject.name }} — 학급 진행 현황</h2>
      <p v-if="classSummaryLoading">불러오는 중…</p>
      <template v-else-if="classSummary">
        <div class="kpi-row">
          <div class="kpi">
            <span class="value">{{ classSummary.student_count }}</span>
            <span class="label">수강 인원</span>
          </div>
          <div class="kpi">
            <span class="value">{{ classSummary.started_count }}</span>
            <span class="label">시작한 학생</span>
          </div>
          <div class="kpi" :class="{ warn: classSummary.not_started_count > 0 }">
            <span class="value">{{ classSummary.not_started_count }}</span>
            <span class="label">아직 시작 안 함</span>
          </div>
          <div class="kpi">
            <span class="value">{{ classSummary.average_achievement ?? '-' }}{{ classSummary.average_achievement !== null ? '%' : '' }}</span>
            <span class="label">평균 성취도</span>
          </div>
        </div>

        <div class="grade-dist">
          <span v-for="g in ['A', 'B', 'C', 'D', 'E']" :key="g" class="grade-dist-item">
            <span class="grade-badge" :class="`grade-${g}`">{{ g }}</span>
            {{ classSummary.grade_distribution[g] }}명
          </span>
          <span class="grade-dist-item not-attempted">미응시 {{ classSummary.grade_distribution['미응시'] }}명</span>
        </div>

        <div class="panel-head">
          <h3>성취기준별 진행 현황</h3>
          <label class="archive-toggle">
            <input v-model="onlyBehind" type="checkbox" /> 아무도 안 푼 성취기준만 보기
          </label>
        </div>
        <table v-if="behindStandards.length">
          <thead>
            <tr>
              <th>성취기준</th>
              <th>단원</th>
              <th>푼 학생</th>
              <th>이론 평균 정답률</th>
              <th>실습 평균 정답률</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="row in behindStandards" :key="row.standard_id">
              <tr :class="{ behind: row.solved_students === 0 }">
                <td class="std-id">{{ row.standard_id }}</td>
                <td>{{ row.단원 }}</td>
                <td>{{ row.solved_students }} / {{ classSummary.student_count }}</td>
                <td>
                  <span v-if="row.avg_accuracy !== null">{{ row.avg_accuracy }}%</span>
                  <span v-else class="not-attempted">미응시</span>
                </td>
                <td>
                  <span v-if="row.avg_practice_accuracy !== null">{{ row.avg_practice_accuracy }}%</span>
                  <span v-else class="not-attempted">미응시</span>
                </td>
                <td class="actions">
                  <button class="link-btn" @click="toggleStandardItems(row.standard_id)">
                    {{ expandedStandard === row.standard_id ? '접기' : '문항별 보기' }}
                  </button>
                </td>
              </tr>
              <tr v-if="expandedStandard === row.standard_id" class="item-detail-row">
                <td colspan="6">
                  <p v-if="standardItemsLoading">불러오는 중…</p>
                  <template v-else-if="standardItems">
                    <template v-if="standardItems.이론.length">
                      <h4>이론 문항</h4>
                      <table class="item-table">
                        <thead>
                          <tr>
                            <th>문항</th>
                            <th>시도</th>
                            <th>정답</th>
                            <th>정답률</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in standardItems.이론" :key="item.id">
                            <td class="item-text">{{ item.문항 }}</td>
                            <td>{{ item.attempted }} / {{ classSummary.student_count }}</td>
                            <td>{{ item.correct }}</td>
                            <td>
                              <span v-if="item.accuracy !== null">{{ item.accuracy }}%</span>
                              <span v-else class="not-attempted">미응시</span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </template>
                    <template v-if="standardItems.실습.length">
                      <h4>실습 문제</h4>
                      <table class="item-table">
                        <thead>
                          <tr>
                            <th>문제</th>
                            <th>시도</th>
                            <th>정답(AC)</th>
                            <th>정답률</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="item in standardItems.실습" :key="item.id">
                            <td class="item-text">{{ item.제목 }}</td>
                            <td>{{ item.attempted }} / {{ classSummary.student_count }}</td>
                            <td>{{ item.correct }}</td>
                            <td>
                              <span v-if="item.accuracy !== null">{{ item.accuracy }}%</span>
                              <span v-else class="not-attempted">미응시</span>
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </template>
                    <p v-if="!standardItems.이론.length && !standardItems.실습.length" class="empty">
                      이 성취기준에 등록된 문항/문제가 없습니다.
                    </p>
                  </template>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
        <p v-else class="empty">해당하는 성취기준이 없습니다.</p>
      </template>
    </section>

    <section v-if="statsSubject" class="panel">
      <h2>{{ statsSubject.name }} — 학생별 종합 성취도</h2>
      <p v-if="classStatsLoading">불러오는 중…</p>
      <table v-else-if="classStats.length">
        <thead>
          <tr>
            <th>학번</th>
            <th>이름</th>
            <th>푼 문제</th>
            <th>정답률</th>
            <th>종합 등급</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in classStats" :key="s.id">
            <td>{{ s.login_id }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.solved }}</td>
            <td>{{ s.accuracy }}%</td>
            <td>
              <span v-if="s.grade" class="grade-badge" :class="`grade-${s.grade}`">{{ s.grade }}</span>
              <span v-else class="not-attempted">-</span>
            </td>
            <td class="actions">
              <button class="link-btn" @click="showStatDetail(s.id)">상세</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">이 과목의 수강생이 없습니다.</p>
    </section>

    <section v-if="statDetail" class="panel">
      <h2>{{ statDetail.student.name }}({{ statDetail.student.login_id }}) — {{ statDetail.subject }} 상세 성취도</h2>
      <p v-if="statDetailLoading">불러오는 중…</p>
      <table v-else-if="statDetail.by_standard.length">
        <thead>
          <tr>
            <th>성취기준</th>
            <th>단원</th>
            <th>이론</th>
            <th>실습</th>
            <th>종합 등급</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in statDetail.by_standard" :key="row.standard_id">
            <td class="std-id">{{ row.standard_id }}</td>
            <td>{{ row.단원 }}</td>
            <td>
              <span v-if="row.solved">{{ row.correct }}/{{ row.solved }} ({{ row.accuracy }}%)</span>
              <span v-else class="not-attempted">미응시</span>
            </td>
            <td>
              <span v-if="row.practice_attempted">
                {{ row.practice_correct }}/{{ row.practice_attempted }} ({{ row.practice_accuracy }}%)
              </span>
              <span v-else class="not-attempted">미응시</span>
            </td>
            <td>
              <span v-if="row.grade" class="grade-badge" :class="`grade-${row.grade}`">{{ row.grade }}</span>
              <span v-else class="not-attempted">-</span>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">아직 푼 문제가 없습니다.</p>
    </section>
  </template>

  <template v-else>
    <section class="panel">
      <h2>과목 선택</h2>
      <div class="subject-picker">
        <button
          v-for="s in subjects"
          :key="s.id"
          class="subject-chip"
          :class="{ active: assignmentsSubject?.id === s.id }"
          @click="selectAssignmentsSubject(s)"
        >
          {{ s.name }}
        </button>
      </div>
    </section>

    <section v-if="assignmentsSubject" class="panel">
      <div class="panel-head">
        <h2>{{ assignmentsSubject.name }} — 과제 목록</h2>
        <button class="link-btn" @click="showNewAssignmentForm = !showNewAssignmentForm">
          {{ showNewAssignmentForm ? '취소' : '+ 새 과제' }}
        </button>
      </div>

      <form v-if="showNewAssignmentForm" class="assignment-form" @submit.prevent="createAssignment">
        <input v-model="newAssignmentTitle" type="text" placeholder="과제 제목" />
        <textarea v-model="newAssignmentDescription" rows="4" placeholder="과제 설명/안내"></textarea>
        <input v-model="newAssignmentUnit" type="text" placeholder="단원 (선택)" />
        <label class="due-label">
          제출 기한 (선택)
          <input v-model="newAssignmentDue" type="datetime-local" />
        </label>
        <button type="submit" :disabled="creatingAssignment">
          {{ creatingAssignment ? '만드는 중…' : '과제 만들기' }}
        </button>
      </form>

      <p v-if="assignmentsLoading">불러오는 중…</p>
      <table v-else-if="assignments.length">
        <thead>
          <tr>
            <th>제목</th>
            <th>단원</th>
            <th>기한</th>
            <th>제출</th>
            <th>채점</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="a in assignments"
            :key="a.id"
            :class="{ selected: selectedAssignment?.id === a.id }"
          >
            <td>{{ a.title }}</td>
            <td>{{ a.단원 || '-' }}</td>
            <td>{{ a.due_at ? new Date(a.due_at).toLocaleString('ko-KR') : '-' }}</td>
            <td>{{ a.submitted_count }}/{{ a.student_count }}</td>
            <td>{{ a.graded_count }}/{{ a.student_count }}</td>
            <td class="actions">
              <button class="link-btn" @click="selectAssignment(a)">제출물 보기</button>
              <button class="link-btn danger" @click="deleteAssignment(a)">삭제</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">아직 과제가 없습니다.</p>
    </section>

    <section v-if="selectedAssignment" class="panel">
      <h2>{{ selectedAssignment.title }} — 제출 현황</h2>
      <p v-if="submissionsLoading">불러오는 중…</p>
      <table v-else-if="assignmentSubmissions.length">
        <thead>
          <tr>
            <th>학번</th>
            <th>이름</th>
            <th>상태</th>
            <th>점수</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in assignmentSubmissions" :key="s.user_id">
            <td>{{ s.login_id }}</td>
            <td>{{ s.name }}</td>
            <td>
              <span class="status-badge" :class="s.status">{{ ASSIGNMENT_STATUS_LABEL[s.status] }}</span>
            </td>
            <td>{{ s.score ?? '-' }}</td>
            <td class="actions">
              <button v-if="s.status !== 'not_submitted'" class="link-btn" @click="openSubmission(s)">
                보기/채점
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">수강생이 없습니다.</p>
    </section>

    <section v-if="selectedSubmission" class="panel">
      <h2>{{ selectedSubmission.name }}({{ selectedSubmission.login_id }}) 제출물</h2>
      <RichEditor v-model="selectedSubmissionContent" readonly />
      <div class="grade-form">
        <label>
          점수
          <input v-model.number="gradeScore" type="number" min="0" max="100" />
        </label>
        <textarea v-model="gradeFeedback" rows="3" placeholder="피드백 코멘트"></textarea>
        <button :disabled="grading" @click="submitGrade">
          {{ grading ? '저장 중…' : '채점 저장' }}
        </button>
      </div>
    </section>
  </template>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 18px;
}

.tabs button {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: none;
  color: var(--text-dim);
  font-size: 13px;
  cursor: pointer;
}

.tabs button.active {
  color: var(--text-h);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.subject-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.subject-chip {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: none;
  color: var(--text-dim);
  font-size: 13px;
  cursor: pointer;
}

.subject-chip.active {
  color: var(--text-h);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.kpi {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kpi.warn .value {
  color: var(--wrong);
}

.kpi .value {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-h);
}

.kpi .label {
  font-size: 12px;
  color: var(--text-dim);
}

.grade-dist {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 20px;
  font-size: 13px;
}

.grade-dist-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

h3 {
  font-size: 14px;
  margin-bottom: 0;
}

tr.behind {
  background: var(--wrong-bg, rgba(220, 38, 38, 0.08));
}

.item-detail-row td {
  background: var(--bg-soft);
  padding: 14px 18px;
}

.item-detail-row h4 {
  font-size: 13px;
  margin-bottom: 8px;
}

.item-detail-row h4:not(:first-child) {
  margin-top: 16px;
}

.item-table {
  font-size: 12px;
}

.item-text {
  max-width: 420px;
}

.panel {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 18px;
  margin-bottom: 20px;
}

.panel h2 {
  font-size: 15px;
  margin-bottom: 14px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.panel-head h2 {
  margin-bottom: 0;
}

.archive-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-dim);
}

.add-form {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.add-form input[type='text'],
.add-form select {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
  color: var(--text-h);
  font-size: 13px;
}

.add-form input[type='text'] {
  width: 140px;
}

.admin-check {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-dim);
}

.add-form button,
.bulk-btn,
.enroll-form button {
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: #ffffff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
}

.add-form button:disabled,
.bulk-btn:disabled,
.enroll-form button:disabled {
  opacity: 0.6;
}

.hint {
  color: var(--text-dim);
  font-size: 12px;
  margin-top: 8px;
}

.error {
  color: var(--wrong);
  font-size: 13px;
  margin-top: 8px;
}

textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
  color: var(--text-h);
  font-size: 13px;
  font-family: var(--mono);
  resize: vertical;
  margin-bottom: 10px;
}

.bulk-result {
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-dim);
}

.bulk-issue {
  color: var(--wrong);
}

.enroll-form {
  margin-bottom: 16px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th,
td {
  text-align: left;
  padding: 8px 10px;
  border-top: 1px solid var(--border);
}

thead th {
  border-top: none;
  color: var(--text-dim);
  font-weight: 500;
}

tr.selected {
  background: var(--accent-bg);
}

tr.archived {
  opacity: 0.55;
}

.role-badge,
.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  display: inline-block;
  margin-right: 4px;
}

.role-badge.teacher {
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.role-badge.admin {
  color: #dc2626;
  border-color: #dc2626;
}

.status-badge.ok {
  color: #16a34a;
  border-color: #16a34a;
}

.status-badge.pending {
  color: #ca8a04;
  border-color: #ca8a04;
}

.status-badge.archived {
  color: var(--text-dim);
}

.status-badge.not_submitted {
  color: var(--wrong);
  border-color: var(--wrong);
}

.status-badge.draft {
  color: #ca8a04;
  border-color: #ca8a04;
}

.status-badge.submitted {
  color: var(--accent);
  border-color: var(--accent-border);
  background: var(--accent-bg);
}

.status-badge.graded {
  color: #16a34a;
  border-color: #16a34a;
  background: rgba(22, 163, 74, 0.1);
  font-weight: 600;
}

.assignment-form,
.grade-form {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 18px;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--bg-soft);
}

.assignment-form input,
.assignment-form textarea,
.grade-form input,
.grade-form textarea {
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text-h);
  font-size: 13px;
}

.due-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--text-dim);
}

.assignment-form button,
.grade-form button {
  align-self: flex-start;
  padding: 8px 16px;
  border: none;
  border-radius: 8px;
  background: var(--accent);
  color: #ffffff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
}

.assignment-form button:disabled,
.grade-form button:disabled {
  opacity: 0.6;
}

.grade-form input[type='number'] {
  width: 100px;
}

.actions {
  white-space: nowrap;
}

.link-btn {
  background: none;
  border: none;
  color: var(--accent);
  cursor: pointer;
  font-size: 12px;
  padding: 4px 6px;
}

.link-btn.danger {
  color: var(--wrong);
}

.empty {
  color: var(--text-dim);
  font-size: 13px;
}

.std-id {
  font-family: var(--mono);
  white-space: nowrap;
}

.not-attempted {
  color: var(--text-dim);
  font-size: 12px;
}

.grade-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 12px;
  color: #ffffff;
}

.grade-A {
  background: #16a34a;
}

.grade-B {
  background: #65a30d;
}

.grade-C {
  background: #ca8a04;
}

.grade-D {
  background: #ea580c;
}

.grade-E {
  background: #dc2626;
}

@media (prefers-color-scheme: dark) {
  .grade-badge {
    color: #0b0b0d;
  }

  .grade-A {
    background: #4ade80;
  }

  .grade-B {
    background: #a3e635;
  }

  .grade-C {
    background: #facc15;
  }

  .grade-D {
    background: #fb923c;
  }

  .grade-E {
    background: #f87171;
  }
}
</style>
