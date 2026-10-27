<template>
  <div>
    <el-card shadow="never" class="scheduler-card">
      <template #header>
        <div class="card-header">
          <span><b>定时监控任务</b></span>
          <div class="header-actions">
            <el-tag :type="status.enabled ? 'success' : 'info'" size="small">
              {{ status.enabled ? '已启用' : '已停用' }}
            </el-tag>
            <el-switch v-model="enabled" @change="saveConfig" />
          </div>
        </div>
      </template>

      <el-descriptions :column="3" border size="small">
        <el-descriptions-item label="调度状态">
          <el-tag :type="status.running ? 'success' : 'danger'" size="small">
            {{ status.running ? '运行中' : '未运行' }}
          </el-tag>
          <el-tag v-if="status.running_now" type="warning" size="small" style="margin-left: 6px">
            执行中
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="周期">{{ status.interval_minutes }} 分钟</el-descriptions-item>
        <el-descriptions-item label="下次运行">{{ status.next_run_time ? formatTime(status.next_run_time) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="上次运行">{{ status.last_run_at ? formatTime(status.last_run_at) : '-' }}</el-descriptions-item>
        <el-descriptions-item label="行情源">{{ sourceLabel }}</el-descriptions-item>
        <el-descriptions-item label="最近错误">{{ status.last_error || '-' }}</el-descriptions-item>
      </el-descriptions>

      <div class="toolbar">
        <el-input-number v-model="intervalMinutes" :min="1" :max="1440" size="small" />
        <span class="unit">分钟</span>
        <el-button type="primary" size="small" @click="saveConfig">保存周期</el-button>
        <el-button type="warning" size="small" :loading="status.running_now" @click="runNow">
          立即执行
        </el-button>
      </div>
      <div v-if="status.last_result" class="last-result">
        <el-tag type="info" size="small">上次执行</el-tag>
        <span>
          检查 {{ status.last_result.checked_stocks }} 只，
          获取 {{ status.last_result.fetched_stocks }} 只，
          触发 {{ status.last_result.triggered_layers }} 层，
          重置 {{ status.last_result.reset_count ?? 0 }} 个策略，
          推送成功 {{ status.last_result.push_ok }}，失败 {{ status.last_result.push_failed }}
        </span>
      </div>
    </el-card>

    <el-card shadow="never">
      <template #header><span><b>最近触发日志</b></span></template>
      <el-table :data="pagedLogs" stripe v-loading="loadingLogs" style="width: 100%">
        <el-table-column prop="stock_code" label="代码" width="110">
          <template #header>
            <div class="header-filter">
              <span>代码</span>
              <el-input v-model="logFilters.stock_code" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="stock_name" label="名称" min-width="140">
          <template #header>
            <div class="header-filter">
              <span>名称</span>
              <el-input v-model="logFilters.stock_name" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="推送状态" width="190">
          <template #header>
            <div class="header-filter">
              <span>推送状态</span>
              <el-input v-model="logFilters.push_status" placeholder="搜索" size="small" clearable />
            </div>
          </template>
          <template #default="{ row }">
            <el-tag v-if="!row.push_status || row.push_status.length === 0" type="info" size="small">
              未发送
            </el-tag>
            <el-tag
              v-for="ch in row.push_status || []"
              :key="ch"
              :type="ch === 'email' ? 'primary' : 'success'"
              size="small"
              style="margin-right: 4px"
            >
              {{ ch === 'wechat' ? '企业微信已发送' : ch === 'dingtalk' ? '钉钉已发送' : '邮箱已发送' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_price" label="触发价格" width="130">
          <template #header>
            <div class="header-filter">
              <span>触发价格</span>
              <el-input v-model="logFilters.trigger_price" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="100">
          <template #header>
            <div class="header-filter">
              <span>方向</span>
              <el-input v-model="logFilters.direction" placeholder="搜索" size="small" clearable />
            </div>
          </template>
          <template #default="{ row }">
            <el-tag :type="row.direction === 'buy' ? 'danger' : 'success'" size="small">
              {{ row.direction === 'buy' ? '买入' : '卖出' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="触发时间" min-width="170">
          <template #header>
            <div class="header-filter">
              <span>触发时间</span>
              <el-input v-model="logFilters.create_time" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination
          v-model:current-page="logPage"
          v-model:page-size="logPageSize"
          :total="filteredLogs.length"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
      <el-empty v-if="!loadingLogs && filteredLogs.length === 0" description="暂无触发日志" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getSchedulerStatus,
  updateSchedulerConfig,
  runSchedulerNow,
  getMonitorLogs,
} from '../../api/index.js'

const status = ref({
  running: false,
  enabled: false,
  interval_minutes: 15,
  next_run_time: null,
  last_run_at: null,
  last_result: null,
  last_error: null,
  running_now: false,
  market_source: { active_source: 'tencent' },
})
const enabled = ref(true)
const intervalMinutes = ref(15)
const logs = ref([])
const loadingLogs = ref(false)
const logFilters = ref({ stock_code: '', stock_name: '', push_status: '', trigger_price: '', direction: '', create_time: '' })
const logPage = ref(1)
const logPageSize = ref(10)

function pushStatusText(row) {
  if (!row.push_status || row.push_status.length === 0) return '未发送'
  return row.push_status.map(ch => (
    ch === 'wechat' ? '企业微信已发送' : ch === 'dingtalk' ? '钉钉已发送' : '邮箱已发送'
  )).join(' ')
}
const filteredLogs = computed(() => {
  const f = logFilters.value
  const hasFilter = Object.values(f).some(v => (v || '').trim() !== '')
  if (!hasFilter) return logs.value
  const match = (field, value) => !(field || '').trim() || String(value ?? '').includes((field || '').trim())
  return logs.value.filter(row => (
    match(f.stock_code, row.stock_code)
    && match(f.stock_name, row.stock_name)
    && match(f.push_status, pushStatusText(row))
    && match(f.trigger_price, row.trigger_price)
    && match(f.direction, row.direction === 'buy' ? '买入' : '卖出')
    && match(f.create_time, row.create_time)
  ))
})
const pagedLogs = computed(() => {
  const start = (logPage.value - 1) * logPageSize.value
  return filteredLogs.value.slice(start, start + logPageSize.value)
})
watch([filteredLogs, logPageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredLogs.value.length / logPageSize.value))
  if (logPage.value > maxPage) logPage.value = maxPage
})
watch(logPageSize, () => { logPage.value = 1 })

const sourceLabel = computed(() => {
  const source = status.value.market_source?.active_source
  if (source === 'sina') return '新浪行情（备）'
  if (source === 'tencent') return '腾讯行情（主）'
  return '无'
})

function formatTime(value) {
  if (!value) return '-'
  return String(value).replace('T', ' ').slice(0, 19)
}

async function fetchStatus() {
  try {
    const r = await getSchedulerStatus()
    status.value = r.data
    enabled.value = r.data.enabled
    intervalMinutes.value = r.data.interval_minutes
  } catch {
    ElMessage.error('获取定时任务状态失败')
  }
}

async function fetchLogs() {
  loadingLogs.value = true
  try {
    const r = await getMonitorLogs()
    logs.value = r.data
  } catch {
    // 日志加载失败不打断页面
  } finally {
    loadingLogs.value = false
  }
}

async function saveConfig() {
  try {
    const r = await updateSchedulerConfig({
      enabled: enabled.value,
      interval_minutes: intervalMinutes.value,
    })
    status.value = r.data
    ElMessage.success('配置已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

async function runNow() {
  try {
    const r = await runSchedulerNow()
    const result = r.data.result || {}
    if (result.skipped) {
      ElMessage.info('任务正在执行中')
    } else {
      ElMessage.success(`执行完成：触发 ${result.triggered_layers ?? 0} 层，重置 ${result.reset_count ?? 0} 个策略`)
    }
    await fetchStatus()
    await fetchLogs()
  } catch {
    ElMessage.error('执行失败')
  }
}

onMounted(() => {
  fetchStatus()
  fetchLogs()
})
</script>

<style scoped>
.scheduler-card {
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.toolbar {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.unit {
  color: #606266;
  font-size: 13px;
}
.last-result {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #606266;
}
</style>
