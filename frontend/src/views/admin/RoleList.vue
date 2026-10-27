<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span><b>角色管理</b></span>
          <el-button type="primary" size="small" @click="openCreate">
            <el-icon><Plus /></el-icon> 新增角色
          </el-button>
        </div>
      </template>
      <el-table :data="roles" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="角色名称" min-width="120" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="预置" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_preset" size="small" type="info">预置</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="功能权限" min-width="220">
          <template #default="{ row }">
            <el-tag v-for="p in row.permissions" :key="p.function_code" size="small"
              style="margin:2px 4px 2px 0">
              {{ FUNC_MAP[p.function_code] || p.function_code }}
              <span style="color:#999">({{ p.data_scope === 'all' ? '全部' : '本人' }})</span>
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEdit(row)">编辑权限</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="editing ? '编辑角色权限' : '新增角色'" width="560px">
      <el-form label-width="90px" size="small">
        <el-form-item label="角色名称" required>
          <el-input v-model="form.name" :disabled="editing" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" />
        </el-form-item>
        <el-form-item label="功能权限">
          <div style="width:100%">
            <div v-for="code in ALL_FUNCS" :key="code" style="display:flex;align-items:center;margin-bottom:8px">
              <el-checkbox v-model="form.selected[code]" :disabled="editing && form.is_preset && form.name === '管理员' && code === 'system_manage'">
                {{ FUNC_MAP[code] || code }}
              </el-checkbox>
              <el-select v-model="form.scopes[code]" size="small" style="width:100px;margin-left:12px"
                :disabled="editing && form.is_preset && form.name === '管理员' && code === 'system_manage'">
                <el-option label="本人" value="self" />
                <el-option label="全部" value="all" />
              </el-select>
            </div>
          </div>
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getRoles, createRole, updateRolePermissions } from '../../api/index.js'

const FUNC_MAP = {
  strategy_manage: '策略管理',
  stock_manage: '标的管理',
  operation_detail: '操作明细',
  monitor_config: '监控设置',
  profit_analysis: '收益分析',
  backtest_manage: '模拟回测',
  document_view: '操作手册',
  message_center: '站内消息',
  system_manage: '系统管理',
}
const ALL_FUNCS = Object.keys(FUNC_MAP)

const roles = ref([])
const loading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const editing = ref(false)
const editId = ref(null)

const form = ref({ name: '', description: '', selected: {}, scopes: {}, is_preset: false })

function emptyForm() {
  const selected = {}
  const scopes = {}
  ALL_FUNCS.forEach(f => { selected[f] = false; scopes[f] = 'self' })
  return { name: '', description: '', selected, scopes, is_preset: false }
}

async function fetchData() {
  loading.value = true
  try {
    const r = await getRoles()
    roles.value = r.data
  } catch { ElMessage.error('加载失败') }
  finally { loading.value = false }
}

function openCreate() {
  editing.value = false
  editId.value = null
  form.value = emptyForm()
  dialogVisible.value = true
}

function openEdit(row) {
  editing.value = true
  editId.value = row.id
  const f = emptyForm()
  f.name = row.name
  f.description = row.description
  f.is_preset = row.is_preset
  row.permissions.forEach(p => {
    f.selected[p.function_code] = true
    f.scopes[p.function_code] = p.data_scope
  })
  if (row.is_preset && row.name === '管理员') {
    f.selected.system_manage = true
    f.scopes.system_manage = 'all'
  }
  form.value = f
  dialogVisible.value = true
}

async function save() {
  saving.value = true
  try {
    const permissions = ALL_FUNCS
      .filter(code => form.value.selected[code])
      .map(code => ({ function_code: code, data_scope: form.value.scopes[code] }))
    if (editing.value) {
      await updateRolePermissions(editId.value, {
        description: form.value.description,
        permissions,
      })
    } else {
      await createRole({
        name: form.value.name,
        description: form.value.description,
        permissions,
      })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    await fetchData()
  } catch (e) { ElMessage.error(e.response?.data?.detail || '保存失败') }
  finally { saving.value = false }
}

onMounted(fetchData)
</script>
