// 데모용 카메라 프레임을 canvas로 그려 base64 JPEG로 돌려준다.
// 실제 사진이 아니라 좌석 영역과 얼굴 없는 실루엣만 그린다(개인정보 지침).
import { cssColor } from '@/utils/cssColor'
import { seatStateAt, FRAME_SIZE } from './state'

function silhouette(ctx, cx, top, w, h, color) {
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.arc(cx, top + h * 0.28, h * 0.17, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.ellipse(cx, top + h * 0.82, w * 0.34, h * 0.32, 0, Math.PI, 0)
  ctx.fill()
}

export function renderFrame(classroomId, cameraId, ts) {
  const state = seatStateAt(classroomId, ts)
  if (!state) return null
  const camera = state.room.classroom.cameras.find((c) => c.camera_id === cameraId) ?? state.room.classroom.cameras[0]

  const { width, height } = FRAME_SIZE
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')

  ctx.fillStyle = cssColor('canvas')
  ctx.fillRect(0, 0, width, height)
  ctx.fillStyle = cssColor('card')
  ctx.fillRect(40, 70, width - 80, height - 110)
  ctx.strokeStyle = cssColor('line')
  ctx.lineWidth = 1
  for (let x = 40; x <= width - 40; x += 80) { ctx.beginPath(); ctx.moveTo(x, 70); ctx.lineTo(x, height - 40); ctx.stroke() }
  for (let y = 70; y <= height - 40; y += 80) { ctx.beginPath(); ctx.moveTo(40, y); ctx.lineTo(width - 40, y); ctx.stroke() }

  camera.seat_ids.forEach((sid) => {
    const [f1, f2, b1, b2] = camera.seat_lines[sid]
    const seatState = state.seats[sid] // 없으면 판정 불가
    const x = Math.min(f1[0], b1[0])
    const y = b1[1]
    const w = Math.max(f2[0], b2[0]) - x
    const h = f1[1] - y

    ctx.beginPath()
    ctx.moveTo(b1[0], b1[1]); ctx.lineTo(b2[0], b2[1]); ctx.lineTo(f2[0], f2[1]); ctx.lineTo(f1[0], f1[1]); ctx.closePath()
    if (seatState === 'occupied') {
      ctx.fillStyle = cssColor('state-occupied', 0.22)
      ctx.strokeStyle = cssColor('state-occupied')
    } else if (seatState === 'empty') {
      ctx.fillStyle = cssColor('state-empty', 0.12)
      ctx.strokeStyle = cssColor('state-empty')
    } else {
      ctx.fillStyle = cssColor('state-unknown', 0.14)
      ctx.strokeStyle = cssColor('state-unknown')
    }
    ctx.lineWidth = 2
    ctx.fill()
    ctx.stroke()

    if (seatState === 'occupied') {
      silhouette(ctx, x + w / 2, y - h * 0.9, w, h * 2.1, cssColor('fg-muted', 0.75))
    } else if (seatState !== 'empty') {
      ctx.fillStyle = cssColor('state-unknown')
      ctx.font = '600 28px "Inter Variable", system-ui, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('?', x + w / 2, y + h / 2 + 10)
    }

    ctx.fillStyle = cssColor('fg-muted')
    ctx.font = '500 16px "Inter Variable", system-ui, sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(sid, x + w / 2, f1[1] + 22)
  })

  ctx.textAlign = 'left'
  ctx.fillStyle = cssColor('fg')
  ctx.font = '600 22px "Inter Variable", "Pretendard Variable", system-ui, sans-serif'
  ctx.fillText(`${state.room.classroom.name} · ${camera.name}`, 44, 44)
  ctx.fillStyle = cssColor('fg-muted')
  ctx.font = '500 16px "Inter Variable", system-ui, sans-serif'
  ctx.fillText(`DEMO · ${state.label}`, width - 220, 44)

  return canvas.toDataURL('image/jpeg', 0.82).split(',')[1]
}
