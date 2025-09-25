<template>
  <div class="app">
    <!-- App Shell -->
    <AppShell>
      <!-- Sidebar -->
      <template #sidebar>
        <AppSidebar />
      </template>

      <!-- Header -->
      <template #header>
        <AppHeader />
      </template>

      <!-- Page Content -->
      <template #default>
        <main class="p-6">
          <RouterView />
        </main>
      </template>
    </AppShell>

    <!-- Global Toast Container -->
    <div id="toast-container" class="fixed top-4 right-4 z-50 space-y-2"></div>
  </div>
</template>

<script setup lang="ts">
import { AppShell } from '@skeletonlabs/skeleton'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
</script>

<style>
.app {
  min-height: 100vh;
}
</style>