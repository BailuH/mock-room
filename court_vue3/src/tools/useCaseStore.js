import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginStore } from '@/tools/Storage'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { baseURL} from '@/config'

export const useCaseStore = defineStore('case', () => {
  const cases = ref([])
  const currentCaseId = ref(null)
  const Store = loginStore()
  //const baseURL = 'http://10914zyur6666.vicp.fun:46398'


  const currentCase = computed(() =>
    cases.value.find(c => c.id === currentCaseId.value)
  )

  // 1. 保存案件
  const saveCase = async (formData) => {
    const username = Store.userName || 'default_user'
    try {
      // 1. 请求后端接口存入 PostgreSQL
      const { data } = await axios.post(`${baseURL}/api/cases`, {
        ...formData,
        username: username
      })
      
      // 2. 后端返回 psql 生成的真实 id
      const newCase = {
        id: data.id, 
        ...formData,
        files: [],
        ocrHistory: []
      }
      cases.value.push(newCase)
      currentCaseId.value = newCase.id
      ElMessage.success('案件保存到数据库成功')
    } catch (error) {
      ElMessage.error('案件保存失败')
    }
  }

  // 2. 删除当前案件
  const deleteCase = async () => {
  if (!currentCaseId.value) return;

  try {
    const currentUser = Store.userName;
    await axios.delete(`${baseURL}/api/cases/${currentCaseId.value}`, {
      params: { username: currentUser } // 校验身份
    });

    // 从本地内存列表中移除
    const index = cases.value.findIndex(c => c.id === currentCaseId.value);
    if (index !== -1) {
      cases.value.splice(index, 1);
    }

    // 重置当前选中的 ID，避免 UI 继续显示已删除的数据
    currentCaseId.value = null;
    
    return true;
  } catch (error) {
    console.error("删除案件失败:", error);
    throw error;
  }
};
const deleteOcrRecord = async (index) => {
  // 1. 弹出确认框
  try{
      if (currentCase.value) {
      // 2. 本地删除
      currentCase.value.ocrHistory.splice(index, 1)

      // 3. 同步到后端 (因为网关问题，建议使用 POST 覆盖)
      await axios.post(`${baseURL}/api/cases/${currentCaseId.value}/ocr`, {
        username: Store.userName,
        ocr_history: currentCase.value.ocrHistory
      })

      ElMessage.success('记录已永久删除')
    }
  } catch (error) {
    if (error === 'cancel') {
      console.log('用户取消了删除操作');
      return; }
    
    if (error !== 'cancel') {
      console.error("删除失败:", error)
      ElMessage.error('删除失败，请稍后重试')
      // 如果后端同步失败，建议重新拉取一次数据，或者让前端回滚，避免数据不一致
    }
  }
}

  // 4. 清空所有数据
  const clearAllData = () => {
    cases.value = []
    currentCaseId.value = null
  }

 const uploadFileToMinio = async (file) => {
    if (!file || !currentCase.value) return

    const username = Store.userName || 'default_user'
    const caseName = currentCase.value.name

    try {
      // Step 1: 获取 MinIO 预签名 URL (后端)
      const { data: params } = await axios.get(`${baseURL}/api/oss/upload-params`, {
        params: { file_name: file.name, username, case_name: caseName }
      })

      // Step 2: 上传文件到 MinIO
      await axios.put(params.uploadUrl, file, {
        headers: { 'Content-Type': file.type }
      })

      // Step 3: 将文件路径存入 PostgreSQL (关键一步！)
      const fileRecord = {
        name: file.name,
        path: params.path,
        size: file.size,
        type: file.type
      }
      await axios.post(`${baseURL}/api/cases/${currentCaseId.value}/files`, fileRecord)

      // Step 4: 更新本地状态
      currentCase.value.files.push(fileRecord)
      ElMessage.success(`${file.name} 上传并记录成功`)
    } catch (error) {
      console.error("文件流程失败", error)
      ElMessage.error('上传失败')
    }
  }
// useCaseStore.js
  const getFilePreviewUrl = async (path) => {
  try {
    const { data } = await axios.get(baseURL + '/api/oss/preview', {
      params: { file_path: path }
    });
    return data.url; // 返回生成好的临时链接
  } catch (error) {
    console.error("获取预览链接失败", error);
    ElMessage.error("预览失败");
  }
}
const fetchCases = async () => {
    const username = Store.userName || 'default_user'
    try {
      const { data } = await axios.get(`${baseURL}/api/cases`, { params: { username } })
      console.log("第一个案件的第一个文件详情：", data[0]?.files[0])
      // data 现在包含了从 psql 查出的嵌套了 files 的案件列表
      cases.value = data.map(item => ({
      ...item,
      caseNo: item.case_no || item.caseNo || '无编号',
      // 这里的 'description' 必须与后端模型字段名一致
      desc: item.description || item.desc || '', 
      // 这里的 'files' 必须与后端 relationship 名一致
      files: (item.files || []).map(f => ({
        id: f.id,
        // 将 file_name 映射为 name
        name: f.file_name || f.name, 
        // 将 file_size 映射为 size
        size: f.file_size || f.size, 
        // 将 file_path 映射为 path
        path: f.file_path || f.path,
        // 其他字段保持原样或按需添加
        type: f.file_type || f.type || 'unknown'
      })), 
      ocrHistory: item.ocr_history || []
    }))
      if (cases.value.length > 0 && !currentCaseId.value) {
        currentCaseId.value = cases.value[0].id
        console.log("后端返回的案件列表：", data)
      }
    } catch (error) {
      console.error("加载案件失败", error)
    }
  }
  const removeFile = async (file, fileList) => {
  // 获取当前登录用户名
  const currentUser = Store.userName;
  if (!currentUser) {
    ElMessage.error('登录已过期，请重新登录');
    return;
  }

  
  try{
    // 调用接口，传递 case_id, username, 以及剔除该文件后的新列表
    await axios.post(`${baseURL}/api/cases/${currentCaseId.value}/files/delete`, {
      username: currentUser,  // 传递用户名
      file_path: file.path,   // 告诉后端要删 MinIO 里的哪个路径
      file_list: fileList.map(f => ({
        name: f.name,
        path: f.path,
        size: f.size,
        type: f.type
      }))
    });

    // 接口成功后，更新本地响应式数据
    const newList = currentCase.value.files.filter(f => f.path !== file.path);
    currentCase.value.files = [...newList];
    ElMessage.success('云端文件已成功删除');

  } catch (err) {
    if (err === 'cancel') {
      console.log('用户取消了删除操作');
      return;}
    if (err !== 'cancel') {
      console.error("文件删除同步失败:", err);
      ElMessage.error('同步删除失败，请检查网络或权限');
    }
  }}


  // 注意：所有的逻辑必须在 return 之前完成
  return {
    cases,
    currentCaseId,
    currentCase,
    saveCase,
    deleteCase,
    deleteOcrRecord,
    clearAllData,
    uploadFileToMinio,
    getFilePreviewUrl,
    fetchCases,
    removeFile
  }
}, //{
  // 持久化配置作为 defineStore 的第二个参数
  //persist: {
   // key: 'court-cases-data',
    //storage: localStorage,
    //paths: ['cases', 'currentCaseId']
  //}
//}
)