 import axios from 'axios'
 
const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器：自动携带 Token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('gts_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：401 跳转登录
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('gts_token')
      localStorage.removeItem('gts_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// === 认证 ===
export const login = (data) => api.post('/auth/login', data)
export const register = (data) => api.post('/auth/register', data)
export const getMe = () => api.get('/auth/me')
export const changePassword = (data) => api.post('/auth/change-password', data)

// === 系统管理 ===
export const getUsers = () => api.get('/users')
export const createUser = (data) => api.post('/users', data)
export const updateUser = (id, data) => api.put(`/users/${id}`, data)
export const getRoles = () => api.get('/roles')
export const createRole = (data) => api.post('/roles', data)
export const updateRolePermissions = (id, permissions) => api.put(`/roles/${id}/permissions`, permissions)
export const getParams = () => api.get('/params')
export const createParam = (data) => api.post('/params', data)
export const updateParam = (id, data) => api.put(`/params/${id}`, data)
export const getAnnouncements = () => api.get('/announcements')
export const createAnnouncement = (data) => api.post('/announcements', data)
export const updateAnnouncement = (id, data) => api.put(`/announcements/${id}`, data)
export const uploadAnnouncementImage = (file) => {
  const fd = new FormData()
  fd.append('file', file)
  return api.post('/announcements/upload-image', fd)
}

// === 文档管理 ===
export const uploadDocument = (formData) => api.post('/documents/upload', formData)
export const getDocuments = (params) => api.get('/documents', { params })
export const updateDocument = (id, data) => api.put(`/documents/${id}`, data)
export const deleteDocument = (id) => api.delete(`/documents/${id}`)
export const downloadDocumentFile = (id) => api.get(`/documents/${id}/download`, { responseType: 'blob' })
 
 // === 策略管理 ===
 export const getStrategyTemplates = () => api.get('/strategies/templates')
 export const getStrategyInstances = () => api.get('/strategies/instances')
 export const createStrategyInstance = (data) => api.post('/strategies/instances', data)
 export const updateStrategyInstance = (id, data) => api.put(`/strategies/instances/${id}`, data)
 export const deleteStrategyInstance = (id) => api.delete(`/strategies/instances/${id}`)
 export const getStrategyDetail = (id) => api.get(`/strategies/instances/${id}`)
 
 // === 标的管理 ===
 export const getStocks = () => api.get('/stocks')
 export const createStock = (data) => api.post('/stocks', data)
 export const deleteStock = (id) => api.delete(`/stocks/${id}`)
 export const bindStrategy = (stockId, instanceId) => api.post(`/stocks/${stockId}/bind`, { instance_id: instanceId })
 export const unbindStrategy = (stockId) => api.post(`/stocks/${stockId}/unbind`)
 export const searchStocks = (keyword) => api.get('/stocks/search', { params: { keyword } })
 
 // === 网格明细 ===
 export const getGridLayers = (instanceId) => api.get(`/strategies/instances/${instanceId}/layers`)
 export const generateGridLayers = (instanceId) => api.post(`/strategies/instances/${instanceId}/layers/generate`)
 export const previewGridLayers = (data) => api.post('/strategies/preview', data)
 
 // === 监控配置 ===
export const getPushConfig = () => api.get('/monitor/push-config')
export const updatePushConfig = (channel, data) => api.put(`/monitor/push-config/${channel}`, data)
export const getMonitorLogs = (params) => api.get('/monitor/logs', { params })
export const getEmailConfig = () => api.get('/monitor/email-config')
export const updateEmailConfig = (data) => api.put('/monitor/email-config', data)
export const sendTestEmail = (data = {}) => api.post('/monitor/email-test', data)
export const getSmtpConfig = () => api.get('/monitor/smtp-config')
export const updateSmtpConfig = (data) => api.put('/monitor/smtp-config', data)

// === 定时任务 ===
export const getSchedulerStatus = () => api.get('/scheduler/status')
export const updateSchedulerConfig = (data) => api.put('/scheduler/config', data)
export const runSchedulerNow = () => api.post('/scheduler/run')
 
 // === 收益分析 ===
 export const getProfitTheoretical = (instanceId) => api.get(`/profit/theoretical/${instanceId}`)
 export const getOperations = (params) => api.get('/profit/operations', { params })
 export const createOperation = (data) => api.post('/profit/operations', data)
 export const deleteOperation = (id) => api.delete(`/profit/operations/${id}`)
 export const getProfitActual = (params) => api.get('/profit/actual', { params })
 
// === 系统 ===
export const healthCheck = () => api.get('/health')
export const getConfig = () => api.get('/config')
export const getFooterConfig = () => api.get('/config/footer')
 
 export default api

// === ???? ===
export const getMessages = () => api.get('/messages')
export const getUnreadCount = () => api.get('/messages/unread-count')
export const markRead = (id) => api.put(/messages//read)
export const markAllRead = () => api.put('/messages/read-all')
export const createMessage = (data) => api.post('/messages', data)
