<template>
  <div class="app h-screen bg-gray-50 flex overflow-hidden">
    <!-- Sidebar - Fixed -->
    <AppSidebar class="hidden lg:flex flex-shrink-0" />

    <!-- Main Content - Scrollable -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- Header - Fixed -->
      <AppHeader class="flex-shrink-0" />

      <!-- Page Content - Scrollable -->
      <main class="flex-1 p-6 overflow-y-auto">
        <RouterView />
      </main>
    </div>

    <!-- Global Toast Container -->
    <div id="toast-container" class="fixed top-4 right-4 z-50 space-y-2"></div>
  </div>
</template>

<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
</script>
