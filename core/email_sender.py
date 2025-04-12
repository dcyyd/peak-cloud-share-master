"""
@file email_sender.py
@description 峰云共享系统邮件发送模块，提供邮件发送功能
@author D.C.Y <https://dcyyd.github.io>
@version 1.2.1
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

# 标准库导入
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

# 本地模块导入
from config.constants import EMAIL_CONFIG

logger = logging.getLogger(__name__)


class EmailSender:
    @staticmethod
    def send_verification_code(email: str, code: str):
        """
        发送验证码邮件（专业商业化实现）

        参数:
            email (str): 收件人邮箱地址
            code (str): 验证码（6位数字或字母组合，需配合后端生成安全校验码）

        功能:
            - 构建符合品牌视觉规范的HTML邮件（背景色#111827）
            - 采用安全的SSL/TLS加密连接传输邮件
            - 实施密码强度校验增强账户安全
            - 详细记录邮件发送日志便于审计追踪

        商业价值:
            - 通过专业化的邮件模板设计提升品牌形象
            - 严格的邮件发送流程确保用户账户安全
            - 完善的日志记录支持运营分析和问题排查
            - 可扩展的邮件服务架构支持未来业务增长
        """
        # 构建符合品牌视觉规范的HTML邮件内容
        # 采用现代网页设计标准，确保跨设备兼容性
        # 使用品牌主色调和渐变效果提升视觉吸引力
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <!-- 邮件头部信息，包含SEO优化和响应式设计 -->
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>【Peak Cloud Share】注册验证码</title>
            <!-- 样式表采用模块化设计，便于维护和扩展 -->
            <style>
                /* 基础样式，确保跨平台一致性 */
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", 
                             Arial, "Noto Sans", "PingFang SC", "Hiragino Sans GB", sans-serif;
                    margin: 0; padding: 20px; background-color: #111827; color: #ffffff;
                    -webkit-font-smoothing: antialiased;
                }}
                /* 容器布局，采用最大宽度限制提升阅读体验 */
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                }}
                /* 头部设计，使用品牌渐变背景提升视觉层次 */
                .header {{ 
                    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                    color: white;
                    padding: 28px;
                    border-radius: 12px 12px 0 0;
                    text-align: center;
                }}
                /* 内容区域，采用白色背景确保可读性 */
                .content {{
                    background-color: #ffffff;
                    color: #1f2937;
                    padding: 32px;
                    border-radius: 0 0 12px 12px;
                    line-height: 1.75;
                }}
                /* 验证码容器，突出显示关键信息 */
                .code-container {{
                    background: #f3f4f6;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 24px 0;
                    text-align: center;
                }}
                /* 验证码样式，采用大字号和品牌色增强辨识度 */
                .verification-code {{
                    color: #2563eb;
                    font-size: 32px;
                    font-weight: 700;
                    letter-spacing: 2px;
                    margin: 12px 0;
                }}
                /* 操作说明，采用灰色字体降低视觉干扰 */
                .instructions {{
                    color: #6b7280;
                    font-size: 14px;
                    margin: 16px 0;
                }}
                /* 安全提示，采用醒目的红色背景强调重要性 */
                .security-note {{
                    background: #fef2f2;
                    color: #dc2626;
                    padding: 12px;
                    border-radius: 6px;
                    font-size: 13px;
                    margin-top: 24px;
                }}
                /* 页脚信息，采用小字号和浅色字体降低视觉权重 */
                .footer {{
                    color: #9ca3af;
                    font-size: 12px;
                    text-align: center;
                    margin-top: 32px;
                    padding-top: 16px;
                    border-top: 1px solid #e5e7eb;
                }}
            </style>
        </head>
        <!-- 邮件正文，采用结构化布局提升可读性 -->
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin:0;font-weight:600;">PEAK CLOUD SHARE</h2>
                    <p style="margin:8px 0 0;font-size:18px;">账户激活验证</p>
                </div>
                
                <div class="content">
                    <p>尊敬的 {email}：</p>
                    
                    <p>感谢您注册 Peak Cloud Share，请使用以下验证码完成账户验证：</p>
                    
                    <div class="code-container">
                        <div class="instructions">验证码（有效期5分钟）</div>
                        <div class="verification-code">{code}</div>
                    </div>

                    <div class="security-note">
                        ⚠️ 安全提示：请勿向任何人泄露此验证码，包括自称平台客服的人员
                    </div>

                    <div class="footer">
                        <p>此邮件由系统自动发送，请勿直接回复</p>
                        <p style="margin-top:8px;">&copy; {datetime.now().year}-{datetime.now().year + 1} Peak Cloud Share. All rights reserved.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # 构建MIME邮件对象，指定HTML格式和UTF-8编码
        msg = MIMEText(html_content, 'html', 'utf-8')
        msg['Subject'] = '【Peak Cloud Share】注册验证码'
        msg['From'] = f'Peak Cloud Mail Server 001 <{EMAIL_CONFIG["sender"]}>'  # 发件人格式优化
        msg['To'] = email

        # 手动构造中文日期字符串，避免依赖系统locale
        now = datetime.now()
        msg['Date'] = f"{now.year}年{now.month}月{now.day}日 {now.hour}:{now.minute}"

        try:
            # 记录邮件发送日志，支持运营监控
            logger.info(f"尝试向 {email} 发送验证码邮件")
            with smtplib.SMTP_SSL(
                    EMAIL_CONFIG['smtp_server'],
                    EMAIL_CONFIG['smtp_port'],
                    timeout=10  # 合理设置超时时间
            ) as server:
                # 安全增强：密码强度校验（可扩展更复杂规则）
                if len(EMAIL_CONFIG['password']) < 12:
                    raise ValueError("邮件服务密码强度不足，至少需要12位字符")
                # 建立安全连接并发送邮件
                server.login(EMAIL_CONFIG['username'], EMAIL_CONFIG['password'])
                logger.info(f"成功登录到 SMTP 服务器: {EMAIL_CONFIG['smtp_server']}")
                server.sendmail(EMAIL_CONFIG['sender'], [email], msg.as_string())
            # 记录成功日志，支持运营分析
            logger.info(f"验证码邮件已成功发送至 {email}")
        except smtplib.SMTPConnectError as e:
            logger.error(f"无法连接到 SMTP 服务器 - 收件人: {email} | 错误详情: {str(e)}", exc_info=True)
            raise RuntimeError(f"无法连接到 SMTP 服务器: {str(e)}") from e
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP 认证失败 - 收件人: {email} | 错误详情: {str(e)}", exc_info=True)
            raise RuntimeError(f"SMTP 认证失败: {str(e)}") from e
        except smtplib.SMTPResponseException as e:
            logger.warning(
                f"SMTP服务器返回非标准响应 - 收件人: {email} | 错误代码: {e.smtp_code} | 错误消息: {e.smtp_error} | "
                f"注意：邮件可能已成功发送，但服务器响应异常",
                exc_info=True
            )
            return True
        except (smtplib.SMTPException, TimeoutError, ValueError) as e:
            # 记录错误日志，支持问题排查
            logger.error(f"邮件发送失败 - 收件人: {email} | 错误详情: {str(e)}", exc_info=True)
            raise RuntimeError(f"邮件发送失败: {str(e)}") from e
