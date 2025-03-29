#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file app.py
@description 企业级文件共享平台主程序入口
@functionality
    - 提供完整的文件上传、下载、管理功能
    - 包含用户认证、文件管理、定时清理等核心模块
    - 支持多用户并发访问和操作
@author D.C.Y <https://dcyyd.github.io>
@version 1.2.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import atexit
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, abort
import socket
import time
from config.constants import *
from core.auth import AuthManager, AuthenticationError
from core.file_manager import FileManager
from core.scheduler import CleanupScheduler
from core.utils import FormatUtils, Pagination
from core.path_manager import PathManager

# 初始化路径
PathManager.initialize()

# ======================
# Flask应用初始化配置
# ======================
app = Flask(__name__,
            template_folder=str(PathManager.get_web_folder()),
            static_folder=str(PathManager.get_assets_folder()))
app.secret_key = SESSION_SECRET
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


# ======================
# 日志系统配置
# ======================
def setup_logging():
    """
    配置应用程序日志系统
    功能:
        - 创建日志文件夹(如果不存在)
        - 设置文件日志和控制台日志处理器
        - 配置日志格式和级别
        - 初始化各模块日志器
    参数: 无
    返回: 无
    """
    LOG_FOLDER.mkdir(parents=True, exist_ok=True)

    # 文件日志格式
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] || %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台日志格式
    console_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] || %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件日志处理器配置
    file_handler = RotatingFileHandler(
        LOG_FOLDER / 'app.log',
        maxBytes=1024 * 1024 * 5,  # 5MB
        backupCount=3,  # 保留3个备份
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # 控制台日志处理器配置
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # 根日志器配置
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(logging.DEBUG)

    # 模块日志器配置
    for logger_name in ('auth', 'file_manager', 'scheduler'):
        module_logger = logging.getLogger(logger_name)
        module_logger.setLevel(logging.DEBUG)
        module_logger.addHandler(file_handler)
        module_logger.addHandler(console_handler)
        module_logger.propagate = False


setup_logging()


# ======================
# 自定义日志适配器
# ======================
class RequestLoggerAdapter(logging.LoggerAdapter):
    """
    自定义日志适配器
    功能: 在日志记录中自动添加请求上下文信息
    继承: logging.LoggerAdapter
    """

    def process(self, msg, kwargs):
        """
        处理日志消息
        参数:
            msg: 原始日志消息
            kwargs: 额外参数
        返回:
            处理后的消息和参数
        """
        # 提供完整的默认值
        extra = kwargs.setdefault('extra', {})
        extra.update({
            'path': getattr(request, 'path', '-'),
            'method': getattr(request, 'method', '-'),
            'status_code': kwargs.pop('status_code', '-'),
            'response_time': kwargs.pop('response_time', '-')
        })

        return msg, kwargs


# 创建日志适配器实例
logger = RequestLoggerAdapter(logging.getLogger('app'), {})

# ======================
# 核心组件初始化
# ======================
auth = AuthManager(USERS_FILE)  # 认证管理器
file_manager = FileManager(UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH)  # 文件管理器
scheduler = CleanupScheduler(CLEANUP_INTERVAL, FILE_RETENTION, UPLOAD_FOLDER)  # 清理调度器

# 启动调度器并注册退出时停止的函数
scheduler.start()
atexit.register(scheduler.stop)


# ======================
# 路由配置
# ======================
def setup_routes(app):
    """
    配置所有应用路由
    参数:
        app: Flask应用实例
    返回: 无
    """

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        登录路由
        功能: 处理用户登录请求
        方法: GET, POST
        返回:
            - GET: 登录页面
            - POST: 登录结果(成功跳转主页/失败返回错误)
        """
        start_time = time.time()

        if request.method == 'GET':
            logger.info("用户尝试访问登录页面",
                        status_code=200, response_time=int((time.time() - start_time) * 1000))

        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()

            try:
                valid, message = auth.validate_credentials(username, password)
                if valid:
                    session['username'] = username.upper()
                    logger.info(f"用户 {username} 登录成功，跳转到主页",
                                status_code=200, response_time=int((time.time() - start_time) * 1000))
                    return redirect(url_for('index'))
                logger.warning(f"用户 {username} 登录失败: {message}，仍留在登录页面",
                               status_code=401, response_time=int((time.time() - start_time) * 1000))
                return render_template('login.html', error=message)
            except Exception as e:
                logger.error(f"登录异常: {str(e)}，仍留在登录页面",
                             status_code=500, response_time=int((time.time() - start_time) * 1000), exc_info=True)
                return render_template('login.html', error="系统错误")

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        """
        注销路由
        功能: 处理用户注销请求
        方法: GET
        返回: 重定向到登录页面
        """
        start_time = time.time()
        username = session.pop('username', None)
        if username:
            logger.info(f"用户 {username} 注销登录，跳转到登录页面",
                        status_code=200, response_time=int((time.time() - start_time) * 1000))
        return redirect(url_for('login'))

    @app.route('/', methods=['GET', 'POST'])
    def index():
        """
        主页路由
        功能:
            - 显示文件列表
            - 处理文件上传
        方法: GET, POST
        返回: 主页模板
        """
        start_time = time.time()

        if 'username' not in session:
            logger.warning(f"未登录用户尝试访问主页，跳转到登录页面",
                           status_code=403, response_time=int((time.time() - start_time) * 1000))
            return redirect(url_for('login'))

        page = request.args.get('page', 1, type=int)
        error = None
        success = None
        files = []
        pagination = {'current': 1, 'total': 1, 'range': []}

        if request.method == 'POST':
            if 'file' not in request.files:
                error = '请选择文件'
                logger.warning(f"用户 {session['username']} 上传文件时未选择文件，仍留在主页",
                               status_code=400, response_time=int((time.time() - start_time) * 1000))
            else:
                file = request.files['file']
                try:
                    filename = file_manager.save_file(file)
                    success = f'上传成功: {filename}'
                    logger.info(f"用户 {session['username']} 上传文件 {filename} 成功，仍留在主页",
                                status_code=200, response_time=int((time.time() - start_time) * 1000))
                except ValueError as e:
                    error = str(e)
                    logger.warning(f"用户 {session['username']} 上传文件失败: {str(e)}，仍留在主页",
                                   status_code=400, response_time=int((time.time() - start_time) * 1000))
                except Exception as e:
                    error = '文件保存失败，请稍后重试'
                    logger.error(f"用户 {session['username']} 上传文件时系统错误: {str(e)}，仍留在主页",
                                 status_code=500, response_time=int((time.time() - start_time) * 1000), exc_info=True)

        try:
            data = file_manager.list_files(page=page)
            files = data['items']
            for f in files:
                f['size'] = FormatUtils.size(f['size'])
                f['upload_time'] = FormatUtils.timestamp(f['upload_time'])
                f['modified_time'] = FormatUtils.timestamp(f['modified_time'])

            pagination = {
                'current': data['page'],
                'total': data['total_pages'],
                'range': Pagination.generate(data['page'], data['total_pages'])
            }
        except Exception as e:
            error = '获取文件列表失败，请稍后重试'
            logger.error(f"用户 {session['username']} 获取文件列表时系统错误: {str(e)}，仍留在主页",
                         status_code=500, response_time=int((time.time() - start_time) * 1000), exc_info=True)

        logger.info(f"用户 {session['username']} 访问主页",
                    status_code=200, response_time=int((time.time() - start_time) * 1000))
        return render_template(
            'index.html',
            files=files,
            pagination=pagination,
            error=error,
            success=success
        )

    @app.route('/download/<filename>')
    def download(filename):
        """
        文件下载路由
        功能: 处理文件下载请求
        参数:
            filename: 要下载的文件名
        返回: 文件下载响应或错误页面
        """
        start_time = time.time()
        if 'username' not in session:
            logger.warning(f"未登录用户尝试下载文件 {filename}，返回403错误",
                           status_code=403, response_time=int((time.time() - start_time) * 1000))
            abort(403)

        try:
            logger.info(f"用户 {session['username']} 尝试下载文件 {filename}")
            response = send_from_directory(
                directory=str(UPLOAD_FOLDER),
                path=filename,
                as_attachment=True
            )
            logger.info(f"用户 {session['username']} 下载文件 {filename} 成功",
                        status_code=200, response_time=int((time.time() - start_time) * 1000))
            return response
        except FileNotFoundError:
            logger.warning(f"用户 {session['username']} 尝试下载的文件 {filename} 不存在，返回404错误",
                           status_code=404, response_time=int((time.time() - start_time) * 1000))
            abort(404)
        except Exception as e:
            logger.error(f"用户 {session['username']} 下载文件 {filename} 时系统错误: {str(e)}，返回500错误",
                         status_code=500, response_time=int((time.time() - start_time) * 1000), exc_info=True)
            abort(500)

    @app.route('/privacy')
    def privacy():
        """
        隐私政策页面路由
        功能: 显示隐私政策
        方法: GET
        返回: 隐私政策页面
        """
        start_time = time.time()
        logger.info(f"用户尝试访问隐私政策页面",
                    status_code=200, response_time=int((time.time() - start_time) * 1000))
        return render_template('privacy.html')

    @app.route('/support')
    def support():
        """
        支持页面路由
        功能: 显示支持信息
        方法: GET
        返回: 支持页面
        """
        start_time = time.time()
        logger.info(f"用户尝试访问支持页面",
                    status_code=200, response_time=int((time.time() - start_time) * 1000))
        return render_template('support.html')

    # ======================
    # 错误处理路由
    # ======================
    @app.errorhandler(403)
    def forbidden(error):
        """
        403错误处理
        功能: 处理权限不足错误
        参数:
            error: 错误对象
        返回: 403错误页面
        """
        start_time = time.time()
        logger.warning(f"403错误: {request.url}，用户被禁止访问",
                       status_code=403, response_time=int((time.time() - start_time) * 1000))
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        """
        404错误处理
        功能: 处理页面不存在错误
        参数:
            error: 错误对象
        返回: 404错误页面
        """
        start_time = time.time()
        logger.warning(f"404错误: {request.url}，页面未找到",
                       status_code=404, response_time=int((time.time() - start_time) * 1000))
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        """
        500错误处理
        功能: 处理服务器内部错误
        参数:
            error: 错误对象
        返回: 500错误页面
        """
        start_time = time.time()
        logger.error(f"500错误: {request.url}, 错误信息: {str(error)}，服务器内部错误",
                     status_code=500, response_time=int((time.time() - start_time) * 1000), exc_info=True)
        return render_template('500.html'), 500


# 设置路由
setup_routes(app)

# ======================
# 主程序入口
# ======================
if __name__ == '__main__':
    host = '0.0.0.0'
    port = 5000

    print("可通过以下地址访问：")
    try:
        hostname = socket.gethostname()
        print(f"  本地：http://127.0.0.1:{port}")
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip != '127.0.0.1':
                print(f"  网络：http://{ip}:{port}")
    except:
        pass

    # 不显示系统启动信息
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.run(host=host, port=port, use_reloader=False)
