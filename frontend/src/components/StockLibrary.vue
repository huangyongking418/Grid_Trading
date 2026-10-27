<template>
  <div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
      <span style="font-size:13px;color:#909399">维护股票 / ETF / 基金字典，绑定关系在「策略列表」中配置</span>
      <el-button type="primary" size="small" @click="openCreateDialog">
        <el-icon><Plus /></el-icon> 新增标的
      </el-button>
    </div>
    <el-table :data="pagedStocks" stripe v-loading="loading" style="width:100%">
      <el-table-column prop="code" label="代码" width="130">
        <template #header>
          <div class="header-filter">
            <span>代码</span>
            <el-input v-model="stockFilters.code" placeholder="搜索" size="small" clearable />
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="140">
        <template #header>
          <div class="header-filter">
            <span>名称</span>
            <el-input v-model="stockFilters.name" placeholder="搜索" size="small" clearable />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="90">
        <template #header>
          <div class="header-filter">
            <span>类型</span>
            <el-input v-model="stockFilters.type" placeholder="搜索" size="small" clearable />
          </div>
        </template>
        <template #default="{ row }">
          <el-tag :type="row.type === 'etf' ? 'success' : row.type === 'fund' ? 'warning' : ''" size="small">
            {{ TYPE_MAP[row.type] || row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="current_price" label="最新价" width="110">
        <template #header>
          <div class="header-filter">
            <span>最新价</span>
            <el-input v-model="stockFilters.current_price" placeholder="搜索" size="small" clearable />
          </div>
        </template>
      </el-table-column>
      <el-table-column label="绑定策略" min-width="160">
        <template #header>
          <div class="header-filter">
            <span>绑定策略</span>
            <el-input v-model="stockFilters.bound" placeholder="搜索" size="small" clearable />
          </div>
        </template>
        <template #default="{ row }">
          <el-tag v-if="row.strategy_instance_id" type="primary" size="small">{{ getBoundName(row) }}</el-tag>
          <el-tag v-else type="info" size="small">未绑定</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button link type="danger" size="small" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="table-footer">
      <el-pagination
        v-model:current-page="stockPage"
        v-model:page-size="stockPageSize"
        :total="filteredStocks.length"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        background
      />
    </div>
    <el-dialog v-model="createVisible" title="新增标的" width="400px">
      <el-form :model="createForm" label-width="80px" size="small">
        <el-form-item label="代码"><el-input v-model="createForm.code" placeholder="如 600519 / 510300" /></el-form-item>
        <el-form-item label="名称"><el-input v-model="createForm.name" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="createForm.type" style="width:100%">
            <el-option label="个股" value="stock" />
            <el-option label="ETF" value="etf" />
            <el-option label="基金" value="fund" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStock" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStocks, createStock, deleteStock, getStrategyInstances } from '../api/index.js'

const TYPE_MAP = { stock: '个股', etf: 'ETF', fund: '基金' }
const loading = ref(false)
const saving = ref(false)
const stocks = ref([])
const instances = ref([])
const stockFilters = ref({ code: '', name: '', type: '', current_price: '', bound: '' })
const stockPage = ref(1)
const stockPageSize = ref(10)
const createVisible = ref(false)
const createForm = ref({ code: '', name: '', type: 'stock' })

const filteredStocks = computed(() => {
  const f = stockFilters.value
  const hasFilter = Object.values(f).some(v => (v || '').trim() !== '')
  if (!hasFilter) return stocks.value
  const match = (field, value) => !(field || '').trim() || String(value ?? '').includes((field || '').trim())
  return stocks.value.filter(row => (
    match(f.code, row.code)
    && match(f.name, row.name)
    && match(f.type, TYPE_MAP[row.type] || row.type)
    && match(f.current_price, row.current_price)
    && match(f.bound, row.strategy_instance_id ? getBoundName(row) : '未绑定')
  ))
})
const pagedStocks = computed(() => {
  const start = (stockPage.value - 1) * stockPageSize.value
  return filteredStocks.value.slice(start, start + stockPageSize.value)
})
watch([filteredStocks, stockPageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredStocks.value.length / stockPageSize.value))
  if (stockPage.value > maxPage) stockPage.value = maxPage
})
watch(stockPageSize, () => { stockPage.value = 1 })

async function fetchData() {
  loading.value = true
  try {
    const [s, i] = await Promise.all([getStocks(), getStrategyInstances()])
    stocks.value = s.data
    instances.value = i.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function getBoundName(stock) {
  const inst = instances.value.find(i => i.id === stock.strategy_instance_id)
  return inst ? (inst.name || '策略#' + inst.id) : ''
}
function openCreateDialog() {
  createForm.value = { code: '', name: '', type: 'stock' }
  createVisible.value = true
}
async function saveStock() {
  saving.value = true
  try {
    await createStock(createForm.value)
    ElMessage.success('已新增')
    createVisible.value = false
    await fetchData()
  } catch { ElMessage.error('新增失败') }
  finally { saving.value = false }
}
async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(
      row.strategy_instance_id ? '该标的已绑定策略，删除后将自动解绑，确定删除？' : '确定删除该标的？',
      '确认'
    )
    await deleteStock(row.id)
    ElMessage.success('已删除')
    await fetchData()
  } catch (e) { if (e !== 'cancel') ElMessage.error('删除失败') }
}
onMounted(fetchData)
defineExpose({ fetchData })
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
