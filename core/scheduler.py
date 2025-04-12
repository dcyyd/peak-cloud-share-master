"""
@file scheduler.py
@description 峰云共享系统定时任务调度模块，主要负责后台定时文件清理任务，具备线程安全的任务调度和可配置的清理间隔与保留时间。
@functionality
    - 后台定时文件清理任务：按照指定的间隔时间，清理指定目录下超过保留时间的文件。
    - 线程安全的任务调度：使用线程和事件机制确保任务的安全启动和停止。
    - 可配置的清理间隔和保留时间：用户可以根据需要设置清理任务的执行间隔和文件保留时间。
@author D.C.Y <https://dcyyd.github.io>
@version 2.0.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import logging
from datetime import datetime
from pathlib import Path
from threading import Thread, Event

from core.path_manager import PathManager

logger = logging.getLogger(__name__)


class CleanupScheduler:
    """智能文件清理调度器

    提供安全可靠的后台文件清理服务，主要功能包括：
    - 定时执行文件清理任务：按照设定的间隔时间周期性地清理过期文件。
    - 线程安全的启动/停止机制：确保在多线程环境下任务的安全启动和停止。
    - 可配置的文件保留策略：允许用户根据需求设置文件的保留时间。

    Attributes:
        interval (int): 清理任务执行间隔，单位为秒。
        retention (float): 文件保留时间，单位为秒。
        upload_folder (Path): 需要清理的目录路径。
        _stop_event (Event): 用于控制任务停止的事件对象。
        _thread (Thread): 执行清理任务的线程对象。
    """

    def __init__(self, interval: int, retention: float, upload_folder: Path):
        """初始化清理调度器

        Args:
            interval (int): 清理任务执行间隔，单位为秒。
            retention (float): 文件保留时间，单位为秒。
            upload_folder (Path): 需要清理的目录路径。
        """
        self.interval = interval
        self.retention = retention
        self.upload_folder = PathManager.get_upload_folder()
        self._stop_event = Event()
        self._thread = None
        # logger.info(f"初始化文件清理调度器，间隔: {interval} 秒，保留时间: {retention} 秒，目录: {os.path.relpath(PathManager.get_upload_folder())}")

    def start(self):
        """安全启动调度器

        当清理任务的执行间隔小于等于 0 时，自动跳过启动，避免不必要的任务执行。

        Note:
            当 interval <= 0 时会自动跳过启动。
        """
        if self.interval <= 0:
            logger.info("清理任务已禁用")
            return

        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        # logger.info(f"启动清理任务，间隔：{self.interval}秒")

    def stop(self):
        """安全停止调度器

        会设置停止事件，等待当前任务完成后再停止线程，确保任务的安全终止。

        Note:
            会等待当前任务完成后再停止。
        """
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        logger.info("清理任务已停止")

    def _run(self):
        """任务主循环

        持续检查停止事件，若未停止则执行文件清理任务，并在出现异常时记录日志，确保线程不会意外终止。

        Note:
            捕获所有异常确保线程不会意外终止。
        """
        while not self._stop_event.is_set():
            try:
                self._cleanup_files()
            except Exception as e:
                logger.error(f"清理任务异常: {str(e)}")
            self._stop_event.wait(self.interval)

    def _cleanup_files(self):
        """安全清理过期文件

        计算截止时间，遍历指定目录下的所有文件，删除修改时间早于截止时间的文件，并在出现错误时记录日志。

        Raises:
            Exception: 当清理过程中发生错误时记录日志。
        """
        try:
            # 计算截止时间，即当前时间减去文件保留时间
            cutoff = datetime.now().timestamp() - self.retention
            # 遍历指定目录下的所有文件和文件夹
            for entry in self.upload_folder.iterdir():
                # 检查是否为文件且修改时间早于截止时间
                if entry.is_file() and entry.stat().st_mtime < cutoff:
                    try:
                        # 删除过期文件
                        entry.unlink()
                        logger.info(f"已清理文件: {entry.name}")
                    except Exception as e:
                        logger.error(f"清理失败: {entry.name} - {str(e)}")
        except Exception as e:
            logger.error(f"文件清理失败: {str(e)}")
