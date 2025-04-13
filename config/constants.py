# -*- coding: utf-8 -*-
"""
@file constants.py
@description 峰云共享系统全局配置文件，保障系统安全、高效、稳定运行。涵盖路径、安全、数据、数据库、邮件等配置。
@author D.C.Y <https://dcyyd.github.io/>
@version 2.0.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import os
from core.path_manager import PathManager

# ============================= 项目路径与目录配置 =============================
# 配置项目的核心路径和目录结构，确保系统的模块化和可扩展性。
BASE_DIR = PathManager.get_base_path()  # 项目根目录，所有其他路径的基准。
UPLOAD_FOLDER = PathManager.get_upload_folder()  # 用户上传文件存储目录，支持加密存储以保护用户隐私。
LOG_FOLDER = PathManager.get_log_folder()  # 系统日志存储目录，按日归档便于长期审计和问题追踪。
WEB_FOLDER = PathManager.get_web_folder()  # 前端静态资源目录，分离前后端提高开发效率。
ASSETS_FOLDER = PathManager.get_assets_folder()  # CDN缓存目录，加速资源加载提升用户体验。
SSL_FOLDER = PathManager.get_cert_folder()  # SSL证书存储目录，确保通信安全。
SSL_CERT = PathManager.get_cert_file()  # SSL证书文件路径，用于HTTPS配置。
SSL_KEY = PathManager.get_cert_key()  # SSL密钥文件路径，用于HTTPS配置。

# ============================= 安全与访问控制配置 =============================
# 配置系统安全策略，防止恶意攻击和资源滥用。
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'docx', 'xlsx'}  # 允许上传的文件类型白名单，确保文件合法性。
HIGH_RISK_EXTENSIONS = {
    'exe', 'bat', 'sh', 'dll', 'js',
    'vbs', 'cmd', 'ps1', 'jar', 'apk', 'scr'
}  # 高危文件类型黑名单，防止恶意文件上传。
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024 * 10  # 单文件最大上传限制为10GB，防止资源耗尽。
SESSION_SECRET = os.urandom(24)  # 动态生成会话密钥，保障用户会话安全，防止会话劫持。

# ============================= 数据生命周期配置 =============================
# 配置数据清理和保留策略，优化存储资源利用率。
CLEANUP_INTERVAL = 24 * 3600  # 自动清理过期数据的时间间隔为24小时，确保系统性能。
FILE_RETENTION = 365 * 24 * 3600  # 用户文件默认保留周期为365天，满足大多数业务需求。

# ============================= 数据库配置 =============================
# 配置数据库连接参数，支持环境变量动态调整。
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'XXX'),  # 数据库主机地址，默认为本地。
    'port': int(os.getenv('DB_PORT', 3306)),  # 数据库端口号，默认为3306（MySQL标准端口）。
    'user': os.getenv('DB_USER', 'XXX'),  # 数据库用户名，默认为root。
    'password': os.getenv('DB_PASSWORD', 'XXX'),  # 数据库密码，建议通过环境变量配置以增强安全性。
    'database': os.getenv('DB_NAME', 'XXX'),  # 数据库名称，默认为file_sharing。
    'charset': 'utf8mb4',  # 数据库字符集，支持多语言字符。
    'autocommit': True,  # 是否自动提交事务，提升性能。
    'pool_size': 5,  # 数据库连接池大小，默认为5个连接。
    'pool_name': 'main_pool'  # 数据库连接池名称，便于监控和管理。
}

# ============================= 邮件配置 =============================
# 配置邮件服务参数，支持环境变量动态调整。
EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'XXX'),  # SMTP服务器地址，默认为腾讯企业邮箱。
    'smtp_port': int(os.getenv('SMTP_PORT', XXX)),  # SMTP服务器端口号，默认为465（SSL加密）。
    'username': os.getenv('SMTP_USERNAME', 'XXX'),  # 邮件用户名，默认为测试账号。
    'password': os.getenv('SMTP_PASSWORD', 'XXX'),  # 邮件密码，建议通过环境变量配置以增强安全性。
    'sender': os.getenv('SMTP_SENDER', 'XXX'),  # 发件人邮箱地址，默认为测试账号。
    'timeout': 10  # 邮件发送超时时间，默认为10秒。
}
