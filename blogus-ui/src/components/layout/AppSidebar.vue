<template>
  <aside class="w-64 h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col">
    <!-- Logo/Brand -->
    <div class="p-4 border-b border-gray-200 dark:border-gray-700">
      <router-link to="/" class="flex items-center gap-2">
        <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </div>
        <span class="text-xl font-bold text-gray-900 dark:text-white">Blogus</span>
      </router-link>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 p-4 overflow-y-auto">
      <!-- Main Section -->
      <div class="space-y-1">
        <NavItem
          v-for="item in mainNavItems"
          :key="item.path"
          :item="item"
          :current-path="currentPath"
        />
      </div>

      <!-- Registry Section -->
      <div class="mt-6">
        <h3 class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Registry
        </h3>
        <div class="space-y-1">
          <NavItem
            v-for="item in registryItems"
            :key="item.path"
            :item="item"
            :current-path="currentPath"
          />
        </div>
      </div>

      <!-- Tools Section -->
      <div class="mt-6">
        <h3 class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Tools
        </h3>
        <div class="space-y-1">
          <NavItem
            v-for="item in toolItems"
            :key="item.path"
            :item="item"
            :current-path="currentPath"
          />
        </div>
      </div>
    </nav>

    <!-- Footer -->
    <div class="p-4 border-t border-gray-200 dark:border-gray-700">
      <p class="text-xs text-gray-500 text-center">
        Blogus v1.0.0
      </p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import NavItem from '@/components/ui/NavItem.vue'
import type { NavItem as NavItemType } from '@/types'

const route = useRoute()
const currentPath = computed(() => route.path)

const mainNavItems: NavItemType[] = [
  {
    name: 'Dashboard',
    path: '/',
    icon: 'home'
  },
  {
    name: 'Prompt Studio',
    path: '/prompts/studio',
    icon: 'sparkles'
  },
  {
    name: 'Prompts',
    path: '/prompts',
    icon: 'document-text'
  }
]

const registryItems: NavItemType[] = [
  {
    name: 'Deployments',
    path: '/deployments',
    icon: 'server'
  },
  {
    name: 'New Deployment',
    path: '/deployments/create',
    icon: 'plus-circle'
  }
]

const toolItems: NavItemType[] = [
  {
    name: 'Analyze',
    path: '/prompts/analyze',
    icon: 'chart-bar'
  },
  {
    name: 'Test Generator',
    path: '/prompts/test',
    icon: 'beaker'
  }
]
</script>
