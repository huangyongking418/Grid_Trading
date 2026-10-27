 import { createRouter, createWebHistory } from 'vue-router'
 
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/messages',
    name: 'MessageCenter',
    component: () => import('../views/MessageCenter.vue'),
    meta: { title: '站内消息', requiresAuth: true },
  },
  {
    path: '/documents',
    name: 'UserDocuments',
    component: () => import('../views/UserDocuments.vue'),
    meta: { title: '操作手册', requiresAuth: true },
  },
  {
     path: '/',
     redirect: '/strategies',
   },
   {
     path: '/strategies',
     name: 'StrategyList',
     component: () => import('../views/StrategyList.vue'),
     meta: { title: '策略管理', requiresAuth: true },
   },
   {
     path: '/stocks',
     redirect: '/strategies',
   },
   {
     path: '/operations',
     name: 'OperationDetail',
     component: () => import('../views/OperationDetail.vue'),
     meta: { title: '操作明细', requiresAuth: true },
   },
   {
     path: '/monitor',
     name: 'MonitorConfig',
     component: () => import('../views/MonitorConfig.vue'),
     meta: { title: '监控设置', requiresAuth: true },
   },
  {
    path: '/profit',
    name: 'ProfitAnalysis',
    component: () => import('../views/ProfitAnalysis.vue'),
    meta: { title: '收益分析', requiresAuth: true },
  },
  {
    path: '/backtest',
    name: 'BacktestStrategyList',
    component: () => import('../views/BacktestStrategyList.vue'),
    meta: { title: '模拟回测', requiresAuth: true },
  },
  {
    path: '/backtest/sessions/:id',
    name: 'BacktestSessionDetail',
    component: () => import('../views/BacktestSessionDetail.vue'),
    meta: { title: '回测详情', requiresAuth: true },
  },
   {
     path: '/admin/users',
     name: 'UserList',
     component: () => import('../views/admin/UserList.vue'),
     meta: { title: '用户管理', requiresAuth: true, adminOnly: true },
   },
   {
     path: '/admin/roles',
     name: 'RoleList',
     component: () => import('../views/admin/RoleList.vue'),
     meta: { title: '角色管理', requiresAuth: true, adminOnly: true },
   },
   {
     path: '/admin/params',
     name: 'ParamList',
     component: () => import('../views/admin/ParamList.vue'),
     meta: { title: '系统参数', requiresAuth: true, adminOnly: true },
   },
   {
     path: '/admin/announcements',
     name: 'AnnouncementList',
     component: () => import('../views/admin/AnnouncementList.vue'),
     meta: { title: '公告配置', requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/scheduler',
    name: 'SchedulerConfig',
    component: () => import('../views/admin/SchedulerConfig.vue'),
    meta: { title: '定时任务', requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/email-config',
    name: 'EmailConfig',
    component: () => import('../views/admin/EmailConfig.vue'),
    meta: { title: '邮件服务配置', requiresAuth: true, adminOnly: true },
  },
  {
    path: '/admin/documents',
    name: 'DocumentList',
    component: () => import('../views/admin/DocumentList.vue'),
    meta: { title: '文档管理', requiresAuth: true, adminOnly: true },
  },
 ]
 
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局路由守卫：登录校验 + 管理员权限
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('gts_token')
  if (to.path === '/login') {
    return token ? next('/strategies') : next()
  }
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }
  if (to.meta.adminOnly) {
    try {
      const user = JSON.parse(localStorage.getItem('gts_user') || '{}')
      if (user.role_name !== '管理员') {
        return next('/strategies')
      }
    } catch {
      return next('/login')
    }
  }
  next()
})

export default router
