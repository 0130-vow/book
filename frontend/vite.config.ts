import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icon-192.png", "icon-512.png"],
      manifest: {
        name: "BookHub 私人书房",
        short_name: "BookHub",
        description: "私人数字阅读聚合平台",
        theme_color: "#173f35",
        background_color: "#f4f6f3",
        display: "standalone",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png" }
        ]
      },
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /\/api\/catalog\/.*\/chapters\//,
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: "bookhub-chapters",
              expiration: { maxEntries: 300, maxAgeSeconds: 60 * 60 * 24 * 90 }
            }
          }
        ]
      }
    })
  ],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000"
    }
  }
});
