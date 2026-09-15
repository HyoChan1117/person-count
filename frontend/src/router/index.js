import { createRouter, createWebHistory } from 'vue-router'
import ClassroomListView from '@/views/ClassroomListView.vue'
import CameraSetupView from '@/views/CameraSetupView.vue'
import DashboardView from '@/views/DashboardView.vue'
import MapEditorView from '@/views/MapEditorView.vue'
import MonitoringView from '@/views/MonitoringView.vue'
const routes = [
  { path: '/', redirect: '/classrooms' },
  { path: '/classrooms', name: 'ClassroomList', component: ClassroomListView },
  { path: '/classrooms/:id/setup', name: 'CameraSetup', component: CameraSetupView },
  { path: '/classrooms/:id/map', name: 'MapEditor', component: MapEditorView },
  { path: '/dashboard/:id', name: 'Dashboard', component: DashboardView },
  { path: '/monitoring/:id', name: 'Monitoring', component: MonitoringView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
