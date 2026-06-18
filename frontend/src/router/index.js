import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/user/Login.vue'
import Dashboard from '../views/Dashboard/index.vue'
import Persons from '../views/Persons/index.vue'
import PersonDetail from '../views/PersonDetail/index.vue'
import Settings from '../views/Settings/index.vue'
import Groups from '../views/Groups/index.vue'
import FamilyRelations from '../views/FamilyRelations/index.vue'

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
    path: '/family',
    name: 'FamilyRelations',
    component: FamilyRelations,
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings,
    meta: { requiresAuth: true }
  },
  {
    path: '/groups',
    name: 'Groups',
    component: Groups,
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