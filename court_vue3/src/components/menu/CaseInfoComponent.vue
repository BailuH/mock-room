<template>
  <div class="page">
    <el-card class="card" shadow="hover">
      <img src="@/assets/模谷趴logo.png" class="peeking-doll" alt="公仔" />
      <template #header>
        <div class="header">案件材料管理</div>
      </template>

      <el-divider content-position="left">案件管理</el-divider>
      <div class="toolbar">
        <el-select v-model="currentCaseId" placeholder="选择案件" style="width:260px">
          <el-option
        v-for="c in cases"
        :key="c.id || Math.random()" 
       :label="`${c.name || '无名称'}（${c.caseNo || '无编号'}）`"
       :value="c.id || ''" 
        />
        </el-select>
        <el-button type="primary" @click="caseDialogVisible = true">新建案件</el-button>
        <el-button type="primary" @click="handleCaseMaterials" disabled>处理案件材料</el-button>
        <el-button type="danger" :disabled="!currentCase" @click="handleDeleteCase">删除当前案件</el-button>
      </div>

      <el-dialog v-model="caseDialogVisible" title="新建案件" width="520px">
        <el-form :model="caseForm" label-position="top">
          <el-form-item label="案件名称"><el-input v-model="caseForm.name" /></el-form-item>
          <el-form-item label="案件编号"><el-input v-model="caseForm.caseNo" /></el-form-item>
          <el-form-item label="相关人员"><el-input v-model="caseForm.people" /></el-form-item>
          <el-form-item label="案件说明"><el-input type="textarea" :rows="3" v-model="caseForm.desc" /></el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="caseDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveCase">保存案件</el-button>
        </template>
      </el-dialog>

      <div v-if="currentCase" style="margin-top: 20px;">
        <el-divider content-position="left">案件基本信息</el-divider>
        <el-descriptions :column="2" size="small">
          <el-descriptions-item label="名称">{{ currentCase.name }}</el-descriptions-item>
          <el-descriptions-item label="编号">{{ currentCase.caseNo }}</el-descriptions-item>
          <el-descriptions-item label="相关人员">{{ currentCase.people || '未填写' }}</el-descriptions-item>
          <el-descriptions-item label="说明">{{ currentCase.desc || '未填写' }}</el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">OCR 文字识别</el-divider>
        <el-upload :show-file-list="false" accept="image/*" :auto-upload="false" :on-change="handleOcr">
          <el-button type="primary" :loading="ocrLoading">上传图片进行识别</el-button>
        </el-upload>
        <el-progress 
          v-if="ocrLoading" 
         :percentage="ocrProgress" 
         :striped="true" 
         :striped-flow="true" 
         style="margin-top: 10px" 
       />

        <el-table :data="currentCase.ocrHistory" size="small" style="margin-top:15px" border>
          <el-table-column prop="time" label="识别时间" width="160" />
          <el-table-column prop="preview" label="内容预览" show-overflow-tooltip />
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button type="primary" link @click="openOcrDetail(scope.row, scope.$index)">详情</el-button>
              <el-button type="danger" link @click="confirmDeleteOcr(scope.$index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <el-divider content-position="left">案件附件</el-divider>
                 <el-upload
                 drag
              multiple
             :auto-upload="false"
              :show-file-list="false"  :on-change="handleFileChange"
              >
          <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
                </el-upload>

            <el-table :data="currentCase.files" size="small" style="margin-top:10px" >
            <el-table-column prop="name" label="文件名" min-width="200" show-overflow-tooltip />
            <el-table-column prop="size" label="大小" :formatter="formatSize" width="100" />
            <el-table-column label="操作" width="160" fixed="right">
           <template #default="scope">
           <el-button type="primary" link @click="previewFile(scope.row)">预览</el-button>
            <el-button type="danger" link @click="handleRemove(scope.row, currentCase.files)">删除</el-button>
          </template>
         </el-table-column>
</el-table>
      </div>
      <el-empty v-else description="请先在上方新建或选择一个案件" />

      <el-dialog v-model="detailVisible" title="识别全文" width="600px" append-to-body>
        <div class="detail-content">
          <pre>{{ activeOcrText }}</pre>
        </div>
        <template #footer>
          <el-button type="danger" @click="deleteFromDetail">删除此条记录</el-button>
          <el-button @click="detailVisible = false">关闭</el-button>
        </template>
      </el-dialog>

      <el-dialog v-model="previewVisible" title="材料预览" width="80%">
        <iframe :src="previewUrl" style="width:100%;height:70vh" />
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref , onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import Tesseract from 'tesseract.js'
import { useCaseStore } from '@/tools/useCaseStore'
import { loginStore} from '@/tools/Storage'
import axios from 'axios'
import { baseURL } from '@/config'
//const baseURL = 'http://localhost:8081'


