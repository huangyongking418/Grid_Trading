<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <div>
        <el-button link type="primary" @click="$router.push('/backtest')">
          <el-icon><ArrowLeft /></el-icon> 返回模拟回测
        </el-button>
        <span style="margin-left:8px;font-weight:600">回测 #{{ session?.id }}</span>
        <el-tag v-if="session" :type="statusType(session.status)" style="margin-left:10px">{{ statusText(session.status) }}</el-tag>
      </div>
      <div>
        <el-button size="small" @click="refreshKlineCache" :loading="refreshingCache">刷新行情缓存</el-button>
        <el-button size="small" type="primary" :loading="rerunning" :disabled="!canRerun" @click="rerun">以此参数重新回测</el-button>
      </div>
    </div>

    <el-alert
      v-if="session?.status === 'failed'"
      type="error"
      :title="session.error_message || '回测失败'"
      show-icon
      :closable="false"
      style="margin-bottom:12px"
    />
    <el-alert
      v-if="session?.data_note"
      type="warning"
      :title="session.data_note"
      show-icon
      :closable="false"
      style="margin-bottom:12px"
    />

    <el-row :gutter="12" v-if="metric">
      <el-col v-for="card in metricCards" :key="card.key" :span="6" :xs="12">
        <div class="metric-card" :class="{ negative: card.negative && card.value < 0 }">
          <div class="metric-label">{{ card.label }}</div>
          <div class="metric-value">{{ card.value }}<span v-if="card.unit" class="metric-unit">{{ card.unit }}</span></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="12" style="margin-top:12px">
      <el-col :span="24" :md="14">
        <el-card shadow="never">
          <template #header><span><b>资产曲线</b> — 回测账户 vs 买入持有基准</span></template>
          <div ref="equityChartRef" style="width:100%;height:340px"></div>
        </el-card>
      </el-col>
      <el-col :span="24" :md="10">
        <el-card shadow="never">
          <template #header><span><b>回撤曲线</b></span></template>
          <div ref="drawdownChartRef" style="width:100%;height:340px"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" style="margin-top:12px">
      <template #header><span><b>K线 + 网格价位 + 成交标记</b>（60分钟 · 前复权）</span></template>
      <div ref="klineChartRef" style="width:100%;height:420px"></div>
    </el-card>

    <el-card shadow="never" style="margin-top:12px">
      <template #header><span><b>成交记录</b> — 共 {{ trades.length }} 条（含现金不足跳过）</span></template>
      <el-table :data="trades" stripe size="small" max-height="420" style="width:100%">
        <el-table-column label="时间" min-width="130">
          <template #default="{ row }">{{ formatTime(row.trade_time) }}</template>
        </el-table-column>
        <el-table-column label="方向" width="70">
          <template #default="{ row }">
            <el-tag :type="row.direction === 'buy' ? 'danger' : 'success'" size="small">{{ row.direction === 'buy' ? '买入' : '卖出' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="layer_index" label="层" width="60" />
        <el-table-column prop="trigger_price" label="成交价" width="90" />
        <el-table-column prop="quantity" label="数量" width="80" />
        <el-table-column prop="amount" label="金额" width="100" />
        <el-table-column prop="fee" label="手续费" width="90" />
        <el-table-column prop="cash_after" label="剩余现金" width="110" />
        <el-table-column prop="note" label="备注" min-width="140">
          <template #default="{ row }">
            <span v-if="row.note" style="color:#e6a23c">{{ row.note }}</span>
            <span v-else style="color:#c0c4cc">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import {
  getBacktestSession,
  getBacktestMetrics,
  getBacktestEquityCurve,
  getBacktestKline,
  getBacktestTrades,
  getBacktestLayers,
  createBacktestSession,
  refreshBacktestKline,
} from '../api/backtest.js'

const route = useRoute()
const router = useRouter()
const sessionId = Number(route.params.id)
const session = ref(null)
const metric = ref(null)
const equityPoints = ref([])
const klines = ref([])
const layers = ref([])
const trades = ref([])
const refreshingCache = ref(false)
const rerunning = ref(false)

const equityChartRef = ref(null)
const drawdownChartRef = ref(null)
const klineChartRef = ref(null)
let equityChart = null
let drawdownChart = null
let klineChart = null

const metricCards = computed(() => {
  if (!metric.value) return []
  const m = metric.value
  return [
    { key: 'total_return_rate', label: '总收益率', value: fmtPct(m.total_return_rate), unit: '%', negative: true },
    { key: 'annual_return_rate', label: '年化收益率', value: fmtPct(m.annual_return_rate), unit: '%', negative: true },
    { key: 'max_drawdown', label: '最大回撤', value: fmtPct(m.max_drawdown), unit: '%' },
    { key: 'sharpe_ratio', label: '夏普比率', value: m.sharpe_ratio ?? 0 },
    { key: 'win_rate', label: '胜率', value: fmtPct(m.win_rate), unit: '%' },
    { key: 'profit_loss_ratio', label: '盈亏比', value: m.profit_loss_ratio ?? 0 },
    { key: 'total_trade_count', label: '成交笔数', value: m.total_trade_count ?? 0 },
    { key: 'benchmark_return_rate', label: '基准收益率', value: fmtPct(m.benchmark_return_rate), unit: '%', negative: true },
  ]
})

const canRerun = computed(() => session.value && session.value.status === 'success')

function fmtPct(v) {
  return v == null ? 0 : v
}

function formatTime(t) {
  return t ? String(t).replace('T', ' ').slice(0, 16) : ''
}

function statusText(status) {
  return { pending: '排队中', running: '回测中', success: '已完成', failed: '失败' }[status] || status
}

function statusType(status) {
  return { pending: 'info', running: 'warning', success: 'success', failed: 'danger' }[status] || 'info'
}

async function loadAll() {
  try {
    const r = await getBacktestSession(sessionId)
    session.value = r.data
    if (session.value.status === 'success') {
      const [m, e, k, t, l] = await Promise.all([
        getBacktestMetrics(sessionId),
        getBacktestEquityCurve(sessionId),
        getBacktestKline(sessionId),
        getBacktestTrades(sessionId, { limit: 1000 }),
        getBacktestLayers(sessionId),
      ])
      metric.value = m.data
      equityPoints.value = e.data.points || []
      klines.value = k.data
      trades.value = t.data
      layers.value = l.data
      renderCharts()
    } else if (session.value.status === 'pending' || session.value.status === 'running') {
      schedulePoll()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '回测详情加载失败')
  }
}

let pollTimer = null
function schedulePoll() {
  clearTimeout(pollTimer)
  pollTimer = setTimeout(loadAll, 3000)
}

function renderCharts() {
  if (!equityChartRef.value || !drawdownChartRef.value || !klineChartRef.value) return
  renderEquityChart()
  renderDrawdownChart()
  renderKlineChart()
}

function renderEquityChart() {
  if (!equityChart) equityChart = echarts.init(equityChartRef.value)
  equityChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['回测资产', '买入持有基准'] },
    grid: { left: '4%', right: '4%', bottom: '4%', containLabel: true },
    xAxis: { type: 'category', data: equityPoints.value.map(p => p.time), boundaryGap: false },
    yAxis: { type: 'value', scale: true },
    series: [
      { name: '回测资产', type: 'line', smooth: true, showSymbol: false, data: equityPoints.value.map(p => p.asset), lineStyle: { width: 2 }, areaStyle: { opacity: 0.08 } },
      { name: '买入持有基准', type: 'line', smooth: true, showSymbol: false, data: equityPoints.value.map(p => p.benchmark_asset), lineStyle: { width: 2, type: 'dashed' } },
    ],
  })
}

