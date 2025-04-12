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
@version 1.2.1
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

# 标准库导入（按字母顺序）
import atexit
import logging
import os
import socket
import sys
import threading
import time
import uuid
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 第三方库导入（按字母顺序）
from flask import (
    Flask,
    abort,
    flash,
    g,
    has_request_context,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for
)

# 本地模块导入（按工程规范）
from config.constants import (
    ALLOWED_EXTENSIONS,
    CLEANUP_INTERVAL,
    FILE_RETENTION,
    LOG_FOLDER,
    MAX_CONTENT_LENGTH,
    SESSION_SECRET,
    UPLOAD_FOLDER
)
from core.auth import AuthManager, AuthenticationError
from core.file_manager import FileManager
from core.log_analysis import AdvancedLogAnalyzer
from core.path_manager import PathManager
from core.scheduler import CleanupScheduler
from core.utils import FormatUtils, Pagination
from mapper.db import Database


# ======================
# 初始化路径
# ======================
def initialize_system():
    """初始化系统路径和基础配置"""
    PathManager.initialize()
    logging.info(f"系统路径初始化完成：")
    # 修改路径显示为相对路径
    logging.info(f"   - 上传目录: {os.path.relpath(UPLOAD_FOLDER)}")
    logging.info(f"   - 日志目录: {os.path.relpath(LOG_FOLDER)}")
    logging.info(f"   - 静态资源目录: {os.path.relpath(PathManager.get_assets_folder())}")
    logging.info(f"   - 模板目录: {os.path.relpath(PathManager.get_web_folder())}")


# ======================
# Flask应用初始化配置
# ======================
def initialize_flask_app():
    """初始化Flask应用"""
    app = Flask(__name__,
                template_folder=str(PathManager.get_web_folder()),
                static_folder=str(PathManager.get_assets_folder()))
    app.secret_key = SESSION_SECRET
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    logging.info("Flask应用初始化完成")
    return app


