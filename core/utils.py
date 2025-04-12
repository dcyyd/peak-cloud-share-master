"""
@file utils.py
@description 峰云共享系统核心工具模块，提供数据格式化和分页生成等常用工具功能。
@functionality
    - 数据格式化工具：包括文件大小和时间戳的格式化。
    - 智能分页生成器：根据当前页码和总页数生成合理的分页导航数组。
@author D.C.Y <https://dcyyd.github.io>
@version 2.0.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FormatUtils:
    """
    数据格式化工具集，封装了常用的数据格式化方法，以提高数据的可读性和用户体验。

    提供的功能包括：
    - 文件大小单位转换：将字节表示的文件大小转换为易读的字符串。
    - 时间戳格式化：将 Unix 时间戳转换为标准的日期时间字符串。
    """

    @staticmethod
    def size(size_bytes: int) -> str:
        """
        将文件大小（以字节为单位）格式化为易读的字符串。

        Args:
            size_bytes (int): 文件的大小，以字节为单位。

        Returns:
            str: 格式化后的文件大小字符串，例如 "1.5 MB"。

        Example:
            >>> FormatUtils.size(1500000)
            '1.4 MB'

        Notes:
            - 支持的单位包括 B、KB、MB、GB 和 TB。
            - 每个单位之间的转换因子为 1024。
        """
        # 定义文件大小单位
        units = ('B', 'KB', 'MB', 'GB', 'TB')
        # 单位转换因子
        factor = 1024.0
        for unit in units:
            if size_bytes < factor:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= factor
        return f"{size_bytes:.1f} {units[-1]}"

    @staticmethod
    def timestamp(ts: float) -> str:
        """
        将 Unix 时间戳格式化为标准的日期时间字符串。

        Args:
            ts (float): Unix 时间戳，表示自 1970 年 1 月 1 日以来的秒数。

        Returns:
            str: 格式化后的日期时间字符串，格式为 "YYYY-MM-DD HH:MM:SS"。

        Notes:
            - 该方法使用 datetime 模块进行时间戳转换。
        """
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


class Pagination:
    """
    智能分页生成器，用于生成符合用户需求的分页导航数组。

    该类的主要功能包括：
    - 自动计算页码范围：根据当前页码和总页数，计算出合理的显示页码范围。
    - 省略号处理：当总页数较多时，使用省略号表示中间未显示的页码。
    - 边界条件处理：确保生成的分页导航数组在各种边界条件下都能正常工作。
    """

    @staticmethod
    def generate(current: int, total_pages: int, margin: int = 2) -> list:
        """
        根据当前页码、总页数和页边距生成分页导航数组。

        Args:
            current (int): 当前页码，从 1 开始计数。
            total_pages (int): 总页数。
            margin (int, optional): 当前页两侧显示的页数，默认为 2。

        Returns:
            list: 分页导航数组，可能包含页码和省略号。

        Example:
            >>> Pagination.generate(5, 10)
            [1, '...', 3, 4, 5, 6, 7, '...', 10]

        Notes:
            - 当总页数小于等于 5 时，显示所有页码。
            - 省略号用于表示中间未显示的页码。
        """
        # 当总页数较少时，直接显示所有页码
        if total_pages <= 5:
            return list(range(1, total_pages + 1))

        pages = []
        # 计算当前页左侧的最小页码
        left = max(1, current - margin)
        # 计算当前页右侧的最大页码
        right = min(total_pages, current + margin)

        # 如果左侧有省略页，添加起始页码和省略号
        if left > 1:
            pages.extend([1, '...'])
        # 添加当前页附近的页码
        pages.extend(range(left, right + 1))
        # 如果右侧有省略页，添加省略号和最后一页页码
        if right < total_pages:
            pages.extend(['...', total_pages])

        # 过滤掉无效的页码和省略号
        return [x for x in pages if x not in ('...', 0)]