function renderDrawdownChart() {
  if (!drawdownChart) drawdownChart = echarts.init(drawdownChartRef.value)
  const points = metric.value?.drawdown_curve || []
  drawdownChart.setOption({
    tooltip: { trigger: 'axis', valueFormatter: (v) => `${v}%` },
    grid: { left: '4%', right: '4%', bottom: '4%', containLabel: true },
    xAxis: { type: 'category', data: points.map(p => p.time), boundaryGap: false },
    yAxis: { type: 'value', axisLabel: { formatter: '{value}%' } },
    series: [
      { type: 'line', smooth: true, showSymbol: false, data: points.map(p => p.drawdown), lineStyle: { width: 2, color: '#f56c6c' }, areaStyle: { color: 'rgba(245,108,108,0.15)' } },
    ],
  })
}

function renderKlineChart() {
  if (!klineChart) klineChart = echarts.init(klineChartRef.value)
  const times = klines.value.map(k => formatTime(k.trade_time))
  const candleData = klines.value.map(k => [k.open, k.close, k.low, k.high])
  const buyMark = layers.value.filter(l => l.direction === 'buy').map(l => ({ yAxis: l.trigger_price, name: `买${l.layer_index}` }))
  const sellMark = layers.value.filter(l => l.direction === 'sell').map(l => ({ yAxis: l.trigger_price, name: `卖${l.layer_index}` }))
  const buyPoints = trades.value.filter(t => t.direction === 'buy' && t.quantity > 0).map(t => [formatTime(t.trade_time), t.trigger_price])
  const sellPoints = trades.value.filter(t => t.direction === 'sell' && t.quantity > 0).map(t => [formatTime(t.trade_time), t.trigger_price])

  klineChart.setOption({
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params) => {
        const list = Array.isArray(params) ? params : [params]
        const candle = list.find(p => p.seriesType === 'candlestick')
        if (candle && klines.value[candle.dataIndex]) {
          const k = klines.value[candle.dataIndex]
          return [
            `<div style="font-weight:600;margin-bottom:4px">${formatTime(k.trade_time)}</div>`,
            `开盘：${k.open}`,
            `收盘：${k.close}`,
            `最高：${k.high}`,
            `最低：${k.low}`,
          ].join('<br/>')
        }
        const scatter = list.find(p => p.seriesType === 'scatter')
        if (scatter) {
          return `${scatter.seriesName}价格：${scatter.value?.[1]}`
        }
        return ''
      },
    },
    legend: { data: ['K线', '买入', '卖出'] },
    grid: { left: '4%', right: '4%', bottom: '4%', containLabel: true },
    xAxis: { type: 'category', data: times, boundaryGap: true },
    yAxis: { type: 'value', scale: true },
    dataZoom: [{ type: 'inside', start: Math.max(0, 100 - 4000 / Math.max(times.length, 1) * 100), end: 100 }],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: candleData,
        itemStyle: { color: '#f56c6c', color0: '#67c23a', borderColor: '#f56c6c', borderColor0: '#67c23a' },
        markLine: {
          symbol: 'none',
          label: { formatter: '{b}: {c}' },
          data: [
            ...buyMark.map(m => ({ ...m, lineStyle: { color: '#f56c6c', type: 'dashed' }, label: { color: '#f56c6c', formatter: `买${m.name}` } })),
            ...sellMark.map(m => ({ ...m, lineStyle: { color: '#67c23a', type: 'dashed' }, label: { color: '#67c23a', formatter: `卖${m.name}` } })),
          ],
        },
      },
      { name: '买入', type: 'scatter', data: buyPoints, symbolSize: 9, itemStyle: { color: '#f56c6c' } },
      { name: '卖出', type: 'scatter', data: sellPoints, symbolSize: 9, itemStyle: { color: '#67c23a' } },
    ],
  })
}