// 初始化 Pinia Store
const store = useCaseStore()
const { cases, currentCaseId, currentCase } = storeToRefs(store)
const userStore = loginStore()


/* 状态控制 */
const caseDialogVisible = ref(false)
const caseForm = ref({ name: '', caseNo: '', people: '', desc: '' })
const ocrLoading = ref(false)
const ocrProgress = ref(0)
const previewVisible = ref(false)
const previewUrl = ref('')
const previewType = ref('')

// OCR 详情弹窗状态
const detailVisible = ref(false)
const activeOcrText = ref('')
const activeOcrIndex = ref(-1)


onMounted(async () => {
  // 页面加载时，根据当前登录用户去数据库刷数据
  // 这会覆盖掉 localStorage 里的旧数据，保证同步
  await store.fetchCases()
})
/* --- 案件管理逻辑 --- */
const handleSaveCase = async () => {
  // 1. 基础校验
  if (!caseForm.value.name) {
    return ElMessage.warning('案件名称不能为空')
  }

  try {
    // 2. 调用 store 里的异步方法，等待后端返回数据库 ID
    // 此时 store.saveCase 内部会执行 axios.post
    await store.saveCase({ ...caseForm.value })

    // 3. 只有后端保存成功后，才执行以下 UI 逻辑
    caseDialogVisible.value = false
    
    // 重置表单
    caseForm.value = { 
      name: '', 
      caseNo: '', 
      people: '', 
      desc: '' 
    }
    
    ElMessage.success('案件创建成功并已存入数据库')
  } catch (error) {
    // 捕获网络错误或后端报错
    console.error("保存案件失败:", error)
    ElMessage.error('案件创建失败，请检查网络或后端状态')
  }
}

const handleDeleteCase = async () => {
  try {
    // 1. 确认弹窗
    await ElMessageBox.confirm(
      '确定删除该案件及其所有识别记录和文件吗？此操作不可撤销！', 
      '严正警告', 
      { 
        type: 'warning',
        confirmButtonText: '彻底删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger' // 让确定按钮变红
      }
    );

    // 2. 执行删除
    await store.deleteCase();

    // 3. 提示并自动跳转（如果是从案件详情页删除，需要回退到列表页）
    ElMessage.success('案件已成功移除');
    
    // 如果你在详情页，建议跳转回案件列表或首页
    // router.push('/dashboard'); 

  } catch (error) {
    // 捕获取消操作或接口错误
    if (error === 'cancel') {
      console.log('用户取消了案件删除');
    } else {
      ElMessage.error('删除案件失败，请检查网络或权限');
    }
  }
};


/* --- OCR 识别逻辑 --- */
const handleOcr = async (file) => {
  // 基础校验
  const currentUser = userStore.userName;
  if (!currentUser || !currentCaseId.value) {
    ElMessage.warning('请先登录并选择案件');
    return;
  }

  ocrLoading.value = true;
  ocrProgress.value = 0;

  // 1. 正确写法：在 createWorker 的第三个参数里传入 logger
  const worker = await Tesseract.createWorker('chi_sim+eng', 1, {
    logger: m => {
      if (m.status === 'recognizing text') {
        ocrProgress.value = Math.round(m.progress * 100);
      }
    }
  });

  try {
    // 2. recognize 现在只需要传入图片数据，不要传第二个语言参数和第三个配置对象
    const res = await worker.recognize(file.raw);

    // 3. 准备新记录
    const newRecord = {
      time: new Date().toLocaleString(),
      text: res.data.text,
      fileName: file.name,
      preview: res.data.text ? res.data.text.slice(0, 50) + '...' : '无文字内容',
    };

    // 4. 更新本地 Store
    if (!currentCase.value.ocrHistory) currentCase.value.ocrHistory = [];
    currentCase.value.ocrHistory.unshift(newRecord);

    // 5. 同步后端 (使用 POST 绕过网关 PATCH 限制)
    await axios.post(`${baseURL}/api/cases/${currentCaseId.value}/ocr`, {
      username: currentUser,
      ocr_history: currentCase.value.ocrHistory
    });

    ElMessage.success('识别结果已存入您的个人记录');
  } catch (e) {
    console.error("OCR 详细失败信息:", e);
    ElMessage.error('识别出错，请检查网络或图片格式');
  } finally {
    // 6. 务必在 finally 里 terminate，防止内存泄漏
    await worker.terminate();
    ocrLoading.value = false;
    ocrProgress.value = 0;
  }
}

