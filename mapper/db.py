"""
@file db.py
@description 峰云共享系统数据库连接管理模块，负责安全高效地管理数据库连接与操作。
@functionality
    - 管理数据库连接池，提升数据库操作效率，减少频繁创建和销毁连接带来的性能损耗，适应高并发业务场景。
    - 执行数据库查询和操作，支持参数化查询防止 SQL 注入，保障数据安全，符合商业数据安全标准。
    - 提供详细的错误日志记录，便于问题排查和维护，助力运维团队快速定位和解决数据库相关问题。
    - 增加重试机制，提高数据库操作的稳定性，降低因临时网络或数据库服务问题导致的操作失败率。
@author  D.C.Y <https://dcyyd.github.io>
@version 2.0.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import logging
import pymysql
from dbutils.pooled_db import PooledDB
from pymysql import cursors
from pymysql.err import OperationalError

# 从配置文件中导入数据库配置常量
# 从配置文件集中管理数据库连接信息，便于维护和修改，符合商业代码可维护性原则
from config import constants

# 配置日志记录
# 配置日志记录级别和格式，详细记录错误信息，为商业系统的运维和监控提供有力支持
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')


class Database:
    """
    数据库连接池类，用于管理数据库连接，提高数据库操作的效率和安全性。
    采用连接池技术，避免频繁创建和销毁数据库连接，同时支持参数化查询防止 SQL 注入。
    在商业场景中，该类能够显著提升系统的响应速度和数据安全性，降低运营成本。
    """
    # 静态变量，用于存储数据库连接池
    # 静态变量确保在整个应用程序生命周期内只有一个连接池实例，实现资源的高效利用
    _pool = None

    @classmethod
    def get_connection(cls):
        """
        获取数据库连接池中的连接。如果连接池未初始化，则进行初始化。

        返回:
            数据库连接对象。

        商业价值:
            - 连接池的使用避免了频繁创建和销毁数据库连接的开销，提高了系统的响应速度和吞吐量。
            - 连接池的复用机制减少了数据库服务器的负载，降低了硬件成本。
            - 统一的连接管理方式便于对数据库连接进行监控和调优。
        """
        if cls._pool is None:
            try:
                # 使用 PooledDB 初始化连接池，提高连接复用率和性能
                cls._pool = PooledDB(
                    # 指定数据库连接的创建者为 pymysql
                    creator=pymysql,
                    # 数据库主机地址
                    host=constants.DB_CONFIG['host'],
                    # 数据库端口号
                    port=constants.DB_CONFIG['port'],
                    # 数据库用户名
                    user=constants.DB_CONFIG['user'],
                    # 数据库用户密码
                    password=constants.DB_CONFIG['password'],
                    # 要连接的数据库名
                    database=constants.DB_CONFIG['database'],
                    # 数据库字符集
                    charset=constants.DB_CONFIG['charset'],
                    # 使用字典游标，使查询结果以字典形式返回
                    # 字典形式的结果更便于业务逻辑处理，提高开发效率
                    cursorclass=cursors.DictCursor,
                    # 是否自动提交事务
                    autocommit=constants.DB_CONFIG['autocommit'],
                    # 连接池中空闲连接的初始数量
                    mincached=constants.DB_CONFIG['pool_size'],
                    # 连接池中空闲连接的最大数量
                    maxcached=constants.DB_CONFIG['pool_size']
                )
            except Exception as e:
                # 记录连接池初始化失败的详细信息
                # 详细的错误日志有助于快速定位和解决问题，减少系统停机时间
                logging.error(f"Failed to initialize database connection pool: {str(e)}")
                raise
        return cls._pool.connection()

    @classmethod
    def execute_query(cls, query, args=None, max_retries=3):
        """
        执行数据库查询或操作。

        参数:
            query (str): 要执行的 SQL 查询或操作语句。
            args (tuple, 可选): 查询参数，用于防止 SQL 注入。
            max_retries (int, 可选): 最大重试次数，默认为 3 次。

        返回:
            list 或 int: 如果是 SELECT 语句，返回查询结果列表；如果是 INSERT 语句，返回插入的行 ID。

        异常:
            OperationalError: 数据库操作出错且达到最大重试次数时抛出。

        商业价值:
            - 参数化查询有效防止 SQL 注入，保护商业数据的安全和完整性。
            - 重试机制提高了数据库操作的成功率，减少了因临时故障导致的业务中断。
            - 详细的日志记录便于对数据库操作进行监控和审计，符合合规要求。
        """
        retries = 0
        while retries < max_retries:
            try:
                # 从连接池获取连接，使用 with 语句确保连接和游标自动关闭
                # 自动关闭连接和游标，避免资源泄漏，提高系统的稳定性
                with cls.get_connection() as conn:
                    with conn.cursor() as cursor:
                        # 使用参数化查询，防止 SQL 注入
                        cursor.execute(query, args)
                        if query.strip().lower().startswith('select'):
                            # 如果是 SELECT 语句，返回所有查询结果
                            return cursor.fetchall()
                        # 如果是其他语句（如 INSERT），返回最后插入的行 ID
                        return cursor.lastrowid
            except OperationalError as e:
                retries += 1
                if retries < max_retries:
                    # 记录重试信息
                    # 记录重试信息有助于分析数据库操作的稳定性和性能瓶颈
                    logging.warning(f"Database operation failed (attempt {retries}): {str(e)}. Retrying...")
                else:
                    # 记录详细的数据库错误信息，方便后续排查问题
                    # 详细的错误日志是快速解决问题的关键，减少对业务的影响
                    logging.error(f"Database error after {max_retries} attempts: {str(e)}")
                    # 重新抛出异常，让调用者处理
                    raise
