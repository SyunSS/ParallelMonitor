"""
网页监控工具 (Web Monitor)
===========================
技术栈：PySide6 + Playwright (async) + pyqtgraph

功能：
- 多网站并发监控 DOM Load 时间
- 实时折线图显示
- 状态颜色标识（绿色成功，红色失败）
- 可配置并发数、超时时间、检测间隔
"""

import asyncio
import base64
import csv
import subprocess
import sys
import os
import time
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path

# Qt imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QDialog,
    QLineEdit, QTextEdit, QDialogButtonBox, QMessageBox,
    QSplitter, QFrame, QScrollArea, QFileDialog,
    QComboBox
)
from PySide6.QtCore import (
    Qt, QObject, Signal, QThread, QTimer, QMutex, QWaitCondition
)
from PySide6.QtGui import QColor, QFont, QPalette, QIcon, QPixmap

# pyqtgraph for plotting
import pyqtgraph as pg

# Playwright async
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PWTimeoutError


# ============================================================
# 内嵌图标（不依赖外部 icon.png 文件）
# ============================================================

_ICON_B64 = "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAHIElEQVR4nO3dvY4bVRjHYe8KmlBQbx3RIwoKUlNzCWm4jhS5DppcAjW1KSgQfbR1agq2CdKiRXLkeD2eD8/HOef/PBJCslbeMeL9+R3b473ZVe7V24fHrY+BbPs3L252lSr6wA03rdgXGomiDsrAk2JfSBA2PwhDT7r9hjHY5BcbeigjBqv+MoMPZYVglV9i8KHMENzuFmb4odz5WawuBh/K3wYW2QAMP9QxV7MWxeBDXdvAbBuA4Yf1zDVvswTA8MP65pi7qwNg+GE7187fVQEw/LC9a+ZwcgAMP5Rj6jxOCoDhh/JMmcvRATD8UK6x8zkqAIYfyjdmTgcHwPBDPYbO6+IXAwHlGhQAz/5QnyFz2xsAww/16ptfpwAQ7GIAPPtD/S7NcWcADD+0o2uenQJAsLMB8OwP7Tk31zYACPYsAJ79oV2n820DgGACAME+C4D1H9p3POc2AAgmABDsUwCs/5DjMO82AAgmABBMACDY/39g0Pk/ZLIBQDABgGACAMEEAIIJAAQTAAgmABBMACDYrQ8BQS4bAAQTAAgmABDsi13h3v1c/CHCRa9/+XdXKhsABBMACFbVfv3y7ssPWx8DDHH/4ePdrgJVBeDJ3w+7Kv7DkuvrF7tqnqicAkAwAYBgAgDBBACCCQAEq+5dgDEef/rx2W03v/42+n6++uObZ7f98/370ffz3V+vn93257fvRt8PzOU2afgv3T5m+C/dPmb4L90Oa2gyAH1DPjQCfUM+NAJ9Qy4CbKW5AAwd7r6fGzrcfT83dLhFgC00FwBgOAGAYAIAwQQAgjUXgKHv8/f93ND3+ft+buj7/D4PwBaaC8CQ4R4aib7hHhqJvuE2/GylyQBcGvKxnwTsGvKxnwTsGnLDz5aa/ijwlI/9njPlY7/nGHZK0+wGAPQTAAgmABBMACCYAECw6t4FqOkrl6F0NgAIJgAQTAAgmABAMAGAYAIAwQQAggkABBMACCYAEEwAIJgAQDABgGACAMEEAIJV930ALXj5++u709vuf3jnew5YnQ0AggkABBMACCYAEEwACn5hEJYmABBMACCYAKzMqk9JBACCCQAEEwAIJgAQTAAK4gVC1iYAEEwAIJgAQDABgGACAMEEAIIJAAQTAAgmABs7/TZgHwZiTQKwotPh9lXgbE0AIJgAQDABgGACAMEE4AyvxJNCADqG/+nfh392DWr1cTGOABQwFGu8HXj82I4jt/TvpWz+PHiBg/B0PEtEobTHyfbiN4AhQ1H74Fw6/tofG9eJDkDX//xpn9ATgVyxATD8EBiAS6/sHz/zt7wFnHtstoBMUQG49D9538DXOiBjjrvWx8h0UQE4N+RPt7X8bH/q8FiTHjPdogJwas0hKPFSYKcCxAVgzDPgmkO6xBeDTL0PpwI54gJwzWCXMBinxzDmmLpOgeY6NuoTGYDazX2dglOBXAJQka6BP3f7lqcQ1EMAerSyIvc9jlYeJ+O4GGjmzxLUfCHP4fjX/r2lu284jjaAGW15ma1BZQoBqPQZ4NIxXRODEh8ryxGACp6Rr72vsUMtAjm8BjDQGtcKnJ6Dd72e0HUsc77+IAIZbAAzWeq99LEXMHktgDEEoDLWeeYkADPaYm22qnMNAYBgArDCVX1zXQps/WduAtAApwFMJQCVMOQsQQAKY9BZkwBAMAGo4Fl8zNeX+dJPxhCAwsxxIY/TCIYSAAjmYqDCHD97L/XlInBgAyiY4WdpArAQw0sNBACCCQAEEwAIJgAQTAAW5G/xUToBgGACAMEEAIIJAAQTgJX53n5KIgAQTAAgmMuBF+aiIEpmA4BgAgDBBACCCQAEEwAIJgAQTAAgmABAMAGAYAIAwQQAggkABBMACCYAEEwAIJgAQDABgGACAMEEAIIJAAQTAAgmABBMACCYAEAwAYBgAgDBqvrTYPcfPt5tfQzQEhsABBMACHbz6u3D49YHAWzDBgDBBACCCQAEEwAIJgAQTAAgmABAsNv9mxc3Wx8EsA0bAAQTAAgmABBMACCYAEAwAYBgAgDBBADSA+DDQJDnae5tABBMACCYAECwTwHwOgDkOMy7DQCCCQAE+ywATgOgfcdzbgOAYAIAwZ4FwGkAtOt0vm0AEOxsAGwB0J5zc20DgGCdAbAFQDu65vniBiACUL9Lc+wUAIL1BsAWAPXqm99BG4AIQH2GzK1TAAg2OAC2AKjH0HkdtQGIAJRvzJyOPgUQASjX2Pmc9BqACEB5pszl5BcBRQDKMXUer3oXQARge9fM4dVvA4oAbOfa+ZvlcwAiAOubY+5m+yCQCMB65pq3We7k1Ku3D49L3C+k2880+It+FNg2AHXM1SIbwDHbAJT7hLr4xUC2ASh3fhbfAI7ZBqCsJ85VA3AgBFDGxrxJAI6JAen2Kw99UQE4Jgak2G849MeKOIgugkAr9oUM/Kn/AFDsWBHyVkV+AAAAAElFTkSuQmCC"

def _get_embedded_icon() -> QIcon:
    """返回内嵌的窗口图标，无需外部文件"""
    pixmap = QPixmap()
    data = base64.b64decode(_ICON_B64)
    if pixmap.loadFromData(data, "PNG"):
        return QIcon(pixmap)
    return QIcon()  # fallback 空图标


# ============================================================
# 数据模型
# ============================================================

@dataclass
class MonitorRecord:
    """单次监控记录"""
    timestamp: str
    dom_load: float  # DOMContentLoaded 时间（毫秒）
    load_time: float  # 完整 Load 时间（毫秒）
    status: str  # success / timeout / error
    resources: Optional[List[dict]] = None  # 资源明细（仅 profiling 开启时有值）


@dataclass
class SiteConfig:
    """站点配置"""
    url: str
    records: List[MonitorRecord] = field(default_factory=list)
    max_records: int = 50  # 图表最多保留的记录数


# ============================================================
# 资源分析输出工具
# ============================================================

OUTPUT_DIR = "monitor_reports"  # 分析报告输出目录


