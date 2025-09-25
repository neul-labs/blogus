<template>
  <nav class="w-64 h-full bg-surface-50-900-token border-r border-surface-300-600-token">
    <div class="p-4">
      <!-- Main Navigation -->
      <div class="space-y-2">
        <h3 class="text-sm font-semibold text-surface-600-300-token uppercase tracking-wider mb-3">
          Navigation
        </h3>

        <NavItem
          v-for="item in navigationItems"
          :key="item.path"
          :item="item"
          :current-path="currentPath"
        />
      </div>

      <!-- Tools Section -->
      <div class="mt-8 space-y-2">
        <h3 class="text-sm font-semibold text-surface-600-300-token uppercase tracking-wider mb-3">
          Tools
        </h3>

        <NavItem
          v-for="item in toolItems"
          :key="item.path"
          :item="item"
          :current-path="currentPath"
        />
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import NavItem from '@/components/ui/NavItem.vue'
import type { NavItem as NavItemType } from '@/types'

const route = useRoute()
const currentPath = computed(() => route.path)

const navigationItems: NavItemType[] = [
  {
    name: 'Dashboard',
    path: '/',
    icon: 'home'
  },
  {
    name: 'Prompts',
    path: '/prompts',
    icon: 'document-text'
  },
  {
    name: 'Templates',
    path: '/templates',
    icon: 'template'
  }
]

const toolItems: NavItemType[] = [
  {
    name: 'Analyze Prompt',
    path: '/prompts/analyze',
    icon: 'chart-bar'
  },
  {
    name: 'Execute Prompt',
    path: '/prompts/execute',
    icon: 'play'
  },
  {
    name: 'Generate Tests',
    path: '/prompts/test',
    icon: 'beaker'
  },
  {
    name: 'Create Template',
    path: '/templates/create',
    icon: 'plus'
  }
]
</script>