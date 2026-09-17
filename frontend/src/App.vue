<template>
  <div class="flex h-screen">
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

const auth = useAuthStore()
</script>
