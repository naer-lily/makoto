import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'

// The production reverse proxy serves /api; dev and preview forward it here.
// Self-checks can point MAKOTO_ENDPOINT at the real internal server.
const apiTarget = process.env.MAKOTO_ENDPOINT || 'http://localhost:8000'

/**
 * Emit the complete hashed build asset list so the service worker can
 * precache every route chunk, not only what index.html references.
 */
function pwaAssetManifest(): Plugin {
  return {
    name: 'makoto-pwa-asset-manifest',
    apply: 'build',
    generateBundle(_options, bundle) {
      const assets = Object.keys(bundle)
        .filter((fileName) => /^assets\/.+\.(css|js)$/.test(fileName))
        .map((fileName) => `/${fileName}`)
        .sort()
      this.emitFile({
        type: 'asset',
        fileName: 'sw-assets.json',
        source: JSON.stringify(assets),
      })
    },
  }
}

export default defineConfig({
  plugins: [vue(), pwaAssetManifest()],
  server: {
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  preview: {
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
})