# ======================
# 日志系统配置（优化版）
# ======================
def setup_logging():
    """
    配置专业级日志系统
    优化功能:
        - 更详细的请求信息记录（方法、路径、状态码、响应时间）
        - 结构化日志格式
        - 分离访问日志和应用日志
        - 增加请求ID追踪
    """
    logging.info("正在配置日志系统...")

    # 确保日志目录存在
    os.makedirs(LOG_FOLDER, exist_ok=True)

    # 日志格式配置
    class RequestFormatter(logging.Formatter):
        """自定义日志格式化器，包含请求上下文"""

        def format(self, record):
            # 确保所有字段都有默认值
            defaults = {
                'request_id': '-',
                'client_ip': '-',
                'method': '-',
                'path': '-',
                'status_code': '-',
                'response_time': '-',
                'user_agent': '-',
                'user': '-',
                'scheme': '-'
            }
            for key, val in defaults.items():
                if not hasattr(record, key):
                    setattr(record, key, val)
            return super().format(record)

    # 主日志格式
    main_format = (
        '[%(asctime)s] [%(levelname)-8s] '
        '[%(name)-20s] [%(client_ip)s] [%(user)s] '
        '%(message)s '
        '[%(scheme)s://%(method)s => %(status_code)s in %(response_time)sms]'
    )
    date_format = '%Y-%m-%d %H:%M:%S'

    # 1. 应用日志（记录所有INFO和WARNING事件）
    app_log_handler = RotatingFileHandler(
        os.path.join(LOG_FOLDER, 'application.log'),
        maxBytes=1024 * 1024 * 100,  # 100MB
        backupCount=5,
        encoding='utf-8'
    )
    app_log_handler.setFormatter(RequestFormatter(main_format, datefmt=date_format))
    app_log_handler.setLevel(logging.INFO)

    # 2. 访问日志（专门记录HTTP请求）
    access_log_handler = RotatingFileHandler(
        os.path.join(LOG_FOLDER, 'access.log'),
        maxBytes=1024 * 1024 * 50,  # 50MB
        backupCount=3,
        encoding='utf-8'
    )
    access_log_handler.setFormatter(RequestFormatter(
        '[%(asctime)s] [%(client_ip)s] [%(request_id)s] '
        '"%(method)s %(path)s" %(status_code)s '
        '%(response_time)sms "%(user_agent)s"',
        datefmt=date_format
    ))
    access_log_handler.setLevel(logging.INFO)
    access_log_handler.addFilter(lambda record: record.name == 'access')

    # 3. 错误日志（记录所有错误）
    error_log_handler = RotatingFileHandler(
        os.path.join(LOG_FOLDER, 'error.log'),
        maxBytes=1024 * 1024 * 50,  # 50MB
        backupCount=3,
        encoding='utf-8'
    )
    error_log_handler.setFormatter(RequestFormatter(main_format, datefmt=date_format))
    error_log_handler.setLevel(logging.ERROR)

    # 4. 控制台日志（仅显示启动流程信息和错误信息）
    console_handler = logging.StreamHandler()

    # 修改控制台日志格式（删除冗余字段）
    console_formatter = RequestFormatter(
        '\033[1;34m%(asctime)s\033[0m '
        '[\033[1;%(colorcode)sm%(levelname)-8s\033[0m] '
        '[\033[1;35m%(name)-20s\033[0m] '
        '%(message)s '
        '\033[1;30m[%(scheme)s://%(method)s => %(status_code)s in %(response_time)sms]\033[0m',
        datefmt=date_format
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # 控制台日志颜色过滤器

    # 控制台日志颜色过滤器（修改过滤逻辑）
    class ConsoleFilter(logging.Filter):
        def filter(self, record):
            # 仅显示系统初始化和启动信息
            allowed_messages = [
                "正在初始化系统路径",
                "系统路径初始化完成",
                "正在初始化Flask应用",
                "Flask应用初始化完成",
                "正在配置日志系统",
                "日志系统配置完成",
                "正在初始化核心组件",
                "认证管理器初始化完成",
                "文件管理器初始化完成",
                "清理调度器初始化完成",
                "清理调度器已启动",
                "正在配置应用路由",
                "应用路由配置完成",
                "正在启动应用程序",
                "找到可用端口",
                "证书检测",
                "应用程序已在"
            ]

            # 只允许系统初始化阶段日志且来自root日志器
            return (
                    record.name == 'root' and
                    any(msg in record.getMessage() for msg in allowed_messages) and
                    not hasattr(record, 'request_id')
            )

    console_handler.addFilter(ConsoleFilter())

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(app_log_handler)
    root_logger.addHandler(error_log_handler)
    root_logger.addHandler(console_handler)

    # 创建专门地访问日志器
    access_logger = logging.getLogger('access')
    access_logger.setLevel(logging.INFO)
    access_logger.addHandler(access_log_handler)
    access_logger.propagate = False

    # 配置模块日志器
    modules = ['auth', 'file_manager', 'scheduler', 'werkzeug']
    for module in modules:
        module_logger = logging.getLogger(module)
        module_logger.setLevel(logging.DEBUG)
        module_logger.addHandler(app_log_handler)
        module_logger.propagate = False

    # 抑制werkzeug的访问日志（使用我们自己的）
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    logging.info("日志系统配置完成：")
    logging.info(f"   - 应用日志: {os.path.relpath(os.path.join(LOG_FOLDER, 'application.log'))}")
    logging.info(f"   - 访问日志: {os.path.relpath(os.path.join(LOG_FOLDER, 'access.log'))}")
    logging.info(f"   - 错误日志: {os.path.relpath(os.path.join(LOG_FOLDER, 'error.log'))}")


# ======================
# 请求钩子（记录详细访问日志）
# ======================
def setup_request_hooks(app):
    @app.before_request
    def before_request():
        """为每个请求分配唯一ID并记录开始时间"""
        request.start_time = time.time()
        request.id = uuid.uuid4().hex[:8]
        g.log_context = {
            'request_id': request.id,
            'method': request.method,  # 直接获取实时方法
            'path': request.path,  # 直接获取实时路径
            'user_agent': request.headers.get('User-Agent', '-'),
            'status_code': 200,
            'response_time': 0,
            'client_ip': request.remote_addr or '-',
            'user': session.get('username', 'GUEST'),  # 默认用户标识
            'scheme': request.environ.get('wsgi.url_scheme', 'http'),
        }

    @app.after_request
    def after_request(response):
        """增强的请求日志记录"""
        response_time = (time.time() - request.start_time) * 1000
        log_context = getattr(g, 'log_context', {})

        # 动态获取最终请求属性
        final_method = request.environ.get('REQUEST_METHOD', request.method)
        final_path = request.environ.get('PATH_INFO', request.path)
        final_scheme = request.environ.get('wsgi.url_scheme', 'http')

        log_context.update({
            'status_code': response.status_code,
            'response_time': f"{response_time:.2f}",
            'method': final_method,
            'path': final_path,
            'scheme': final_scheme
        })

        # 记录访问日志（使用独立日志器）
        access_logger = logging.getLogger('access')
        access_logger.info(
            f"{response.status_code} {final_method} {final_path}",
            extra=log_context
        )

        return response


# ======================
# 更新日志适配器
# ======================
class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        request_context = {}

        if has_request_context():
            request_context = {
                'method': request.method,
                'path': request.path,
                'scheme': request.scheme,
                'client_ip': request.remote_addr or '-',
                'user_agent': request.headers.get('User-Agent', '-'),
                'request_id': getattr(request, 'id', 'SYSTEM'),
                'user': session.get('username', 'GUEST')
            }
        else:
            request_context = {
                'method': 'SYSTEM',
                'path': 'N/A',
                'scheme': 'internal',
                'client_ip': '-',
                'user_agent': '-',
                'request_id': 'SYSTEM',
                'user': 'SYSTEM'
            }

        merged_context = {
            'status_code': 0,
            'response_time': 0,
            **request_context,
            **extra
        }

        # 增强的response_time处理
        try:
            rt = merged_context.get('response_time', 0)
            if callable(rt):
                rt = rt()
            merged_context['response_time'] = float(rt)
        except (TypeError, ValueError):
            merged_context['response_time'] = 0.0

        # 确保status_code为整型
        try:
            merged_context['status_code'] = int(merged_context.get('status_code', 0))
        except (TypeError, ValueError):
            merged_context['status_code'] = 0

        kwargs['extra'] = merged_context
        return msg, kwargs


# ======================
# 核心组件初始化
# ======================
def initialize_core_components():
    """初始化核心组件"""
    logging.info("正在初始化核心组件：")

    # 认证管理器
    global auth
    auth = AuthManager()
    logging.info(f"   - 认证管理器初始化完成")

    # 文件管理器
    global file_manager
    file_manager = FileManager(UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH)
    logging.info(
        f"   - 文件管理器初始化完成 - 间隔: {CLEANUP_INTERVAL / 60 / 60 / 24} 天，保留时间: {FILE_RETENTION / 86400} 天，目录: {os.path.relpath(UPLOAD_FOLDER)}")

    # 清理调度器
    global scheduler
    scheduler = CleanupScheduler(CLEANUP_INTERVAL, FILE_RETENTION, UPLOAD_FOLDER)
    # // 相对路径
    logging.info(f"   - 清理调度器初始化完成 - 清理间隔: {CLEANUP_INTERVAL / 60 / 60 / 24} 天")

    # 启动调度器
    scheduler.start()
    logging.info("   - 清理调度器已启动")
    atexit.register(scheduler.stop)


# ======================
# 路由配置
# ======================
def setup_routes(app):
    """配置所有应用路由"""

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """登录路由"""
        start_time = time.time()
        log_ctx = {
            'status_code': 302,
            'response_time': 0,
            'method': request.method,
            'path': request.path,
            'client_ip': request.remote_addr or '-'
        }

        if request.method == 'GET':
            logger.info("访问登录页面", extra=log_ctx)
            return render_template('login.html')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        try:
            valid, message = auth.validate_credentials(username, password)
            if valid:
                session['username'] = username.upper()
                log_ctx['status_code'] = 200
                log_ctx['response_time'] = int((time.time() - start_time) * 1000)
                logger.info(f"用户 {username} 登录成功", extra=log_ctx)
                return redirect(url_for('index'))

            log_ctx['status_code'] = 401
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.warning(f"用户 {username} 登录失败: {message}", extra=log_ctx)
            return render_template('login.html', error=message)
        except Exception as e:
            log_ctx['status_code'] = 500
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.error(f"登录异常: {str(e)}", extra=log_ctx)
            return render_template('login.html', error="系统错误")

    @app.route('/register', methods=['POST'])
    def register():
        try:
            email = request.form.get('email').lower().strip()
            # 增加用户存在性检查
            existing_user = auth._load_user(email)
            if existing_user:
                return render_template('login.html', error="该邮箱已注册")

            code = request.form.get('code').strip()
            password = request.form.get('password').strip()
            confirm_password = request.form.get('confirmPassword').strip()

            if password != confirm_password:
                return render_template('login.html', error="两次密码输入不一致")

            if not auth.verify_code(email, code):
                return render_template('login.html', error="验证码错误或已过期")

            hashed_password = auth.hash_password(password)

            query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"
            args = (email, hashed_password, email)
            try:
                Database.execute_query(query, args)
                logger.info(f"新用户注册成功: {email}")
                return redirect(url_for('login'))
            except Exception as db_error:
                # 捕获数据库唯一性约束错误
                if "Duplicate entry" in str(db_error):
                    return render_template('login.html', error="该邮箱已注册")
                logger.error(f"数据库插入用户失败: {str(db_error)}", exc_info=True)
                return render_template('login.html', error="注册失败，请稍后重试")
        except Exception as e:
            logger.error(f"注册失败: {str(e)}")
            return render_template('login.html', error="注册失败")

    @app.route('/logout')
    def logout():
        """注销路由"""
        username = session.pop('username', None)
        if username:
            logger.info(f"用户 {username} 注销登录", extra={
                'method': request.method,
                'path': request.path,
                'status_code': 200,
                'client_ip': request.remote_addr or '-'
            })
        return redirect(url_for('login'))

    @app.route('/send_code', methods=['POST'])
    def send_verification_code():
        try:
            email = request.form.get('email').lower().strip()
            code = auth.generate_verification_code(email)
            return jsonify(success=True, message="验证码已发送")
        except AuthenticationError as e:
            logger.error(f"验证码发送失败: {str(e)}")
            return jsonify(success=False, message=str(e)), 400
        except Exception as e:
            logger.error(f"邮件发送异常: {str(e)}")
            return jsonify(success=True, message="验证码已发送，请查收")

    @app.route('/', methods=['GET', 'POST'])
    def index():
        """主页路由"""
        start_time = time.time()
        log_ctx = {
            'status_code': 200,
            'response_time': 0,
            'method': request.method,
            'path': request.path,
            'client_ip': request.remote_addr or '-'
        }

        if 'username' not in session:
            log_ctx['status_code'] = 403
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.warning("未登录用户尝试访问主页", extra=log_ctx)
            return redirect(url_for('login'))

        page = request.args.get('page', 1, type=int)
        files = []
        pagination = {'current': 1, 'total': 1, 'range': []}

        if request.method == 'POST':
            if 'file' not in request.files:
                flash('请选择文件', 'error')
                logger.warning("用户提交表单但未选择文件", extra=log_ctx)
            else:
                uploaded_files = request.files.getlist('file')
                success_count = 0
                error_messages = []

                try:
                    # 新增文件夹容量验证（后端校验）
                    file_manager.validate_folder_size(uploaded_files)
                except ValueError as e:
                    flash(str(e), 'error')
                    logger.error(f"文件夹容量验证失败: {str(e)}", extra=log_ctx)
                    return redirect(url_for('index'))

                for file in uploaded_files:
                    if file.filename == '':
                        continue
                    try:
                        # 单个文件大小验证（双重校验）
                        if file.content_length > file_manager.max_size:
                            raise ValueError("单个文件超过10GB限制")

                        filename = file_manager.save_file(file, session['username'])
                        success_count += 1
                        logger.info(f"用户 {session['username']} 上传文件 {filename} 成功", extra=log_ctx)
                    except ValueError as ve:
                        error_messages.append(f"{file.filename}: {str(ve)}")
                        logger.error(f"文件大小验证失败: {file.filename} - {str(ve)}", extra=log_ctx)
                    except Exception as e:
                        error_messages.append(f"{file.filename}: 上传失败")
                        logger.error(f"用户 {session['username']} 上传文件 {file.filename} 失败: {str(e)}",
                                     extra=log_ctx, exc_info=True)

                if success_count > 0:
                    flash(f'成功上传 {success_count} 个文件', 'success')
                if error_messages:
                    flash('部分文件上传失败: ' + '; '.join(error_messages), 'error')

                return redirect(url_for('index'))

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
            log_ctx['status_code'] = 500
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.error(f"获取文件列表时系统错误: {str(e)}", extra=log_ctx, exc_info=True)
            flash(error, 'error')

        log_ctx['response_time'] = int((time.time() - start_time) * 1000)
        logger.info(f"用户 {session['username']} 访问主页", extra=log_ctx)

        return render_template('index.html', files=files, pagination=pagination)

    @app.route('/download/<path:filename>')
    def download(filename):
        """文件下载路由"""
        start_time = time.time()
        log_ctx = {
            'status_code': 200,
            'response_time': 0,
            'method': request.method,
            'path': request.path,
            'client_ip': request.remote_addr or '-'
        }

        if 'username' not in session:
            log_ctx['status_code'] = 403
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.warning(f"未授权用户尝试下载文件 {filename}", extra=log_ctx)
            abort(403)

        try:
            logger.info(f"用户 {session['username']} 尝试下载文件 {filename}", extra=log_ctx)
            response = send_from_directory(
                directory=str(UPLOAD_FOLDER),
                path=filename,
                as_attachment=True
            )
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.info(f"用户 {session['username']} 下载文件 {filename} 成功", extra=log_ctx)
            return response
        except FileNotFoundError:
            log_ctx['status_code'] = 404
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.warning(f"文件 {filename} 不存在", extra=log_ctx)
            abort(404)
        except Exception as e:
            log_ctx['status_code'] = 500
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.error(f"下载文件 {filename} 时系统错误: {str(e)}", extra=log_ctx)
            abort(500)

    @app.route('/privacy')
    def privacy():
        """隐私政策页面"""
        logger.info("访问隐私政策页面", extra={
            'method': request.method,
            'path': request.path,
            'status_code': 200,
            'client_ip': request.remote_addr or '-'
        })
        return render_template('privacy.html')

    @app.route('/support')
    def support():
        """支持页面"""
        logger.info("访问支持页面", extra={
            'method': request.method,
            'path': request.path,
            'status_code': 200,
            'client_ip': request.remote_addr or '-'
        })
        return render_template('support.html')

    @app.route('/full_analysis.html')
    def full_analysis():
        start_time = time.time()
        log_ctx = {
            'status_code': 200,
            'response_time': 0,
            'method': request.method,
            'path': request.path,
            'client_ip': request.remote_addr or '-'
        }
        logger.info("开始处理完整分析报告页面请求", extra=log_ctx)
        try:
            # 直接返回静态文件，不通过模板引擎
            return send_from_directory(
                directory=str(PathManager.get_web_folder()),
                path='full_analysis.html'
            )
        except Exception as e:
            log_ctx['status_code'] = 500
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.error(f"加载完整分析报告失败: {str(e)}", extra=log_ctx)
            abort(500)
        finally:
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.info("完整分析报告页面请求处理完成", extra=log_ctx)

    @app.route('/logs')
    def log_analysis():
        """优化后的日志分析路由"""
        start_time = time.time()
        log_ctx = {
            'status_code': 200,
            'client_ip': request.remote_addr or '-',
            'response_time': lambda: int((time.time() - start_time) * 1000)
        }
        logger.info("开始处理日志分析请求", extra=log_ctx)
        if 'username' not in session:
            log_ctx['status_code'] = 302
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.info("未登录用户重定向到登录页面", extra=log_ctx)
            return redirect(url_for('login'))

        try:
            # 获取项目根目录路径
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent

            logs_dir = base_dir / 'logs'
            web_dir = base_dir / 'web'
            logger.info(f"项目根目录: {base_dir}", extra=log_ctx)
            logger.info(f"日志目录: {logs_dir}", extra=log_ctx)
            logger.info(f"Web目录: {web_dir}", extra=log_ctx)

            # 确保web目录存在
            web_dir.mkdir(exist_ok=True)
            logger.info("Web目录已确保存在", extra=log_ctx)

            # 初始化分析器
            analyzer = AdvancedLogAnalyzer()
            logger.info("日志分析器已初始化", extra=log_ctx)

            # 定义日志文件路径
            log_files = {
                'access.log': logs_dir / 'access.log',
                'application.log': logs_dir / 'application.log',
                'error.log': logs_dir / 'error.log'
            }
            logger.info("日志文件路径已定义", extra=log_ctx)

            # 解析日志文件
            for log_type, file_path in log_files.items():
                if file_path.exists():
                    logger.info(f"开始解析 {log_type} 文件", extra=log_ctx)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if log_type == 'access.log':
                                analyzer.parse_access_log(line)
                            elif log_type == 'application.log':
                                analyzer.parse_application_log(line)
                            elif log_type == 'error.log':
                                analyzer.parse_error_log(line)
                    logger.info(f"{log_type} 文件解析完成", extra=log_ctx)
                else:
                    logger.warning(f"{log_type} 文件不存在", extra=log_ctx)

            # 分析并生成报告
            logger.info("开始分析日志并生成报告", extra=log_ctx)
            analyzer.analyze_logs()
            analyzer.generate_visualizations()
            analyzer.generate_report()
            logger.info("日志分析和报告生成完成", extra=log_ctx)

            # 返回报告文件
            response = send_from_directory(
                directory=str(web_dir),
                path='report.html',
                as_attachment=False
            )
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.info("日志分析报告已返回", extra=log_ctx)
            return response

        except Exception as e:
            log_ctx['status_code'] = 500
            log_ctx['response_time'] = int((time.time() - start_time) * 1000)
            logger.error(f"日志分析失败: {str(e)}", extra=log_ctx)
            abort(500)

    # 错误处理路由
    @app.errorhandler(404)
    def page_not_found(error):
        logger.error(f"404 Error: {error}", extra={
            'method': request.method,
            'path': request.path,
            'status_code': 404,
            'client_ip': request.remote_addr or '-'
        })
        return render_template('error.html', code=404, message='The requested page does not exist'), 404

    @app.errorhandler(403)
    def forbidden(error):
        logger.error(f"403 Error: {error}", extra={
            'method': request.method,
            'path': request.path,
            'status_code': 403,
            'client_ip': request.remote_addr or '-'
        })
        return render_template('error.html', code=403, message='Access to this page is prohibited'), 403

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 Error: {error}", extra={
            'method': request.method,
            'path': request.path,
            'status_code': 500,
            'client_ip': request.remote_addr or '-'
        })
        return render_template('error.html', code=500, message='Internal Server Error'), 500

    logging.info("应用路由配置完成")


