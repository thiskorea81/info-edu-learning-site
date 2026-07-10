import { createRouter, createWebHistory } from 'vue-router'
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

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'subjects', component: SubjectList },
    { path: '/subjects/:subject', name: 'subject-units', component: UnitList, props: true },
    {
      path: '/subjects/:subject/units/:unit',
      name: 'unit-questions',
      component: UnitQuestions,
      props: true,
    },
    { path: '/questions/:id', name: 'question-solve', component: QuestionSolve, props: true },
    { path: '/wrong-notes', name: 'wrong-notes', component: WrongNotes },
    {
      path: '/practice/:standardId',
      name: 'similar-practice',
      component: SimilarPractice,
      props: true,
    },
    { path: '/stats', name: 'stats', component: Stats },
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
  ],
})

export default router
