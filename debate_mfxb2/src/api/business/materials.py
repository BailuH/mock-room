"""案件材料生成模块。

功能：
    - 调用多模态大模型分析案件文件
    - 生成结构化案件材料（证据列表、被告信息等）
    - 获取已生成的案件材料

处理流程：
    1. 从 MinIO 下载案件相关文件
    2. 将文件转换为 LLM 可处理的格式（图片转 Base64，PDF 逐页转换）
    3. 调用多模态大模型进行分析
    4. 解析返回的 JSON 并保存到数据库
"""
import io
import json
import base64
from typing import List, Dict, Any
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from minio.error import S3Error
import fitz  # PyMuPDF
import docx
import requests

from src.api.models.base import get_db
from src.api.models.case import CaseModel
from src.api.business.storage import get_minio, MinIOService
from dotenv import load_dotenv

load_dotenv()
# 创建 FastAPI 路由
router = APIRouter(prefix="/api/cases", tags=["案件材料"])


# ==================== 请求/响应模型 ====================


class MaterialRequest(BaseModel):
    """案件材料生成请求模型。"""
    case_id: int
    filePaths: List[str]


class MaterialResponse(BaseModel):
    """案件材料响应模型。"""
    case_material: Dict[str, Any]


# ==================== 文件处理函数 ====================


def download_file_from_minio(minio: MinIOService, file_path: str) -> bytes:
    """从 MinIO 下载文件并返回字节流。
    
    Args:
        minio: MinIO 服务实例
        file_path: 文件在 MinIO 中的路径
        
    Returns:
        文件字节流
        
    Raises:
        HTTPException: 文件下载失败
    """
    try:
        response = minio.client.get_object(minio.bucket, file_path)
        return response.read()
    except S3Error as e:
        raise HTTPException(
            status_code=404, 
            detail=f"文件拉取失败 {file_path}: {str(e)}"
        )
    finally:
        if 'response' in locals():
            response.close()
            response.release_conn()


def process_file_for_llm(file_path: str, file_bytes: bytes) -> List[Dict[str, Any]]:
    """将文件转换为 LLM 可处理的格式。
    
    支持的文件类型：
        - 图片：jpg, jpeg, png, webp → Base64 编码
        - PDF：逐页转换为图片 Base64，可选提取文本
        - Word：doc, docx → 提取纯文本
    
    Args:
        file_path: 文件路径（用于判断文件类型）
        file_bytes: 文件字节流
        
    Returns:
        LLM 消息内容列表
    """
    ext = file_path.split('.')[-1].lower()
    items = []

    # 1. 处理图片
    if ext in ['jpg', 'jpeg', 'png', 'webp']:
        base64_img = base64.b64encode(file_bytes).decode('utf-8')
        mime_type = 'jpeg' if ext == 'jpg' else ext
        items.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/{mime_type};base64,{base64_img}"}
        })

    # 2. 处理 PDF（逐页转图片）
    elif ext == 'pdf':
        try:
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                for page_index in range(len(doc)):
                    page = doc[page_index]
                    
                    # 将页面渲染为图片（2倍分辨率提高 OCR 识别率）
                    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
                    img_bytes = pix.tobytes("png")
                    base64_img = base64.b64encode(img_bytes).decode('utf-8')
                    
                    items.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_img}"}
                    })
                    
                    # 可选：附加该页文本内容（双重保障）
                    text = page.get_text()
                    if text.strip():
                        items.append({
                            "type": "text", 
                            "text": f"第{page_index+1}页文本：{text}"
                        })
                        
        except Exception as e:
            items.append({
                "type": "text", 
                "text": f"PDF 解析失败 {file_path}: {str(e)}"
            })

    # 3. 处理 Word 文档
    elif ext in ['doc', 'docx']:
        try:
            doc_obj = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc_obj.paragraphs])
            items.append({
                "type": "text", 
                "text": f"【Word文档 {file_path} 内容】:\n{text}"
            })
        except Exception as e:
            items.append({
                "type": "text", 
                "text": f"Word 解析失败: {str(e)}"
            })

    return items


# ==================== 大模型调用 ====================


SYSTEM_PROMPT = """你是一个专业的法律案件分析助手。请分析提供的所有案件材料（包含文档文本或图片）。
请你提取关键信息，！！！并且evidence_list里的provider字段一定只能是prosecutor或者defendant。并**必须且只能**输出一个符合以下结构的 JSON，不要包含任何额外的 Markdown 标记（如 ```json）:
{
  "messages": [],
  "phase": "opening",
  "evidence_list": [
    {
      "id":"E001",
      "name": "",
      "content": "",
      "provider": "defendant",
      "status": "pending"
    }
  ],
  "meta": {
    "abstract": "",
    "prosecutor_title": "",
    "prosecutor_name": "",
    "statement_charge": "",
    "defendant_name": "",
    "defendant_former_name": "",
    "defendant_birthdate": "",
    "defendant_birthplace": "海宁省武鸣市彩云县",
    "defendant_ethnicity": "汉族",
    "defendant_education": "初中",
    "defendant_occupation": "工人",
    "defendant_employer": "华盛电子厂",
    "defendant_residence": "海宁省江山市北湖区小石镇华盛电子厂宿舍",
    "defendant_ID_number": "456878198909236532",
    "defendant_legal_record": "无",
    "detention_date": "2016-03-25",
    "indictment_date": "2016-04-20",
    "attorney_name": "李某（北京典谟律师事务所）",
    "court_name": "江山市北湖区人民法院",
    "judge_name": "张审判长",
    "judge_name_2": "王陪审员",
    "clerk_name": "李书记员",
    "case_id": "江公北诉字[2016]03449号"
  },
  "user_input": null,
  "pros_question_rounds": 3,
  "pros_evience_rounds": 3,
  "pros_focus_rounds": 2,
  "current_evidence": null,
  "evidence_show_type": "single",
  "focus": [],
  "focus_index": 0
}"""


