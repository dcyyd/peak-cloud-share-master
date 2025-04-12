"""
@file file_manager.py
@description 峰云共享系统核心文件管理模块
@functionality
    - 安全文件上传与存储
    - 文件名消毒处理
    - 高危文件类型检测
    - 分页文件列表查询
@author D.C.Y <https://dcyyd.github.io>
@version 2.0.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

# 导入日志模块，用于记录程序运行信息
import logging
# 导入操作系统相关功能模块
import os
# 导入日期时间模块，用于处理日期和时间
from datetime import datetime
# 导入 Path 类，用于处理文件路径
from pathlib import Path
# 导入 Dict 类型注解，用于类型提示
from typing import Dict

# 从 Flask 框架导入 request 对象和 has_request_context 函数
from flask import request, has_request_context
# 从 werkzeug 库导入 FileStorage 类，用于处理文件上传
from werkzeug.datastructures import FileStorage

# 从配置模块导入高危文件扩展名常量
from config.constants import HIGH_RISK_EXTENSIONS
# 从路径管理模块导入 PathManager 类
from core.path_manager import PathManager

# 获取名为 __name__ 的日志记录器
logger = logging.getLogger(__name__)


class FileManager:
    """安全文件管理服务"""

    def __init__(self, upload_folder: Path, allowed_extensions: set, max_size: int):
        """
        初始化文件管理服务。

        :param upload_folder: 上传文件的存储目录
        :param allowed_extensions: 允许的文件扩展名集合
        :param max_size: 允许上传的文件最大大小
        """
        # 文件夹最大允许大小
        self.folder_max_size = max_size
        # 获取上传文件夹路径
        self.upload_folder = PathManager.get_upload_folder()
        # 允许的文件扩展名集合
        self.allowed_extensions = allowed_extensions
        # 允许上传的文件最大大小
        self.max_size = max_size
        # 确保上传目录存在
        self._ensure_directories()

    def validate_folder_size(self, files: list) -> bool:
        """
        验证文件夹总大小。

        :param files: 文件列表
        :return: 如果文件夹总大小未超过限制返回 True，否则抛出异常
        """
        # 计算文件列表中所有文件的总大小
        total_size = sum(f.content_length for f in files if f)
        # 检查总大小是否超过文件夹最大允许大小
        if total_size > self.folder_max_size:
            # 若超过限制，抛出 ValueError 异常
            raise ValueError(f"文件夹总大小超过10GB限制（当前：{total_size / 1024 / 1024 / 1024:.2f}GB）")
        return True

    def _ensure_directories(self):
        """
        确保上传目录存在，如果不存在则创建。

        :raises Exception: 如果创建目录失败，抛出异常
        """
        try:
            # 创建上传目录，父目录不存在时一并创建，目录已存在时不报错
            self.upload_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # 记录创建目录失败的错误信息
            logger.error(f"创建上传目录失败: {str(e)}")
            # 重新抛出异常
            raise

    def validate_extension(self, filename: str) -> bool:
        """
        验证文件扩展名（允许所有类型）。

        :param filename: 文件名
        :return: 始终返回 True，表示允许所有文件类型
        """
        # 允许所有文件类型
        return True

    def is_high_risk(self, filename: str) -> bool:
        """
        检测高危文件类型。

        :param filename: 文件名
        :return: 如果是高危文件类型返回 True，否则返回 False
        """
        # 如果文件名中不包含扩展名分隔符，则不是高危文件
        if '.' not in filename:
            return False
        # 获取文件扩展名并转换为小写
        ext = filename.rsplit('.', 1)[1].lower()
        # 检查扩展名是否在高危文件扩展名列表中
        return ext in HIGH_RISK_EXTENSIONS

    def sanitize_filename(self, filename: str) -> str:
        """
        增强文件名消毒，支持目录结构。

        :param filename: 原始文件名
        :return: 消毒后的文件名
        """
        # 保留合法路径分隔符
        cleaned = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.', '/', '\\'))
        # 标准化路径，统一使用正斜杠
        cleaned = cleaned.replace('\\', '/')
        # 防止目录遍历
        cleaned = os.path.normpath(cleaned).lstrip('/')
        # 移除可能的目录遍历字符
        cleaned = cleaned.replace('../', '').replace('./', '')
        return cleaned

    def save_file(self, file: FileStorage, username: str) -> str:
        """
        保存文件到指定目录。

        :param file: 要保存的文件对象
        :param username: 上传文件的用户名
        :return: 文件保存后的相对路径
        :raises ValueError: 如果文件大小超过限制或文件名无效
        :raises RuntimeError: 如果文件保存失败
        """
        # 检测文件大小
        if file.content_length > self.max_size:
            # 若文件大小超过限制，抛出 ValueError 异常
            raise ValueError("单个文件大小超过10GB限制")

        # 检测文件类型
        if self.is_high_risk(file.filename):
            # 若为高危文件类型，抛出 ValueError 异常
            raise ValueError("检测到高危文件类型，禁止上传")

        # 检测文件扩展名
        filename = self.sanitize_filename(file.filename)
        if not filename:
            # 若文件名无效，抛出 ValueError 异常
            raise ValueError("无效的文件名")

        # 生成用户目录结构
        date_str = datetime.now().strftime('%Y-%m-%d')
        base_dir = self.upload_folder / username / date_str
        full_path = base_dir / filename

        # 创建目录结构
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 保存文件到指定路径
            file.save(str(full_path))
            # 记录文件保存成功的日志信息
            logger.info(
                "文件保存成功: %s",
                str(f"{username}/{date_str}/{filename}"),
                extra={
                    'method': 'POST',
                    'path': '/',
                    'status_code': 200,
                    'client_ip': request.remote_addr if has_request_context() else '-',
                    'request_id': request.id if has_request_context() else '-',
                    'user': username
                }
            )
            return filename
        except Exception as e:
            # 记录文件保存失败的日志信息
            logger.error(
                "文件保存失败: %s", str(e),
                extra={
                    'method': 'POST',
                    'path': '/',
                    'status_code': 500,
                    'client_ip': request.remote_addr if has_request_context() else '-',
                    'request_id': request.id if has_request_context() else '-',
                    'user': username
                }
            )
            # 重新抛出异常
            raise

    def list_files(self, page: int = 1, per_page: int = 20) -> Dict:
        """
        分页获取文件列表。

        :param page: 页码，默认为 1
        :param per_page: 每页显示的文件数量，默认为 20
        :return: 包含文件列表、当前页码、总页数和文件总数的字典
        """
        # 存储文件信息的列表
        files = []
        try:
            # 递归遍历所有子目录
            for entry in self.upload_folder.glob('**/*'):
                if entry.is_file():
                    # 获取文件的相对路径
                    relative_path = entry.relative_to(self.upload_folder)
                    # 获取文件的统计信息
                    stat = entry.stat()
                    # 将文件信息添加到列表中
                    files.append({
                        'name': str(relative_path),
                        'size': stat.st_size,
                        'upload_time': stat.st_ctime,
                        'modified_time': stat.st_mtime
                    })

            # 按修改时间降序排序
            files.sort(key=lambda x: x['modified_time'], reverse=True)
            # 计算文件总数
            total = len(files)
            # 计算总页数
            total_pages = max(1, (total + per_page - 1) // per_page)
            # 确保页码在有效范围内
            page = max(1, min(page, total_pages))
            # 计算当前页的起始索引
            start = (page - 1) * per_page
            # 计算当前页的结束索引
            end = start + per_page

            return {
                'items': files[start:end],
                'page': page,
                'total_pages': total_pages,
                'total': total
            }
        except Exception as e:
            # 记录获取文件列表失败的错误信息
            logger.error(f"获取文件列表失败: {str(e)}", exc_info=True)
            return {'items': [], 'page': 1, 'total_pages': 1, 'total': 0}
