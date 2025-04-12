"""
@file log_analysis.py
@description 峰云共享系统高级日志分析模块，通过对多种类型日志的解析和分析，生成可视化图表和分析报告，为系统运维和决策提供数据支持。
@functionality
    - 解析访问日志、应用日志和错误日志，提取关键信息。
    - 对日志数据进行统计分析，包括时间分布、请求类型、状态码等。
    - 生成可视化图表，直观展示日志分析结果。
    - 生成包含统计数据和可视化图表的分析报告。
@author D.C.Y <https://dcyyd.github.io>
@version 2.0.0
@license MIT
@copyright © 2025 D.C.Y. All rights reserved.
"""

import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots


class AdvancedLogAnalyzer:
    """
    高级日志分析器类，用于对系统日志进行全面的解析、分析和可视化展示。
    在商业环境中，该类可帮助运维团队快速定位系统问题，优化系统性能，同时为业务决策提供数据支持。
    """

    def __init__(self):
        """
        初始化日志分析器，创建日志数据存储和分析结果存储的容器。
        此初始化方法为后续的日志解析和分析工作做好准备，确保数据有统一的存储结构。
        """
        # 初始化日志数据存储，按日志类型分类存储解析后的日志条目
        self.log_data = {
            'access': [],
            'application': [],
            'error': []
        }

        # 初始化分析结果存储，存储各种统计分析结果
        self.analysis_result = {
            'time_distribution': defaultdict(int),
            'request_types': defaultdict(int),
            'status_codes': defaultdict(int),
            'ip_activities': defaultdict(int),
            'log_levels': defaultdict(int),
            'handlers': defaultdict(int),
            'user_actions': defaultdict(lambda: defaultdict(int)),
            'protocols': defaultdict(int),
            'security_events': [],
            'file_types': defaultdict(int),
            'users': defaultdict(int),
            'download_stats': defaultdict(int),
            'response_times': [],
            'interface_response_times': defaultdict(list)
        }

    def parse_access_log(self, line):
        """
        解析访问日志行，提取关键信息并存储到日志数据和分析结果中。
        该方法通过正则表达式匹配访问日志格式，为后续的访问日志分析提供数据基础。

        参数:
            line (str): 单行访问日志内容。
        """
        # 定义访问日志的正则表达式模式
        pattern = r'\[(.*?)\] \[(.*?)\] \[(.*?)\] "(.*?)" (\d+) (.*?)ms "(.*?)"'
        # 尝试匹配日志行
        match = re.match(pattern, line)  # 传统赋值语句
        if match:  # 传统条件判断
            # 提取匹配到的信息并构建日志条目
            entry = {
                'timestamp': datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S'),
                'ip': match.group(2),
                'request_id': match.group(3),
                'method': match.group(4).split()[0],
                'path': match.group(4).split()[1] if len(match.group(4).split()) > 1 else '',
                'status_code': int(match.group(5)),
                'response_time': float(match.group(6)),
                'user_agent': match.group(7),
                'protocol': 'HTTP/1.1',
                'log_type': 'access'
            }
            # 将日志条目添加到访问日志数据中
            self.log_data['access'].append(entry)
            # 将响应时间添加到分析结果的响应时间列表中
            self.analysis_result['response_times'].append(entry['response_time'])

            # 按接口路径统计响应时间
            path = entry['path'].split('?')[0] if '?' in entry['path'] else entry['path']
            self.analysis_result['interface_response_times'][path].append(entry['response_time'])

    def parse_application_log(self, line):
        """
        解析应用日志行，提取关键信息并存储到日志数据和分析结果中。
        该方法通过正则表达式匹配应用日志格式，可用于分析应用程序的运行状态和用户行为。

        参数:
            line (str): 单行应用日志内容。
        """
        # 定义应用日志的正则表达式模式
        pattern = r'\[(.*?)\] \[(\w+)\s*\] \[(\w+)\s*\] \[(.*?)\] \[(.*?)\] (.*?) \[(.*?)\]'
        # 尝试匹配日志行
        match = re.match(pattern, line)  # 传统赋值语句
        if match:  # 传统条件判断
            # 提取匹配到的信息并构建日志条目
            entry = {
                'timestamp': datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S'),
                'log_level': match.group(2).strip(),
                'module': match.group(3).strip(),
                'ip': match.group(4),
                'request_id': match.group(5),
                'message': match.group(6),
                'context': match.group(7),
                'log_type': 'application'
            }
            # 将日志条目添加到应用日志数据中
            self.log_data['application'].append(entry)

            # 提取用户信息
            if '用户' in match.group(6):
                user = re.search(r'用户 (.*?) ', match.group(6))
                if user:
                    # 统计用户请求次数
                    self.analysis_result['users'][user.group(1)] += 1

    def parse_error_log(self, line):
        """
        解析错误日志行，提取关键信息并存储到日志数据中。
        该方法通过正则表达式匹配错误日志格式，有助于快速定位系统中的错误和异常情况。

        参数:
            line (str): 单行错误日志内容。
        """
        # 定义错误日志的正则表达式模式
        pattern = r'\[(.*?)\] \[(\w+)\s*\] \[(\w+)\s*\] \[(.*?)\] \[(.*?)\] (.*?) \[(.*?)\]'
        # 尝试匹配日志行
        match = re.match(pattern, line)  # 传统赋值语句
        if match:  # 传统条件判断
            # 提取匹配到的信息并构建日志条目
            entry = {
                'timestamp': datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S'),
                'log_level': match.group(2).strip(),
                'module': match.group(3).strip(),
                'ip': match.group(4),
                'request_id': match.group(5),
                'message': match.group(6),
                'context': match.group(7),
                'log_type': 'error'
            }
            # 将日志条目添加到错误日志数据中
            self.log_data['error'].append(entry)

    def analyze_logs(self):
        """
        分析日志数据，对解析后的日志条目进行统计和汇总。
        该方法对不同类型的日志进行综合分析，生成各种统计结果，为后续的可视化和报告生成提供数据支持。
        """
        for log_type in ['access', 'application', 'error']:
            for entry in self.log_data[log_type]:
                hour = entry['timestamp'].hour
                self.analysis_result['time_distribution'][hour] += 1

                if log_type == 'access':
                    self.analysis_result['request_types'][entry['method']] += 1
                    self.analysis_result['status_codes'][entry['status_code']] += 1
                    self.analysis_result['ip_activities'][entry['ip']] += 1
                    self.analysis_result['protocols'][entry['protocol']] += 1

                    # 提取用户信息
                    if 'user=' in entry.get('context', ''):
                        user_match = re.search(r'user=([^\s]+)', entry['context'])
                        if user_match:
                            user = user_match.group(1)
                            self.analysis_result['user_actions'][user]['requests'] += 1

                    # 提取下载信息
                    if 'download' in entry['path']:
                        filename = entry['path'].split('/')[-1]
                        file_ext = filename.split('.')[-1] if '.' in filename else 'unknown'
                        self.analysis_result['file_types'][file_ext] += 1
                        self.analysis_result['download_stats'][filename] += 1

                self.analysis_result['log_levels'][entry.get('log_level', '')] += 1

                # 提取接口路径
                if 'path=' in entry.get('context', ''):
                    path_match = re.search(r'path=([^\s]+)', entry['context'])
                    if path_match:
                        path = path_match.group(1)
                        self.analysis_result['handlers'][path] += 1

                # 提取安全事件
                if entry.get('log_level') == 'ERROR' and '高危文件类型' in entry.get('message', ''):
                    message = entry.get('message')
                    if message:
                        filename_match = re.search(r'上传文件 (.*?) 失败', message)
                        if filename_match:
                            filename = filename_match.group(1)
                            file_ext = filename.split('.')[-1] if '.' in filename else 'unknown'
                            user_match = re.search(r'用户 (.*?) ', message)
                            if user_match:
                                user = user_match.group(1)
                                self.analysis_result['security_events'].append({
                                    'timestamp': entry['timestamp'],
                                    'user': user,
                                    'filename': filename,
                                    'type': '高危文件拦截',
                                    'extension': file_ext
                                })

    def generate_visualizations(self):
        """
        生成可视化图表，将分析结果以图表形式展示。
        该方法使用 Plotly 库生成多个子图，直观展示日志分析的各项统计结果，帮助用户快速理解数据。
        """
        # 检查是否有日志数据
        if not any(self.log_data.values()):
            print("警告: 没有解析到任何日志数据，无法生成可视化图表。")
            return

        # 创建子图网格
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                "每小时请求量热力图", "状态码分布", "请求方法分布",
                "日志级别分布", "TOP 10活跃用户", "协议类型分布",
                "安全事件统计", "文件类型分布", "下载统计"
            ),
            specs=[
                [{'type': 'heatmap'}, {'type': 'pie'}, {'type': 'bar'}],
                [{'type': 'bar'}, {'type': 'bar'}, {'type': 'pie'}],
                [{'type': 'bar'}, {'type': 'pie'}, {'type': 'bar'}]
            ]
        )

        # 每小时请求量热力图
        time_data = pd.DataFrame.from_dict(self.analysis_result['time_distribution'], orient='index').reset_index()
        time_data.columns = ['Hour', 'Count']
        fig.add_trace(go.Heatmap(
            x=time_data['Hour'],
            y=['Count'],
            z=[time_data['Count']],
            colorscale='Viridis',
            showscale=False
        ), row=1, col=1)

        # 状态码分布
        status_codes = self.analysis_result['status_codes']
        fig.add_trace(go.Pie(
            labels=list(status_codes.keys()),
            values=list(status_codes.values()),
            marker=dict(colors=px.colors.sequential.Blues)
        ), row=1, col=2)

        # 请求方法分布
        methods = self.analysis_result['request_types']
        fig.add_trace(
            go.Bar(
                x=list(methods.keys()),
                y=list(methods.values()),
                marker=dict(color=px.colors.qualitative.Plotly)
            ),
            row=1, col=3
        )

        # 日志级别分布
        levels = self.analysis_result['log_levels']
        fig.add_trace(
            go.Bar(
                x=list(levels.keys()),
                y=list(levels.values()),
                marker=dict(color=px.colors.qualitative.Pastel)
            ),
            row=2, col=1
        )

        # TOP 10活跃用户
        user_data = sorted(
            [(user, count) for user, count in self.analysis_result['users'].items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        fig.add_trace(go.Bar(
            x=[u[0] for u in user_data],
            y=[u[1] for u in user_data],
            marker=dict(color=px.colors.sequential.Tealgrn)
        ), row=2, col=2)

        # 协议类型分布
        protocols = self.analysis_result['protocols']
        fig.add_trace(go.Pie(
            labels=list(protocols.keys()),
            values=list(protocols.values()),
            marker=dict(colors=px.colors.sequential.Reds)
        ), row=2, col=3)

        # 高危文件拦截统计
        security_events = defaultdict(int)
        for event in self.analysis_result['security_events']:
            security_events[event['extension']] += 1
        fig.add_trace(go.Bar(
            x=list(security_events.keys()),
            y=list(security_events.values()),
            marker=dict(color=px.colors.sequential.Purples)
        ), row=3, col=1)

        # 文件类型分布
        file_types = self.analysis_result['file_types']
        fig.add_trace(go.Pie(
            labels=list(file_types.keys()),
            values=list(file_types.values()),
            marker=dict(colors=px.colors.qualitative.Alphabet)
        ), row=3, col=2)

        # 下载统计 (前5文件)
        download_stats = dict(sorted(self.analysis_result['download_stats'].items(), key=lambda x: x[1], reverse=True))
        top_downloads = dict(list(download_stats.items())[:5])
        fig.add_trace(go.Bar(
            x=list(top_downloads.keys()),
            y=list(top_downloads.values()),
            marker=dict(color=px.colors.sequential.Greens)
        ), row=3, col=3)

        # 更新布局
        fig.update_layout(
            height=1200,
            width=1200,
            title_text="综合日志分析可视化",
            template="plotly_dark",
            plot_bgcolor="#111827",
            paper_bgcolor="#111827",
            font=dict(color="white", family="Arial, sans-serif"),
            margin=dict(l=40, r=40, t=80, b=40),
            showlegend=False
        )

        # 保存图表 判断是否为打包环境
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent

        web_dir = base_dir / 'web'
        web_dir.mkdir(exist_ok=True)  # 确保目录存在
        output_path = web_dir / 'full_analysis.html'

        pio.write_html(fig, file=output_path, auto_open=False)

    def generate_report(self):
        """
        生成分析报告，将分析结果以 HTML 格式输出。
        该方法生成包含统计数据表格和可视化图表链接的 HTML 报告，为运维人员和决策者提供全面的日志分析结果。
        """
        # 计算总请求量
        total_requests = sum(self.analysis_result['time_distribution'].values())
        if self.log_data['access']:
            # 计算平均响应时间
            average_response_time = f"{sum(entry['response_time'] for entry in self.log_data['access']) / len(self.log_data['access']):.2f}ms"
        else:
            average_response_time = "0.00ms"

        # 安全事件表格
        security_table = "<table><tr><th>时间</th><th>用户</th><th>事件类型</th><th>文件名称</th></tr>"
        for event in self.analysis_result['security_events'][:5]:
            filename = event['filename'][:20] + "..." if len(event['filename']) > 20 else event['filename']
            security_table += f"<tr><td>{event['timestamp'].strftime('%Y-%m-%d %H:%M')}</td><td>{event['user']}</td><td>{event['type']}</td><td>{filename}</td></tr>"
        security_table += "</table>"

        # 热门接口表格
        handler_table = "<table><tr><th>接口路径</th><th>调用次数</th></tr>"
        for path, count in sorted(self.analysis_result['handlers'].items(), key=lambda x: x[1], reverse=True)[:5]:
            handler_table += f"<tr><td>{path}</td><td>{count}</td></tr>"
        handler_table += "</table>"

        # 文件类型表格
        file_type_table = "<table><tr><th>文件类型</th><th>下载次数</th></tr>"
        for ext, count in sorted(self.analysis_result['file_types'].items(), key=lambda x: x[1], reverse=True):
            file_type_table += f"<tr><td>{ext}</td><td>{count}</td></tr>"
        file_type_table += "</table>"

        # 下载统计表格
        download_stats = dict(sorted(self.analysis_result['download_stats'].items(), key=lambda x: x[1], reverse=True))
        top_downloads = dict(list(download_stats.items())[:5])
        download_table = "<table><tr><th>文件名</th><th>下载次数</th></tr>"
        for filename, count in top_downloads.items():
            download_table += f"<tr><td>{filename}</td><td>{count}</td></tr>"
        download_table += "</table>"

        # TOP用户表格
        user_data = sorted(
            [(user, count) for user, count in self.analysis_result['users'].items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        user_table = "<table><tr><th>用户</th><th>请求次数</th></tr>"
        for user, count in user_data:
            user_table += f"<tr><td>{user}</td><td>{count}</td></tr>"
        user_table += "</table>"

        # 响应时间统计
        response_times = self.analysis_result['response_times']
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0

        # 生成报告
        report_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="icon" href="assets/img/favicon.ico">
            <title>综合日志分析报告 | 峰云共享</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 20px;
                    background-color: #111827;
                    color: #e5e7eb;
                }}
                h1 {{
                    color: #ffffff;
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 2.5rem;
                }}
                h2 {{
                    color: #a3a3a3;
                    margin-top: 20px;
                    margin-bottom: 15px;
                    font-size: 1.8rem;
                    border-bottom: 1px solid #2d3748;
                    padding-bottom: 10px;
                }}
                p {{
                    margin-bottom: 10px;
                    font-size: 16px;
                    line-height: 1.6;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 30px;
                    background-color: #1f2937;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }}
                th, td {{
                    padding: 15px;
                    text-align: left;
                    border-bottom: 1px solid #2d3748;
                }}
                th {{
                    background-color: #1e293b;
                    color: #cbd5e1;
                }}
                tr:nth-child(even) {{
                    background-color: #1f2937;
                }}
                tr:hover {{
                    background-color: #2d3748;
                }}
                iframe {{
                    width: 100%;
                    height: 1000px;
                    border: none;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 40px;
                    color: #6b7280;
                    font-size: 14px;
                }}
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background-color: #1f2937;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                }}
                .stat-title {{
                    font-size: 1.2rem;
                    color: #a3a3a3;
                    margin-bottom: 10px;
                }}
                .stat-value {{
                    font-size: 2rem;
                    color: #ffffff;
                    font-weight: bold;
                }}
                /* 添加返回主页按钮样式 */
                .home-button {{
                    display: inline-block;
                    background-color: #3b82f6;
                    color: #ffffff;
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-size: 16px;
                    margin-bottom: 20px;
                }}
                .home-button:hover {{
                    background-color: #2563eb;
                }}
                .footer-link{{
                    color:#3b82f6;
                    text-decoration: none;
                }}
                .footer-link{{
                    text-decoration: underline;
                }}
            </style>
            <link rel="preload" as="style" href="assets/css/styles.css" onload="this.rel='stylesheet'">
            <link rel="stylesheet" href="assets/css/styles.css">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span>
                        <h1>综合日志分析报告</h1>
                        <a href="/" class="home-button">返回主页</a>
                    </span>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-title">总请求量</div>
                        <div class="stat-value">{total_requests}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">平均响应时间</div>
                        <div class="stat-value">{average_response_time}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">最大响应时间</div>
                        <div class="stat-value">{max_response_time:.2f}ms</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">最小响应时间</div>
                        <div class="stat-value">{min_response_time:.2f}ms</div>
                    </div>
                </div>

                <h2>TOP 10活跃用户</h2>
                {user_table}

                <h2>安全事件统计</h2>
                {security_table}

                <h2>热门接口统计</h2>
                {handler_table}

                <h2>文件类型统计</h2>
                {file_type_table}

                <h2>下载统计 (前5文件)</h2>
                {download_table}

                <h2>完整分析图表</h2>
                <iframe src="full_analysis.html"></iframe>

                <div class="footer">
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>&copy; <span id="current-year"></span>-<span id="next-current-year"></span>
                        <a href="https://dcyyd.github.io" class="footer-link" target="_blank">D.C.Y</a>
                             | <span
                            data-lang-key="footer_version">v2.0.0</span> |
                        <span data-lang-key="footer_internal_system">PeakCloud Internal System</span></p>
                </div>
            </div>
        </body>
        <script src="assets/js/scripts.js"></script>
        </html>
        """
        # 保存报告 判断是否为打包环境
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent

        web_dir = base_dir / 'web'
        web_dir.mkdir(exist_ok=True)  # 确保目录存在
        output_path = web_dir / 'report.html'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
