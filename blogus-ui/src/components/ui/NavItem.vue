<template>
  <RouterLink
    :to="item.path"
    class="nav-item"
    :class="{
      'nav-item--active': isActive
    }"
  >
    <div class="nav-item__content">
      <!-- Icon -->
      <div class="nav-item__icon">
        <component :is="iconComponent" class="w-5 h-5" />
      </div>

      <!-- Label -->
      <span class="nav-item__label">{{ item.name }}</span>
    </div>

    <!-- Badge (if any) -->
    <div v-if="item.badge" class="nav-item__badge">
      {{ item.badge }}
    </div>
  </RouterLink>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { NavItem } from '@/types'

interface Props {
  item: NavItem
  currentPath: string
}

const props = defineProps<Props>()

const isActive = computed(() => {
  if (props.item.path === '/') {
    return props.currentPath === '/'
  }
  return props.currentPath.startsWith(props.item.path)
})

// Simple icon mapping - in a real app you'd use a proper icon library
const iconComponents = {
  home: 'HomeIcon',
  'document-text': 'DocumentTextIcon',
  template: 'TemplateIcon',
  'chart-bar': 'ChartBarIcon',
  play: 'PlayIcon',
  beaker: 'BeakerIcon',
  plus: 'PlusIcon'
}

const iconComponent = computed(() => {
  return iconComponents[props.item.icon as keyof typeof iconComponents] || 'div'
})
</script>

<script lang="ts">
// Icon components - simplified SVG icons
export default {
  components: {
    HomeIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z"/>
        </svg>
      `
    },
    DocumentTextIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"/>
        </svg>
      `
    },
    TemplateIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
        </svg>
      `
    },
    ChartBarIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
        </svg>
      `
    },
    PlayIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
        </svg>
      `
    },
    BeakerIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M7 2a1 1 0 00-.707 1.707L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7zm2 6.172V4h2v4.172a3 3 0 00.879 2.12l1.027 1.028a4 4 0 00-2.171.102l-.47.156a4 4 0 01-2.53 0l-.563-.187a1.993 1.993 0 00-.306-.084l1.342-1.342A3 3 0 009 8.172z" clip-rule="evenodd"/>
        </svg>
      `
    },
    PlusIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd"/>
        </svg>
      `
    }
  }
}
</script>

<style scoped>
.nav-item {
  @apply flex items-center justify-between w-full px-3 py-2 text-sm rounded-lg transition-colors;
  @apply text-surface-700 dark:text-surface-300;
  @apply hover:bg-surface-200 dark:hover:bg-surface-700;
  @apply focus:bg-surface-200 dark:focus:bg-surface-700 focus:outline-none;
}

.nav-item--active {
  @apply bg-primary-100 dark:bg-primary-900;
  @apply text-primary-700 dark:text-primary-300;
  @apply border-r-2 border-primary-500;
}

.nav-item__content {
  @apply flex items-center space-x-3;
}

.nav-item__icon {
  @apply flex-shrink-0;
}

.nav-item__label {
  @apply font-medium;
}

.nav-item__badge {
  @apply inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none;
  @apply text-white bg-primary-600 rounded-full;
}
</style>