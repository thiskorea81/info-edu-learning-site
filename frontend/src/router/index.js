import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, isTeacher, mustChangePassword } from '../auth'
import Login from '../views/Login.vue'
import ChangePassword from '../views/ChangePassword.vue'
import TeacherDashboard from '../views/TeacherDashboard.vue'
import SubjectList from '../views/SubjectList.vue'
import UnitList from '../views/UnitList.vue'
import UnitQuestions from '../views/UnitQuestions.vue'
import QuestionSolve from '../views/QuestionSolve.vue'
import WrongNotes from '../views/WrongNotes.vue'
import SimilarPractice from '../views/SimilarPractice.vue'
import Stats from '../views/Stats.vue'
import ProblemList from '../views/ProblemList.vue'
import ProblemTextbookCategories from '../views/ProblemTextbookCategories.vue'
import ProblemCategory from '../views/ProblemCategory.vue'
import ProblemSolve from '../views/ProblemSolve.vue'
import AddQuestion from '../views/AddQuestion.vue'
import MaterialSubjectList from '../views/MaterialSubjectList.vue'
import MaterialUnitList from '../views/MaterialUnitList.vue'
import MaterialUnitStandards from '../views/MaterialUnitStandards.vue'
import MaterialDetail from '../views/MaterialDetail.vue'
import AssignmentList from '../views/AssignmentList.vue'
import AssignmentDetail from '../views/AssignmentDetail.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: Login, meta: { public: true } },
    { path: '/change-password', name: 'change-password', component: ChangePassword },
    {
      path: '/teacher',
      name: 'teacher-dashboard',
      component: TeacherDashboard,
      meta: { teacherOnly: true },
    },
    { path: '/', name: 'subjects', component: SubjectList },
    { path: '/subjects/:subject', name: 'subject-units', component: UnitList, props: true },
    {
      path: '/subjects/:subject/units/:unit',
      name: 'unit-questions',
      component: UnitQuestions,
      props: true,
    },
    { path: '/questions/:id', name: 'question-solve', component: QuestionSolve, props: true },
    { path: '/wrong-notes', name: 'wrong-notes', component: WrongNotes, meta: { studentOnly: true } },
    {
      path: '/practice/:standardId',
      name: 'similar-practice',
      component: SimilarPractice,
      props: true,
      meta: { studentOnly: true },
    },
    { path: '/stats', name: 'stats', component: Stats, meta: { studentOnly: true } },
    { path: '/problems', name: 'problems', component: ProblemList },
    { path: '/problems/textbook', name: 'problem-textbook', component: ProblemTextbookCategories },
    {
      path: '/problems/category/:categoryKey',
      name: 'problem-category',
      component: ProblemCategory,
      props: true,
    },
    { path: '/problems/:id', name: 'problem-solve', component: ProblemSolve, props: true },
    { path: '/add-question', name: 'add-question', component: AddQuestion },
    { path: '/materials', name: 'materials', component: MaterialSubjectList },
    {
      path: '/materials/subjects/:subject',
      name: 'material-subject-units',
      component: MaterialUnitList,
      props: true,
    },
    {
      path: '/materials/subjects/:subject/units/:unit',
      name: 'material-unit-standards',
      component: MaterialUnitStandards,
      props: true,
    },
    {
      path: '/materials/:standardId',
      name: 'material-detail',
      component: MaterialDetail,
      props: true,
    },
    {
      path: '/assignments',
      name: 'assignments',
      component: AssignmentList,
      meta: { studentOnly: true },
    },
    {
      path: '/assignments/:id',
      name: 'assignment-detail',
      component: AssignmentDetail,
      props: true,
      meta: { studentOnly: true },
    },
  ],
})

router.beforeEach((to) => {
  if (!to.meta.public && !isLoggedIn()) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (isLoggedIn() && mustChangePassword() && to.name !== 'change-password') {
    return { name: 'change-password' }
  }
  if (to.meta.teacherOnly && !isTeacher()) {
    return { name: 'subjects' }
  }
  if (to.meta.studentOnly && isTeacher()) {
    return { name: 'subjects' }
  }
  if (to.name === 'login' && isLoggedIn()) {
    return { name: 'subjects' }
  }
  return true
})

export default router
