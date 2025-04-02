"""
@file path_manager.py
@description 峰云共享系统路径管理模块，负责动态获取项目路径
@functionality
    - 动态获取项目根目录
    - 支持打包后的路径解析
@author D.C.Y <https://dcyyd.github.io>
@version 1.2.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import sys
import os
from pathlib import Path


class PathManager:
    """路径管理器，负责动态获取项目路径"""

    @staticmethod
    def get_base_path() -> Path:
        """
        获取项目根目录路径
        - 在普通运行时，返回脚本所在目录
        - 在打包后，返回临时解压目录
        """
        if getattr(sys, 'frozen', False):
            # 打包后的运行环境
            base_path = Path(sys._MEIPASS)
        else:
            # 普通运行环境
            base_path = Path(__file__).parent.parent

        return base_path

    @staticmethod
    def get_upload_folder() -> Path:
        """获取文件上传存储目录"""
        return PathManager.get_base_path() / 'uploads'

    @staticmethod
    def get_users_file() -> Path:
        """获取用户数据文件路径"""
        return PathManager.get_base_path() / 'mapper/users.json'

    @staticmethod
    def get_log_folder() -> Path:
        """获取日志文件存储目录"""
        return PathManager.get_base_path() / 'log'

    @staticmethod
    def get_web_folder() -> Path:
        """获取Web前端资源目录"""
        return PathManager.get_base_path() / 'web'

    @staticmethod
    def get_assets_folder() -> Path:
        """获取静态资源目录"""
        return PathManager.get_base_path() / 'web/assets'

    @classmethod
    def initialize(cls):
        """初始化所有必要目录"""
        for path in [
            cls.get_upload_folder(),
            cls.get_log_folder(),
            cls.get_web_folder(),
            cls.get_assets_folder()
        ]:
            path.mkdir(parents=True, exist_ok=True)
