from pathlib import Path
import os
from core.path_manager import PathManager

# ==================== 基础路径配置 ====================
BASE_DIR = PathManager.get_base_path()
UPLOAD_FOLDER = PathManager.get_upload_folder()
USERS_FILE = PathManager.get_users_file()
LOG_FOLDER = PathManager.get_log_folder()
WEB_FOLDER = PathManager.get_web_folder()
ASSETS_FOLDER = PathManager.get_assets_folder()

# ==================== 安全配置 ====================
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}  # 允许上传的文件扩展名
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 最大上传文件大小(1GB)
SESSION_SECRET = os.urandom(24)  # 会话加密密钥(每次启动随机生成)

# ==================== 清理策略 ====================
CLEANUP_INTERVAL = 3600  # 文件清理任务执行间隔(秒)
FILE_RETENTION = 7 * 24 * 3600  # 文件保留时间(7天)
