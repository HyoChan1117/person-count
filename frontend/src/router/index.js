import { createRouter, createWebHistory } from 'vue-router'
// 기존 HomeView.vue는 롤백용으로 파일만 보존한다(이 라우트에서는 더 이상 쓰지 않는다)
import HomeView from '@/views/HomeDashboardView.vue'
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

// 디자인 토대 확인용 (개발 모드에서만 등록, 프로덕션 빌드에는 포함되지 않는다)
if (import.meta.env.DEV) {
  routes.push({ path: '/__ds', name: 'DesignPreview', component: () => import('@/views/DesignPreview.vue') })
}

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
