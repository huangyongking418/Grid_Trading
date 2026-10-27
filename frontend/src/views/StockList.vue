<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span><b>标的管理</b></span>
          <el-button type="primary" size="small" @click="openCreateDialog"><el-icon><Plus /></el-icon> 添加标的</el-button>
        </div>
      </template>
      <el-table :data="stocks" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="code" label="代码" width="120" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.type === 'etf' ? 'success' : row.type === 'fund' ? 'warning' : ''" size="small">{{ row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_price" label="最新价" width="100" />
        <el-table-column label="绑定策略" min-width="150">
          <template #default="{ row }">{{ getBoundName(row) || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openBindDialog(row)">绑定策略</el-button>
            <el-button link type="danger" size="small" @click="confirmDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    <el-dialog v-model="createVisible" title="添加标的" width="400px">
      <el-form :model="createForm" label-width="80px" size="small">
        <el-form-item label="代码"><el-input v-model="createForm.code" /></el-form-item>
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
    <el-dialog v-model="bindVisible" title="绑定策略" width="400px">
      <p>为 <b>{{ bindTarget?.name }}</b> 选择策略：</p>
      <el-select v-model="bindInstanceId" placeholder="选择策略" style="width:100%">
        <el-option v-for="inst in instances" :key="inst.id" :label="inst.name || '策略#'+inst.id" :value="inst.id" />
      </el-select>
      <template #footer>
        <el-button @click="bindVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBind" :loading="binding">绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getStocks, createStock, deleteStock, getStrategyInstances, bindStrategy, unbindStrategy } from '../api/index.js'
const loading = ref(false); const saving = ref(false); const binding = ref(false)
const stocks = ref([]); const instances = ref([])
const createVisible = ref(false); const bindVisible = ref(false)
const bindTarget = ref(null); const bindInstanceId = ref(null)
const createForm = ref({ code: '', name: '', type: 'stock' })
async function fetchData() {
  loading.value = true
  try { const [s, i] = await Promise.all([getStocks(), getStrategyInstances()]); stocks.value = s.data; instances.value = i.data }
  catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}
function getBoundName(stock) {
  const inst = instances.value.find(i => i.id === stock.strategy_instance_id)
  return inst ? (inst.name || '策略#' + inst.id) : null
}
function openCreateDialog() { createForm.value = { code: '', name: '', type: 'stock' }; createVisible.value = true }
async function saveStock() {
  saving.value = true
  try { await createStock(createForm.value); ElMessage.success('已添加'); createVisible.value = false; await fetchData() }
  catch { ElMessage.error('添加失败') }
  finally { saving.value = false }
}
function openBindDialog(stock) { bindTarget.value = stock; bindInstanceId.value = stock.strategy_instance_id; bindVisible.value = true }
async function confirmBind() {
  binding.value = true
  try {
    if (bindInstanceId.value) { await bindStrategy(bindTarget.value.id, bindInstanceId.value) }
    else { await unbindStrategy(bindTarget.value.id) }
    ElMessage.success('绑定已更新'); bindVisible.value = false; await fetchData()
  } catch { ElMessage.error('绑定失败') }
  finally { binding.value = false }
}
async function confirmDelete(row) {
  try { await ElMessageBox.confirm('确定删除吗？', '确认'); await deleteStock(row.id); ElMessage.success('已删除'); await fetchData() }
  catch { if (e !== 'cancel') ElMessage.error('删除失败') }
}
onMounted(fetchData)
</script>