def save_resource_report(url: str, timestamp: str, resources: List[dict],
                         dom_load: float, load_time: float, status: str) -> Optional[str]:
    """
    将单次检测的资源分析数据保存为 JSON 文件
    返回保存的文件路径，失败返回 None
    """
    try:
        import json as _json
        Path(OUTPUT_DIR).mkdir(exist_ok=True)

        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or "unknown"
        safe_host = hostname.replace(".", "_").replace(":", "_")
        ts_safe = timestamp.replace(":", "-")

        filename = f"{safe_host}_{ts_safe}_profile.json"
        filepath = Path(OUTPUT_DIR) / filename

        # 按耗时降序排序
        sorted_resources = sorted(
            [r for r in resources if r.get('duration', 0) > 0],
            key=lambda x: x['duration'],
            reverse=True
        )

        # 按域名聚合统计
        domain_stats: Dict[str, dict] = {}
        for r in resources:
            domain = r.get('domain', 'unknown')
            if domain not in domain_stats:
                domain_stats[domain] = {
                    'domain': domain,
                    'count': 0,
                    'total_duration': 0,
                    'max_duration': 0,
                    'resource_types': set()
                }
            d = domain_stats[domain]
            dur = r.get('duration', 0)
            d['count'] += 1
            d['total_duration'] += dur
            if dur > d['max_duration']:
                d['max_duration'] = dur
            d['resource_types'].add(r.get('type', 'other'))

        # 转换 set 为 list 以便 JSON 序列化
        for d in domain_stats.values():
            d['resource_types'] = list(d['resource_types'])
            d['avg_duration'] = round(d['total_duration'] / d['count'], 1)

        report = {
            'url': url,
            'timestamp': timestamp,
            'status': status,
            'timing': {
                'dom_content_loaded_ms': round(dom_load, 1),
                'load_complete_ms': round(load_time, 1),
                'resource_count': len(resources)
            },
            'top_slowest_resources': sorted_resources[:20],
            'domain_breakdown': sorted(
                domain_stats.values(),
                key=lambda x: x['total_duration'],
                reverse=True
            ),
            'all_resources': sorted_resources
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            _json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        return str(filepath)

    except Exception as e:
        print(f"[资源报告保存失败] {e}")
        return None


def save_round_report(results: List[dict], timestamp: str) -> Optional[str]:
    """
    将一轮所有站点的测试结果汇总保存为文件（JSON + CSV 双格式）
    
    Args:
        results: 每个站点的结果列表，每项包含 url/dom_load/load_time/status
        timestamp: 本轮测试的时间戳
    
    返回: 保存的文件路径，失败返回 None
    
    输出格式：
    - JSON: monitor_reports/round_YYYYMMDD_HHMMSS.json （完整数据）
    - CSV:  monitor_reports/round_YYYYMMDD_HHMMSS.csv  （3列简表：域名/DOM/LOAD）
    """
    try:
        import json as _json
        import csv as _csv

        Path(OUTPUT_DIR).mkdir(exist_ok=True)

        ts_safe = timestamp.replace(":", "-")
        base_name = f"round_{ts_safe}"

        # ---- 构建数据行（所有站点都保留） ----
        rows = []
        from urllib.parse import urlparse
        for r in results:
            hostname = urlparse(r['url']).hostname or r['url']
            rows.append({
                'domain': hostname,
                'dom_ms': round(r['dom_load'], 1) if r.get('dom_load') is not None else None,
                'load_ms': round(r['load_time'], 1) if r.get('load_time') is not None else None,
                'status': r.get('status', 'unknown'),
                'url': r.get('url', '')
            })

        # ---- 保存 CSV 简表（3列核心 + 状态） ----
        csv_path = Path(OUTPUT_DIR) / f"{base_name}.csv"
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = _csv.writer(f)
            writer.writerow(['域名', 'DOM (ms)', 'LOAD (ms)', '状态'])
            for row in rows:
                dom_str = f"{row['dom_ms']:.0f}" if row['dom_ms'] is not None and row['dom_ms'] >= 0 else '--'
                load_str = f"{row['load_ms']:.0f}" if row['load_ms'] is not None and row['load_ms'] >= 0 else '--'
                status_cn = {
                    'success': '✅ 正常',
                    'timeout': '⏰ 超时',
                    'error': '❌ 错误'
                }.get(row['status'], row['status'])
                writer.writerow([row['domain'], dom_str, load_str, status_cn])

        # ---- 保存 JSON 完整报告 ----
        json_path = Path(OUTPUT_DIR) / f"{base_name}.json"
        report = {
            'type': 'round_summary',
            'timestamp': timestamp,
            'total_sites': len(rows),
            'success_count': sum(1 for r in rows if r['status'] == 'success'),
            'error_count': sum(1 for r in rows if r['status'] != 'success'),
            'results': rows,
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            _json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        return str(csv_path)

    except Exception as e:
        print(f"[轮次报告保存失败] {e}")
        return None


# ============================================================
# 自定义信号类（跨线程通信）
# ============================================================

class MonitorSignals(QObject):
    """监控信号 - 用于后台线程向主线程传递数据"""
    # 参数: url, timestamp_str, dom_content_load_ms, load_time_ms, status
    record_ready = Signal(str, str, float, float, str)
    # 参数: url, status_text
    status_update = Signal(str, str)
    # 参数: message (用于日志)
    log_message = Signal(str)
    # 监控循环已停止
    stopped = Signal()
    # 资源分析报告就绪: (url, timestamp, file_path, resource_count)
    profile_saved = Signal(str, str, str, int)
    # 轮次汇总报告就绪: (timestamp, file_path, total_count)
    round_report_saved = Signal(str, str, int)


# ============================================================
# 异步监控引擎（在独立线程中运行）
# ============================================================

class AsyncMonitorEngine:
    """
    异步监控引擎
    使用 Playwright 并发检测多个网站的 DOM Load 时间
    支持：资源分析（Profiling）模式
    """

    def __init__(
        self,
        sites: List[str],
        signals: MonitorSignals,
        concurrency: int = 3,
        timeout_ms: int = 30000,
        interval_sec: int = 10,
        enable_profiling: bool = False,
        cron_expr: str = "",
        enable_round_report: bool = False
    ):
        self.sites = sites
        self.signals = signals
        self.concurrency = concurrency
        self.timeout_ms = timeout_ms
        self.interval_sec = interval_sec
        self.enable_profiling = enable_profiling
        self.cron_expr = cron_expr.strip()  # Cron 表达式，空字符串表示间隔模式
        self.enable_round_report = enable_round_report
        self.sites = [self._normalize_url(u) for u in sites]
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._semaphore: Optional[asyncio.Semaphore] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def stop(self):
        """请求优雅停止"""
        self._running = False

    async def _init_browser(self):
        """初始化浏览器实例（优先使用系统浏览器，回退到Playwright自带）"""
        if self._browser is None:
            mode_msg = " + 🔍 资源分析已开启" if self.enable_profiling else ""
            self._playwright = await async_playwright().start()

            # 三级回退：Edge → Chrome → Playwright Chromium
            channels = [
                ("msedge", "Microsoft Edge"),
                ("chrome",  "Google Chrome"),
            ]

            launched = False
            browser_name = ""
            for ch, name in channels:
                try:
                    self._browser = await self._playwright.chromium.launch(
                        headless=True,
                        channel=ch,
                        args=[
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--disable-http-cache',       # 禁用HTTP缓存，每次都是干净的请求
                            '--disable-background-networking',
                        ]
                    )
                    browser_name = f"{name} ({ch})"
                    launched = True
                    break
                except Exception as e:
                    self.signals.log_message.emit(f"⚠️ {name} 启动失败: {e}")

            if not launched:
                # 最终回退到 Playwright 自带的 Chromium
                try:
                    self._browser = await self._playwright.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-gpu',
                            '--disable-http-cache',       # 禁用HTTP缓存
                            '--disable-background-networking',
                        ]
                    )
                    browser_name = "Playwright Chromium (内置)"
                except Exception:
                    self.signals.log_message.emit("❌ 所有浏览器启动失败！请运行: python -m playwright install chromium")
                    raise

            self._semaphore = asyncio.Semaphore(self.concurrency)
            self.signals.log_message.emit(
                f"✅ 浏览器已启动 [{browser_name}] (并发数: {self.concurrency}{mode_msg}) 🚫缓存已禁用"
            )

    async def _close_browser(self):
        """关闭浏览器"""
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self.signals.log_message.emit("🔌 浏览器已关闭")

    async def _collect_resources(self, page: Page) -> list:
        """
        收集页面加载的所有资源明细（含 DNS 解析 IP）
        返回资源列表，每项包含: name, domain, ip, type, duration, size, start_time
        """
        raw_resources = await page.evaluate('''() => {
            const entries = performance.getEntriesByType('resource');
            return entries.map(e => ({
                name: e.name || '',
                initiatorType: e.initiatorType || 'other',
                duration: Math.round(e.duration * 10) / 10,
                transferSize: e.transferSize || 0,
                encodedBodySize: e.encodedBodySize || 0,
                startTime: Math.round(e.startTime * 10) / 10,
                responseStart: Math.round(e.responseStart * 10) / 10,
                responseEnd: Math.round(e.responseEnd * 10) / 10
            }));
        }''')

        from urllib.parse import urlparse
        import socket as _socket
        resources = []
        seen_names = set()
        dns_cache = {}  # 域名 → IP 缓存，避免重复解析

        for r in raw_resources:
            name = r.get('name', '')
            if not name or name in seen_names:
                continue
            seen_names.add(name)

            try:
                parsed = urlparse(name)
                domain = parsed.hostname or 'unknown'
            except Exception:
                domain = 'unknown'

            # DNS 解析域名获取 IP（带缓存）
            ip = '--'
            if domain != 'unknown':
                if domain not in dns_cache:
                    try:
                        ips = await asyncio.get_event_loop().getaddrinfo(domain, None)
                        if ips:
                            ip = ips[0][4][0]  # 取第一个解析结果的 IP
                    except Exception:
                        ip = '(DNS失败)'
                    dns_cache[domain] = ip
                else:
                    ip = dns_cache[domain]

            # 转换 transferSize: -1 表示跨域不可见，0 可能来自缓存
            transfer_size = r.get('transferSize', 0)
            if transfer_size > 0:
                size_str = f"{transfer_size / 1024:.1f} KB"
            elif transfer_size == 0:
                size_str = "(cache)"
            else:
                size_str = "(cross-origin)"

            resources.append({
                'name': name[:200],
                'domain': domain,
                'ip': ip,
                'type': r.get('initiatorType', 'other'),
                'duration': round(r.get('duration', 0), 1),
                'size': size_str,
                'start_time': round(r.get('startTime', 0), 1),
                'response_start': round(r.get('responseStart', 0), 1),
                'response_end': round(r.get('responseEnd', 0), 1)
            })

        return resources

    async def _measure_dom_load(self, page: Page, url: str) -> tuple:
        """
        测量单个页面的 DOM Load 和完整 Load 时间
        支持 HTTPS → HTTP 自动降级：https 失败后尝试 http
        返回: (dom_content_load_ms, load_time_ms, status, resources_or_None)
        """
        dom_load = 0.0
        load_time = 0.0
        status = "success"
        resources = []

        # 构造降级链：原始URL优先，如果是https则追加http作为回退
        urls_to_try = [url]
        if url.startswith('https://'):
            fallback_url = url.replace('https://', 'http://', 1)
            urls_to_try.append(fallback_url)

        last_error = None
        tried_urls = []

        for try_url in urls_to_try:
            tried_urls.append(try_url)
            try:
                # 重置状态（可能上次尝试改了值）
                dom_load = 0.0
                load_time = 0.0
                status = "success"
                resources = []

                page.set_default_timeout(self.timeout_ms)

                response = await page.goto(
                    try_url,
                    wait_until='load',
                    timeout=self.timeout_ms
                )

                timing_data = await page.evaluate('''() => {
                    const entries = performance.getEntriesByType('navigation');
                    if (entries && entries.length > 0) {
                        return {
                            domContent: entries[0].domContentLoadedEventEnd || 0,
                            load: entries[0].loadEventEnd || 0
                        };
                    }
                    return { domContent: 0, load: 0 };
                }''')

                dom_load = timing_data['domContent']
                load_time = timing_data['load']

                if self.enable_profiling:
                    resources = await self._collect_resources(page)

                if response and response.status >= 400:
                    status = "error"
                    self.signals.log_message.emit(
                        f"⚠️ {try_url} 返回状态码: {response.status}"
                    )
                else:
                    # 如果走了降级，提示一下
                    if try_url != url:
                        self.signals.log_message.emit(
                            f"🔀 {url} (HTTPS失败) → 已切换 {try_url}"
                        )
                # 成功则跳出循环
                break

            except PWTimeoutError:
                last_error = f"超时 ({self.timeout_ms}ms)"
                status = "timeout"
                dom_load = -1
                load_time = -1
                self.signals.log_message.emit(f"⏰ {try_url} 超时 ({self.timeout_ms}ms)")
                continue

            except Exception as e:
                last_error = str(e)[:100]
                status = "error"
                dom_load = -1
                load_time = -1
                error_type = type(e).__name__
                err_msg = str(e)[:100]

                # 判断是否值得尝试降级（连接/SSL/协议类错误才降级）
                should_fallback = any(
                    kw in err_msg.lower() or kw in error_type.lower()
                    for kw in ['invalid url', 'ssl', 'tls', 'certificate',
                               'connection', 'refused', 'reset', 'aborted',
                               'err_name', 'net::']
                ) or error_type in ('Error', 'PlaywrightError')

                if should_fallback and try_url != urls_to_try[-1]:
                    self.signals.log_message.emit(
                        f"🔄 {try_url} 失败 [{error_type}]，尝试降级..."
                    )
                    continue
                else:
                    self.signals.log_message.emit(
                        f"❌ {try_url} 错误 [{error_type}]: {err_msg}"
                    )
                    break

        return (dom_load, load_time, status, resources if self.enable_profiling else None)

    async def _monitor_single_site(self, url: str):
        """监控单个站点（受信号量控制）"""
        if not self._browser or not self._running:
            return

        context = None
        page = None

        try:
            async with self._semaphore:
                if not self._running:
                    return

                # 为每个请求创建独立的浏览器上下文
                context = await self._browser.new_context(
                    user_agent=(
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/120.0.0.0 Safari/537.36'
                    )
                )
                page = await context.new_page()

                # 拦截所有请求，强制绕过缓存（确保每次都是干净的请求）
                async def _bypass_cache(route):
                    await route.continue_(
                        headers={**(route.request.headers), 'Cache-Control': 'no-cache'}
                    )
                await page.route('**', _bypass_cache)

                # 执行测量
                timestamp = datetime.now().strftime('%H:%M:%S')
                dom_load, load_time, status, resources = await self._measure_dom_load(page, url)

                # 发送结果到主线程
                self.signals.record_ready.emit(url, timestamp, dom_load, load_time, status)
                self.signals.status_update.emit(url, f"{status.upper()}")

                # 收集本轮结果（用于汇总报告）
                if hasattr(self, '_round_results'):
                    self._round_results.append({
                        'url': url,
                        'timestamp': timestamp,
                        'dom_load': dom_load,
                        'load_time': load_time,
                        'status': status,
                    })

                # 资源分析：保存报告文件（无论成败都记录）
                if self.enable_profiling:
                    report_path = save_resource_report(
                        url=url,
                        timestamp=timestamp,
                        resources=resources if (status == "success" and resources) else [],
                        dom_load=dom_load,
                        load_time=load_time,
                        status=status
                    )
                    if report_path:
                        self.signals.profile_saved.emit(
                            url, timestamp, report_path, len(resources) if resources else 0
                        )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.signals.log_message.emit(f"💥 {url} 未预期异常: {str(e)[:100]}")
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass

    async def _monitoring_loop(self):
        """主监控循环（支持间隔模式 & Cron 定时模式）"""
        await self._init_browser()
        self._running = True

        # 根据模式显示启动信息
        if self.cron_expr:
            self.signals.log_message.emit(f"🚀 监控已启动 [⏰ Cron: {self.cron_expr}]")
        else:
            self.signals.log_message.emit("🚀 监控已启动")

        try:
            while self._running:
                cycle_start = time.time()

                # 初始化本轮结果收集
                if self.enable_round_report:
                    self._round_results = []
                    self._round_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # 并发检测所有站点
                tasks = [
                    self._monitor_single_site(url)
                    for url in self.sites
                ]
                await asyncio.gather(*tasks, return_exceptions=True)

                if not self._running:
                    break

                # ── 轮次汇总报告 ──────────────────
                if self.enable_round_report and hasattr(self, '_round_results') and self._round_results:
                    report_path = save_round_report(
                        results=self._round_results,
                        timestamp=self._round_timestamp
                    )
                    if report_path:
                        ok = sum(1 for r in self._round_results if r['status'] == 'success')
                        total = len(self._round_results)
                        self.signals.round_report_saved.emit(
                            self._round_timestamp, report_path, total
                        )
                        self.signals.log_message.emit(
                            f"📋 本轮汇总报告已保存 ({ok}/{total} 成功)"
                        )

                # ── 计算下次执行时间 ──────────────
                if self.cron_expr:
                    # Cron 模式：计算到下一个触发点的时间
                    wait_sec = self._cron_next_wait()
                    next_time_str = datetime.fromtimestamp(
                        time.time() + wait_sec
                    ).strftime("%Y-%m-%d %H:%M:%S")
                    self.signals.log_message.emit(
                        f"⏰ 本轮完成，下次执行 → {next_time_str}（等待 {self._fmt_duration(wait_sec)}）"
                    )
                    # 分段 sleep 以便响应停止
                    await self._interruptible_sleep(wait_sec)
                else:
                    # 间隔模式
                    elapsed = time.time() - cycle_start
                    if elapsed >= self.interval_sec:
                        # 本轮耗时已超过间隔 → 立即开始下一轮，不等了
                        self.signals.log_message.emit(
                            f"⏱️ 本轮耗时 {self._fmt_duration(elapsed)} ≥ 间隔 {self._fmt_duration(self.interval_sec)}，立即开始下一轮..."
                        )
                        # 不需要额外 sleep，直接进入下轮循环
                    else:
                        # 正常情况：等够剩余间隔时间
                        sleep_time = self.interval_sec - elapsed
                        self.signals.log_message.emit(
                            f"⏱️ 本轮完成，{sleep_time:.1f}s 后开始下一轮..."
                        )
                        await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.signals.log_message.emit(f"💥 监控循环异常: {str(e)}")
        finally:
            await self._close_browser()
            self._running = False
            self.signals.stopped.emit()
            self.signals.log_message.emit("⏹️ 监控已停止")

    def _cron_next_wait(self) -> float:
        """根据 Cron 表达式计算距离下一次执行的秒数"""
        now = datetime.now()
        parts = self.cron_expr.split()
        if len(parts) != 5:
            return self.interval_sec  # 格式错误时回退到间隔模式

        minute, hour, dom, month, dow = parts

        # 简单的 Cron 下次执行计算（覆盖常用场景）
        import re as _re
        candidates = []

        # 尝试未来 366 天内找到匹配时间
        for day_offset in range(0, 366 * 24 * 60):  # 按分钟步进，最多搜一年
            candidate = now + __import__('datetime').timedelta(minutes=day_offset + 1)
            if self._match_cron(candidate, minute, hour, dom, month, dow):
                return (candidate - now).total_seconds()

        # 找不到匹配（理论上不会发生），回退到默认间隔
        return float(self.interval_sec)

    @staticmethod
    def _match_cron(dt: datetime, minute: str, hour: str, dom: str, month: str, dow: str) -> bool:
        """检查给定时间是否匹配 Cron 表达式的各字段"""
        import re as _re

        def _match(value: int, pattern: str) -> bool:
            """单个字段匹配"""
            if pattern == "*":
                return True
            if "/" in pattern:
                base, step = pattern.split("/")
                step = int(step)
                base_val = int(base) if base != "*" else 0
                return (value - base_val) % step == 0
            if "," in pattern:
                return value in [int(x.strip()) for x in pattern.split(",")]
            try:
                return value == int(pattern)
            except ValueError:
                return False

        if not _match(dt.minute, minute):
            return False
        if not _match(dt.hour, hour):
            return False
        if not _match(dt.day, dom):
            return False
        if not _match(dt.month, month):
            return False
        if not _match(dt.isoweekday() % 7, dow):  # Python: Mon=1..Sun=7, Cron: Sun=0..Sat=6
            return False
        return True

    async def _interruptible_sleep(self, total_seconds: float):
        """可中断的睡眠，每 30 秒检查一次是否需要停止"""
        remaining = total_seconds
        while remaining > 0 and self._running:
            chunk = min(30.0, remaining)
            await asyncio.sleep(chunk)
            remaining -= chunk

    @staticmethod
    @staticmethod
    def _normalize_url(url: str) -> str:
        """自动为缺少协议前缀的 URL 补上 https://"""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url

    def _fmt_duration(self, seconds: float) -> str:
        """格式化持续时间（人类友好格式）"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f"{m}分{s}秒"
        else:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            if h >= 24:
                d = h // 24
                h = h % 24
                return f"{d}天{h}小时{m}分"
            return f"{h}小时{m}分"


# ============================================================
# 后台线程（运行 asyncio 事件循环）
# ============================================================

class MonitorWorkerThread(QThread):
    """
    工作线程：在其中运行 asyncio 事件循环执行监控任务
    """

    def __init__(
        self,
        sites: List[str],
        signals: MonitorSignals,
        concurrency: int = 3,
        timeout_ms: int = 30000,
        interval_sec: int = 10,
        enable_profiling: bool = False,
        cron_expr: str = "",
        enable_round_report: bool = False
    ):
        super().__init__()
        self.sites = sites
        self.signals = signals
        self.concurrency = concurrency
        self.timeout_ms = timeout_ms
        self.interval_sec = interval_sec
        self.enable_profiling = enable_profiling
        self.cron_expr = cron_expr
        self.enable_round_report = enable_round_report

        self._engine: Optional[AsyncMonitorEngine] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def run(self):
        """线程入口：创建并运行 asyncio 事件循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._engine = AsyncMonitorEngine(
            sites=self.sites,
            signals=self.signals,
            concurrency=self.concurrency,
            timeout_ms=self.timeout_ms,
            interval_sec=self.interval_sec,
            enable_profiling=self.enable_profiling,
            cron_expr=self.cron_expr,
            enable_round_report=self.enable_round_report
        )

        try:
            self._loop.run_until_complete(self._engine._monitoring_loop())
        except Exception as e:
            self.signals.log_message.emit(f"线程异常退出: {e}")
        finally:
            self._loop.close()

    def stop(self):
        """请求停止监控"""
        if self._engine and self._engine.is_running:
            self._engine.stop()
            # 安排一个协程来取消所有任务，加速停止
            if self._loop and self._loop.is_running():
                for task in asyncio.all_tasks(self._loop):
                    task.cancel()


