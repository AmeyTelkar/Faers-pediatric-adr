import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    // Layer 16: Strip all console logs and comments in production
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.warn', 'console.error', 'console.debug'],
        passes: 3,
      },
      format: {
        comments: false,
      },
      mangle: {
        // Mangle variable names to make code unreadable
        toplevel: true,
        properties: {
          regex: /^_/,  // Mangle properties starting with _
        },
      },
    },
    // Chunk splitting to obscure code structure
    rollupOptions: {
      output: {
        manualChunks: undefined,
        entryFileNames: 'assets/pt-[hash].js',
        chunkFileNames: 'assets/pt-[hash].js',
        assetFileNames: 'assets/pt-[hash].[ext]',
      },
    },
    sourcemap: false, // NEVER expose source maps in production
  },
}))
