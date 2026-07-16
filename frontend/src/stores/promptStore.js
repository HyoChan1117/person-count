import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const usePromptStore = defineStore('prompt', () => {
  const config = ref({ system_prompt: '', default_user_prompt: '' })
  const loading = ref(false)
  const saving = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const { data } = await api.get('/prompts/')
      config.value = data
    } finally {
      loading.value = false
    }
  }

  async function save(payload) {
    saving.value = true
    try {
      const { data } = await api.put('/prompts/', payload)
      config.value = data
    } finally {
      saving.value = false
    }
  }

  return { config, loading, saving, fetch, save }
})
