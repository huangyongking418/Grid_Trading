<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span><b>站内消息</b> <el-tag v-if="unreadCount > 0" type="danger" size="small">{{ unreadCount }} 条未读</el-tag></span>
          <el-button size="small" @click="markAllRead" :disabled="unreadCount === 0">
            <el-icon><Check /></el-icon> 全部标记已读
          </el-button>
        </div>
      </template>
      <el-table :data="pagedMessages" stripe v-loading="loading" style="width:100%">
        <el-table-column width="50">
          <template #default="{ row }">
            <el-tag v-if="!row.is_read" type="danger" size="small" effect="dark" style="border-radius:50%;padding:0 4px">●</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="130">
          <template #header>
            <div class="header-filter">
              <span>类型</span>
              <el-input v-model="messageFilters.type" placeholder="搜索" size="small" clearable />
            </div>
          </template>
          <template #default="{ row }">
            <el-tag :type="TYPE_MAP[row.message_type]?.type || ''" size="small">
              {{ TYPE_MAP[row.message_type]?.label || row.message_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="190">
          <template #header>
            <div class="header-filter">
              <span>标题</span>
              <el-input v-model="messageFilters.title" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="260" show-overflow-tooltip>
          <template #header>
            <div class="header-filter">
              <span>内容</span>
              <el-input v-model="messageFilters.content" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="时间" width="170">
          <template #header>
            <div class="header-filter">
              <span>时间</span>
              <el-input v-model="messageFilters.time" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button v-if="!row.is_read" link type="primary" size="small" @click="markRead(row)">标记已读</el-button>
            <span v-else style="color:#999;font-size:12px">已读</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination
          v-model:current-page="messagePage"
          v-model:page-size="messagePageSize"
          :total="filteredMessages.length"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
      <el-empty v-if="!loading && filteredMessages.length === 0" description="暂无消息" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMessages, getUnreadCount, markRead as apiMarkRead, markAllRead as apiMarkAllRead } from '../api/index.js'

const TYPE_MAP = {
  reset_expiry: { label: '重置提醒', type: 'warning' },
  buy_trigger: { label: '买入提醒', type: 'danger' },
  sell_trigger: { label: '卖出提醒', type: 'success' },
}

const messages = ref([])
const unreadCount = ref(0)
const loading = ref(false)
const messageFilters = ref({ type: '', title: '', content: '', time: '' })
const messagePage = ref(1)
const messagePageSize = ref(10)

const filteredMessages = computed(() => {
  const f = messageFilters.value
  const hasFilter = Object.values(f).some(v => (v || '').trim() !== '')
  if (!hasFilter) return messages.value
  const match = (field, value) => !(field || '').trim() || String(value ?? '').includes((field || '').trim())
  return messages.value.filter(row => (
    match(f.type, TYPE_MAP[row.message_type]?.label || row.message_type)
    && match(f.title, row.title)
    && match(f.content, row.content)
    && match(f.time, row.create_time)
  ))
})
const pagedMessages = computed(() => {
  const start = (messagePage.value - 1) * messagePageSize.value
  return filteredMessages.value.slice(start, start + messagePageSize.value)
})
watch([filteredMessages, messagePageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredMessages.value.length / messagePageSize.value))
  if (messagePage.value > maxPage) messagePage.value = maxPage
})
watch(messagePageSize, () => { messagePage.value = 1 })

async function fetchData() {
  loading.value = true
  try {
    const [mRes, cRes] = await Promise.all([getMessages(), getUnreadCount()])
    messages.value = mRes.data
    unreadCount.value = cRes.data.count
  } catch { ElMessage.error('加载消息失败') }
  finally { loading.value = false }
}

async function markRead(row) {
  try {
    await apiMarkRead(row.id)
    row.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  } catch { ElMessage.error('操作失败') }
}

async function markAllRead() {
  try {
    await apiMarkAllRead()
    messages.value.forEach(m => m.is_read = true)
    unreadCount.value = 0
    ElMessage.success('已全部标记')
  } catch { ElMessage.error('操作失败') }
}

onMounted(fetchData)
</script>

<style scoped>
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
