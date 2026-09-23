// 실제 카메라/사진이 없을 때 로컬 플레이스홀더 이미지를 생성한다.
export function generateMockImageDataUrl(text = 'MOCK', width = 640, height = 360, bg = '#3f3f46') {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  ctx.fillStyle = bg
  ctx.fillRect(0, 0, width, height)
  ctx.strokeStyle = 'rgba(255,255,255,0.15)'
  ctx.lineWidth = 1
  for (let x = 0; x < width; x += 32) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke()
  }
  for (let y = 0; y < height; y += 32) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke()
  }
  ctx.fillStyle = 'rgba(255,255,255,0.7)'
  ctx.font = `bold ${Math.round(height * 0.09)}px sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, width / 2, height / 2)
  return canvas.toDataURL('image/jpeg', 0.85)
}