def call_llm_for_material_analysis(file_contents: List[Any]) -> Dict[str, Any]:
    # 1. 扁平化处理消息内容 (确保不是嵌套列表)
    llm_message_content = [{"type": "text", "text": "以下是本次案件的所有材料：\n"}]
    for items in file_contents:
        if isinstance(items, list):
            llm_message_content.extend(items)
        else:
            llm_message_content.append(items)

    # 2. 配置 (建议从环境变量读取)
    api_key = "r3CVtHos4AdGDvRniZ5hYyyE8sep19ulZ2NC9MMaS1qjUL2s"
    # 必须加上 /chat/ 路径
    url = "https://funhpc.com/v1/completions" 
    model_name = "Qwen3-VL-32B-Instruct"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": llm_message_content}
        ],
        "temperature": 0.4,
        "max_tokens": 4096, # 建议先调低，确保稳定性
        "stream": False
    }

    try:
        # 增加超时时间，多模态推理较慢
        response = requests.post(url, headers=headers, json=payload, timeout=150)
        
        # 如果非 200，打印详细错误并抛出
        if response.status_code != 200:
            print(f"API Error Response: {response.text}")
            raise HTTPException(status_code=500, detail=f"模型服务商返回错误: {response.text}")
            
        result_data = response.json()
        print(result_data)
        content = result_data['choices'][0]['message']['content']
        
        # --- 逻辑修正：将解析放在异常捕获之外 ---
        # 尝试直接解析
        try:
            # 清理模型可能返回的 Markdown 标签
            clean_json = content.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except json.JSONDecodeError:
            # 正则提取 JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', clean_json)
            if json_match:
                return json.loads(json_match.group(0))
            raise HTTPException(status_code=500, detail="模型未返回有效的 JSON 结构")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"网络请求失败: {str(e)}")


async def save_case_material(
    case_id: int, 
    material: Dict[str, Any], 
    db: AsyncSession
) -> Dict[str, str]:
    """保存案件材料到数据库。
    
    Args:
        case_id: 案件 ID
        material: 案件材料数据
        db: 数据库会话
        
    Returns:
        保存结果
        
    Raises:
        HTTPException: 案件不存在或保存失败
    """
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    db_case = result.scalars().first()
    
    if not db_case:
        raise HTTPException(status_code=404, detail="案件未找到")
    
    db_case.case_material = material
    
    try:
        await db.commit()
        return {"msg": "案件材料已保存"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"保存案件材料失败: {str(e)}")


# ==================== API 端点 ====================


@router.post("/materials")
async def generate_case_materials(
    payload: MaterialRequest,
    db: AsyncSession = Depends(get_db),
    minio: MinIOService = Depends(get_minio),
) -> Dict[str, Any]:
    """生成案件材料。
    
    根据提供的文件路径列表，调用多模态大模型分析案件材料，
    生成结构化的案件信息（证据列表、被告信息、庭审配置等）。
    
    Args:
        payload: 包含 case_id 和 filePaths 的请求数据
        db: 数据库会话
        minio: MinIO 服务
        
    Returns:
        生成结果
        
    Raises:
        HTTPException: 处理失败
    """
    case_id = payload.case_id
    file_paths = payload.filePaths
    
    if not file_paths:
        raise HTTPException(status_code=400, detail="没有传入可处理的文件路径")

    # 1. 批量从 MinIO 拉取并处理文件
    file_contents = []
    
    for path in file_paths:
        try:
            # 拉取文件
            file_bytes = download_file_from_minio(minio, path)
            # 预处理转换
            content_items = process_file_for_llm(path, file_bytes)
            file_contents.extend(content_items)
        except Exception as e:
            print(f"处理文件 {path} 出现异常: {e}")
            continue

    if not file_contents:
        raise HTTPException(status_code=400, detail="没有成功处理任何文件")

    # 2. 调用多模态大模型
    print("正在请求 API 分析案件材料，请稍候...")
    material_dict = call_llm_for_material_analysis(file_contents)
    
    # 3. 保存到数据库
    await save_case_material(case_id, material_dict, db)
    
    return {
        "code": 200,
        "message": "案件材料生成成功",
        "data": material_dict
    }


@router.get("/materials/{case_id}")
async def get_case_material(
    case_id: int,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """获取案件材料。
    
    根据案件 ID 返回已生成的案件材料。
    
    Args:
        case_id: 案件 ID
        db: 数据库会话
        
    Returns:
        案件材料数据
        
    Raises:
        HTTPException: 案件不存在或未生成材料
    """
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    case = result.scalars().first()
    
    if not case:
        raise HTTPException(status_code=404, detail="未找到该案件")
    
    if not case.case_material:
        raise HTTPException(status_code=404, detail="该案件尚未生成材料")
    
    return {
        "case_material": case.case_material
    }