def find_available_port(host, base_port, max_attempts):
    """
    可用端口查找函数（修复后版本）
    参数：
    - host: 主机名或IP地址
    - base_port: 起始端口号
    - max_attempts: 最大尝试次数
    返回：
    - 找到的可用端口号
    异常：
    - 如果在指定范围内找不到可用端口，抛出异常
    """
    for port in range(base_port, base_port + max_attempts):
        try:
            # 创建临时 socket 检测端口是否可用
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
                logging.info(f"   - 找到可用端口 {port}")
                return port
        except socket.error as e:
            # 兼容Linux和Windows错误码
            if e.errno in (98, 10048):  # 端口已占用
                logging.warning(f"   - 端口 {port} 已被占用，尝试下一个端口")
                continue
            else:
                raise RuntimeError(f"端口检测错误: {str(e)}")
    raise RuntimeError(f"无法找到可用端口（尝试范围：{base_port}-{base_port + max_attempts - 1}）")


def configure_ssl_context():
    """
    SSL上下文配置函数
    返回：
    - SSL上下文对象或None
    - 协议字符串（http或https）
    """
    cert_folder = PathManager.get_cert_folder()
    cert_file = PathManager.get_cert_file()
    key_file = PathManager.get_cert_key()

    logging.info(f"   - 证书检测:")
    logging.info(f"      - 证书目录: {os.path.relpath(str(cert_folder))}")
    logging.info(f"      - 证书文件: {os.path.relpath(str(cert_file))}")
    logging.info(f"      - 密钥文件: {os.path.relpath(str(key_file))}")

    ssl_context = None
    protocol = 'http'
    if cert_file.exists() and key_file.exists():
        ssl_context = (str(cert_file), str(key_file))
        protocol = 'https'

    if protocol == 'http':
        logging.warning("      - 未检测到SSL证书文件，将以HTTP模式运行")
    return ssl_context, protocol


