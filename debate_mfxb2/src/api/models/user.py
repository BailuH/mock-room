"""用户模型。

对应数据库表：user_list

功能：
    - 用户认证（登录/注册）
    - 用户信息管理（用户名、邮箱、头像）
"""
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship

from src.api.models.base import Base


class User(Base):
    """用户模型。

    属性：
        id: 主键
        phone: 手机号（唯一，用于登录）
        password: 密码（明文存储，生产环境应使用哈希）
        user_name: 用户名/昵称
        email: 邮箱地址
        online_number: 在线编号
        avatar_url: 头像 URL（MinIO 路径）
        cases: 关联的案件列表（一对多关系）
    """
    __tablename__ = "user_list"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False, comment="手机号（登录账号）")
    password = Column(String, nullable=False, comment="密码")
    user_name = Column(String, comment="用户名/昵称")
    email = Column(String, comment="邮箱")
    online_number = Column(Integer, comment="在线编号")
    avatar_url = Column(String, comment="头像URL")

    # 关系：一个用户可以有多个案件
    cases = relationship("CaseModel", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone}, user_name={self.user_name})>"
