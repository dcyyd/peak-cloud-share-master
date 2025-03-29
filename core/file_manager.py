"""
@file file_manager.py
@description 峰云共享系统核心文件管理模块
@functionality
    - 安全文件上传与存储
    - 文件名消毒处理
    - 文件类型验证
    - 分页文件列表查询
@author D.C.Y <https://dcyyd.github.io>
@version 1.2.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List
from werkzeug.datastructures import FileStorage
from core.path_manager import PathManager

logger = logging.getLogger(__name__)


class FileManager:
    """安全文件管理服务

    提供完整的文件管理功能，包括：
    - 安全文件上传与存储
    - 文件名消毒处理
    - 文件类型验证
    - 分页文件列表查询

    Attributes:
        upload_folder (Path): 文件上传存储目录
        allowed_extensions (set): 允许的文件扩展名集合
        max_size (int): 最大文件大小限制(字节)
    """

    def __init__(self, upload_folder: Path, allowed_extensions: set, max_size: int):
        """初始化文件管理器

        Args:
            upload_folder: 文件上传存储目录
            allowed_extensions: 允许的文件扩展名集合
            max_size: 最大文件大小限制(字节)
        """
        self.upload_folder = PathManager.get_upload_folder()
        self.allowed_extensions = allowed_extensions
        self.max_size = max_size
        self._ensure_directories()

    def _ensure_directories(self):
        """确保上传目录存在

        Raises:
            RuntimeError: 当目录创建失败时抛出
        """
        try:
            self.upload_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"创建上传目录失败: {str(e)}")
            raise

    def sanitize_filename(self, filename: str) -> str:
        """增强型文件名消毒

        Args:
            filename: 原始文件名

        Returns:
            str: 消毒后的安全文件名

        Note:
            移除所有非字母数字字符(除_-.外)和路径遍历符号
        """
        cleaned = ''.join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))
        return cleaned.replace('..', '').lstrip('/')

    def validate_extension(self, filename: str) -> bool:
        """扩展名验证

        Args:
            filename: 要验证的文件名

        Returns:
            bool: 是否允许该文件类型
        """
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save_file(self, file: FileStorage) -> str:
        """安全保存上传文件

        Args:
            file: 上传的文件对象

        Returns:
            str: 保存后的唯一文件名

        Raises:
            ValueError: 当文件大小或类型不合法时
            RuntimeError: 当文件保存失败时
        """
        if file.content_length > self.max_size:
            raise ValueError("文件大小超过限制")

        filename = self.sanitize_filename(file.filename)
        if not self.validate_extension(filename):
            raise ValueError("不支持的文件类型")

        timestamp = int(time.time())
        unique_name = f"{timestamp}_{filename}"
        save_path = self.upload_folder / unique_name

        try:
            file.save(str(save_path))
            logger.info(f"文件保存成功: {unique_name}")
            return unique_name
        except Exception as e:
            logger.error(f"文件保存失败: {str(e)}")
            raise RuntimeError("文件保存失败") from e

    def list_files(self, page: int = 1, per_page: int = 10) -> Dict:
        """安全分页文件列表

        Args:
            page: 当前页码(从1开始)
            per_page: 每页显示数量

        Returns:
            Dict: 包含分页信息的文件列表字典，结构为:
                {
                    'items': 文件列表,
                    'page': 当前页码,
                    'total_pages': 总页数,
                    'total': 总文件数
                }
        """
        files = []
        total = 0
        try:
            entries = list(self.upload_folder.iterdir())
            for entry in entries:
                if entry.is_file():
                    stat = entry.stat()
                    files.append({
                        'name': entry.name,
                        'size': stat.st_size,
                        'upload_time': stat.st_ctime,
                        'modified_time': stat.st_mtime
                    })

            # 排序和分页计算
            files.sort(key=lambda x: x['modified_time'], reverse=True)
            total = len(files)
            total_pages = max(1, (total + per_page - 1) // per_page)
            page = max(1, min(page, total_pages))
            start = (page - 1) * per_page
            end = start + per_page

            return {
                'items': files[start:end],
                'page': page,
                'total_pages': total_pages,
                'total': total
            }
        except Exception as e:
            logger.error(f"获取文件列表失败: {str(e)}", exc_info=True)
            return {
                'items': [],
                'page': 1,
                'total_pages': 1,
                'total': 0
            }
