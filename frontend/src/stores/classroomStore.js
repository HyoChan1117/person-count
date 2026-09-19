import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useClassroomStore = defineStore('classroom', () => {
  const classrooms = ref([])
  const current = ref(null)
  const loading = ref(false)
  const error = ref(null)

  async function fetchAll() {
    loading.value = true
    try {
      const { data } = await api.get('/classrooms/')
      classrooms.value = data
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.get(`/classrooms/${id}`)
      current.value = data
    } catch (e) {
      // 이전 교실의 이름·좌석이 새 교실 화면에 남지 않도록 비운다
      current.value = null
      error.value = e.response?.data?.detail ?? e.message
    } finally {
      loading.value = false
    }
  }

  async function createClassroom(payload) {
    const { data } = await api.post('/classrooms/', payload)
    classrooms.value.push(data)
    return data
  }

  async function saveClassroom(id, payload) {
    const { data } = await api.put(`/classrooms/${id}`, payload)
    current.value = data
    const idx = classrooms.value.findIndex(c => c.id === id)
    if (idx !== -1) classrooms.value[idx] = data
    return data
  }

  async function deleteClassroom(id) {
    await api.delete(`/classrooms/${id}`)
    classrooms.value = classrooms.value.filter(c => c.id !== id)
    if (current.value?.id === id) current.value = null
  }

  return { classrooms, current, loading, error, fetchAll, fetchOne, createClassroom, saveClassroom, deleteClassroom }
})
