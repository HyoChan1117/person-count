/** @type {import('tailwindcss').Config} */

// 색은 style.css의 CSS 변수(RGB 채널)를 참조한다. 컴포넌트에서는 hex를 쓰지 않고
// 여기서 노출한 토큰(bg-card, text-fg-muted, bg-state-occupied ...)만 사용한다.
const token = (name) => `rgb(var(--color-${name}) / <alpha-value>)`

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        canvas: token('canvas'),
        card: token('card'),
        line: token('line'),
        fg: token('fg'),
        'fg-muted': token('fg-muted'),
        // 상태색은 4가지 고정. 다른 용도로 쓰지 않는다.
        state: {
          occupied: token('state-occupied'),
          empty: token('state-empty'),
          unknown: token('state-unknown'),
          alert: token('state-alert'),
        },
      },
      fontFamily: {
        // 영문·숫자는 Inter, 한글은 Pretendard(Inter에는 한글이 없어 자동으로 넘어간다)
        ds: ['"Inter Variable"', '"Pretendard Variable"', 'Pretendard', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        // 1920x1080 기준: 멀리서도 읽히는 핵심 숫자 / 카드 라벨
        'metric-lg': ['6rem', { lineHeight: '1', fontWeight: '700', letterSpacing: '-0.02em' }],
        metric: ['4.5rem', { lineHeight: '1', fontWeight: '700', letterSpacing: '-0.02em' }],
        'metric-sm': ['2.5rem', { lineHeight: '1.1', fontWeight: '700', letterSpacing: '-0.01em' }],
        label: ['0.875rem', { lineHeight: '1.25rem', fontWeight: '500' }],
      },
      spacing: {
        gutter: '1rem',
        card: '1.5rem',
        section: '2rem',
      },
      borderRadius: {
        card: '0.75rem',
      },
    },
  },
  plugins: [],
}
