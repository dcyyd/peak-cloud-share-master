# -*- coding: utf-8 -*-
"""
@file auth.py
@description 峰云共享系统用户认证模块，提供用户注册、登录、密码重置等功能。
@author D.C.Y <https://dcyyd.github.io/>
@version 2.0.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

# 标准库导入
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

# 第三方库导入
import bcrypt  # 密码哈希库

# 本地库导入
from mapper.db import Database

# 初始化独立安全日志记录器（与系统其他日志分离）
logger = logging.getLogger('auth')
logger.setLevel(logging.DEBUG)

# 用户名正则验证：4-20位字母/数字/下划线的任意组合，不能以数字或下划线开头
USERNAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{3,19}$')
# 密码正则验证：8-32位字母/数字/下划线/特殊符号的任意组合，不能以数字或下划线开头
PASSWORD_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_!@#$%^&*]{7,31}$')


class AuthenticationError(Exception):
    """用户认证业务逻辑异常基类

    触发场景：
    - 用户账户被锁定
    - 无效的用户名或密码
    - 用户数据文件损坏
    - 系统级I/O错误

    示例：
        raise AuthenticationError("Invalid credentials")
    """
    pass


class AuthManager:
    def __init__(self, lock_duration=300, max_attempts=3):
        """初始化认证管理器

        :param lock_duration: 账户锁定时长（秒）
        :param max_attempts: 最大失败尝试次数
        """
        self.lock_duration = lock_duration
        self.max_attempts = max_attempts
        self._init_db()

    def _init_db(self):
        """初始化数据库表结构"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(20) PRIMARY KEY,
            password VARCHAR(255) NOT NULL,
            attempts INT DEFAULT 0,
            lock_time DATETIME
        ) CHARSET=utf8mb4
        """
        Database.execute_query(create_table_sql)

    def _load_user(self, username: str) -> dict:
        """从数据库加载单个用户

        :param username: 用户名
        :return: 用户数据字典，若用户不存在则返回 None
        """
        query = "SELECT * FROM users WHERE username = %s"
        result = Database.execute_query(query, (username.upper(),))
        return result[0] if result else None

    def _save_user(self, user_data: dict) -> None:
        """原子化更新用户数据

        :param user_data: 用户数据字典
        """
        query = """
        INSERT INTO users 
            (username, password, email, attempts, lock_time)
        VALUES 
            (%(username)s, %(password)s, %(email)s, %(attempts)s, %(lock_time)s)
        ON DUPLICATE KEY UPDATE
            password = VALUES(password),
            email = VALUES(email),
            attempts = VALUES(attempts),
            lock_time = VALUES(lock_time)
        """
        Database.execute_query(query, user_data)

    def validate_credentials(self, username: str, password: str) -> Tuple[bool, Optional[str]]:
        """验证用户凭据

        :param username: 用户名
        :param password: 密码
        :return: 验证结果及错误信息（若有）
        """
        clean_user = username.upper().strip()
        user_data = self._load_user(clean_user)

        if not user_data:
            return False, "用户不存在"

        # 账户锁定检查
        if self._is_locked(user_data):
            remain_sec = self._remaining_lock_time(user_data)
            return False, f"账户已锁定，请{remain_sec}秒后重试"

        # 密码验证
        hashed_password = user_data['password'].encode('utf-8')
        if not bcrypt.checkpw(password.encode('utf-8'), hashed_password):
            user_data['attempts'] += 1
            if user_data['attempts'] >= self.max_attempts:
                user_data['lock_time'] = datetime.now(timezone.utc)
                user_data['attempts'] = 0
            self._save_user(user_data)
            return False, "密码错误"

        # 登录成功重置状态
        user_data['attempts'] = 0
        user_data['lock_time'] = None
        self._save_user(user_data)
        return True, None

    def generate_verification_code(self, email: str) -> str:
        """生成并存储验证码

        :param email: 用户邮箱
        :return: 生成的验证码
        """
        from core.email_sender import EmailSender
        import random

        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise AuthenticationError("无效的邮箱格式")

        # 生成6位数字验证码
        code = ''.join(random.choices('0123456789', k=6))
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        # 存储到数据库
        query = """
        INSERT INTO verification_codes 
        (email, code, expires_at)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            code = VALUES(code),
            expires_at = VALUES(expires_at)
        """
        Database.execute_query(query, (email, code, expires_at))

        # 发送邮件
        try:
            EmailSender.send_verification_code(email, code)
        except Exception as e:
            raise AuthenticationError(str(e))

        return code

    def verify_code(self, email: str, code: str) -> bool:
        """验证验证码有效性

        :param email: 用户邮箱
        :param code: 验证码
        :return: 验证结果
        """
        query = """
        SELECT code, expires_at FROM verification_codes
        WHERE email = %s AND expires_at > UTC_TIMESTAMP()
        ORDER BY created_at DESC
        LIMIT 1
        """
        result = Database.execute_query(query, (email,))
        if not result:
            return False
        stored_code = result[0].get('code')
        return stored_code == code

    def _is_locked(self, user_data: dict) -> bool:
        """判断用户账户是否被锁定

        :param user_data: 包含lock_time的用户数据
        :return: 如果账户被锁定返回 True，否则返回 False
        """
        try:
            lock_time = user_data.get('lock_time')
            if lock_time:
                lock_time = datetime.fromisoformat(lock_time).astimezone(timezone.utc)
                expiry_time = lock_time + timedelta(seconds=self.lock_duration)
                return expiry_time > datetime.now(timezone.utc)
            return False
        except Exception as e:
            logger.error("判断锁定状态失败", exc_info=True, extra={'error': str(e)})
            return False

    def _remaining_lock_time(self, user_data: dict) -> int:
        """计算剩余锁定时间（秒）

        :param user_data: 包含lock_time的用户数据
        :return: 剩余锁定时间，单位秒（不小于0）
        """
        try:
            lock_time = datetime.fromisoformat(user_data['lock_time']).astimezone(timezone.utc)
            expiry_time = lock_time + timedelta(seconds=self.lock_duration)
            delta = max(expiry_time - datetime.now(timezone.utc), timedelta(0))
            remain_sec = int(delta.total_seconds())
            logger.debug("计算剩余锁定时间", extra={
                'lock_time': user_data['lock_time'],
                'remaining_seconds': remain_sec
            })
            return remain_sec
        except Exception as e:
            logger.error("计算锁定时间失败", exc_info=True, extra={'error': str(e)})
            return 0

    def hash_password(self, password: str) -> str:
        """对密码进行哈希处理

        :param password: 明文密码
        :return: 哈希后的密码
        """
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
