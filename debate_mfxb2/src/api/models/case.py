"""案件和文件模型。

对应数据库表：
    - cases: 案件信息
    - case_files: 案件关联文件

功能：
    - 案件 CRUD 操作
    - 文件上传管理
    - OCR 历史记录
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, BigInteger, JSON
from sqlalchemy.orm import relationship

from src.api.models.base import Base


class CaseModel(Base):
    """案件模型。

    属性：
        id: 主键
        user_id: 所属用户 ID（外键）
        username: 用户名（冗余存储，方便查询）
        name: 案件名称
        case_no: 案件编号
        people: 涉案人员
        description: 案件描述
        ocr_history: OCR 识别历史（JSON 格式）
        files: 关联的文件列表（一对多关系）
        owner: 关联的用户（多对一关系）
    """
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_list.id", ondelete="CASCADE"), nullable=False)
    username = Column(String, index=True, comment="用户名（冗余存储）")
    name = Column(String, nullable=False, comment="案件名称")
    case_no = Column(String, comment="案件编号")
    people = Column(Text, comment="涉案人员")
    description = Column(Text, comment="案件描述")
    ocr_history = Column(JSON, default=list, comment="OCR识别历史")

    # 关系：一个案件可以有多个文件
    files = relationship("FileModel", back_populates="case", cascade="all, delete-orphan")
    # 关系：一个案件属于一个用户
    owner = relationship("User", back_populates="cases")

    def __repr__(self):
        return f"<CaseModel(id={self.id}, name={self.name}, case_no={self.case_no})>"


class FileModel(Base):
    """文件模型。

    属性：
        id: 主键
        case_id: 所属案件 ID（外键）
        file_name: 文件名
        file_path: MinIO 存储路径
        file_size: 文件大小（字节）
        file_type: 文件 MIME 类型
        case: 关联的案件（多对一关系）
    """
    __tablename__ = "case_files"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False, comment="文件名")
    file_path = Column(Text, nullable=False, comment="MinIO存储路径")
    file_size = Column(BigInteger, comment="文件大小（字节）")
    file_type = Column(String, comment="文件MIME类型")

    # 关系：一个文件属于一个案件
    case = relationship("CaseModel", back_populates="files")

    def __repr__(self):
        return f"<FileModel(id={self.id}, file_name={self.file_name}, case_id={self.case_id})>"
