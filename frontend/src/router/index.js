import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/user/Login.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    redirect: '/login'
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
