import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './composables/useTheme'
import './styles/global.css'

/**
 * Expose the visible viewport height (which shrinks when a mobile keyboard
 * opens) so dialogs can keep their footer/buttons on screen.
 */
function syncViewportHeight(): void {
  const height = window.visualViewport?.height ?? window.innerHeight
  document.documentElement.style.setProperty('--app-viewport-height', `${Math.round(height)}px`)
}

syncViewportHeight()
window.visualViewport?.addEventListener('resize', syncViewportHeight)
window.addEventListener('orientationchange', syncViewportHeight)

const app = createApp(App)
app.use(ElementPlus)
app.use(router)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')

/**
 * Register the app-shell service worker. `updateViaCache: 'none'` ensures the
 * browser revalidates sw.js, and update() checks for a new worker immediately.
 */
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/', updateViaCache: 'none' })
      .then((registration) => registration.update())
      .catch((error: unknown) => {
        console.warn('Service worker registration failed', error)
      })
  })
}
