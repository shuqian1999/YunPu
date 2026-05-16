import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/user/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import Persons from '../views/Persons.vue'
import PersonDetail from '../views/PersonDetail.vue'
import FamilyTree from '../views/FamilyTree.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/persons',
    name: 'Persons',
    component: Persons,
    meta: { requiresAuth: true }
  },
  {
    path: '/persons/:id',
    name: 'PersonDetail',
    component: PersonDetail,
    meta: { requiresAuth: true }
  },
  {
    path: '/family/tree',
    name: 'FamilyTree',
    component: FamilyTree,
    meta: { requiresAuth: true }
  },
  {
    path: '/',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('token') !== null
  
  if (to.meta.requiresAuth !== false && !isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router