<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import api from '../api'
import RichEditor from '../components/RichEditor.vue'

const route = useRoute()

const subjects = ref([])
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

async function loadSubjects() {
  const { data } = await api.get('/api/subject-admin')
  subjects.value = data
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
  const match = subjects.value.find((s) => s.name === subjectName)
  if (!match) return
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
  await loadSubjects()
  if (route.query.subject) {
    await applyReportQuickCreate()
  }
})
</script>

<template>
  <h1>과제</h1>

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

<style scoped>
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

.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--border);
  display: inline-block;
  margin-right: 4px;
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
</style>
