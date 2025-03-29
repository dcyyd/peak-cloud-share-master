"""
@file utils.py
@description 峰云共享系统核心工具模块
@functionality
    - 数据格式化工具(文件大小、时间戳)
    - 智能分页生成器
@author D.C.Y <https://dcyyd.github.io>
@version 1.2.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FormatUtils:
    """数据格式化工具集

    提供常用的数据格式化功能，包括：
    - 文件大小单位转换
    - 时间戳格式化
    """

    @staticmethod
    def size(size_bytes: int) -> str:
        """格式化文件大小为易读字符串

        Args:
            size_bytes: 文件大小(字节)

        Returns:
            str: 格式化后的字符串(如"1.5 MB")

        Example:
            >>> FormatUtils.size(1500000)
            '1.4 MB'
        """
        units = ('B', 'KB', 'MB', 'GB', 'TB')
        factor = 1024.0
        for unit in units:
            if size_bytes < factor:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= factor
        return f"{size_bytes:.1f} {units[-1]}"

    @staticmethod
    def timestamp(ts: float) -> str:
        """格式化时间戳为标准日期时间字符串

        Args:
            ts: Unix时间戳

        Returns:
            str: 格式化后的日期时间字符串(如"2023-01-01 12:00:00")
        """
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


class Pagination:
    """智能分页生成器

    提供分页导航生成功能，支持：
    - 自动计算页码范围
    - 省略号处理
    - 边界条件处理
    """

    @staticmethod
    def generate(current: int, total_pages: int, margin: int = 2) -> list:
        """生成分页导航数组

        Args:
            current: 当前页码(从1开始)
            total_pages: 总页数
            margin: 当前页两侧显示的页数(默认为2)

        Returns:
            list: 分页导航数组，可能包含页码和省略号

        Example:
            >>> Pagination.generate(5, 10)
            [1, '...', 3, 4, 5, 6, 7, '...', 10]
        """
        if total_pages <= 5:
            return list(range(1, total_pages + 1))

        pages = []
        left = max(1, current - margin)
        right = min(total_pages, current + margin)

        if left > 1:
            pages.extend([1, '...'])
        pages.extend(range(left, right + 1))
        if right < total_pages:
            pages.extend(['...', total_pages])

        return [x for x in pages if x not in ('...', 0)]