const openOcrDetail = (row, index) => {
  activeOcrText.value = row.text
  activeOcrIndex.value = index
  detailVisible.value = true
}

const confirmDeleteOcr = async (index) => { // 1. 添加 async
  try {
    // 2. 添加 await，这会让 try...catch 真正生效
    await ElMessageBox.confirm('确定删除该条识别记录？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    // 3. 只有点击“确定”才会执行这里
    store.deleteOcrRecord(index);
    ElMessage.success('已删除');

  } catch (error) {
    // 4. 用户点击“取消”或关闭弹窗，会进入这里
    if (error === 'cancel') {
      console.log('用户取消了删除操作');
    } else {
      console.error('删除过程出错:', error);
    }
  }
};

const deleteFromDetail = () => {
  store.deleteOcrRecord(activeOcrIndex.value)
  detailVisible.value = false
  ElMessage.success('已从详情中删除')
}

/* --- 文件管理逻辑 --- */
const handleFileChange = async (file, fileList) => {
  if (file && file.raw) {
    try {
      await store.uploadFileToMinio(file.raw); // 传 file.raw !!
    } catch (err) {
      console.error("上传失败", err);
    }
  }
  if (currentCase.value) {
    
    currentCase.value.files = fileList
    await store.fetchCases()
  }
}

const handleRemove = async (file,fileList) => {
  // 情况 A：如果是本地选定但还未上传到云端的文件，直接更新本地列表
  if (!file.path) {
    currentCase.value.files = fileList;
    return;
  }
   console.log("点击了删除按钮", file); // 如果点击没反应，这行就不会打印
  // 情况 B：已上传的文件，需要前后端同步删除
  try{
    await ElMessageBox.confirm('此操作将永久删除该云端文件，是否继续？', '警告', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消'
    });
    await store.removeFile(file, fileList)
    await store.fetchCases()
    ElMessage.success('文件已删除')
}catch (error) {
    // 处理取消逻辑
    if (error === 'cancel') {
      console.log('用户取消了删除');
    } else {
      console.error('删除过程出错:', error);
    }
  }
}
/* --- 改进后的文件管理逻辑 --- */

const previewFile = async (file) => {
  // 1. 如果有 raw 对象（刚选中的文件），使用本地 URL 快速预览
  if (file.raw) {
    previewUrl.value = URL.createObjectURL(file.raw)
    previewType.value = file.raw.type // 记录文件类型
    previewVisible.value = true
    return
  }

  // 2. 如果没有 raw（历史上传的文件），从后端获取 MinIO 签名 URL
  // 这里的 file.path 是你之前 uploadFileToMinio 存入 currentCase.value.files 的路径
  if (file.path) {
    const url = await store.getFilePreviewUrl(file.path)
    if (url) {
      previewUrl.value = url
      previewType.value = file.type || '' 
      previewVisible.value = true
    } else {
      ElMessage.error('无法获取文件预览地址')
    }
  } else {
    ElMessage.warning('该文件缺少路径信息，无法预览')
  }
}

const formatSize = (row, col, val) => {
  if (!val) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(val) / Math.log(1024))
  return (val / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

 //案件材料处理功能
 const handleCaseMaterials = async() => {
    //1.确认弹窗
    await ElMessageBox.confirm(
      '确定开始处理该案件材料吗？','（将生成模拟法庭所需数据）' ,
      {
        type: 'warning',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    );
    if (!currentCase.value.files.length) return ElMessage.warning('没有可处理的文件')

    ocrLoading.value = true;
    //2.调用后台的接口进行处理
    //2.1 需要向后台发送的数据
    const data = {
          case_id: currentCaseId.value,
          filePaths: currentCase.value.files.map(file => file.path)
        }
    //2.2 调用后台接口
    try {
      const res = await axios.post(`${baseURL}/api/cases/materials`, data)
      if (res.data.code === 200) {
        return ElMessage.success('材料处理成功')
      }
    }catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('处理失败：' + (error.response?.data?.detail || '网络异常'));
    }
  } finally {
    ocrLoading.value = false;
  }
 } 


