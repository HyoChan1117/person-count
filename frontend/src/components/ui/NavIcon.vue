<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.75"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="shrink-0"
    aria-hidden="true"
    v-html="PATHS[name]"
  />
</template>

<script setup>
// 단색(currentColor) 아이콘. 이모지 대신 쓴다. 새 아이콘 라이브러리 없이 필요한 것만 직접 정의한다.
// PATHS는 이 파일에 고정된 상수 문자열이라 v-html에 사용자 입력이 들어가지 않는다.
defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 20 },
})

const PATHS = {
  brand: '<rect x="3" y="7" width="13" height="10" rx="2.5"/><path d="m16 11 5-3v8l-5-3"/>',
  home: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  seats: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  face: '<path d="M4 8V6a2 2 0 0 1 2-2h2M16 4h2a2 2 0 0 1 2 2v2M20 16v2a2 2 0 0 1-2 2h-2M8 20H6a2 2 0 0 1-2-2v-2"/><path d="M9 10v1M15 10v1"/><path d="M9 15c.9.8 1.9 1.2 3 1.2s2.1-.4 3-1.2"/>',
  settings: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  camera: '<rect x="3" y="7" width="13" height="10" rx="2.5"/><path d="m16 11 5-3v8l-5-3"/>',
  desk: '<path d="M5 10h14"/><path d="M7 10v8M17 10v8"/><path d="M8 6h8a2 2 0 0 1 2 2v2H6V8a2 2 0 0 1 2-2z"/><path d="M6 18h2M16 18h2"/>',
  chair: '<path d="M8 4v8h8V4"/><path d="M7 12h10a2 2 0 0 1 2 2v2H5v-2a2 2 0 0 1 2-2z"/><path d="M7 16v4M17 16v4"/>',
  trash: '<path d="M4 7h16"/><path d="M10 11v6M14 11v6"/><path d="M6 7l1 14h10l1-14"/><path d="M9 7V4h6v3"/>',
  image: '<rect x="4" y="5" width="16" height="14" rx="2"/><circle cx="9" cy="10" r="1.5"/><path d="m7 17 4-4 3 3 2-2 3 3"/>',
  pin: '<path d="M12 21s6-5.2 6-11a6 6 0 0 0-12 0c0 5.8 6 11 6 11z"/><circle cx="12" cy="10" r="2"/>',
}
</script>
