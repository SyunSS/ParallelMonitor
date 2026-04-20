# 🔍 ParallelMonitor

**网页性能监控工具** — 多网站并发监控，实时可视化分析

![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ 功能一览

### 📊 实时监控
- **多网站并发检测** — 同时监控多个网站的页面加载性能
- **DOM Load / 总加载时间** — 精确记录关键时间指标
- **实时折线图** — 每个站点独立折线图，直观展示响应趋势
- **状态颜色标识** — 🟢 成功（绿色） / 🔴 超时失败（红色）

### 📈 资源分析面板
- **资源明细表格** — 所有请求资源的完整记录（名称、域名、IP、类型、耗时、大小、开始时间）
- **按类型/域名筛选** — 快速过滤 JS、图片、CSS、字体等资源
- **域名耗时柱状图** — 直观对比各域名的总耗时
- **资源类型分布** — 柱状图展示各类型资源占比
- **表格排序** — 点击表头可按数值大小正确排序
- **双击复制单元格** — 双击任意单元格即可复制内容到剪贴板
- **独立窗口** — 报告面板为独立窗口，支持调整大小、最大化、最小化，不阻塞主界面

### 🛠️ 高级功能
- **DNS IP 解析** — 自动解析每个资源对应的 IP 地址并显示
- **缓存绕过** — 每次检测均为干净访问，不受浏览器缓存影响
- **智能浏览器选择** — 优先使用系统 Edge / Chrome，回退至 Playwright 内置 Chromium
- **数据持久化** — 自动保存监控结果到 JSON 文件，报告查看器可切换历史文件
- **导出功能** — 支持导出监控数据
- **自定义图标** — 内嵌应用图标，无需外部文件

### ⚙️ 可配置参数
| 参数 | 说明 | 默认值 |
|------|------|--------|
| 并发数 | 同时检测的网站数量 | 3 |
| 超时时间 | 单个网站等待上限（秒） | 30 |
| 检测间隔 | 每轮检测间隔（秒） | 60 |

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Windows 10/11

### 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

> ⚠️ `playwright install chromium` 必须执行，用于安装浏览器引擎（约 290MB）
> 优先调用Windows自带edge浏览器或chrome浏览器，若都无则调用headless chromium

### 运行程序

```bash
python web_monitor.py
```

### 打包为 EXE

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包（带自定义图标）
python -m PyInstaller --onefile --noconsole --windowed --name ParallelMonitor --icon=icon.ico web_monitor.py

# 打包产物位于 dist/ParallelMonitor.exe
```

## 📁 项目结构

```
├── web_monitor.py      # 主程序（单文件完整应用）
├── icon.ico            # 应用图标（打包用）
├── icon.png            # PNG 格式图标源文件
├── requirements.txt    # 依赖清单
└── monitor_reports/    # 监控报告数据目录（运行时自动创建）
    └── *.json          # 各站点的历史监控记录
```

## 🏗️ 技术栈

| 组件 | 技术 |
|------|------|
| GUI 框架 | [PySide6](https://pyside6.io/) (Qt6 for Python) |
| 浏览器引擎 | [Playwright](https://playwright.dev/) (async) |
| 数据绑图 | [pyqtgraph](https://www.pyqtgraph.org/) |
| 打包工具 | PyInstaller |

## 🎮 使用说明

1. **添加网站** — 点击「添加网站」按钮输入 URL
2. **配置参数** — 根据需要调整并发数、超时时间、检测间隔
3. **开始监控** — 点击「开始监控」按钮启动检测
4. **实时观察** — 主界面显示各站点实时折线图和最新耗时
5. **查看报告** — 点击「查看报告」打开资源分析面板，深度分析每次检测结果
   - 切换顶部下拉框可浏览不同时间点的历史报告
   - 使用类型/域名筛选器快速定位目标资源
   - 双击表格单元格复制内容
6. **停止/导出** — 随时可停止监控或导出数据

## 📋 依赖清单

```
PySide6>=6.5.0       # GUI 框架
playwright>=1.40.0   # 浏览器自动化
pyqtgraph>=0.13.0    # 数据绑图
```
