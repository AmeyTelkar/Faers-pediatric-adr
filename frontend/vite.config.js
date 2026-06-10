import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { viteObfuscateFile } from 'vite-plugin-obfuscator'

export default defineConfig(({ mode }) => ({
  plugins: [
    react(),
    // Layer 17: JavaScript Obfuscation (production only)
    ...(mode === 'production' ? [
      viteObfuscateFile({
        options: {
          compact: true,
          controlFlowFlattening: true,
          controlFlowFlatteningThreshold: 0.75,
          deadCodeInjection: true,
          deadCodeInjectionThreshold: 0.4,
          debugProtection: true,
          debugProtectionInterval: 2000,
          disableConsoleOutput: true,
          identifierNamesGenerator: 'hexadecimal',
          log: false,
          numbersToExpressions: true,
          renameGlobals: false,
          selfDefending: true,
          simplify: true,
          splitStrings: true,
          splitStringsChunkLength: 5,
          stringArray: true,
          stringArrayCallsTransform: true,
          stringArrayEncoding: ['base64'],
          stringArrayIndexShift: true,
          stringArrayRotate: true,
          stringArrayShuffle: true,
          stringArrayWrappersCount: 2,
          stringArrayWrappersChainedCalls: true,
          stringArrayWrappersParametersMaxCount: 4,
          stringArrayWrappersType: 'function',
          stringArrayThreshold: 0.75,
          transformObjectKeys: true,
          unicodeEscapeSequence: false,
        },
      }),
    ] : []),
  ],
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

