<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span><b>系统参数配置</b></span>
          <el-button type="primary" size="small" @click="openCreate">
            <el-icon><Plus /></el-icon> 新增参数
          </el-button>
        </div>
      </template>
      <el-table :data="pagedParams" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="90">
          <template #header>
            <div class="header-filter">
              <span>ID</span>
              <el-input v-model="paramFilters.id" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="param_key" label="参数键" min-width="190">
          <template #header>
            <div class="header-filter">
              <span>参数键</span>
              <el-input v-model="paramFilters.param_key" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="param_value" label="参数值" min-width="130">
          <template #header>
            <div class="header-filter">
              <span>参数值</span>
              <el-input v-model="paramFilters.param_value" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="210">
          <template #header>
            <div class="header-filter">
              <span>说明</span>
              <el-input v-model="paramFilters.description" placeholder="搜索" size="small" clearable />
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="table-footer">
        <el-pagination
          v-model:current-page="paramPage"
          v-model:page-size="paramPageSize"
          :total="filteredParams.length"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          background
        />
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑参数' : '新增参数'" width="420px">
      <el-form :model="form" label-width="90px" size="small">
        <el-form-item label="参数键" required>
          <el-input v-model="form.param_key" :disabled="editing" />
        </el-form-item>
        <el-form-item label="参数值" required>
          <el-input v-model="form.param_value" />
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getParams, createParam, updateParam } from '../../api/index.js'

const params = ref([])
const loading = ref(false)
const paramFilters = ref({ id: '', param_key: '', param_value: '', description: '' })
const paramPage = ref(1)
const paramPageSize = ref(10)
const saving = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref(null)
const form = ref({})

const filteredParams = computed(() => {
  const f = paramFilters.value
  const hasFilter = Object.values(f).some(v => (v || '').trim() !== '')
  if (!hasFilter) return params.value
  const match = (field, value) => !(field || '').trim() || String(value ?? '').includes((field || '').trim())
  return params.value.filter(row => (
    match(f.id, row.id)
    && match(f.param_key, row.param_key)
    && match(f.param_value, row.param_value)
    && match(f.description, row.description)
  ))
})
const pagedParams = computed(() => {
  const start = (paramPage.value - 1) * paramPageSize.value
  return filteredParams.value.slice(start, start + paramPageSize.value)
})
watch([filteredParams, paramPageSize], () => {
  const maxPage = Math.max(1, Math.ceil(filteredParams.value.length / paramPageSize.value))
  if (paramPage.value > maxPage) paramPage.value = maxPage
})
watch(paramPageSize, () => { paramPage.value = 1 })

async function fetchData() {
  loading.value = true
  try {
    const r = await getParams()
    params.value = r.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = false
  form.value = { param_key: '', param_value: '', description: '' }
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = true
  editId.value = row.id
  form.value = { param_key: row.param_key, param_value: row.param_value, description: row.description }
  dialogVisible.value = true
}

async function save() {
  saving.value = true
  try {
    if (editing.value) {
      await updateParam(editId.value, form.value)
    } else {
      await createParam(form.value)
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
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
