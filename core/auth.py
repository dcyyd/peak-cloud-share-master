"""
@file auth.py
@description 峰云共享系统用户认证模块，用于管理用户登录和账户锁定。
@functionality
- 用户文件的初始化与校验
- 用户登录验证
- 账户锁定机制
- 原子化用户数据保存
@author D.C.Y <https://dcyyd.github.io>
@version 1.2.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple
from core.path_manager import PathManager

# 初始化日志记录器，将日志保存到独立的安全日志文件
logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """自定义异常类，用于处理用户认证相关的错误。"""
    pass


class AuthManager:
    """
    用户认证管理类，负责用户数据的加载、保存以及认证逻辑的实现。

    功能包括：
    - 用户文件的初始化与校验
    - 用户登录验证
    - 账户锁定机制
    - 原子化用户数据保存
    """

    def __init__(self, users_file: Path, lock_duration: int = 300, max_attempts: int = 3):
        """
        初始化认证管理器。

        :param users_file: 用户数据文件路径
        :param lock_duration: 账户锁定时长（秒），默认300秒（5分钟）
        :param max_attempts: 允许的最大连续登录失败次数，默认3次
        """
        self.users_file = PathManager.get_users_file()
        self.lock_duration = lock_duration
        self.max_attempts = max_attempts
        logger.info(f"初始化认证系统，用户文件路径: {self.users_file}")
        self._ensure_users_file()

    def _ensure_users_file(self):
        """
        确保用户文件存在并具有正确的格式。

        - 如果文件不存在，则创建一个空的字典结构。
        - 如果文件为空或格式不正确，则重置为字典格式。
        - 如果检测到旧版列表格式，则自动转换为字典格式。
        """
        try:
            # 确保父目录存在
            self.users_file.parent.mkdir(parents=True, exist_ok=True)

            # 创建正确的初始文件结构
            if not self.users_file.exists():
                logger.warning("用户文件不存在，正在创建空文件")
                with self.users_file.open('w') as f:
                    json.dump({}, f)  # 初始化为空字典
            else:
                # 验证现有文件结构
                with self.users_file.open('r') as f:
                    content = f.read()
                    if not content.strip():
                        logger.warning("空用户文件，重置为字典格式")
                        with self.users_file.open('w') as fw:
                            json.dump({}, fw)
                    elif content.startswith('['):  # 修复旧版列表格式
                        logger.warning("检测到旧版列表格式，自动转换")
                        old_data = json.loads(content)
                        valid_data = old_data[0] if isinstance(old_data, list) and len(old_data) > 0 else {}
                        with self.users_file.open('w') as fw:
                            json.dump(valid_data, fw)

        except Exception as e:
            logger.critical(f"初始化用户文件失败: {str(e)}", exc_info=True)
            raise

    def _load_users(self) -> Dict:
        """
        加载用户数据文件。

        :return: 包含用户数据的字典
        """
        try:
            with self.users_file.open('r', encoding='utf-8') as f:
                users = json.load(f)
                if not isinstance(users, dict):
                    logger.error(f"无效的用户文件格式，期望字典，实际得到 {type(users)}")
                    return {}

                # logger.debug(f"成功加载 {len(users)} 个用户")
                return users

        except json.JSONDecodeError as e:
            logger.error(f"用户文件格式错误: {str(e)}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"加载用户数据失败: {str(e)}", exc_info=True)
            return {}

    def validate_credentials(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """
        验证用户凭据。

        :param username: 用户名
        :param password: 密码
        :return: (验证结果, 错误信息)
        """
        clean_username = username.upper().strip()
        logger.info(f"登录尝试 - 用户名: {clean_username}")

        try:
            users = self._load_users()
            # logger.debug(f"当前用户数据库: {users}")

            if not clean_username:
                logger.warning("空用户名尝试")
                return False, "用户名不能为空"

            if clean_username not in users:
                logger.error(f"用户不存在: {clean_username} (现有用户: {list(users.keys())})")
                return False, "用户不存在"

            user = users[clean_username]
            # logger.debug(f"用户数据详情: {user}")
            if self._is_locked(user):
                remaining = self._remaining_lock_time(user)
                logger.warning(f"账户已锁定: {username} 剩余时间: {remaining}秒")
                return False, f"账户已锁定，剩余时间：{remaining}秒"

            if user['password'] != password:
                logger.warning(f"密码错误: {username}")
                user['attempts'] = user.get('attempts', 0) + 1
                if user['attempts'] >= self.max_attempts:
                    user['lock_time'] = datetime.now(timezone.utc).isoformat()
                    user['attempts'] = 0
                    logger.warning(f"账户锁定: {username}")
                self._save_users(users)
                return False, "密码错误"

            # 登录成功处理
            user.pop('lock_time', None)
            user['attempts'] = 0
            self._save_users(users)
            logger.info(f"登录成功: {username}")
            return True, None
        except Exception as e:
            logger.error(f"验证异常: {str(e)}", exc_info=True)
            return False, "系统错误"

    def _save_users(self, users: Dict):
        """
        原子化保存用户数据。

        :param users: 用户数据字典
        """
        temp_file = self.users_file.with_suffix('.tmp')
        try:
            with temp_file.open('w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
            temp_file.replace(self.users_file)
        except Exception as e:
            logger.error(f"保存用户数据失败: {str(e)}", exc_info=True)
            temp_file.unlink(missing_ok=True)
            raise

    def _is_locked(self, user: dict) -> bool:
        """
        检查用户账户是否被锁定。

        :param user: 用户数据字典
        :return: 是否被锁定
        """
        lock_time = user.get('lock_time')
        if not lock_time:
            return False

        try:
            lock_dt = datetime.fromisoformat(lock_time).astimezone(timezone.utc)
            unlock_time = lock_dt + timedelta(seconds=self.lock_duration)
            return datetime.now(timezone.utc) < unlock_time
        except ValueError:
            logger.error(f"无效的锁定时间格式: {lock_time}")
            return False

    def _remaining_lock_time(self, user: dict) -> int:
        """
        计算用户账户的剩余锁定时间。

        :param user: 用户数据字典
        :return: 剩余锁定时间（秒）
        """
        lock_time = datetime.fromisoformat(user['lock_time']).astimezone(timezone.utc)
        unlock_time = lock_time + timedelta(seconds=self.lock_duration)
        return max(0, int((unlock_time - datetime.now(timezone.utc)).total_seconds()))
