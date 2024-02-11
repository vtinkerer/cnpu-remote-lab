import { fileURLToPath, URL } from 'node:url';

import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import { nxViteTsPaths } from '@nx/vite/plugins/nx-tsconfig-paths.plugin';

// https://vitejs.dev/config/
export default ({ mode }: any) => {
  process.env = { ...process.env, ...loadEnv(mode, process.cwd()) };

  return defineConfig({
    plugins: [vue(), nxViteTsPaths()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      proxy: {
        '/api': {
          target:
            process.env.VITE_USE_OVERRIDE_HOSTS?.toLowerCase() === 'true'
              ? `http://${process.env.VITE_BACKEND_HOST}`
              : '/api', // replace with your backend API URL
          changeOrigin: true,
          secure: false,
        },
      },
    },
    esbuild: {
      keepNames: true,
    },
    // build: {
    //   minify: false,
    // },
    // build: {
    //   commonjsOptions: {
    //     transformMixedEsModules: true,
    //   },
    // },
  });
};
