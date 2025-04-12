from cx_Freeze import setup, Executable
import os

# 项目元数据配置
PROJECT_NAME = "PeakCloudShare"
VERSION = "2.0.0"
AUTHOR = "D.C.Y."
AUTHOR_EMAIL = "dcyyd_kcug@yeah.net"
LICENSE = "MIT License"
DESCRIPTION = "Peak Cloud Share 企业级文件共享平台，支持安全文件管理、多用户认证、定时清理、日志分析等功能"
PROJECT_URL = "https://github.com/dcyyd/peak-cloud-share-master.git"

# 图标资源配置
ICON_PATH = os.path.join("web", "assets", "img", "favicon.ico")

# 打包配置参数
base = None  # 控制台模式，如需GUI模式改为 "Win32GUI"
include_files = [
    ("config", "config"),
    ("certs", "certs"),
    ("core", "core"),
    ("docs", "docs"),
    ("logs", "logs"),
    ("mapper", "mapper"),
    ("web", "web"),
    "app.py",
    "requirements.txt",
    "README.md",
    "LICENSE",
    ICON_PATH
]

setup(
    name=PROJECT_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=PROJECT_URL,
    license=LICENSE,
    options={
        "build_exe": {
            "include_files": include_files,
            "excludes": [],
            "packages": []
        }
    },
    executables=[
        Executable(
            "app.py",
            base=base,
            icon=ICON_PATH,
            target_name=PROJECT_NAME,
            copyright=f"Copyright (c) {VERSION} {AUTHOR}"
        )
    ]
)