# ======================
# 主程序入口
# ======================
if __name__ == '__main__':
    setup_logging()
    initialize_system()
    app = initialize_flask_app()
    setup_request_hooks(app)
    initialize_core_components()
    setup_routes(app)

    logging.info("正在启动应用程序：")

    host = '0.0.0.0'
    base_port = 5000
    max_attempts = 100

    try:
        # 自动查找可用端口
        port = find_available_port(host, base_port, max_attempts)
        if port is None:
            logging.error("启动失败：无法找到可用端口")
            sys.exit(1)

        # 配置SSL上下文
        ssl_context, protocol = configure_ssl_context()

        # 显示启动信息
        try:
            hostname = socket.gethostname()
            logging.info(f"   - 应用程序已在：{protocol}://{host}:{port} 启动，访问地址如下：")
            logging.info(f"      - 本地：{protocol}://127.0.0.1:{port}")
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if ip != '127.0.0.1':
                    logging.info(f"      - 网络：{protocol}://{ip}:{port}")
        except Exception as e:
            logging.error(f"获取网络地址失败: {str(e)}")

        logging.info("   - 按 Ctrl+C 停止服务")

        # 配置werkzeug日志
        werkzeug_log = logging.getLogger('werkzeug')
        werkzeug_log.setLevel(logging.WARNING)
        werkzeug_log.addHandler(logging.StreamHandler())

        # 创建应用日志器
        logger = RequestLoggerAdapter(logging.getLogger('app'), {})

        # 启动应用
        app.run(
            host=host,
            port=port,
            use_reloader=False,
            ssl_context=ssl_context
        )
    except RuntimeError as e:
        logging.error(f"端口查找失败: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"应用启动失败: {str(e)}")
        sys.exit(1)
