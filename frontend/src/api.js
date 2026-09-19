import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'
import { demoAdapter } from '@/demo/adapter'

const api = axios.create({ baseURL: '/api' })

// 데모 모드(VITE_DEMO_MODE=true)에서만 실제 네트워크 대신 목 데이터를 돌려준다.
if (import.meta.env.VITE_DEMO_MODE === 'true') api.defaults.adapter = demoAdapter

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
