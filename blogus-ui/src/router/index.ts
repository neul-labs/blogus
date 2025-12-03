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
    // Deployments (Registry)
    {
      path: '/deployments',
      name: 'deployments',
      component: () => import('@/views/DeploymentsPage.vue'),
      meta: {
        title: 'Deployments - Blogus'
      }
    },
    {
      path: '/deployments/create',
      name: 'create-deployment',
      component: () => import('@/views/CreateDeploymentPage.vue'),
      meta: {
        title: 'Create Deployment - Blogus'
      }
    },
    {
      path: '/deployments/:name',
      name: 'deployment-detail',
      component: () => import('@/views/DeploymentDetailPage.vue'),
      meta: {
        title: 'Deployment Details - Blogus'
      }
    },
    // Prompts
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
      path: '/prompts/studio',
      name: 'prompt-studio',
      component: () => import('@/views/PromptStudioPage.vue'),
      meta: {
        title: 'Prompt Studio - Blogus'
      }
    },
    {
      path: '/prompts/studio/:name',
      name: 'prompt-studio-edit',
      component: () => import('@/views/PromptStudioPage.vue'),
      meta: {
        title: 'Edit Prompt - Blogus'
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
      path: '/prompts/scan',
      name: 'scan',
      component: () => import('@/views/ScanResultsPage.vue'),
      meta: {
        title: 'Project Scan - Blogus'
      }
    },
    // Redirects for old routes
    {
      path: '/prompts/execute',
      redirect: '/prompts/studio'
    },
    {
      path: '/templates',
      redirect: '/prompts'
    },
    {
      path: '/templates/:id',
      redirect: '/prompts'
    },
    // Errors
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