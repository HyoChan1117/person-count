import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import ClassroomListView from '@/views/ClassroomListView.vue'
import CameraSetupView from '@/views/CameraSetupView.vue'
import DashboardView from '@/views/DashboardView.vue'
import MapEditorView from '@/views/MapEditorView.vue'
import MonitoringView from '@/views/MonitoringView.vue'
import FacePlaceListView from '@/views/FacePlaceListView.vue'
import FaceZoneView from '@/views/FaceZoneView.vue'
import FaceCameraSetupView from '@/views/FaceCameraSetupView.vue'
import FaceMonitoringView from '@/views/FaceMonitoringView.vue'
import FacePeopleView from '@/views/FacePeopleView.vue'
const routes = [
  { path: '/', name: 'Home', component: HomeView },
  { path: '/classrooms', name: 'ClassroomList', component: ClassroomListView },
  { path: '/classrooms/:id/setup', name: 'CameraSetup', component: CameraSetupView },
  { path: '/classrooms/:id/map', name: 'MapEditor', component: MapEditorView },
  { path: '/dashboard/:id', name: 'Dashboard', component: DashboardView },
  { path: '/monitoring/:id', name: 'Monitoring', component: MonitoringView },
  { path: '/face', name: 'FacePlaceList', component: FacePlaceListView },
  { path: '/face/people', name: 'FacePeople', component: FacePeopleView },
  { path: '/face/:id/zones', name: 'FaceZones', component: FaceZoneView },
  { path: '/face/:id/camera', name: 'FaceCameraSetup', component: FaceCameraSetupView },
  { path: '/face/:id/monitoring', name: 'FaceMonitoring', component: FaceMonitoringView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
