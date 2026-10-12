import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  // 3d-force-graph 体积大且通过动态 import 懒加载，显式纳入预构建，
  // 避免运行时首次发现依赖触发二次预构建导致 ERR_ABORTED
  optimizeDeps: {
    include: ['3d-force-graph']
  },
  server: {
    host: '0.0.0.0',
    allowedHosts: [
      '7d29555a711646dca61e9517c53cb25a--5173.ap-shanghai2.cloudstudio.club',
      '.cloudstudio.club',
      'localhost',
      '127.0.0.1'
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern-compiler',
        silenceDeprecations: ['legacy-js-api']
      }
    }
  },
})