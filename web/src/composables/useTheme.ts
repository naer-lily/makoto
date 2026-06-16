import { ref, computed, watch } from 'vue'

type ThemeMode = 'light' | 'dark' | 'auto'

const STORAGE_KEY = 'makoto_theme'

function getStoredMode(): ThemeMode {
  try {
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === 'light' || v === 'dark' || v === 'auto') return v
  } catch {
    // localStorage unavailable, fall through
  }
  return 'auto'
}

const mode = ref<ThemeMode>(getStoredMode())

const systemDark = ref(window.matchMedia('(prefers-color-scheme: dark)').matches)
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  systemDark.value = e.matches
})

const isDark = computed(() => (mode.value === 'auto' ? systemDark.value : mode.value === 'dark'))

watch(
  isDark,
  (dark) => {
    document.documentElement.classList.toggle('dark', dark)
  },
  { immediate: true },
)

export function useTheme() {
  function setTheme(newMode: ThemeMode) {
    mode.value = newMode
    try {
      localStorage.setItem(STORAGE_KEY, newMode)
    } catch {
      // localStorage unavailable
    }
  }

  function toggleTheme() {
    const cycle: Record<ThemeMode, ThemeMode> = { light: 'dark', dark: 'auto', auto: 'light' }
    setTheme(cycle[mode.value])
  }

  const modeLabel = computed(() => {
    const labels: Record<ThemeMode, string> = { light: '浅色模式', dark: '深色模式', auto: '跟随系统' }
    return labels[mode.value]
  })

  return { mode, isDark, modeLabel, setTheme, toggleTheme }
}
