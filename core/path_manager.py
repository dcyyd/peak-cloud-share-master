"""
@file path_manager.py
@description 峰云共享系统路径管理模块，负责动态解析项目路径并管理目录结构
@functionality
    - 智能识别开发环境与打包环境，动态获取项目根目录
    - 统一管理文件存储、用户数据、日志、前端资源等核心路径
    - 提供目录初始化功能，确保系统运行环境完整性
@author D.C.Y <https://dcyyd.github.io>
@version 2.0.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import sys
from pathlib import Path


class PathManager:
    """
    项目路径管理核心类

    特性：
    - 环境自适应：自动区分开发环境与打包环境（如cx_Freeze）
    - 路径统一管理：通过属性方法获取各类系统路径
    - 安全初始化：自动创建必要目录结构，确保系统运行基础

    使用示例：
    >>> upload_path = PathManager.get_upload_folder()
    >>> users_file = PathManager.get_users_file()
    """

    @staticmethod
    def get_base_path() -> Path:
        """
        动态获取项目根路径

        实现逻辑：
        - 开发环境：返回当前文件父目录的上级目录（项目根目录）
        - 打包环境：返回可执行文件所在目录

        Returns:
            Path: 项目根路径对象

        Raises:
            FileNotFoundError: 当路径解析异常时可能抛出（极低概率）
        """
        if getattr(sys, 'frozen', False):
            # 打包环境：使用可执行文件所在目录
            base_path = Path(sys.executable).parent
        else:
            # 开发环境：基于文件位置向上回溯两级
            base_path = Path(__file__).resolve().parent.parent
        return base_path

    @staticmethod
    def get_upload_folder() -> Path:
        """
        获取文件上传存储目录路径

        路径结构：
        - {项目根目录}/uploads/

        Returns:
            Path: 上传目录路径对象
        """
        return PathManager.get_base_path() / 'uploads'

    @staticmethod
    def get_users_file() -> Path:
        """
        获取用户数据文件绝对路径

        文件格式：
        - JSON格式存储用户数据

        路径结构：
        - {项目根目录}/mapper/users.json

        Returns:
            Path: 用户数据文件路径对象
        """
        return PathManager.get_base_path() / 'mapper/users.json'

    @staticmethod
    def get_log_folder() -> Path:
        """
        获取日志文件存储目录路径

        路径结构：
        - {项目根目录}/log/

        Returns:
            Path: 日志目录路径对象
        """
        return PathManager.get_base_path() / 'logs'

    @staticmethod
    def get_web_folder() -> Path:
        """
        获取前端资源根目录路径

        包含内容：
        - HTML/CSS/JavaScript等前端静态文件

        路径结构：
        - {项目根目录}/web/

        Returns:
            Path: Web资源目录路径对象
        """
        return PathManager.get_base_path() / 'web'

    @staticmethod
    def get_assets_folder() -> Path:
        """
        获取静态资源目录路径

        包含内容：
        - 图片/字体/样式表等静态资源

        路径结构：
        - {项目根目录}/web/assets/

        Returns:
            Path: 静态资源目录路径对象
        """
        return PathManager.get_base_path() / 'web/assets'

    @staticmethod
    def get_cert_folder() -> Path:
        """
        获取证书存储目录路径

        包含内容：
        - SSL证书文件

        路径结构：
        - {项目根目录}/certs/
        """
        return PathManager.get_base_path() / 'certs'

    @classmethod
    def get_cert_file(cls):
        """
        获取服务器证书文件路径
        """
        return cls.get_cert_folder() / 'server.crt'

    @classmethod
    def get_cert_key(cls):
        """
        获取服务器证书密钥文件路径
        """
        return cls.get_cert_folder() / 'server.key'

    @classmethod
    def initialize(cls):
        """
        初始化系统目录结构

        功能特性：
        - 幂等操作：重复调用不会产生副作用
        - 自动创建缺失目录：
            * 上传目录
            * 日志目录
            * Web资源目录
            * 静态资源目录

        Raises:
            PermissionError: 当目录创建权限不足时抛出
        """
        for path in [
            cls.get_upload_folder(),
            cls.get_log_folder(),
            cls.get_web_folder(),
            cls.get_assets_folder(),
            cls.get_cert_folder()
        ]:
            path.mkdir(parents=True, exist_ok=True)