</script>
<style scoped>
/* ========== 1. 页面基础容器 (法庭纸张感) ========== */
.page { 
  padding: 30px; 
  background: #fcfaf7; 
  min-height: 100vh; 
  display: flex; 
  justify-content: center; 
  border-radius: 10px;
  font-size: 16px;
  font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

/* ========== 2. 核心卡片样式 ========== */
.card { 
  width: 1000px; 
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #d7ccc8;
  box-shadow: 0 10px 30px rgba(62, 39, 35, 0.05) !important;
  position: relative;
  overflow: visible !important;
}

.header { 
  font-size: 24px; 
  font-weight: bold; 
  color: #3e2723; 
  letter-spacing: 1px;
}

/* 2. 公仔图片的定位样式 */
.peeking-doll {
  position: absolute;
  top: -45px;    /* 向上偏移，让它看起来趴在边框上 */
  right: 1px;
  width: 170px;   /* 根据公仔图片大小调整 */
  height: auto;
  z-index: 100;  /* 确保在所有内容之上 */
  pointer-events: none; /* 让鼠标可以透过公仔点击下方的按钮 */
  
  /* 可选：增加一点自然的倾斜效果 */
  transform: rotate(5deg);
  transition: all 0.3s ease;
}

.card:hover .peeking-doll {
  transform: rotate(0deg) scale(1.1);
}

/* ========== 3. 工具栏与功能按钮 ========== */
.toolbar { 
  display: flex; 
  gap: 12px; 
  margin-bottom: 20px; 
}

/* 顶部主按钮保持实色以示区分 */
:deep(.el-button--primary) {
  background-color: #8d6e63 !important;
  border-color: #795548 !important;
}
:deep(.el-button--danger) {
  background-color: #a64452 !important;
  border-color: #82343f !important;
}

/* ========== 4. 去除颜色后的“预览”与“删除”按钮 (文字链接风格) ========== */

/* 统一重置链接按钮，去掉默认蓝色/红色的背景块 */
:deep(.el-button.is-link) {
  padding: 0 8px;
  height: auto;
  font-weight: 500;
  background: transparent !important;
  border: none !important;
}

/* 预览按钮：改为深灰文字，悬停时加重 */
:deep(.el-button--primary.is-link) {
  color: #5d4037 !important; /* 使用深木色文字代替蓝色 */
}
:deep(.el-button--primary.is-link:hover) {
  color: #3e2723 !important;
  text-decoration: underline;
}

/* 删除按钮：改为浅灰红文字，悬停时变深红 */
:deep(.el-button--danger.is-link) {
  color: #909399 !important; /* 平时显示为中性灰色，降低视觉压迫感 */
}
:deep(.el-button--danger.is-link:hover) {
  color: #a64452 !important; /* 悬停时恢复警示红 */
  text-decoration: underline;
}

/* ========== 5. 信息展示与表格优化 ========== */
:deep(.el-descriptions__label) {
  background-color: #fdfbf9 !important;
  color: #795548 !important;
  font-weight: 600;
}

:deep(.el-table) {
  --el-table-border-color: #f0ece9;
  --el-table-header-bg-color: #fdfbf9;
  color: #3e2723;
}

:deep(.el-table__header th) {
  color: #5d4037;
  font-weight: 700;
}

/* 分割线 */
:deep(.el-divider__text) {
  background-color: #ffffff;
  color: #8d6e63;
  font-weight: bold;
}

/* ========== 6. 内容详情与 OCR 区 ========== */
.detail-content {
  background: #fdfbf9;
  padding: 25px;
  border-radius: 4px;
  max-height: 450px;
  overflow-y: auto;
  border: 1px solid #e0d7d3;
  font-size: 16px;
  color: #3e2723;
}

.detail-content::-webkit-scrollbar {
  width: 6px;
}
.detail-content::-webkit-scrollbar-thumb {
  background: #d7ccc8;
  border-radius: 10px;
}

.detail-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  line-height: 1.8;
  margin: 0;
  font-family: inherit;
}

/* ========== 7. 上传与进度条 ========== */
:deep(.el-upload-dragger) {
  background-color: #fdfbf9;
  border: 2px dashed #d7ccc8;
}
:deep(.el-upload-dragger:hover) { border-color: #8d6e63; }
:deep(.el-upload__text em) { color: #8d6e63; }

:deep(.el-progress-bar__inner) {
  background-color: #8d6e63 !important;
}
</style>