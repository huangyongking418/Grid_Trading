<template>
  <div>
    <el-card shadow="never" class="section-card">
      <template #header><span><b>推送渠道配置</b></span></template>
      <el-form label-width="120px" size="small">
        <el-form-item label="企业微信">
          <div style="display:flex;flex-direction:column;gap:4px">
            <div style="display:flex;align-items:center;gap:8px">
              <el-input v-model="wechat.webhook_url" placeholder="企业微信机器人 Webhook URL" style="width:350px" />
              <el-switch v-model="wechat.enabled" active-text="启用" />
            </div>
            <div class="field-tip">面向群聊，需首先建群再创建机器人</div>
          </div>
        </el-form-item>
        <el-form-item label="钉钉">
          <div style="display:flex;flex-direction:column;gap:4px">
            <div style="display:flex;align-items:center;gap:8px">
              <el-input v-model="dingtalk.webhook_url" placeholder="钉钉机器人 Webhook URL" style="width:350px" />
              <el-switch v-model="dingtalk.enabled" active-text="启用" />
            </div>
            <div class="field-tip">面向群聊，需首先建群再创建机器人</div>
          </div>
        </el-form-item>
        <el-form-item label="邮箱">
          <div style="display:flex;flex-direction:column;gap:4px">
            <div style="display:flex;align-items:center;gap:8px">
              <el-input v-model="email.to_email" placeholder="收件人邮箱（多个用逗号分隔）" style="width:330px" />
              <el-switch v-model="email.enabled" active-text="启用" />
            </div>
            <div class="field-tip">建议设置成QQ 邮箱。微信绑定QQ邮箱，开启QQ邮箱提醒功能可实现微信收到消息通知</div>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="saveConfig" :loading="saving">保存配置</el-button>
          <el-button type="warning" @click="testEmail" :loading="testing">发送测试邮件</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-card shadow="never">
      <template #header><span><b>监控触发日志</b></span></template>
      <el-table :data="pagedLogs" stripe v-loading="loading" style="width:100%">
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
              style="margin-right:4px"
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
        <el-table-column label="方向" width="90">
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
      <el-empty v-if="!loading && filteredLogs.length === 0" description="暂无监控日志" />
    </el-card>
  </div>
</template>
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getPushConfig,
  updatePushConfig,
  getMonitorLogs,
  getEmailConfig,
  updateEmailConfig,
  sendTestEmail,
} from '../api/index.js'
const wechat = ref({ webhook_url: '', enabled: false })
const dingtalk = ref({ webhook_url: '', enabled: false })
const email = ref({ to_email: '', enabled: false })
const logs = ref([])
const logFilters = ref({ stock_code: '', stock_name: '', push_status: '', trigger_price: '', direction: '', create_time: '' })
const logPage = ref(1)
const logPageSize = ref(10)
const saving = ref(false)
const testing = ref(false)
const loading = ref(false)

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
async function fetchData() {
  try {
    const r = await getPushConfig()
    r.data.forEach(c => { if (c.channel === 'wechat') wechat.value = c; if (c.channel === 'dingtalk') dingtalk.value = c })
  } catch {}
  try {
    const r = await getEmailConfig()
    email.value = { ...email.value, ...r.data }
  } catch {}
  loading.value = true
  try { const r = await getMonitorLogs(); logs.value = r.data } catch {}
  finally { loading.value = false }
}
async function saveConfig() {
  saving.value = true
  try {
    await Promise.all([
      updatePushConfig('wechat', wechat.value),
      updatePushConfig('dingtalk', dingtalk.value),
      updateEmailConfig(email.value),
    ])
    ElMessage.success('已保存')
  } catch { ElMessage.error('保存失败') }
  finally { saving.value = false }
}
async function testEmail() {
  testing.value = true
  try {
    const r = await sendTestEmail()
    if (r.data.ok) ElMessage.success('测试邮件发送成功')
    else ElMessage.error('发送失败：' + (r.data.error || '未知错误'))
  } catch { ElMessage.error('发送失败') }
  finally { testing.value = false }
}
onMounted(fetchData)
</script>

<style scoped>
.field-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
.header-filter {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.header-filter .el-input {
  width: 100%;
}
.table-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
}
</style>
