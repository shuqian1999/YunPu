import { defineStore } from 'pinia'
import { login, register } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async login(credentials) {
      try {
        const response = await login(credentials)
        this.token = response.data.access_token
        localStorage.setItem('token', this.token)
        // You can decode token to get user info if needed
        return response
      } catch (error) {
        throw error
      }
    },

    async register(userData) {
      try {
        const response = await register(userData)
        this.token = response.data.access_token
        localStorage.setItem('token', this.token)
        return response
      } catch (error) {
        throw error
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    }
  }
})