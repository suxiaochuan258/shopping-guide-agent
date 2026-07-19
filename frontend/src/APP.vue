<template>
  <div id="app">
    <a-layout style="min-height: 100vh">
      <a-layout-header style="background: #001529; padding: 0 50px">
        <!-- 🔥 改成电商标题 -->
        <div style="color: white; font-size: 24px; font-weight: bold">
          🛒 HelloAgents智能电商导购助手
        </div>
      </a-layout-header>
      <a-layout-content style="padding: 24px">
        <router-view />
      </a-layout-content>
      <a-layout-footer style="text-align: center">
        <!-- 🔥 底部版权也改成电商 -->
        HelloAgents智能电商导购助手 ©2026 基于HelloAgents框架
      </a-layout-footer>
    </a-layout>
  </div>
</template>

<script setup lang="ts">
</script>

<style>
#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    Noto Sans, sans-serif;
}
</style>