import { createRouter, createWebHistory } from 'vue-router'
import { useAdminStore } from '../store/admin'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('../views/layout/AdminLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘' },
      },
      {
        path: 'news',
        name: 'NewsList',
        component: () => import('../views/news/NewsList.vue'),
        meta: { title: '新闻管理' },
      },
      {
        path: 'news/import',
        name: 'NewsImport',
        component: () => import('../views/news/ImportNews.vue'),
        meta: { title: '导入新闻' },
      },
      {
        path: 'news/create',
        name: 'NewsCreate',
        component: () => import('../views/news/NewsForm.vue'),
        meta: { title: '新建新闻' },
      },
      {
        path: 'news/:id/edit',
        name: 'NewsEdit',
        component: () => import('../views/news/NewsForm.vue'),
        meta: { title: '编辑新闻' },
      },
      {
        path: 'users',
        name: 'UserList',
        component: () => import('../views/users/UserList.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'categories',
        name: 'CategoryList',
        component: () => import('../views/categories/CategoryList.vue'),
        meta: { title: '分类管理' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const adminStore = useAdminStore()
  if (to.meta.requiresAuth && !adminStore.isLogin) {
    next('/login')
  } else if (to.path === '/login' && adminStore.isLogin) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
