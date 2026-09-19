import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

function getInitial() {
  const saved = localStorage.getItem('theme')
  if (saved === 'dark' || saved === 'light') return saved
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref(getInitial())

  function apply() {
    document.documentElement.classList.toggle('dark', mode.value === 'dark')
  }

  function toggle() {
    mode.value = mode.value === 'dark' ? 'light' : 'dark'
  }

  watch(mode, (v) => {
    localStorage.setItem('theme', v)
    apply()
  }, { immediate: true })

  return { mode, toggle }
})