# ============================================================
# 单个站点的 Tab 内容组件
# ============================================================

class SiteTab(QWidget):
    """单个网站的监控 Tab 页面 - 支持双指标（DOM Load + 完整 Load）"""

    MAX_TABLE_ROWS = 200  # 表格最多保留行数
    CHART_MAX_POINTS = 50  # 图表最多显示数据点数

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.records: List[MonitorRecord] = []

        self._setup_ui()

    def _setup_ui(self):
        """构建 UI 布局"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # === 状态信息区 ===
        info_group = QGroupBox("状态信息")
        info_layout = QVBoxLayout(info_group)

        # URL 显示
        url_row = QHBoxLayout()
        url_label = QLabel("URL:")
        url_label.setFont(QFont("", -1, QFont.Weight.Bold))
        url_label.setFixedWidth(60)
        self.url_display = QLabel(self.url)
        self.url_display.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.url_display.setWordWrap(True)
        url_row.addWidget(url_label)
        url_row.addWidget(self.url_display, 1)
        info_layout.addLayout(url_row)

        # 状态显示 + 双时间指标（同一行）
        metrics_row = QHBoxLayout()

        status_label = QLabel("状态:")
        status_label.setFixedWidth(50)
        self.status_display = QLabel("等待中...")
        self.status_display.setFont(QFont("", 11, QFont.Weight.Bold))
        self.status_display.setStyleSheet(
            "color: #888; padding: 4px 12px; border-radius: 4px;"
            "background: rgba(128,128,128,0.1);"
        )
        metrics_row.addWidget(status_label)
        metrics_row.addWidget(self.status_display)

        metrics_row.addSpacing(20)

        # DOM ContentLoaded 指标
        dom_label = QLabel("DCL:")
        dom_label.setFont(QFont("", -1, QFont.Weight.Bold))
        dom_label.setToolTip("DOMContentLoaded - HTML解析完成时间")
        self.dom_display = QLabel("-- ms")
        self.dom_display.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.dom_display.setStyleSheet("color: #00d4aa;")
        metrics_row.addWidget(dom_label)
        metrics_row.addWidget(self.dom_display)

        metrics_row.addSpacing(15)

        # 完整 Load 时间指标
        load_label = QLabel("Load:")
        load_label.setFont(QFont("", -1, QFont.Weight.Bold))
        load_label.setToolTip("Load - 全部资源加载完成时间")
        self.load_display = QLabel("-- ms")
        self.load_display.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.load_display.setStyleSheet("color: #3b82f6;")
        metrics_row.addWidget(load_label)
        metrics_row.addWidget(self.load_display)

        metrics_row.addStretch()
        info_layout.addLayout(metrics_row)

        layout.addWidget(info_group)

        # === 实时图表（双折线）===
        chart_group = QGroupBox("加载时间趋势 (ms)")
        chart_layout = QVBoxLayout(chart_group)

        # 图例标签
        legend_row = QHBoxLayout()
        legend_dcl = QLabel("● DCL (DOM)")
        legend_dcl.setStyleSheet(f"color: #00d4aa; font-weight: bold; font-size: 11px;")
        legend_load = QLabel("● Load (完整)")
        legend_load.setStyleSheet(f"color: #3b82f6; font-weight: bold; font-size: 11px;")
        legend_err = QLabel("● 异常")
        legend_err.setStyleSheet(f"color: #ff6b6b; font-weight: bold; font-size: 11px;")
        legend_row.addWidget(legend_dcl)
        legend_row.addSpacing(15)
        legend_row.addWidget(legend_load)
        legend_row.addSpacing(15)
        legend_row.addWidget(legend_err)
        legend_row.addStretch()
        chart_layout.addLayout(legend_row)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e2e')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Time', units='ms')
        self.plot_widget.setLabel('bottom', 'Samples', units='')
        self.plot_widget.setMaximumHeight(220)
        self.plot_widget.addLegend(offset=(70, 5))

        # DCL 曲线（青绿色）
        self.curve_dcl = self.plot_widget.plot(
            pen=pg.mkPen(color='#00d4aa', width=2),
            symbol='o',
            symbolSize=5,
            symbolBrush='#00d4aa',
            symbolPen='#00d4aa',
            name='DOM Content'
        )

        # Load 曲线（蓝色）
        self.curve_load = self.plot_widget.plot(
            pen=pg.mkPen(color='#3b82f6', width=2),
            symbol='s',
            symbolSize=5,
            symbolBrush='#3b82f6',
            symbolPen='#3b82f6',
            name='Full Load'
        )

        # 异常散点
        self.scatter = pg.ScatterPlotItem(
            size=10,
            brush=pg.mkBrush('#ff6b6b'),
            pen=pg.mkPen(None),
            name='Error/Timeout'
        )
        self.plot_widget.addItem(self.scatter)

        chart_layout.addWidget(self.plot_widget)
        layout.addWidget(chart_group, stretch=1)

        # === 数据表格（4列）===
        table_group = QGroupBox("历史记录")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["时间", "DOM Content (ms)", "Load (ms)", "状态"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setMaximumHeight(180)

        table_layout.addWidget(self.table)
        layout.addWidget(table_group)

    def add_record(self, record: MonitorRecord):
        """添加新的监控记录并更新 UI"""
        self.records.append(record)

        if len(self.records) > self.MAX_TABLE_ROWS:
            self.records = self.records[-self.MAX_TABLE_ROWS:]

        # 状态颜色
        if record.status == "success":
            color = "#22c55e"
            bg_color = "rgba(34,197,94,0.15)"
        elif record.status == "timeout":
            color = "#f59e0b"
            bg_color = "rgba(245,158,11,0.15)"
        else:
            color = "#ef4444"
            bg_color = "rgba(239,68,68,0.15)"

        # 状态显示
        self.status_display.setText(record.status.upper())
        self.status_display.setStyleSheet(
            f"color: {color}; padding: 4px 12px; border-radius: 4px; "
            f"background: {bg_color};"
        )

        # DOM Content 显示
        if record.dom_load >= 0:
            self.dom_display.setText(f"{record.dom_load:.0f} ms")
            self.dom_display.setStyleSheet(f"color: {'#00d4aa' if record.status == 'success' else color}; "
                                          f"font-weight: bold;")
        else:
            self.dom_display.setText("-- ms")
            self.dom_display.setStyleSheet("color: #666;")

        # Load 显示
        if record.load_time >= 0:
            self.load_display.setText(f"{record.load_time:.0f} ms")
            self.load_display.setStyleSheet(f"color: {'#3b82f6' if record.status == 'success' else color}; "
                                           f"font-weight: bold;")
        else:
            self.load_display.setText("-- ms")
            self.load_display.setStyleSheet("color: #666;")

        # 表格插入新行
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)

        time_item = QTableWidgetItem(record.timestamp)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row_idx, 0, time_item)

        dom_item = QTableWidgetItem(f"{record.dom_load:.0f}" if record.dom_load >= 0 else "--")
        dom_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        dom_item.setForeground(QColor("#00d4aa") if record.status == "success" else QColor(color))
        self.table.setItem(row_idx, 1, dom_item)

        load_item = QTableWidgetItem(f"{record.load_time:.0f}" if record.load_time >= 0 else "--")
        load_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        load_item.setForeground(QColor("#3b82f6") if record.status == "success" else QColor(color))
        self.table.setItem(row_idx, 2, load_item)

        status_item = QTableWidgetItem(record.status.upper())
        status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        status_item.setForeground(QColor(color))
        self.table.setItem(row_idx, 3, status_item)

        self.table.scrollToBottom()

        while self.table.rowCount() > self.MAX_TABLE_ROWS:
            self.table.removeRow(0)

        self._update_chart()

    def _update_chart(self):
        """更新实时双线折线图"""
        recent = self.records[-self.CHART_MAX_POINTS:]

        success_dcl = [(i, r.dom_load) for i, r in enumerate(recent)
                       if r.status == "success" and r.dom_load >= 0]
        success_load = [(i, r.load_time) for i, r in enumerate(recent)
                        if r.status == "success" and r.load_time >= 0]
        fail_data = [i for i, r in enumerate(recent) if r.status != "success"]

        # DCL 曲线
        if success_dcl:
            x_dcl, y_dcl = zip(*success_dcl)
            self.curve_dcl.setData(list(x_dcl), list(y_dcl))
        else:
            self.curve_dcl.setData([], [])

        # Load 曲线
        if success_load:
            x_load, y_load = zip(*success_load)
            self.curve_load.setData(list(x_load), list(y_load))
        else:
            self.curve_load.setData([], [])

        # 异常散点
        if fail_data:
            last_good_y = success_dcl[-1][1] if success_dcl else 0
            self.scatter.setData(fail_data, [last_good_y] * len(fail_data))
        else:
            self.scatter.setData([], [])

        # Y轴自动范围
        all_valid = [r.dom_load for r in recent if r.dom_load > 0] + \
                    [r.load_time for r in recent if r.load_time > 0]
        if all_valid:
            ymin = min(all_valid) * 0.7
            ymax = max(all_valid) * 1.25
            self.plot_widget.setYRange(ymin, ymax)

        # 自动调整Y轴范围
        valid_values = [r.dom_load for r in self.records[-self.CHART_MAX_POINTS:] if r.dom_load > 0]
        if valid_values:
            ymin = min(valid_values) * 0.8
            ymax = max(valid_values) * 1.2
            self.plot_widget.setYRange(ymin, ymax)


# ============================================================
# URL 输入对话框
# ============================================================


class SortableTableWidgetItem(QTableWidgetItem):
    """支持数值排序的表格项，按数字值排序而非字符串"""

    def __init__(self, text: str, sort_key=None):
        super().__init__(text)
        # sort_key 为 None 时回退到字符串排序
        self._sort_key = sort_key if sort_key is not None else text

    def __lt__(self, other):
        if isinstance(other, SortableTableWidgetItem):
            try:
                return float(self._sort_key) < float(other._sort_key)
            except (ValueError, TypeError):
                return str(self._sort_key) < str(other._sort_key)
        return super().__lt__(other)


class UrlInputDialog(QDialog):
    """用于首次启动时输入 URL 列表的对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加监控网站")
        self.setMinimumSize(500, 350)
        self.urls: List[str] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 提示信息
        hint = QLabel(
            "请输入要监控的网站URL，每行一个：\n"
            "例如:\n"
            "https://www.baidu.com\n"
            "https://www.taobao.com\n"
            "https://github.com"
        )
        hint.setStyleSheet("color: #666; padding: 8px;")
        layout.addWidget(hint)

        # 文本输入框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("在此输入网址，每行一个...")
        self.text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(self.text_edit)

        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请至少输入一个URL！")
            return

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        urls = []
        for line in lines:
            if not line.startswith(('http://', 'https://')):
                line = 'https://' + line
            urls.append(line)

        self.urls = urls
        self.accept()


