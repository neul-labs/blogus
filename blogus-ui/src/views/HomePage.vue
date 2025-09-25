<template>
  <div class="space-y-8">
    <!-- Hero Section -->
    <section class="text-center py-12">
      <h1 class="text-4xl md:text-6xl font-bold gradient-text mb-4">
        Welcome to Blogus
      </h1>
      <p class="text-xl text-surface-600-300-token mb-8 max-w-3xl mx-auto">
        A comprehensive platform for crafting, analyzing, and perfecting AI prompts with advanced features
      </p>

      <div class="flex flex-wrap justify-center gap-4">
        <RouterLink
          to="/prompts/analyze"
          class="btn variant-filled-primary"
        >
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
          </svg>
          Analyze Prompt
        </RouterLink>

        <RouterLink
          to="/templates"
          class="btn variant-outline-primary"
        >
          <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z"/>
          </svg>
          Browse Templates
        </RouterLink>
      </div>
    </section>

    <!-- Features Grid -->
    <section class="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="feature in features"
        :key="feature.title"
        class="card p-6 space-y-4 hover:scale-105 transition-transform"
      >
        <div class="flex items-center space-x-3">
          <div class="p-2 bg-primary-500 rounded-lg">
            <component :is="feature.icon" class="w-6 h-6 text-white" />
          </div>
          <h3 class="text-xl font-semibold">{{ feature.title }}</h3>
        </div>

        <p class="text-surface-600-300-token">
          {{ feature.description }}
        </p>

        <RouterLink
          :to="feature.link"
          class="btn btn-sm variant-ghost-primary inline-flex items-center"
        >
          Learn More
          <svg class="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </RouterLink>
      </div>
    </section>

    <!-- Quick Stats -->
    <section class="bg-surface-100-800-token rounded-lg p-6">
      <h2 class="text-2xl font-semibold mb-6 text-center">Quick Stats</h2>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="text-center">
          <div class="text-3xl font-bold text-primary-500">{{ stats.prompts }}</div>
          <div class="text-sm text-surface-600-300-token">Total Prompts</div>
        </div>

        <div class="text-center">
          <div class="text-3xl font-bold text-secondary-500">{{ stats.templates }}</div>
          <div class="text-sm text-surface-600-300-token">Templates</div>
        </div>

        <div class="text-center">
          <div class="text-3xl font-bold text-tertiary-500">{{ stats.analyses }}</div>
          <div class="text-sm text-surface-600-300-token">Analyses Run</div>
        </div>

        <div class="text-center">
          <div class="text-3xl font-bold text-success-500">{{ stats.executions }}</div>
          <div class="text-sm text-surface-600-300-token">Executions</div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const stats = ref({
  prompts: 0,
  templates: 0,
  analyses: 0,
  executions: 0
})

const features = [
  {
    title: 'Prompt Analysis',
    description: 'Analyze your prompts for effectiveness and goal alignment with advanced AI models.',
    icon: 'AnalyzeIcon',
    link: '/prompts/analyze'
  },
  {
    title: 'Prompt Execution',
    description: 'Execute prompts against various LLM models and compare results instantly.',
    icon: 'ExecuteIcon',
    link: '/prompts/execute'
  },
  {
    title: 'Test Generation',
    description: 'Automatically generate comprehensive test cases for your prompts.',
    icon: 'TestIcon',
    link: '/prompts/test'
  },
  {
    title: 'Template Management',
    description: 'Create, organize, and reuse prompt templates with variable substitution.',
    icon: 'TemplateIcon',
    link: '/templates'
  },
  {
    title: 'Batch Processing',
    description: 'Process multiple prompts efficiently with batch operations and parallel execution.',
    icon: 'BatchIcon',
    link: '/prompts'
  },
  {
    title: 'Model Integration',
    description: 'Connect with multiple AI providers including OpenAI, Anthropic, and Groq.',
    icon: 'ModelIcon',
    link: '/prompts/execute'
  }
]

onMounted(() => {
  // Simulate loading stats - in real app, fetch from API
  setTimeout(() => {
    stats.value = {
      prompts: 127,
      templates: 34,
      analyses: 892,
      executions: 1456
    }
  }, 500)
})
</script>

<script lang="ts">
export default {
  components: {
    AnalyzeIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/>
        </svg>
      `
    },
    ExecuteIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd"/>
        </svg>
      `
    },
    TestIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M7 2a1 1 0 00-.707 1.707L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7zm2 6.172V4h2v4.172a3 3 0 00.879 2.12l1.027 1.028a4 4 0 00-2.171.102l-.47.156a4 4 0 01-2.53 0l-.563-.187a1.993 1.993 0 00-.306-.084l1.342-1.342A3 3 0 009 8.172z" clip-rule="evenodd"/>
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
    BatchIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"/>
          <path fill-rule="evenodd" d="M4 5a2 2 0 012-2v1a1 1 0 001 1h6a1 1 0 001-1V3a2 2 0 012 2v6h-3a1 1 0 100 2h3v3a2 2 0 01-2 2H6a2 2 0 01-2-2V5z" clip-rule="evenodd"/>
        </svg>
      `
    },
    ModelIcon: {
      template: `
        <svg fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
      `
    }
  }
}
</script>

<style scoped>
.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
</style>