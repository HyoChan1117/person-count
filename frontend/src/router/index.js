import { createRouter, createWebHistory } from 'vue-router'
import ClassroomListView from '@/views/ClassroomListView.vue'
import CameraSetupView from '@/views/CameraSetupView.vue'
import DashboardView from '@/views/DashboardView.vue'
import MapEditorView from '@/views/MapEditorView.vue'

const routes = [
  { path: '/', redirect: '/classrooms' },
  { path: '/classrooms', name: 'ClassroomList', component: ClassroomListView },
  { path: '/classrooms/:id/setup', name: 'CameraSetup', component: CameraSetupView },
  { path: '/classrooms/:id/map', name: 'MapEditor', component: MapEditorView },
  { path: '/dashboard/:id', name: 'Dashboard', component: DashboardView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
