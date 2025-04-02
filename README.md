<div align="center">
    <h1>Peak Cloud Share - 安全高效的文件共享平台</h1>
    <p>
        <img src="https://img.shields.io/badge/Flask-3.1.0-44b883?logo=flask&logoColor=white">
        <img src="https://img.shields.io/badge/Python-3.10+-3670A0?logo=python&logoColor=white">
        <img src="https://img.shields.io/badge/License-MIT-000000?logo=mit&logoColor=white">
        <img src="https://img.shields.io/badge/Security-OWASP%20Top%2010%20Compliant-green">
    </p>
</div>

### 📚 简介

Peak Cloud Share 是基于 **Flask** 和 **Python** 的安全文件共享平台，支持**多用户认证**、**文件管理**、**主题/语言切换**
等功能，严格遵循 **OWASP Top 10** 安全标准。

### 💻 技术栈

| **分类**     | **技术/工具**                      | **📌 关键描述**                                                |
|------------|--------------------------------|------------------------------------------------------------|
| 🌶️ **后端** | Flask 3.10+<br>Python 3.10+    | • 轻量级WSGI框架，支持异步视图（Flask 2.0+）<br>• 基于Werkzeug路由和安全组件      |
| 🌐 **前端**  | Tailwind CSS 3.3<br>Vanilla JS | • 采用Utility-First CSS框架，支持按需构建样式<br>• 原生JS实现主题切换/语言切换/分页交互 |
| 📝 **存储**  | JSON (users.json)              | • 基于JSON文件的键值存储，支持用户信息持久化<br>• 简单文件型数据库，无需服务器依赖            |
| 🔒 **安全**  | OWASP Top 10 合规方案              | • 实施CSP策略禁止非法脚本执行<br>• 上传文件类型白名单校验（MIME+后缀双重验证）            |

### ✨ 核心功能

| **功能模块**     | **核心功能**                                | **详细说明**                                                                                               |
|--------------|-----------------------------------------|--------------------------------------------------------------------------------------------------------|
| **🔒 用户认证**  | 多用户账号体系 + 密码错误锁定（5次尝试）<br>密码强度校验        | 支持多账号登录<br>连续5次密码错误自动锁定账号（可配置解锁时间）<br>密码需≥8位，包含**大小写字母、数字、符号**至少两种组合                                   |
| **📁 文件管理**  | 10+格式上传<br>自动清理过期文件<br>分页列表 + 排序+下载日志记录 | 支持**PDF/Word/Excel/图片/压缩包**等格式<br>可配置文件保留时间（如7天/30天），过期自动删除<br>支持**分页浏览**、**按时间倒序排序**，显示**文件大小、类型、日志** |
| **🎨 交互体验**  | 主题切换<br>语言切换<br>响应式设计                   | 一键切换**深色/浅色主题**<br>实时切换**中文/英文**界面<br>适配**手机/平板/PC**，自动调整布局                                            |
| **🛡️ 安全防护** | 禁用右键/选择/开发者工具<br>文件名清洗                  | 通过前端脚本**禁用右键菜单、文本选择、F12开发者工具**<br>过滤文件名中的**非法字符**（如`../`），防止路径遍历                                       |

### 🚀 快速开始

#### 🔧 环境准备

```bash
# 克隆项目
git clone https://github.com/dcyyd/peak-cloud-share.git  
cd peak-cloud-share
```

#### 📦 安装依赖

```bash
# 创建虚拟环境
python -m venv venv  
source venv/bin/activate  # Linux/macOS  
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt  # 包含Flask, watchdog等
```

#### ⚙️ 配置文件

修改 `conf/__init__.py`：

```python
UPLOAD_FOLDER = "uploads/"  # 上传目录
CLEANUP_INTERVAL = 3600  # 每小时清理
FILE_RETENTION = 86400  # 文件保留24小时
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB限制
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'png', 'jpg'}
```

### 🛠️ 运行与打包

#### 🔥 启动服务

```bash
python app.py  # 访问 http://127.0.0.1:5000
```

#### 📦 生成可执行文件（Windows）

```bash
# 生成spec（首次需要）
pyinstaller --onefile --add-data "web;web" --icon web/assets/img/favicon.ico app.py

# 打包
pyinstaller app.spec --clean  # 结果在dist目录
```

### 📁 项目结构

```
peak-cloud-share-master/             # 根目录：配置、核心代码、静态资源等
├── config/                          # 配置文件目录
├── core/                            # 核心模块：认证、文件管理、定时任务等
│   ├── auth.py                      # 用户认证模块
│   ├── file_manager.py              # 文件上传/下载管理
│   ├── path_manager.py              # 路径管理
│   ├── scheduler.py                 # 后台任务调度
│   └── utils.py                     # 通用工具函数
├── log/                             # 日志存储目录
├── mapper/                          # 数据映射目录
├── uploads/                         # 用户上传文件存储目录
├── web/                             # 前端相关文件
│   ├── assets/                      # 静态资源（CSS/JS/图片/字体）
│   │   ├── css/                     # CSS 样式文件
│   │   ├── img/                     # 图片资源
│   │   ├── js/                      # JavaScript 脚本
│   │   └── webfonts/                # 网页字体文件
│   ├── index.html                   # 主页面
│   ├── login.html                   # 登录页面
│   ├── privacy.html                 # 隐私政策页面
│   └── support.html                 # 技术支持页面
├── .gitignore                       # Git 忽略规则
├── app.py                           # Flask 应用入口文件
├── app.spec                         # PyInstaller 打包配置
├── LICENSE                          # 开源许可证
├── README.md                        # 项目说明文档
└── requirements.txt                 # Python 依赖列表
```

### 🔐 安全注意事项

1. 生产环境必须启用 **HTTPS**（建议使用Nginx+Let's Encrypt）
2. 定期备份 `users.json` 和 `uploads/`
3. 限制上传目录权限：`chmod 700 uploads`
4. 考虑集成 **CSRF保护** 和 **速率限制**

### 📄 许可证

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  
本项目采用 MIT 协议，允许自由修改和商业使用。

### 📧 联系我们

有任何问题请联系：  
📩 **email**: <a href="mailto:dcyyd_kcug@yeah.net">dcyyd_kcug@yeah.net</a>  
📞 **电 话**: <a href="tel:17633963626">+86 17633963626</a>