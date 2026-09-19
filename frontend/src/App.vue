<template>
  <div class="flex h-screen bg-canvas text-fg">
    <template v-if="auth.isAdmin">
      <Sidebar />
      <main class="flex-1 overflow-hidden">
        <router-view />
      </main>
    </template>
    <AdminLoginModal v-else />
  </div>
</template>

<script setup>
import Sidebar from '@/components/layout/Sidebar.vue'
import AdminLoginModal from '@/components/modals/AdminLoginModal.vue'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'

const auth = useAuthStore()
useThemeStore()
</script>
