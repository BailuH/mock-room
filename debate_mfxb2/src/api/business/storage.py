"""MinIO 对象存储服务。

功能：
    - 生成上传预签名 URL
    - 生成预览预签名 URL
    - 删除文件

Docker 配置：
    MinIO Console: http://localhost:9001 (用户名: root, 密码: @Aa123456)
    需要先创建名为 "court-cases" 的桶
"""
from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from minio import Minio

from src.api.config import settings

# 创建 FastAPI 路由
router = APIRouter(prefix="/api/oss", tags=["存储"])


class MinIOService:
    """MinIO 对象存储服务类。

    提供文件上传、预览和删除功能。
    """

    def __init__(self):
        """初始化 MinIO 客户端，并确保 bucket 存在。"""
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """确保 MinIO bucket 存在，不存在则自动创建。"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
                print(f"[MinIO] Bucket '{self.bucket}' 创建成功")
            else:
                print(f"[MinIO] Bucket '{self.bucket}' 已存在")
        except Exception as e:
            print(f"[MinIO] Bucket 检查/创建失败: {e}")
            # 不抛出异常，让后续操作决定是否需要报错

    async def get_upload_url(self, username: str, case_name: str, file_name: str) -> Dict[str, str]:
        """获取文件上传预签名 URL。

        Args:
            username: 用户名
            case_name: 案件名称
            file_name: 文件名

        Returns:
            包含 uploadUrl 和 path 的字典
        """
        # 构造 MinIO 对象路径：{username}/{case_name}/{file_name}
        object_name = f"{username}/{case_name}/{file_name}"

        try:
            # 生成 10 分钟有效的上传 URL
            url = self.client.presigned_put_object(
                self.bucket,
                object_name,
                expires=timedelta(minutes=10),
            )
            return {"uploadUrl": url, "path": object_name}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MinIO 上传 URL 生成失败: {str(e)}")

    async def get_preview_url(self, file_path: str) -> str:
        """获取文件预览预签名 URL。

        Args:
            file_path: 文件在 MinIO 中的路径

        Returns:
            预览 URL（1 小时有效）
        """
        try:
            url = self.client.presigned_get_object(
                self.bucket,
                file_path,
                expires=timedelta(hours=1),
            )
            return url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MinIO 预览 URL 生成失败: {str(e)}")

    async def delete_file(self, file_path: str) -> None:
        """删除文件。

        Args:
            file_path: 文件在 MinIO 中的路径
        """
        try:
            self.client.remove_object(self.bucket, file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"MinIO 文件删除失败: {str(e)}")


# 单例模式
_minio_service = None


def get_minio() -> MinIOService:
    """获取 MinIO 服务实例（单例）。"""
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service


# ==================== API 端点 ====================


@router.get("/upload-params")
async def get_upload_params(
    file_name: str,
    username: str,
    case_name: str,
    minio: MinIOService = Depends(get_minio),
) -> Dict[str, str]:
    """获取文件上传参数（预签名 URL）。

    Query 参数:
        file_name: 文件名
        username: 用户名
        case_name: 案件名称

    Returns:
        包含 uploadUrl 和 path 的字典
    """
    return await minio.get_upload_url(username, case_name, file_name)


@router.get("/preview")
async def get_preview_url(
    file_path: str,
    minio: MinIOService = Depends(get_minio),
) -> Dict[str, str]:
    """获取文件预览 URL。

    Query 参数:
        file_path: 文件在 MinIO 中的路径

    Returns:
        包含 url 的字典
    """
    url = await minio.get_preview_url(file_path)
    return {"url": url}
