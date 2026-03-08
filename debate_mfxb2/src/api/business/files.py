"""文件管理模块。

功能：
    - 添加文件记录（MinIO 上传后调用）
    - 删除文件（同步删除 MinIO 和数据库记录）
"""
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.models.base import get_db
from src.api.models.case import CaseModel, FileModel
from src.api.business.storage import MinIOService, get_minio

# 创建 FastAPI 路由
router = APIRouter(prefix="/api/cases", tags=["文件"])


# ==================== 请求模型 ====================


class FileRecordRequest(BaseModel):
    """文件记录请求模型。"""
    name: str
    path: str
    size: int
    type: str


class FileDeleteRequest(BaseModel):
    """文件删除请求模型。"""
    username: str
    file_path: str


# ==================== API 端点 ====================


@router.post("/{case_id}/files")
async def add_file_record(
    case_id: int,
    file_data: FileRecordRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """添加文件记录（MinIO 上传成功后调用）。

    Args:
        case_id: 案件 ID
        file_data: 文件数据
        db: 数据库会话

    Returns:
        添加结果

    Raises:
        HTTPException: 案件不存在
    """
    # 确认案件是否存在
    result = await db.execute(select(CaseModel).where(CaseModel.id == case_id))
    target_case = result.scalars().first()
    if not target_case:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 创建文件记录
    new_file = FileModel(
        case_id=case_id,
        file_name=file_data.name,
        file_path=file_data.path,
        file_size=file_data.size,
        file_type=file_data.type,
    )
    db.add(new_file)
    await db.commit()

    return {"status": "file_recorded"}


@router.post("/{case_id}/files/delete")
async def delete_case_file(
    case_id: int,
    data: FileDeleteRequest,
    db: AsyncSession = Depends(get_db),
    minio: MinIOService = Depends(get_minio),
) -> Dict:
    """删除案件文件（同步删除 MinIO 和数据库记录）。

    Args:
        case_id: 案件 ID
        data: 包含 username 和 file_path 的请求数据
        db: 数据库会话
        minio: MinIO 服务

    Returns:
        删除结果

    Raises:
        HTTPException: 无权操作或文件不存在
    """
    username = data.username
    file_path = data.file_path

    # 查询案件并预加载关联的文件列表
    stmt = (
        select(CaseModel)
        .where(
            CaseModel.id == case_id,
            CaseModel.username == username,
        )
        .options(selectinload(CaseModel.files))
    )
    result = await db.execute(stmt)
    db_case = result.scalars().first()

    if not db_case:
        raise HTTPException(status_code=403, detail="无权操作此案件或案件不存在")

    # 在关联的文件列表中定位要删除的对象
    target_file = None
    for f in db_case.files:
        if f.file_path == file_path:
            target_file = f
            break

    if not target_file:
        raise HTTPException(status_code=404, detail="数据库中未找到该文件记录")

    try:
        # 执行删除逻辑
        # a. 从内存集合中移除
        db_case.files.remove(target_file)

        # b. 从数据库中删除记录
        await db.delete(target_file)

        # c. 物理删除 MinIO 中的文件
        await minio.delete_file(file_path)

        # d. 提交事务
        await db.commit()

        return {"msg": "文件已从数据库和云端成功删除"}

    except Exception as e:
        await db.rollback()
        print(f"删除失败日志: {e}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# 补充：获取用户信息的端点
user_info_router = APIRouter(prefix="/api", tags=["用户"])


@user_info_router.get("/basicInfo/{phone}")
async def get_basic_info(
    phone: str,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """获取用户基本信息。

    Args:
        phone: 手机号
        db: 数据库会话

    Returns:
        用户信息

    Raises:
        HTTPException: 用户不存在
    """
    from src.api.models.user import User

    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail={"msg": "用户不存在"})

    return {
        "username": user.user_name,
        "phone": user.phone,
        "email": user.email,
        "avatarUrl": user.avatar_url,
        "onlineNumber": user.online_number,
    }


class UpdateUserInfoRequest(BaseModel):
    """更新用户信息请求模型。"""
    user_name: str
    email: str
    avatar_url: str


@user_info_router.post("/basicInfo/update/{phone}")
async def update_basic_info(
    phone: str,
    request: UpdateUserInfoRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    """更新用户基本信息。

    Args:
        phone: 手机号
        request: 更新数据
        db: 数据库会话

    Returns:
        更新后的用户信息

    Raises:
        HTTPException: 用户不存在或更新失败
    """
    from src.api.models.user import User

    result = await db.execute(select(User).where(User.phone == phone))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail={"msg": "用户不存在"})

    # 修改数据
    user.user_name = request.user_name
    user.email = request.email
    user.avatar_url = request.avatar_url

    try:
        await db.commit()
        await db.refresh(user)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail={"msg": "更新失败", "error": str(e)})

    return {
        "msg": "修改成功",
        "data": {
            "username": user.user_name,
            "phone": user.phone,
            "email": user.email,
            "avatarUrl": user.avatar_url,
        },
    }


# 导出用户信息路由
__all__ = ["router", "user_info_router"]