# ============================================================
# 资源报告查看器（全功能分析面板）
# ============================================================

class ReportViewerDialog(QDialog):
    """
    全功能资源分析面板
    功能：
    - 可排序的资源明细表格（点击表头排序）
    - 域名耗时柱状图
    - 资源类型饼图
    - 按类型/域名筛选联动
    """

    # 资源类型配色方案（用于类型柱状图）
    TYPE_COLORS = {
        'script': '#ef4444',   # 红色 - JS
        'img': '#3b82f6',      # 蓝色 - 图片
        'css': '#8b5cf6',       # 紫色 - 样式
        'font': '#f59e0b',      # 橙色 - 字体
        'fetch': '#06b6d4',     # 青色 - API请求
        'xmlhttprequest': '#06b6d4',
        'other': '#9ca3af',     # 灰色 - 其他
        'link': '#10b981',      # 绿色 - 预加载
        'iframe': '#ec4899',    # 粉色
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📊 资源分析面板")
        self.setMinimumSize(1000, 700)
        self.resize(1300, 850)  # 默认初始大小
        # 设置为独立窗口：有最小化/最大化/关闭按钮，不属于主窗口
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        # 设置图标（内嵌，无需外部文件）
        self.setWindowIcon(_get_embedded_icon())
        self._report_data: dict = {}
        self._all_resources: List[dict] = []
        self._domain_stats: List[dict] = []
        self._sort_column = 5  # 默认按耗时降序
        self._sort_order = Qt.SortOrder.DescendingOrder

        self._setup_ui()
        # 延迟到事件循环空闲后加载数据，避免 PlotWidget 未就绪时绘制报错
        QTimer.singleShot(0, self._load_latest_report)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # ======== 顶部：文件选择 + 基本信息 ========
        top_layout = QHBoxLayout()

        file_label = QLabel("📂 选择报告:")
        file_label.setFont(QFont("", -1, QFont.Weight.Bold))
        top_layout.addWidget(file_label)

        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(350)
        self.file_combo.setStyleSheet("padding: 6px; border: 2px solid #ccd0da; border-radius: 6px;")
        self.file_combo.currentIndexChanged.connect(self._on_file_changed)
        top_layout.addWidget(self.file_combo, stretch=1)

        refresh_btn = QPushButton("🔄 刷新列表")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._refresh_files)
        top_layout.addWidget(refresh_btn)

        open_folder_btn = QPushButton("📁 打开目录")
        open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_folder_btn.clicked.connect(self._open_report_dir)
        top_layout.addWidget(open_folder_btn)

        layout.addLayout(top_layout)

        # === 基本信息 ===
        info_group = QGroupBox("检测概览")
        info_layout = QHBoxLayout(info_group)

        self.info_url = QLabel("--")
        self.info_url.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_url.setFont(QFont("", 10))
        info_layout.addWidget(QLabel("URL:"))
        info_layout.addWidget(self.info_url, stretch=1)

        self.info_time = QLabel("--")
        info_layout.addWidget(QLabel("时间:"))
        info_layout.addWidget(self.info_time)

        self.info_dcl = QLabel("--")
        self.info_dcl.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.info_dcl.setStyleSheet("color: #00d4aa;")
        info_layout.addWidget(QLabel("DCL:"))
        info_layout.addWidget(self.info_dcl)

        self.info_load = QLabel("--")
        self.info_load.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.info_load.setStyleSheet("color: #3b82f6;")
        info_layout.addWidget(QLabel("Load:"))
        info_layout.addWidget(self.info_load)

        self.info_count = QLabel("--")
        self.info_count.setStyleSheet("color: #f59e0b; font-weight: bold;")
        info_layout.addWidget(QLabel("资源数:"))
        info_layout.addWidget(self.info_count)

        layout.addWidget(info_group)

        # ======== 中间区域：左右分栏 ========
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- 左侧：表格 ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        # 筛选栏
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("筛选:"))

        filter_row.addWidget(QLabel("类型:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("全部", None)
        _type_options = [
            ("script (JS)", "script"), ("img (图片)", "img"),
            ("css (样式)", "css"), ("font (字体)", "font"),
            ("fetch/API", "fetch"), ("link", "link"), ("iframe", "iframe"),
            ("其他", "other")
        ]
        for text, val in _type_options:
            self.type_filter.addItem(text, val)
        self.type_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.type_filter)

        filter_row.addWidget(QLabel("域名:"))
        self.domain_filter = QComboBox()
        self.domain_filter.addItem("全部", None)
        self.domain_filter.currentIndexChanged.connect(self._apply_filters)
        filter_row.addWidget(self.domain_filter, stretch=1)

        search_label = QLabel("搜索:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("输入关键字过滤 URL...")
        self.search_edit.textChanged.connect(self._apply_filters)
        filter_row.addWidget(search_label)
        filter_row.addWidget(self.search_edit)

        left_layout.addLayout(filter_row)

        # 资源表格
        table_group = QGroupBox("资源明细 (点击表头排序)")
        table_layout = QVBoxLayout(table_group)
        self.resource_table = QTableWidget()
        self.resource_table.setColumnCount(8)
        self.resource_table.setHorizontalHeaderLabels(
            ["#", "资源名称", "域名", "IP", "类型", "耗时(ms)", "大小", "开始时间"]
        )
        self.resource_table.horizontalHeader().setSectionsClickable(True)
        self.resource_table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self.resource_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.resource_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.resource_table.setAlternatingRowColors(True)
        self.resource_table.verticalHeader().setVisible(False)
        self.resource_table.setWordWrap(False)

        header = self.resource_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.resource_table.setColumnWidth(0, 40)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.resource_table.setColumnWidth(3, 120)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.resource_table.setColumnWidth(4, 70)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.resource_table.setColumnWidth(5, 85)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.resource_table.setColumnWidth(6, 90)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.resource_table.setColumnWidth(7, 80)

        self.resource_table.itemDoubleClicked.connect(self._on_item_double_clicked)
        table_layout.addWidget(self.resource_table)
        left_layout.addWidget(table_group, stretch=1)

        # 统计标签
        self.filter_result_label = QLabel("")
        self.filter_result_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.filter_result_label.setStyleSheet("color: #666; font-size: 11px;")
        left_layout.addWidget(self.filter_result_label)

        splitter.addWidget(left_widget)

        # --- 右侧：图表区 ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 域名柱状图
        bar_group = QGroupBox("📊 各域名总耗时 (ms)")
        bar_layout = QVBoxLayout(bar_group)
        self.bar_chart = pg.PlotWidget()
        self.bar_chart.setBackground('#f8fafc')
        self.bar_chart.showGrid(x=False, y=True, alpha=0.2)
        self.bar_chart.setLabel('left', 'Total Time', units='ms')
        self.bar_chart.setMaximumHeight(280)
        # 不隐藏底部X轴（用于显示域名标签）
        self.bar_plot = pg.BarGraphItem(x=[], height=[], width=0.7, brush=pg.mkBrush('#3b82f6'))
        self.bar_chart.addItem(self.bar_plot)
        self.bar_labels: list = []
        bar_layout.addWidget(self.bar_chart)
        right_layout.addWidget(bar_group, stretch=1)

        # 资源类型柱状图（替代不存在的 WedgeItem 饼图）
        type_group = QGroupBox("📊 资源类型分布")
        type_layout = QVBoxLayout(type_group)
        self.type_chart = pg.PlotWidget()
        self.type_chart.setBackground('#f8fafc')
        self.type_chart.showGrid(x=False, y=True, alpha=0.2)
        self.type_chart.setLabel('left', 'Count', units='条')
        self.type_chart.setMaximumHeight(260)
        self.type_plot = pg.BarGraphItem(x=[], height=[], width=0.6)
        self.type_chart.addItem(self.type_plot)
        self.type_labels: list = []  # 类型名称标签
        type_layout.addWidget(self.type_chart)
        right_layout.addWidget(type_group, stretch=1)

        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 3)   # 表格占 60%
        splitter.setStretchFactor(1, 2)   # 图表占 40%

        layout.addWidget(splitter, stretch=1)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.setMinimumWidth(100)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    # ========== 文件加载 ==========

    def _refresh_files(self):
        """刷新报告文件列表"""
        self.file_combo.clear()
        report_dir = Path(OUTPUT_DIR)
        if not report_dir.exists():
            return

        json_files = sorted(report_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in json_files:
            self.file_combo.addItem(f.name, str(f))

        if self.file_combo.count() > 0:
            self.load_report(str(json_files[0]))

    def _load_latest_report(self):
        """加载最新的报告"""
        self._refresh_files()

    def _open_report_dir(self):
        """打开报告目录（monitor_reports/）"""
        path = Path(OUTPUT_DIR).resolve()
        if sys.platform == 'win32':
            os.startfile(str(path))
        elif sys.platform == 'darwin':
            subprocess.run(['open', str(path)])
        else:
            subprocess.run(['xdg-open', str(path)])

    def load_report(self, filepath: str):
        """加载并解析一个 JSON 报告文件"""
        try:
            import json as _json
            with open(filepath, 'r', encoding='utf-8') as f:
                self._report_data = _json.load(f)

            self._all_resources = self._report_data.get('all_resources', [])
            self._domain_stats = self._report_data.get('domain_breakdown', [])

            # 更新基本信息
            timing = self._report_data.get('timing', {})
            self.info_url.setText(self._report_data.get('url', '--'))
            self.info_url.setToolTip(self._report_data.get('url', ''))
            self.info_time.setText(self._report_data.get('timestamp', '--'))
            dcl = timing.get('dom_content_loaded_ms', 0)
            load_t = timing.get('load_complete_ms', 0)
            self.info_dcl.setText(f"{dcl:.0f} ms")
            self.info_load.setText(f"{load_t:.0f} ms")
            count = timing.get('resource_count', 0)
            self.info_count.setText(f"{count} 个")

            status = self._report_data.get('status', '')
            if status == 'success':
                self.info_count.setStyleSheet("color: #22c55e; font-weight: bold;")
            else:
                self.info_count.setStyleSheet("color: #ef4444; font-weight: bold;")

            # 更新域名筛选项
        except Exception as e:
            QMessageBox.warning(self, "加载失败", f"无法读取报告文件：\n{e}")
            return

        self._update_domain_filter_options()
        self._populate_table()
        self._update_charts()

    def _on_file_changed(self, index: int):
        """切换报告文件"""
        if index >= 0:
            data = self.file_combo.currentData()
            if data:
                self.load_report(data)

    # ========== 表格 & 排序 ==========

    def _populate_table(self):
        """填充表格数据"""
        resources = self._get_filtered_resources()
        self.resource_table.setRowCount(len(resources))

        for row, r in enumerate(resources):
            idx_item = SortableTableWidgetItem(str(row + 1), sort_key=row + 1)
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            idx_item.setForeground(QColor("#888888"))
            self.resource_table.setItem(row, 0, idx_item)

            name_item = QTableWidgetItem(r.get('name', '')[:120])
            name_item.setToolTip(r.get('name', ''))
            self.resource_table.setItem(row, 1, name_item)

            domain_item = QTableWidgetItem(r.get('domain', ''))
            domain_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.resource_table.setItem(row, 2, domain_item)

            ip_item = QTableWidgetItem(r.get('ip', '--'))
            ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            ip_item.setFont(QFont("Consolas", 9))
            ip_item.setForeground(QColor("#6366f1"))
            ip_item.setToolTip(f"{r.get('domain', '')} → {r.get('ip', '--')}")
            self.resource_table.setItem(row, 3, ip_item)

            type_item = QTableWidgetItem(r.get('type', 'other'))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = self.TYPE_COLORS.get(r.get('type', 'other'), self.TYPE_COLORS['other'])
            type_item.setForeground(QColor(color))
            type_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.resource_table.setItem(row, 4, type_item)

            dur = r.get('duration', 0)
            dur_text = f"{dur:.1f}" if dur > 0 else "--"
            dur_item = SortableTableWidgetItem(dur_text, sort_key=dur if dur > 0 else -1)
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            dur_item.setFont(QFont("Consolas", -1, QFont.Weight.Bold))
            if dur > 2000:
                dur_item.setForeground(QColor("#ef4444"))   # 红色 > 2s
            elif dur > 500:
                dur_item.setForeground(QColor("#f59e0b"))  # 橙色 > 500ms
            else:
                dur_item.setForeground(QColor("#22c55e"))   # 绿色正常
            self.resource_table.setItem(row, 5, dur_item)

            size_item = QTableWidgetItem(r.get('size', '--'))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.resource_table.setItem(row, 6, size_item)

            start_time = r.get('start_time', 0)
            start_item = SortableTableWidgetItem(f"{start_time:.1f}", sort_key=start_time)
            start_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            start_item.setFont(QFont("Consolas", 9))
            self.resource_table.setItem(row, 7, start_item)

        # 应用当前排序
        self.resource_table.sortItems(self._sort_column, self._sort_order)

        # 更新筛选结果计数
        total = len(self._all_resources)
        shown = len(resources)
        self.filter_result_label.setText(f"显示 {shown} / {total} 条记录")

    def _on_header_clicked(self, col_idx: int):
        """点击表头排序"""
        if col_idx == self._sort_column:
            self._sort_order = (
                Qt.SortOrder.AscendingOrder
                if self._sort_order == Qt.SortOrder.DescendingOrder
                else Qt.SortOrder.DescendingOrder
            )
        else:
            self._sort_column = col_idx
            self._sort_order = Qt.SortOrder.DescendingOrder

        self.resource_table.sortItems(col_idx, self._sort_order)

    def _on_item_double_clicked(self, item: QTableWidgetItem):
        """双击复制当前单元格内容"""
        text = item.text()
        if text:
            QApplication.clipboard().setText(text)
            col_header = self.resource_table.horizontalHeaderItem(item.column())
            col_name = col_header.text() if col_header else f"列{item.column()}"
            self.statusTip(f"✅ 已复制 [{col_name}]: {text[:40]}{'...' if len(text) > 40 else ''}")

    # ========== 筛选 ==========

    def _update_domain_filter_options(self):
        """更新域名下拉选项"""
        self.domain_filter.blockSignals(True)
        current_text = self.domain_filter.currentText()
        self.domain_filter.clear()
        self.domain_filter.addItem("全部", None)
        domains = sorted(set(r.get('domain', '') for r in self._all_resources))
        for d in domains:
            if d:
                self.domain_filter.addItem(d, d)
        # 尝试恢复之前的选择
        idx = self.domain_filter.findText(current_text)
        if idx >= 0:
            self.domain_filter.setCurrentIndex(idx)
        self.domain_filter.blockSignals(False)

    def _get_filtered_resources(self) -> List[dict]:
        """根据当前筛选条件返回资源列表"""
        resources = self._all_resources[:]

        # 类型筛选
        type_data = self.type_filter.currentData()
        if type_data:
            resources = [r for r in resources if r.get('type') == type_data]

        # 域名筛选
        domain = self.domain_filter.currentData()
        if domain is not None:
            resources = [r for r in resources if r.get('domain') == domain]

        # 关键字搜索
        keyword = self.search_edit.text().strip().lower()
        if keyword:
            resources = [r for r in resources if keyword in r.get('name', '').lower()]

        return resources

    def _apply_filters(self):
        """应用所有筛选条件并刷新"""
        self._populate_table()
        self._update_charts()

    # ========== 图表 ==========

    def _update_charts(self):
        """更新柱状图和饼图"""
        filtered = self._get_filtered_resources()

        # ---- 域名柱状图 ----
        from collections import defaultdict
        domain_totals = defaultdict(float)
        for r in filtered:
            domain_totals[r.get('domain', 'other')] += max(0, r.get('duration', 0))

        domains_sorted = sorted(domain_totals.items(), key=lambda x: x[1], reverse=True)[:12]
        if domains_sorted:
            names = [d[0][:20] for d in domains_sorted]
            values = [d[1] for d in domains_sorted]
            x_pos = list(range(len(names)))
            self.bar_plot.setOpts(x=x_pos, height=values, width=0.7,
                                 brush='#3b82f6')
            # 清除旧的文本项
            for lbl in self.bar_labels:
                self.bar_chart.removeItem(lbl)
            self.bar_labels.clear()
            # X轴刻度显示域名
            ax = self.bar_chart.getAxis('bottom')
            ticks = [(i, n) for i, n in enumerate(names)]
            ax.setTicks([ticks])
            self.bar_chart.showAxis('bottom')
            self.bar_chart.setXRange(-0.5, len(names) - 0.5)
            ymax = max(values) * 1.25 if values else 100
            self.bar_chart.setYRange(0, max(ymax, 10))
        else:
            self.bar_plot.setOpts(x=[], height=[], width=0.7)
            self.bar_chart.setXRange(0, 1)
            self.bar_chart.setYRange(0, 1)

        # ---- 资源类型柱状图 ----
        type_counts: Dict[str, float] = defaultdict(float)
        for r in filtered:
            t = r.get('type', 'other')
            type_counts[t] += 1

        if type_counts:
            items_sorted = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            names = [t[0] for t in items_sorted]
            values = [t[1] for t in items_sorted]
            x_pos = list(range(len(names)))

            # 使用单色（pyqtgraph 柱状图的列表着色不稳定，统一用蓝色）
            self.type_plot.setOpts(x=x_pos, height=values, width=0.6,
                                   brush='#8b5cf6')

            # 清除旧的文本标签
            for lbl in self.type_labels:
                self.type_chart.removeItem(lbl)
            self.type_labels.clear()

            # 标签放在每根柱子内部底部（文字锚点在上方）
            for i, n in enumerate(names):
                label = pg.TextItem(n, color='white', anchor=(0.5, 0))
                label.setFont(QFont("Consolas", 9))
                label.setPos(i, max(values[i] * 0.05, 1))  # 柱内偏下位置
                self.type_chart.addItem(label)
                self.type_labels.append(label)

            # 显示X轴并设置刻度标签为类型名
            ax = self.type_chart.getAxis('bottom')
            ax.setStyle(tickLength=0, tickFont=None)  # 隐藏默认刻度线
            ticks = [(i, n) for i, n in enumerate(names)]
            ax.setTicks([ticks])

            self.type_chart.setXRange(-0.5, len(names) - 0.5)
            ymax = max(values) * 1.25 if values else 10
            self.type_chart.setYRange(0, max(ymax, 5))
            self.type_chart.showAxis('bottom')  # 确保X轴可见
        else:
            self.type_plot.setOpts(x=[], height=[], width=0.6)
            self.type_chart.setXRange(0, 1)
            self.type_chart.setYRange(0, 1)



# ============================================================
# 主窗口
# ============================================================

class WebMonitorWindow(QMainWindow):
    """主窗口"""

    SITE_FILE = "site.txt"
    DEFAULT_INTERVAL = 10  # 默认检测间隔（秒）

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 网页监控工具 v1.3")
        self.setMinimumSize(1100, 750)

        # 设置窗口图标（内嵌，无需外部文件）
        self.setWindowIcon(_get_embedded_icon())

        # 数据
        self.sites: List[str] = []
        self.site_tabs: Dict[str, SiteTab] = {}
        self.worker_thread: Optional[MonitorWorkerThread] = None
        self.monitor_signals = MonitorSignals()

        # UI 构建
        self._setup_ui()
        self._connect_signals()
        self._load_sites()

        # 应用样式
        self._apply_style()

    def _setup_ui(self):
        """构建主界面"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # ======== 顶部控制区 ========
        control_group = QGroupBox("控制面板")
        control_layout = QHBoxLayout(control_group)

        # Start / Stop 按钮
        self.start_btn = QPushButton("▶ 开始监控")
        self.start_btn.setMinimumHeight(38)
        self.start_btn.setFont(QFont("", 10, QFont.Weight.Bold))
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #22c55e, stop:1 #16a34a);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #16a34a, stop:1 #15803d);
            }
            QPushButton:pressed {
                background: #15803d;
            }
            QPushButton:disabled {
                background: #9ca3af;
            }
        """)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹ 停止监控")
        self.stop_btn.setMinimumHeight(38)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setFont(QFont("", 10, QFont.Weight.Bold))
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ef4444, stop:1 #dc2626);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #dc2626, stop:1 #b91c1c);
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
            QPushButton:disabled {
                background: #9ca3af;
            }
        """)
        control_layout.addWidget(self.stop_btn)

        # 导出数据按钮
        self.export_btn = QPushButton("📥 导出数据")
        self.export_btn.setMinimumHeight(38)
        self.export_btn.setFont(QFont("", 10, QFont.Weight.Bold))
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
        """)
        control_layout.addWidget(self.export_btn)

        # 查看报告按钮
        self.view_report_btn = QPushButton("📊 查看报告")
        self.view_report_btn.setMinimumHeight(38)
        self.view_report_btn.setFont(QFont("", 10, QFont.Weight.Bold))
        self.view_report_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_report_btn.setToolTip(
            "打开资源分析面板\n"
            "查看已收集的资源明细报告\n"
            "支持：排序 / 筛选 / 图表联动"
        )
        self.view_report_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #6d28d9);
            }
            QPushButton:pressed {
                background: #6d28d9;
            }
        """)
        control_layout.addWidget(self.view_report_btn)

        control_layout.addSpacing(20)

        # 并发数设置
        conc_label = QLabel("并发数:")
        conc_label.setFont(QFont("", -1, QFont.Weight.Bold))
        control_layout.addWidget(conc_label)

        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 10)
        self.concurrency_spin.setValue(3)
        self.concurrency_spin.setFixedWidth(70)
        control_layout.addWidget(self.concurrency_spin)

        control_layout.addSpacing(15)

        # 超时时间设置
        timeout_label = QLabel("超时(ms):")
        timeout_label.setFont(QFont("", -1, QFont.Weight.Bold))
        control_layout.addWidget(timeout_label)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1000, 600000)
        self.timeout_spin.setValue(30000)
        self.timeout_spin.setSingleStep(10000)
        self.timeout_spin.setSuffix(" ms")
        self.timeout_spin.setFixedWidth(100)
        control_layout.addWidget(self.timeout_spin)

        control_layout.addSpacing(15)

        # 间隔时间设置
        interval_label = QLabel("间隔(s):")
        interval_label.setFont(QFont("", -1, QFont.Weight.Bold))
        control_layout.addWidget(interval_label)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(3, 86400)  # 最小 3s，最大 24h（86400s）
        self.interval_spin.setValue(self.DEFAULT_INTERVAL)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setFixedWidth(100)
        self.interval_spin.setToolTip("检测间隔（秒），支持 3 ~ 86400（24小时）\n如需更灵活的定时调度，请使用 Cron 模式 →")
        control_layout.addWidget(self.interval_spin)

        # ── Cron 定时调度区域 ──────────────────
        from PySide6.QtWidgets import QFrame

        # Cron 模式开关
        self.cron_mode_check = QPushButton("⏰ Cron")
        self.cron_mode_check.setCheckable(True)
        self.cron_mode_check.setFixedWidth(70)
        self.cron_mode_check.setMinimumHeight(32)
        self.cron_mode_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cron_mode_check.setStyleSheet("""
            QPushButton { background: #2d2d35; color: #9ca3af; border: 1px solid #444; border-radius: 6px; font-weight: bold; }
            QPushButton:checked { background: #2563eb; color: white; border-color: #3b82f6; }
            QPushButton:hover { background: #3d3d45; }
            QPushButton:checked:hover { background: #1d4ed8; }
        """)
        self.cron_mode_check.setToolTip("开启后使用 Cron 表达式进行定时调度\n支持：每 N 小时、每天固定时间、每周等\n适合一天一次或更长周期的场景")
        self.cron_mode_check.toggled.connect(self._on_cron_toggled)
        control_layout.addWidget(self.cron_mode_check)

        # Cron 表达式输入（默认隐藏）
        self.cron_edit = QLineEdit()
        self.cron_edit.setPlaceholderText("cron 表达式，如: 0 8 * * *")
        self.cron_edit.setFixedWidth(150)
        self.cron_edit.setMinimumHeight(32)
        self.cron_edit.setVisible(False)
        self.cron_edit.setToolTip(
            "Cron 表达式格式: 分 时 日 月 周\n"
            "示例:\n"
            "  0 */6 * * *   → 每 6 小时\n"
            "  0 8 * * *     → 每天 08:00\n"
            "  0 0 * * 1     → 每周一 00:00\n"
            "  30 9 1 * *    → 每月 1 号 09:30"
        )
        control_layout.addWidget(self.cron_edit)

        # Cron 预设按钮
        cron_presets = [
            ("每小时", "0 * * * *"),
            ("每6h", "0 */6 * * *"),
            ("每天", "0 8 * * *"),
            ("每周一", "0 0 * * 1"),
        ]
        self.cron_preset_btns = []
        for preset_name, preset_expr in cron_presets:
            btn = QPushButton(preset_name)
            btn.setFixedSize(52, 28)
            btn.setVisible(False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"预设: {preset_expr}")
            btn.clicked.connect(lambda checked, e=preset_expr: self._apply_cron_preset(e))
            btn.setStyleSheet("""
                QPushButton { background: #2a2a32; color: #b0b5c0; border: 1px solid #38383f; border-radius: 4px; font-size: 11px; }
                QPushButton:hover { background: #36363f; color: white; }
            """)
            self.cron_preset_btns.append(btn)
            control_layout.addWidget(btn)

        # Cron 预览标签
        self.cron_preview = QLabel("")
        self.cron_preview.setStyleSheet("color: #22c55e; font-size: 11px;")
        self.cron_preview.setVisible(False)
        control_layout.addWidget(self.cron_preview)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #ccd0da; margin: 0 10px;")
        control_layout.addWidget(sep)

        # 资源分析开关
        profile_label = QLabel("🔍 资源分析:")
        profile_label.setFont(QFont("", -1, QFont.Weight.Bold))
        profile_label.setToolTip("开启后记录每个页面加载的所有资源明细\n输出 JSON 报告到 monitor_reports/ 目录")
        control_layout.addWidget(profile_label)

        self.profile_check = QPushButton("OFF")
        self.profile_check.setCheckable(True)
        self.profile_check.setFixedWidth(60)
        self.profile_check.setMinimumHeight(32)
        self.profile_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.profile_check.setToolTip(
            "开启资源分析模式\n"
            "记录所有加载的资源（图片/CSS/JS/字体等）\n"
            "自动保存为 JSON 报告到 monitor_reports/\n"
            "\n"
            "报告内容:\n"
            "• Top 20 最慢资源\n"
            "• 按域名聚合统计\n"
            "• 全量资源列表（含耗时和大小）"
        )
        self.profile_check.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #374151;
                border: 2px solid #d1d5db;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                padding: 4px;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #f59e0b, stop:1 #d97706);
                color: white;
                border-color: #f59e0b;
            }
            QPushButton:disabled {
                background: #9ca3af;
                color: white;
            }
        """)
        control_layout.addWidget(self.profile_check)

        # 轮次汇总报告开关
        round_label = QLabel("📋 汇总报告:")
        round_label.setFont(QFont("", -1, QFont.Weight.Bold))
        round_label.setToolTip("开启后每轮测试结束后自动生成汇总文件\n包含所有站点的 DOM/LOAD 数据（含失败项）\n输出 CSV + JSON 到 monitor_reports/ 目录")
        control_layout.addWidget(round_label)

        self.round_report_check = QPushButton("OFF")
        self.round_report_check.setCheckable(True)
        self.round_report_check.setFixedWidth(60)
        self.round_report_check.setMinimumHeight(32)
        self.round_report_check.setCursor(Qt.CursorShape.PointingHandCursor)
        self.round_report_check.setToolTip(
            "开启轮次汇总报告\n"
            "每轮测试完成后自动生成汇总文件\n"
            "适合每天定时监控的数据收集场景\n"
            "\n"
            "输出内容:\n"
            "• CSV 简表：域名 / DOM(ms) / LOAD(ms) / 状态\n"
            "• JSON 完整报告：含统计摘要和全部数据\n"
            "\n"
            "无论成功或失败的站点都会被记录"
        )
        self.round_report_check.setStyleSheet("""
            QPushButton {
                background: #e5e7eb;
                color: #374151;
                border: 2px solid #d1d5db;
                border-radius: 16px;
                font-weight: bold;
                font-size: 12px;
                padding: 4px;
            }
            QPushButton:hover {
                background: #d1d5db;
            }
            QPushButton:checked {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border-color: #10b981;
            }
            QPushButton:disabled {
                background: #9ca3af;
                color: white;
            }
        """)
        control_layout.addWidget(self.round_report_check)

        control_layout.addStretch()

        main_layout.addWidget(control_group)

        # ======== 中间 Tab 区域 ========
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setDocumentMode(True)
        main_layout.addWidget(self.tab_widget, stretch=1)

        # ======== 底部日志区域 ========
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        log_layout.addWidget(self.log_text)
        main_layout.addWidget(log_group)

    def _apply_style(self):
        """应用全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background: #eff1f5;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 2px solid #ccd0da;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 8px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                color: #4c4f69;
            }
            QTableWidget {
                gridline-color: #e6e9ef;
                border: 1px solid #ccd0da;
                border-radius: 6px;
                background: #ffffff;
                alternate-background-color: #f5f7fa;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background: #e6e9ef;
                color: #4c4f69;
                font-weight: bold;
                padding: 6px;
                border: 1px solid #ccd0da;
            }
            QTabWidget::pane {
                border: 2px solid #ccd0da;
                border-radius: 10px;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #e6e9ef;
                color: #4c4f69;
                padding: 10px 20px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #1e66f5;
                border-bottom: 3px solid #1e66f5;
            }
            QTabBar::tab:hover:!selected {
                background: #dfdce5;
            }
            QSpinBox {
                padding: 6px;
                border: 2px solid #ccd0da;
                border-radius: 6px;
                background: white;
            }
            QSpinBox:focus {
                border-color: #1e66f5;
            }
        """)

    def _connect_signals(self):
        """连接信号和槽"""
        self.start_btn.clicked.connect(self._on_start)
        self.stop_btn.clicked.connect(self._on_stop)
        self.export_btn.clicked.connect(self._on_export)
        self.view_report_btn.clicked.connect(self._on_view_reports)
        self.profile_check.toggled.connect(self._on_profile_toggled)
        self.round_report_check.toggled.connect(self._on_round_report_toggled)

        # Cron 表达式输入时实时预览
        self.cron_edit.textChanged.connect(self._update_cron_preview)
        self.monitor_signals.record_ready.connect(self._on_record_ready)
        self.monitor_signals.status_update.connect(self._on_status_update)
        self.monitor_signals.log_message.connect(self._append_log)
        self.monitor_signals.stopped.connect(self._on_monitor_stopped)
        self.monitor_signals.profile_saved.connect(self._on_profile_saved)
        self.monitor_signals.round_report_saved.connect(self._on_round_report_saved)

    @staticmethod
    def _normalize_url(url: str) -> str:
        """自动为缺少协议前缀的 URL 补上 https://"""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url

    def _load_sites(self):
        """加载站点列表"""
        site_path = Path(self.SITE_FILE)

        if site_path.exists():
            # 从文件读取
            try:
                content = site_path.read_text(encoding='utf-8').strip()
                self.sites = [self._normalize_url(line) for line in content.split('\n') if line.strip()]
                self._create_tabs()
                self._append_log(f"📄 已从 {self.SITE_FILE} 加载 {len(self.sites)} 个网站")
            except Exception as e:
                self._append_log(f"❌ 读取 site.txt 失败: {e}")
                self._prompt_for_urls()
        else:
            # 弹窗输入
            self._prompt_for_urls()

    def _prompt_for_urls(self):
        """弹窗让用户输入 URL"""
        dialog = UrlInputDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.sites = dialog.urls
            self._save_sites()
            self._create_tabs()
            self._append_log(f"✅ 已添加 {len(self.sites)} 个监控网站")
        else:
            self._append_log("⚠️ 未添加任何网站，请手动编辑 site.txt 后重启程序")

    def _save_sites(self):
        """保存站点列表到文件"""
        try:
            Path(self.SITE_FILE).write_text('\n'.join(self.sites), encoding='utf-8')
        except Exception as e:
            self._append_log(f"❌ 保存 site.txt 失败: {e}")

    def _create_tabs(self):
        """为每个站点创建 Tab"""
        self.tab_widget.clear()
        self.site_tabs.clear()

        for url in self.sites:
            tab = SiteTab(url)
            # 用简短的域名作为 Tab 标签
            from urllib.parse import urlparse
            parsed = urlparse(url)
            label = parsed.hostname or url[:30]
            if len(label) > 25:
                label = label[:22] + "..."

            self.tab_widget.addTab(tab, f"🌐 {label}")
            self.site_tabs[url] = tab

    # ========== 槽函数 ==========

    def _on_start(self):
        """点击开始按钮"""
        if not self.sites:
            QMessageBox.warning(self, "提示", "没有可监控的网站！\n请在 site.txt 中添加URL后重启。")
            return

        # Cron 模式校验
        cron_expr = ""
        if self.cron_mode_check.isChecked():
            cron_expr = self.cron_edit.text().strip()
            parts = cron_expr.split()
            if len(parts) != 5:
                QMessageBox.warning(self, "Cron 格式错误",
                    f"Cron 表达式格式不正确（需要 5 个字段: 分 时 日 月 周）\n当前: '{cron_expr}'\n\n示例: 0 8 * * * （每天8点）")
                return

        # 超时时间 vs 间隔时间合理性检查
        timeout_ms = self.timeout_spin.value()
        interval_sec = self.interval_spin.value() if not self.cron_mode_check.isChecked() else None
        if interval_sec and (timeout_ms / 1000) > interval_sec:
            self._append_log(
                f"⚠️ 超时({timeout_ms / 1000:.0f}s) > 间隔({interval_sec}s)，"
                f"每轮可能连续执行不等待，建议调大间隔或减小超时"
            )

        # 禁用/启用控件
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.concurrency_spin.setEnabled(False)
        self.timeout_spin.setEnabled(False)
        self.interval_spin.setEnabled(False)
        self.profile_check.setEnabled(False)   # 运行中锁定开关
        self.round_report_check.setEnabled(False)  # 运行中锁定开关
        self.cron_mode_check.setEnabled(False)  # 运行中锁定 Cron 开关
        self.cron_edit.setEnabled(False)
        for btn in self.cron_preset_btns:
            btn.setEnabled(False)

        # 启动工作线程
        self.worker_thread = MonitorWorkerThread(
            sites=self.sites,
            signals=self.monitor_signals,
            concurrency=self.concurrency_spin.value(),
            timeout_ms=self.timeout_spin.value(),
            interval_sec=self.interval_spin.value(),
            enable_profiling=self.profile_check.isChecked(),
            cron_expr=cron_expr,
            enable_round_report=self.round_report_check.isChecked()
        )
        self.worker_thread.finished.connect(self._on_thread_finished)
        self.worker_thread.start()

        profiling_status = "🔍 已开启" if self.profile_check.isChecked() else ""
        round_status = "📋 汇总已开启" if self.round_report_check.isChecked() else ""
        extra = " ".join(filter(None, [profiling_status, round_status]))
        self._append_log(f"🎬 正在启动监控... {extra}")

    def _on_stop(self):
        """点击停止按钮"""
        self._append_log("🛑 正在停止监控...")

        if self.worker_thread:
            self.worker_thread.stop()

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.concurrency_spin.setEnabled(True)    # 停止后恢复可调
        self.timeout_spin.setEnabled(True)         # 停止后恢复可调
        self.profile_check.setEnabled(True)        # 停止后恢复可调
        self.round_report_check.setEnabled(True)    # 停止后恢复可调
        self.cron_mode_check.setEnabled(True)      # 恢复 Cron 开关
        self.cron_edit.setEnabled(True)            # 恢复编辑

        # 间隔时间根据 Cron 状态决定是否恢复
        if not self.cron_mode_check.isChecked():
            self.interval_spin.setEnabled(True)

        for btn in self.cron_preset_btns:
            btn.setEnabled(True)

    def _on_record_ready(self, url: str, timestamp: str, dom_load: float, load_time: float, status: str):
        """收到新记录信号"""
        if url in self.site_tabs:
            record = MonitorRecord(
                timestamp=timestamp,
                dom_load=dom_load,
                load_time=load_time,
                status=status
            )
            self.site_tabs[url].add_record(record)

    def _on_status_update(self, url: str, status: str):
        """收到状态更新信号"""
        # 状态更新已在 add_record 中处理，此处可扩展
        pass

    def _append_log(self, message: str):
        """追加日志消息"""
        now = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f"[{now}] {message}")
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_monitor_stopped(self):
        """监控停止信号"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.concurrency_spin.setEnabled(True)
        self.timeout_spin.setEnabled(True)
        self.profile_check.setEnabled(True)
        self.round_report_check.setEnabled(True)
        self.cron_mode_check.setEnabled(True)
        self.cron_edit.setEnabled(True)
        if not self.cron_mode_check.isChecked():
            self.interval_spin.setEnabled(True)
        for btn in self.cron_preset_btns:
            btn.setEnabled(True)
        self._append_log("✅ 监控已完全停止")

    def _on_thread_finished(self):
        """工作线程结束"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.concurrency_spin.setEnabled(True)
        self.timeout_spin.setEnabled(True)
        self.profile_check.setEnabled(True)
        self.round_report_check.setEnabled(True)
        self.cron_mode_check.setEnabled(True)
        self.cron_edit.setEnabled(True)
        if not self.cron_mode_check.isChecked():
            self.interval_spin.setEnabled(True)
        for btn in self.cron_preset_btns:
            btn.setEnabled(True)

    def _on_profile_toggled(self, checked: bool):
        """资源分析开关切换"""
        if checked:
            self.profile_check.setText("ON")
            self._append_log("🔍 资源分析已开启 - 报告将保存到 monitor_reports/ 目录")
        else:
            self.profile_check.setText("OFF")
            self._append_log("🔍 资源分析已关闭")

    def _on_round_report_toggled(self, checked: bool):
        """轮次汇总报告开关切换"""
        if checked:
            self.round_report_check.setText("ON")
            self._append_log("📋 汇总报告已开启 - 每轮测试后自动保存到 monitor_reports/")
        else:
            self.round_report_check.setText("OFF")
            self._append_log("📋 汇总报告已关闭")

    def _on_round_report_saved(self, timestamp: str, file_path: str, total_count: int):
        """轮次汇总报告保存完成"""
        self._append_log(f"📋 汇总已导出 → {Path(file_path).name} ({total_count} 个站点)")

    # ── Cron 定时调度相关方法 ──────────────────

    def _on_cron_toggled(self, checked: bool):
        """Cron 模式开关切换"""
        self.cron_edit.setVisible(checked)
        for btn in self.cron_preset_btns:
            btn.setVisible(checked)
        self.cron_preview.setVisible(checked)
        if checked:
            # 开启 Cron 模式 → 隐藏间隔时间（Cron 自己决定间隔）
            self.interval_spin.setEnabled(False)
            self.interval_spin.setToolTip("已由 Cron 调度接管")
            self._update_cron_preview()
            self._append_log("⏰ Cron 定时模式已开启")
        else:
            self.interval_spin.setEnabled(True)
            self.interval_spin.setToolTip("检测间隔（秒），支持 3 ~ 86400（24小时）\n如需更灵活的定时调度，请使用 Cron 模式 →")
            self.cron_preview.setText("")

    def _apply_cron_preset(self, expr: str):
        """应用预设的 Cron 表达式"""
        self.cron_edit.setText(expr)
        self._update_cron_preview()

    def _update_cron_preview(self):
        """更新 Cron 表达式的自然语言预览"""
        expr = self.cron_edit.text().strip()
        preview = self._cron_to_human(expr)
        self.cron_preview.setText(f"📌 {preview}")
        # 根据是否有效改变颜色
        if expr and len(expr.split()) == 5:
            self.cron_preview.setStyleSheet("color: #22c55e; font-size: 11px;")
        else:
            self.cron_preview.setStyleSheet("color: #f59e0b; font-size: 11px;")

    @staticmethod
    def _cron_to_human(expr: str) -> str:
        """将 Cron 表达式翻译成中文自然语言描述"""
        expr = expr.strip()
        if not expr:
            return "单次运行（不重复）"
        parts = expr.strip().split()
        if len(parts) != 5:
            return f"自定义表达式: {expr}"

        minute, hour, dom, month, dow = parts

        # 每 N 分钟
        m = __import__('re').match(r'^\*/(\d+)$', minute)
        if m and hour == "*" and dom == "*" and month == "*" and dow == "*":
            n = int(m.group(1))
            return f"每隔 {n} 分钟执行一次"

        # 每小时第 N 分
        m = __import__('re').match(r'^(\d+)$', minute)
        if m and hour == "*" and dom == "*" and month == "*" and dow == "*":
            return f"每小时第 {m.group(1)} 分钟"

        # 每天 H:M
        mm = __import__('re').match(r'^(\d+)$', minute)
        hm = __import__('re').match(r'^(\d+)$', hour)
        if mm and hm and dom == "*" and month == "*" and dow == "*":
            return f"每天 {hm.group(1)}:{int(mm.group(1)):02d}"

        # 每隔 N 小时
        if minute == "0":
            hm2 = __import__('re').match(r'^\*/(\d+)$', hour)
            if hm2 and dom == "*" and month == "*" and dow == "*":
                return f"每隔 {hm2.group(1)} 小时"

        # 每周几 H:M
        mm = __import__('re').match(r'^(\d+)$', minute)
        hm = __import__('re').match(r'^(\d+)$', hour)
        dm = __import__('re').match(r'^(\d)$', dow)
        DOW_CN = {"0": "周日", "1": "周一", "2": "周二", "3": "周三", "4": "周四", "5": "周五", "6": "周六", "7": "周日"}
        if mm and hm and dm and dom == "*" and month == "*":
            return f"每{DOW_CN.get(dm.group(1), '周' + dm.group(1))} {hm.group(1)}:{int(mm.group(1)):02d}"

        return f"自定义计划: {expr}"

    def _on_profile_saved(self, url: str, timestamp: str, file_path: str, resource_count: int):
        """资源报告保存完成"""
        from urllib.parse import urlparse
        hostname = urlparse(url).hostname or url[:20]
        filename = os.path.basename(file_path)
        self._append_log(
            f"📊 [{hostname}] 资源报告已保存: {filename} ({resource_count} 个资源)"
        )

    def _on_view_reports(self):
        """打开资源分析面板（完全独立的 Windows 窗口）"""
        # 不传 parent，让报告窗口成为完全独立的顶级窗口
        self.report_viewer = ReportViewerDialog(parent=None)
        self.report_viewer.show()

    def _on_export(self):
        """
        导出所有站点的监控数据为 CSV 文件
        每个网站一个 sheet（用文件名区分）
        或合并导出为一个 CSV（每个站点一个 section）
        """
        if not self.site_tabs:
            QMessageBox.information(self, "提示", "没有可导出的数据！\n请先启动监控收集一些数据。")
            return

        # 检查是否有任何数据
        total_records = sum(len(tab.records) for tab in self.site_tabs.values())
        if total_records == 0:
            QMessageBox.information(self, "提示", "当前没有任何监控记录！\n请先点击「开始监控」采集数据。")
            return

        # 弹出保存对话框
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"monitor_data_{timestamp}.csv"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出监控数据",
            default_name,
            "CSV 文件 (*.csv);;所有文件 (*)"
        )

        if not file_path:
            return  # 用户取消

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)

                for url, tab in self.site_tabs.items():
                    # 所有站点都保留，即使没有记录或只有失败记录
                    from urllib.parse import urlparse
                    hostname = urlparse(url).hostname or url[:30]

                    # 写 section 标题
                    writer.writerow([f"=== {hostname} ({url}) ==="])
                    writer.writerow([])  # 空行

                    # 写表头（4列）
                    writer.writerow(["时间 (Time)", "DOM Content (ms)", "Load (ms)", "状态 (Status)"])

                    # 写数据行（所有记录，含失败/超时）
                    if tab.records:
                        for record in tab.records:
                            dom_str = f"{record.dom_load:.0f}" if record.dom_load >= 0 else "--"
                            load_str = f"{record.load_time:.0f}" if record.load_time >= 0 else "--"
                            writer.writerow([record.timestamp, dom_str, load_str, record.status.upper()])
                    else:
                        writer.writerow(["(暂无监控记录)", "--", "--", "--"])

                    # 统计摘要（双指标）
                    success_records = [r for r in tab.records if r.status == "success" and r.dom_load > 0]
                    if success_records:
                        avg_dcl = sum(r.dom_load for r in success_records) / len(success_records)
                        min_dcl = min(r.dom_load for r in success_records)
                        max_dcl = max(r.dom_load for r in success_records)
                        avg_load = sum(r.load_time for r in success_records) / len(success_records)
                        min_load = min(r.load_time for r in success_records)
                        max_load = max(r.load_time for r in success_records)
                        writer.writerow([])
                        writer.writerow([f"--- 统计: 共{len(tab.records)}条 | 成功{len(success_records)}条 ---"])
                        writer.writerow([f"    DCL: 平均 {avg_dcl:.0f}ms | 最小 {min_dcl:.0f}ms | 最大 {max_dcl:.0f}ms"])
                        writer.writerow([f"    Load: 平均 {avg_load:.0f}ms | 最小 {min_load:.0f}ms | 最大 {max_load:.0f}ms"])

                    writer.writerow([])  # 站点间空行分隔

            self._append_log(f"💾 数据已导出: {os.path.basename(file_path)} "
                            f"(共 {total_records} 条记录, {len(self.site_tabs)} 个站点)")
            QMessageBox.information(
                self, "导出成功",
                f"✅ 已成功导出！\n\n"
                f"📁 文件：{file_path}\n"
                f"📊 记录数：{total_records} 条\n"
                f"🌐 站点数：{len(self.site_tabs)} 个（含失败/无数据站点）"
            )

        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"❌ 导出过程中出错：\n{e}")
            self._append_log(f"❌ 导出失败: {e}")

    def closeEvent(self, event):
        """窗口关闭时的清理操作"""
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, '确认退出',
                '监控正在运行中，确定要退出吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker_thread.stop()
                self.worker_thread.wait(5000)  # 等待最多5秒
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ============================================================
# 程序入口
# ============================================================

def main():
    """主函数"""
    # 高DPI支持
    if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    app = QApplication(sys.argv)
    app.setApplicationName("网页监控工具")
    app.setStyle('Fusion')  # 使用 Fusion 风格以获得更一致的跨平台外观

    window = WebMonitorWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
