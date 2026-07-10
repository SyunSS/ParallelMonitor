# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for ParallelMonitor
# Usage: pyinstaller ParallelMonitor.spec

import sys
from pathlib import Path

# ---------- 需要额外收集的隐式导入 ----------
hidden_imports = [
    # PySide6 相关（PyInstaller 自带 hook，此处作为保险）
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    # Playwright
    'playwright.async_api',
    'playwright._impl._api_types',
    'playwright._impl._browser',
    'playwright._impl._browser_context',
    'playwright._impl._page',
    'playwright._impl._network',
    # pyqtgraph
    'pyqtgraph',
    'numpy',               # pyqtgraph 依赖
    # 网络相关
    'dnspython',
    'httpx',
    # 标准库中可能漏掉的
    'asyncio',
    'json',
    'uuid',
    'datetime',
    'pathlib',
]

# ---------- 需要一起打包的数据文件 ----------
# 图标已内嵌为 base64，无需外部文件
datas = []

# ---------- 排除不需要的模块（减小体积） ----------
excludes = [
    'tkinter',
    'matplotlib',
    'scipy',
    'pandas',
    'PIL',
    'curses',
    'email',
    'distutils',
    'setuptools',
    'pkg_resources',
    'unittest',
    'test',
]

a = Analysis(
    ['ParallelMonitor.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ParallelMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # 不显示控制台窗口（GUI 应用）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # 使用项目自带图标
    icon=['icon.ico'] if Path('icon.ico').exists() else None,
)
