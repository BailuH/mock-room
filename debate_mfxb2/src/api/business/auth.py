"""用户认证模块。

功能：
    - 用户登录
    - 用户注册

注意：
    - 密码目前使用明文存储，生产环境应使用哈希加密
    - 手机号作为唯一标识符
"""
from typing import Dict, Union

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.models.base import get_db
from src.api.models.user import User

# 创建 FastAPI 路由
router = APIRouter(prefix="/api", tags=["认证"])


# ==================== 请求/响应模型 ====================


class AuthRequest(BaseModel):
    """认证请求模型。"""
    type: str  # "login" 或 "register"
    phone: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型。"""
    msg: str
    userName: str
    phone: str


class RegisterResponse(BaseModel):
    """注册响应模型。"""
    msg: str
    userName: str


# ==================== API 端点 ====================


@router.post("/login")
async def auth_handler(
    request: AuthRequest,
    db: AsyncSession = Depends(get_db),
) -> Union[RegisterResponse, LoginResponse]:
    """处理用户登录和注册。

    Args:
        request: 认证请求（type="login" 或 "register"）
        db: 数据库会话

    Returns:
        登录/注册响应

    Raises:
        HTTPException: 认证失败时
    """
    if request.type == "register":
        # 注册新用户
        result = await db.execute(select(User).where(User.phone == request.phone))
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"msg": "该手机号已注册"},
            )

        new_user = User(
            phone=request.phone,
            password=request.password,
            user_name=f"法官_{request.phone[-4:]}",
        )
        db.add(new_user)
        await db.commit()

        return RegisterResponse(
            msg="申请已提交，注册顺利完成",
            userName=new_user.user_name,
        )

    if request.type == "login":
        # 用户登录
        result = await db.execute(select(User).where(User.phone == request.phone))
        user = result.scalars().first()

        if not user or user.password != request.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"msg": "用户名或密码错误"},
            )

        return LoginResponse(
            msg="验证通过，登录顺利完成",
            userName=user.user_name,
            phone=user.phone,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={"msg": "无效的请求类型，应为 'login' 或 'register'"},
    )
