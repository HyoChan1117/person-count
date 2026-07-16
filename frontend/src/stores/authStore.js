import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('auth_token'))
  const user = ref(JSON.parse(localStorage.getItem('auth_user') || 'null'))

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => !!user.value?.is_admin)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('auth_token', newToken)
    try {
      const payload = JSON.parse(atob(newToken.split('.')[1]))
      user.value = { email: payload.sub, name: payload.name, picture: payload.picture, is_admin: payload.is_admin }
      localStorage.setItem('auth_user', JSON.stringify(user.value))
    } catch {
      // ignore malformed token
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  }

  return { token, user, isAuthenticated, isAdmin, setToken, logout }
})
