import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('admin_token'))

  const isAdmin = computed(() => !!token.value)

  async function login(password) {
    const res = await axios.post('/auth/admin/login', { password })
    token.value = res.data.token
    localStorage.setItem('admin_token', token.value)
  }

  function logout() {
    token.value = null
    localStorage.removeItem('admin_token')
  }

  return { token, isAdmin, login, logout }
})
