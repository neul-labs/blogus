import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '@/views/HomePage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomePage,
      meta: {
        title: 'Blogus - AI Prompt Engineering'
      }
    },
    {
      path: '/prompts',
      name: 'prompts',
      component: () => import('@/views/PromptsPage.vue'),
      meta: {
        title: 'Prompts - Blogus'
      }
    },
    {
      path: '/prompts/analyze',
      name: 'analyze',
      component: () => import('@/views/AnalyzePage.vue'),
      meta: {
        title: 'Analyze Prompt - Blogus'
      }
    },
    {
      path: '/prompts/execute',
      name: 'execute',
      component: () => import('@/views/ExecutePage.vue'),
      meta: {
        title: 'Execute Prompt - Blogus'
      }
    },
    {
      path: '/prompts/test',
      name: 'test',
      component: () => import('@/views/TestPage.vue'),
      meta: {
        title: 'Generate Tests - Blogus'
      }
    },
    {
      path: '/templates',
      name: 'templates',
      component: () => import('@/views/TemplatesPage.vue'),
      meta: {
        title: 'Templates - Blogus'
      }
    },
    {
      path: '/templates/create',
      name: 'create-template',
      component: () => import('@/views/CreateTemplatePage.vue'),
      meta: {
        title: 'Create Template - Blogus'
      }
    },
    {
      path: '/templates/:id',
      name: 'template-detail',
      component: () => import('@/views/TemplateDetailPage.vue'),
      meta: {
        title: 'Template Details - Blogus'
      }
    },
    {
      path: '/404',
      name: 'not-found',
      component: () => import('@/views/NotFoundPage.vue'),
      meta: {
        title: 'Page Not Found - Blogus'
      }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/404'
    }
  ]
})

// Global navigation guards
router.beforeEach((to, from, next) => {
  // Update document title
  if (to.meta.title) {
    document.title = to.meta.title as string
  }

  next()
})

export default router