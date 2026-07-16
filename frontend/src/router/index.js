import { createRouter, createWebHistory } from 'vue-router'
import ClassroomListView from '@/views/ClassroomListView.vue'
import CameraSetupView from '@/views/CameraSetupView.vue'
import DashboardView from '@/views/DashboardView.vue'
import MapEditorView from '@/views/MapEditorView.vue'
import LoginView from '@/views/LoginView.vue'
import { useAuthStore } from '@/stores/authStore'

const routes = [
  { path: '/login', name: 'Login', component: LoginView, meta: { public: true } },
  { path: '/', redirect: '/classrooms' },
  { path: '/classrooms', name: 'ClassroomList', component: ClassroomListView },
  { path: '/classrooms/:id/setup', name: 'CameraSetup', component: CameraSetupView, meta: { admin: true } },
  { path: '/classrooms/:id/map', name: 'MapEditor', component: MapEditorView, meta: { admin: true } },
  { path: '/dashboard/:id', name: 'Dashboard', component: DashboardView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) return { name: 'Login' }
  if (to.name === 'Login' && auth.isAuthenticated) return { name: 'ClassroomList' }
  if (to.meta.admin && !auth.isAdmin) return { name: 'ClassroomList' }
})

export default router