async function rerun() {
  try {
    await ElMessageBox.confirm('将以本次回测相同的策略参数和区间创建新的回测记录，是否继续？', '重新回测')
  } catch {
    return
  }
  rerunning.value = true
  try {
    const r = await createBacktestSession({
      strategy_id: session.value.strategy_id,
      start_date: session.value.start_date,
      end_date: session.value.end_date,
      fee_config: session.value.fee_config,
    })
    ElMessage.success('已创建新回测')
    router.replace(`/backtest/sessions/${r.data.id}`)
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '创建回测失败')
  } finally {
    rerunning.value = false
  }
}

async function refreshKlineCache() {
  if (!session.value) return
  refreshingCache.value = true
  try {
    await refreshBacktestKline(session.value.stock_code)
    ElMessage.success('已清空行情缓存，下次回测将重新获取')
  } catch {
    ElMessage.error('刷新失败')
  } finally {
    refreshingCache.value = false
  }
}

onMounted(async () => {
  await loadAll()
  await nextTick()
  renderCharts()
})

onUnmounted(() => {
  clearTimeout(pollTimer)
  equityChart?.dispose()
  drawdownChart?.dispose()
  klineChart?.dispose()
})
</script>

<style scoped>
.metric-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 12px;
}
.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.metric-value {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  letter-spacing: 0;
}
.metric-value.negative-negative .metric-value {
  color: inherit;
}
.metric-card.negative .metric-value {
  color: #f56c6c;
}
.metric-unit {
  font-size: 13px;
  font-weight: 400;
  color: #909399;
  margin-left: 2px;
}
</style>
