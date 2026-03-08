"""案件管理模块。

功能：
    - 创建案件
    - 获取案件列表
    - 删除案件
    - 更新 OCR 记录
"""
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.models.base import get_db
from src.api.models.case import CaseModel, FileModel
from src.api.models.user import User

# 创建 FastAPI 路由
router = APIRouter(prefix="/api/cases", tags=["案件"])


# ==================== 请求/响应模型 ====================


class CaseCreateRequest(BaseModel):
    """创建案件请求模型。"""
    name: str
    caseNo: Optional[str] = None
    people: Optional[str] = None
    desc: Optional[str] = None
    username: Optional[str] = None


class FileResponse(BaseModel):
    """文件响应模型。"""
    id: int
    name: str = Field(alias="file_name")
    path: str = Field(alias="file_path")
    size: Optional[int] = Field(default=None, alias="file_size")
    type: Optional[str] = Field(default=None, alias="file_type")

    class Config:
        from_attributes = True
        populate_by_name = True


class CaseResponse(BaseModel):
    """案件响应模型。"""
    id: int
    name: str
    case_no: Optional[str] = None
    people: Optional[str] = None
    description: Optional[str] = None
    ocr_history: List[Dict] = []
    files: List[FileResponse] = []

    class Config:
        from_attributes = True


class OcrUpdateRequest(BaseModel):
    """OCR 更新请求模型。"""
    username: str
    ocr_history: List[Dict]


# ==================== API 端点 ====================


@router.post("")
async def create_case(
    case_data: CaseCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """创建新案件。"""
    username = case_data.username

    # 检查用户是否存在，不存在则创建
    result = await db.execute(select(User).where(User.phone == username))
    user = result.scalars().first()
    if not user:
        user = User(
            user_name="",
            phone=username,
            password="default_password",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 创建案件
    new_case = CaseModel(
        user_id=user.id,
        username=user.phone,
        name=case_data.name,
        case_no=case_data.caseNo,
        people=case_data.people,
        description=case_data.desc,
        ocr_history=[],
    )
    db.add(new_case)
    await db.commit()
    await db.refresh(new_case)

    return {"id": new_case.id, "status": "success"}


@router.get("", response_model=List[CaseResponse])
async def get_cases(
    username: str = Query(..., description="用户名"),
    db: AsyncSession = Depends(get_db),
) -> List[CaseModel]:
    """获取当前用户的所有案件。"""
    stmt = (
        select(CaseModel)
        .options(selectinload(CaseModel.files))
        .where(CaseModel.username == username)
    )
    result = await db.execute(stmt)
    cases = result.scalars().all()
    return cases  # FastAPI 会自动使用 CaseResponse 转换


@router.delete("/{case_id}")
async def delete_case(
    case_id: int,
    username: str = Query(..., description="用户名"),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """删除案件（级联删除关联文件）。"""
    stmt = select(CaseModel).where(
        CaseModel.id == case_id,
        CaseModel.username == username,
    )
    result = await db.execute(stmt)
    db_case = result.scalars().first()

    if not db_case:
        raise HTTPException(status_code=404, detail="案件不存在或无权操作")

    try:
        await db.delete(db_case)
        await db.commit()
        return {"msg": "案件及相关数据已全部清理"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.post("/{case_id}/ocr")
async def update_ocr(
    case_id: int,
    data: OcrUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """更新案件的 OCR 记录。"""
    stmt = select(CaseModel).where(
        CaseModel.id == case_id,
        CaseModel.username == data.username,
    )
    result = await db.execute(stmt)
    db_case = result.scalars().first()

    if not db_case:
        raise HTTPException(status_code=404, detail="案件未找到或无权访问")

    db_case.ocr_history = data.ocr_history
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(db_case, "ocr_history")

    try:
        await db.commit()
        return {
            "msg": "OCR 记录已同步",
            "count": len(db_case.ocr_history),
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="保存失败")
