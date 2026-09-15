import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401 || err.response?.status === 403) {
      useAuthStore().logout()
    }
    return Promise.reject(err)
  }
)

export default api
