import api from './index.js'

// === 模拟策略 ===
export const getBacktestStrategies = () => api.get('/backtest/strategies')
export const createBacktestStrategy = (data) => api.post('/backtest/strategies', data)
export const updateBacktestStrategy = (id, data) => api.put(`/backtest/strategies/${id}`, data)
export const deleteBacktestStrategy = (id) => api.delete(`/backtest/strategies/${id}`)
export const previewBacktestLayers = (id) => api.post(`/backtest/strategies/${id}/preview-layers`)

// === 回测会话 ===
export const getBacktestSessions = () => api.get('/backtest/sessions')
export const createBacktestSession = (data) => api.post('/backtest/sessions', data)
export const getBacktestSession = (id) => api.get(`/backtest/sessions/${id}`)
export const deleteBacktestSession = (id) => api.delete(`/backtest/sessions/${id}`)
export const getBacktestTrades = (id, params) => api.get(`/backtest/sessions/${id}/trades`, { params })
export const getBacktestLayers = (id) => api.get(`/backtest/sessions/${id}/layers`)
export const getBacktestMetrics = (id) => api.get(`/backtest/sessions/${id}/metrics`)
export const getBacktestEquityCurve = (id) => api.get(`/backtest/sessions/${id}/equity-curve`)
export const getBacktestKline = (id) => api.get(`/backtest/sessions/${id}/kline`)
export const refreshBacktestKline = (stockCode) => api.post('/backtest/kline/refresh', { stock_code: stockCode })
