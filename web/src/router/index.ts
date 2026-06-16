import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/',
      component: () => import('../layouts/MainLayout.vue'),
      children: [
        {
          path: '',
          name: 'dashboard',
          component: () => import('../views/DashboardView.vue'),
          meta: { title: '仪表盘' },
        },
        {
          path: 'foods',
          name: 'foods',
          component: () => import('../views/FoodsView.vue'),
          meta: { title: '食物库' },
        },
        {
          path: 'diet',
          name: 'diet',
          component: () => import('../views/DietLogsView.vue'),
          meta: { title: '饮食记录' },
        },
        {
          path: 'exercise',
          name: 'exercise',
          component: () => import('../views/ExerciseLogsView.vue'),
          meta: { title: '运动记录' },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('../views/ProfileView.vue'),
          meta: { title: '个人画像' },
        },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('makoto_token')
  if (to.path !== '/login' && !token) {
    return '/login'
  }
})

export default router
