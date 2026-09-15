<template>
  <div class="flex flex-col h-screen">
    <template v-if="auth.isAdmin">
      <NavBar />
      <main class="flex-1 overflow-hidden">
        <router-view />
      </main>
    </template>
    <AdminLoginModal v-else />
  </div>
</template>

<script setup>
import NavBar from '@/components/layout/NavBar.vue'
import AdminLoginModal from '@/components/modals/AdminLoginModal.vue'
import { useAuthStore } from '@/stores/authStore'

const auth = useAuthStore()
</script>
