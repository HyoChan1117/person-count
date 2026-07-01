<template>
  <div class="flex flex-col h-screen">
    <NavBar />
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from '@/components/layout/NavBar.vue'
</script>
