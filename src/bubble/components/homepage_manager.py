"""
主页管理器 (Homepage Manager)

该模块负责管理 Bubble 应用的主页功能，包括：
- AI平台选择界面
- 用户首次启动时的AI选择提示
- AI平台的增删功能
- 用户配置的保存和加载

主页管理器复用现有的窗口创建和UI逻辑，提供用户友好的AI平台管理体验。
"""

import os
import json
from typing import Dict, List, Optional
import objc
from Foundation import NSObject, NSUserDefaults
from .config_manager import ConfigManager
from ..i18n import t as _t


class HomepageManager(NSObject):
    """
    主页管理器类
    
    负责管理应用主页的所有功能，包括AI平台选择、配置管理、
    以及与用户的交互流程。
    """
    
    def init(self):
        """初始化主页管理器"""
        self = objc.super(HomepageManager, self).init()
        if self is None:
            return None
        self.user_defaults = NSUserDefaults.standardUserDefaults()
        # Use centralized config path (migrated location)
        try:
            self.config_file_path = ConfigManager.config_path()
        except Exception:
            self.config_file_path = os.path.expanduser("~/Library/Application Support/Bubble/config.json")
        self.default_ai_platforms = {
            "openai": {
                "name": "ChatGPT",
                "url": "https://chat.openai.com",
                "display_name": "OpenAI ChatGPT",
                "enabled": True,
                "max_windows": 5
            },
            "gemini": {
                "name": "Gemini", 
                "url": "https://gemini.google.com",
                "display_name": "Google Gemini",
                "enabled": True,
                "max_windows": 5
            },
            "grok": {
                "name": "Grok",
                "url": "https://grok.com", 
                "display_name": "xAI Grok",
                "enabled": True,
                "max_windows": 5
            },
            "claude": {
                "name": "Claude",
                "url": "https://claude.ai/chat",
                "display_name": "Anthropic Claude", 
                "enabled": True,
                "max_windows": 5
            },
            "deepseek": {
                "name": "DeepSeek",
                "url": "https://chat.deepseek.com",
                "display_name": "DeepSeek AI",
                "enabled": True,
                "max_windows": 5
            },
            "zai": {
                "name": "GLM",
                "url": "https://chat.z.ai/",
                "display_name": "GLM",
                "enabled": False,
                "max_windows": 5
            },
            "mistral": {
                "name": "Mistral",
                "url": "https://chat.mistral.ai",
                "display_name": "Mistral",
                "enabled": False,
                "max_windows": 5
            },
            "perplexity": {
                "name": "Perplexity",
                "url": "https://www.perplexity.ai",
                "display_name": "Perplexity",
                "enabled": False,
                "max_windows": 5
            },
            "qwen": {
                "name": "Qwen",
                "url": "https://chat.qwen.ai/", 
                "display_name": "Qwen",
                "enabled": False,
                "max_windows": 5
            },
            "kimi": {
                "name": "Kimi",
                "url": "https://www.kimi.com/",
                "display_name": "Kimi",
                "enabled": False,
                "max_windows": 5
            }
        }
        self._ensure_config_directory()
        self._load_user_config()
        # Runtime-only flag：调试用，强制显示一次导览
        self._force_tour_once = False
        # 尝试加载内置logo为 data URL，供主页展示
        try:
            self._load_logo_data_url()
        except Exception:
            self.logo_data_url = None
        return self

    def on_language_changed(self):
        """Hook for language change; homepage will be re-rendered on next load."""
        # No persistent state to update here; UI will rebuild via AppDelegate._load_homepage()
        return True

    def _load_logo_data_url(self):
        import base64
        import pkgutil
        # Try pkg data first (py2app zip-safe)
        for name in (
            'logo/icon.iconset/icon_64x64.png',
            'logo/icon.iconset/icon_128x128.png',
            'logo/icon.iconset/icon_32x32.png',
        ):
            try:
                data = pkgutil.get_data('bubble', name)
                if data:
                    b64 = base64.b64encode(data).decode('ascii')
                    self.logo_data_url = f"data:image/png;base64,{b64}"
                    return
            except Exception:
                pass
        # Fallback to filesystem in dev
        # components/ -> package root (../)
        base = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        for p in (
            os.path.join(base, 'logo', 'icon.iconset', 'icon_64x64.png'),
            os.path.join(base, 'logo', 'icon.iconset', 'icon_128x128.png'),
            os.path.join(base, 'logo', 'icon.iconset', 'icon_32x32.png'),
        ):
            if os.path.exists(p):
                with open(p, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode('ascii')
                self.logo_data_url = f"data:image/png;base64,{b64}"
                return
        self.logo_data_url = None
    
    def _ensure_config_directory(self):
        """确保配置目录存在"""
        config_dir = os.path.dirname(self.config_file_path)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
    
    def _load_user_config(self):
        """加载用户配置"""
        try:
            if os.path.exists(self.config_file_path):
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    self.user_config = json.load(f)
            else:
                # 首次启动，创建默认配置
                self.user_config = {
                    "default_ai": None,  # 用户首次启动时需要选择
                    "enabled_platforms": [],  # 首次启动不启用任何平台
                    "window_positions": {},
                    "ui_preferences": {
                        "transparency": 1.0,
                        "show_homepage_on_startup": True,
                        "hide_memory_bubble": False
                    },
                    "platform_windows": {}  # 记录每个平台的窗口信息
                }
                self._save_user_config()
        except Exception as e:
            print(f"加载用户配置失败，使用默认配置: {e}")
            self.user_config = {
                "default_ai": None,
                "enabled_platforms": [],  # 首次启动不启用任何平台
                "window_positions": {},
                "ui_preferences": {
                    "transparency": 1.0,
                    "show_homepage_on_startup": True,
                    "hide_memory_bubble": False
                },
                "platform_windows": {}
            }
    
    def _save_user_config(self):
        """保存用户配置"""
        try:
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存用户配置失败: {e}")
    
    def is_first_launch(self) -> bool:
        """检查是否为首次启动"""
        return self.user_config.get("default_ai") is None

    def should_show_homepage_on_startup(self) -> bool:
        """是否在启动时显示主页（由用户偏好控制，默认 True）"""
        try:
            return bool(self.user_config.get("ui_preferences", {}).get("show_homepage_on_startup", True))
        except Exception:
            return True
    
    def get_enabled_platforms(self) -> Dict[str, Dict]:
        """获取已启用的AI平台列表"""
        enabled = {}
        for platform_id in self.user_config.get("enabled_platforms", []):
            if platform_id in self.default_ai_platforms:
                enabled[platform_id] = self.default_ai_platforms[platform_id].copy()
        return enabled
    
    def get_available_platforms(self) -> Dict[str, Dict]:
        """获取所有可用的AI平台列表"""
        return self.default_ai_platforms.copy()
    
    def add_platform(self, platform_id: str) -> bool:
        """
        添加AI平台到用户配置
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 添加是否成功
        """
        if platform_id not in self.default_ai_platforms:
            print(f"不支持的平台: {platform_id}")
            return False
        
        if platform_id not in self.user_config.get("enabled_platforms", []):
            # 默认不限制启用平台数量
            self.user_config.setdefault("enabled_platforms", []).append(platform_id)
            self._save_user_config()
            return True
        
        print(f"平台 {platform_id} 已经启用")
        return False
    
    def remove_platform(self, platform_id: str) -> bool:
        """
        从用户配置中移除AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 移除是否成功
        """
        if platform_id in self.user_config.get("enabled_platforms", []):
            self.user_config["enabled_platforms"].remove(platform_id)
            # 同时清理该平台的窗口信息
            if platform_id in self.user_config.get("platform_windows", {}):
                del self.user_config["platform_windows"][platform_id]
            self._save_user_config()
            return True
        
        print(f"平台 {platform_id} 未启用")
        return False
    
    def set_default_ai(self, platform_id: str) -> bool:
        """
        设置默认AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 设置是否成功
        """
        if platform_id in self.default_ai_platforms:
            self.user_config["default_ai"] = platform_id
            # 确保默认AI在启用列表中
            if platform_id not in self.user_config.get("enabled_platforms", []):
                self.add_platform(platform_id)
            self._save_user_config()
            return True
        
        print(f"不支持的平台: {platform_id}")
        return False
    
    def get_default_ai(self) -> Optional[str]:
        """获取默认AI平台"""
        return self.user_config.get("default_ai")
    
    def add_platform_window(self, platform_id: str, window_id: str, window_info: Dict) -> bool:
        """
        为平台添加新窗口
        
        Args:
            platform_id: 平台标识符
            window_id: 窗口标识符
            window_info: 窗口信息
            
        Returns:
            bool: 添加是否成功
        """
        if platform_id not in self.default_ai_platforms:
            return False
        
        platform_windows = self.user_config.setdefault("platform_windows", {})
        platform_windows.setdefault(platform_id, {})
        
        # 默认不限制同一平台窗口数量，由上层通过内存提示进行引导
        platform_windows[platform_id][window_id] = window_info
        self._save_user_config()
        return True
    
    def remove_platform_window(self, platform_id: str, window_id: str) -> bool:
        """
        移除平台窗口
        
        Args:
            platform_id: 平台标识符
            window_id: 窗口标识符
            
        Returns:
            bool: 移除是否成功
        """
        platform_windows = self.user_config.get("platform_windows", {})
        if platform_id in platform_windows and window_id in platform_windows[platform_id]:
            del platform_windows[platform_id][window_id]
            # 如果该平台没有窗口了，清理空字典
            if not platform_windows[platform_id]:
                del platform_windows[platform_id]
            self._save_user_config()
            return True
        
        return False
    
    def get_platform_windows(self, platform_id: str) -> Dict[str, Dict]:
        """获取指定平台的所有窗口"""
        return self.user_config.get("platform_windows", {}).get(platform_id, {})
    
    def get_all_windows(self) -> Dict[str, Dict[str, Dict]]:
        """获取所有平台的窗口信息"""
        return self.user_config.get("platform_windows", {})
    
    def get_total_window_count(self) -> int:
        """获取总窗口数量"""
        total = 0
        for platform_windows in self.user_config.get("platform_windows", {}).values():
            total += len(platform_windows)
        return total

    # MARK: - 首次使用引导（homepage 导览）
    def should_show_homepage_tour(self) -> bool:
        """是否需要显示主页导览（仅显示一次）。"""
        try:
            ui = self.user_config.get("ui_preferences", {})
            # 未设置或显式为 False 时显示
            return not bool(ui.get("homepage_tour_done", False))
        except Exception:
            return True

    def request_force_homepage_tour(self) -> None:
        """请求在下一次主页渲染时强制显示一次导览（不改持久化配置）。"""
        try:
            self._force_tour_once = True
        except Exception:
            pass

    def consume_force_homepage_tour(self) -> bool:
        """消费一次强制导览标志。返回 True 表示本次应强制显示，并重置标志。"""
        try:
            if getattr(self, '_force_tour_once', False):
                self._force_tour_once = False
                return True
        except Exception:
            pass
        return False

    def mark_homepage_tour_done(self) -> None:
        """标记主页导览已完成并持久化。"""
        try:
            ui = self.user_config.setdefault("ui_preferences", {})
            ui["homepage_tour_done"] = True
            self._save_user_config()
        except Exception as _e:
            print(f"保存主页导览完成状态失败: {_e}")
    
    def can_add_window(self) -> bool:
        """检查是否还能添加新窗口

        注：调整策略以允许超过5个页面常驻，后续通过 UI 气泡提示占用内存风险。
        """
        return True
    
    def show_homepage(self):
        """显示主页（统一使用新版行样式）。"""
        return self._show_platform_management_rows()

    def _show_platform_management_rows(self) -> str:
        """横条风格主页：一行一平台，点击行切换启用；右侧省略号可“重复添加”；气泡展示多页面数量并可删除。

        同时在顶部显示品牌区（包含 Bubble logo），保证开发与打包后显示一致：
        - 优先使用打包资源（pkgutil.get_data）生成 data URL
        - 开发模式回退到文件系统路径（src/bubble/logo/...）
        """
        enabled = self.get_enabled_platforms()
        available = self.get_available_platforms()
        # Load local driver.js/css text for inline embedding (fallback to CDN when empty)
        def _read_asset_text(rel: str) -> str:
            try:
                import pkgutil
                data = pkgutil.get_data('bubble', rel)
                if data:
                    return data.decode('utf-8', 'ignore')
            except Exception:
                pass
            # dev filesystem fallback
            try:
                base = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
                p = os.path.join(base, rel)
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        return f.read()
            except Exception:
                pass
            return ''
        self._driver_css_text = _read_asset_text('assets/vendor/driver.js/driver.min.css')
        self._driver_js_text = _read_asset_text('assets/vendor/driver.js/driver.min.js')
        # helpers used in HTML template
        def _get_driver_css():
            return self._driver_css_text or ''
        def _get_driver_js_json():
            try:
                import json as _json
                return _json.dumps(self._driver_js_text or '')
            except Exception:
                return '""'
        # expose helpers to f-string via bound methods
        self._get_driver_css = _get_driver_css
        self._get_driver_js_json = _get_driver_js_json
        # 选择一个用于导览的首个平台（用于定位示例元素）
        try:
            tour_first_pid = next(iter(available.keys())) if available else "openai"
        except Exception:
            tour_first_pid = "openai"
        def _windows_list(pid):
            m = self.get_platform_windows(pid)
            items = list(m.items())
            try:
                items.sort(key=lambda kv: kv[1].get('createdAt',''))
            except Exception:
                pass
            arr = []
            for idx,(wid,_) in enumerate(items, start=1):
                arr.append({"id": wid, "idx": idx})
            return arr
        import json as _json
        rows = ""
        for pid, info in available.items():
            is_on = pid in enabled
            wl = _windows_list(pid)
            wcnt = len(wl)
            # 始终渲染按钮与气泡（隐藏时保留占位，避免布局抖动）
            # 省略号在平台启用时始终可见（即便为0页也可“新建页面”）
            # 将省略号替换为加号；选中卡片后显示加号，未选中隐藏
            more_btn = f'<button class="more{("" if is_on else " hidden")}">+</button>'
            # 首次添加也要有反馈：>=1 显示气泡
            bubble = f'<span class="bubble{("" if wcnt>=1 else " hidden")}">{wcnt}</span>'
            # 本地化名称（简洁）
            try:
                title_txt = _t(f'platform.{pid}', default=info.get('display_name') or info.get('name') or pid.title())
            except Exception:
                title_txt = info.get('display_name') or info.get('name') or pid.title()
            # 特殊：mistral/perplexity 仅首字母大写
            if pid in ("mistral", "perplexity"):
                try:
                    title_txt = str(title_txt).capitalize()
                except Exception:
                    pass
            # 平台描述（优势）
            _desc_defaults = {
                'openai': '通用对话，生态丰富',
                'gemini': '多模态理解与生成',
                'grok': '实时信息与风趣回复',
                'claude': '长文本与安全对话',
                'deepseek': '高性价比与中文友好',
                'zai': '中文理解与推理',
                'qwen': '中文与工具调用',
                'mistral': '轻量快速与高效',
                'perplexity': '搜索增强问答',
                'kimi': '长文档阅读与总结',
            }
            try:
                sub_txt = _t(f'platform.desc.{pid}', default=_desc_defaults.get(pid, ''))
            except Exception:
                sub_txt = _desc_defaults.get(pid, '')
            # icon：仅使用打包资源，转为 data URL（避免 WKWebView 对 file:// 的限制）
            icon_src = ''
            try:
                import pkgutil, base64
                data = pkgutil.get_data('bubble', f'assets/icons/{pid}.png')
                if data:
                    icon_src = 'data:image/png;base64,' + base64.b64encode(data).decode('ascii')
            except Exception:
                icon_src = ''
            if not icon_src:
                try:
                    import base64
                    base = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
                    p = os.path.join(base, 'assets', 'icons', f'{pid}.png')
                    if os.path.exists(p):
                        with open(p, 'rb') as f:
                            icon_src = 'data:image/png;base64,' + base64.b64encode(f.read()).decode('ascii')
                except Exception:
                    icon_src = ''
            icon_html = f"<img class=\"icon\" src=\"{icon_src}\" alt=\"\">" if icon_src else ""
            rows += f"""
            <div id=\"row-{pid}\" class=\"hrow{' active' if is_on else ''}\" data-pid=\"{pid}\" data-windows='{_json.dumps(wl)}'>
              <div class=\"title\">{icon_html}<span class=\"name\">{title_txt}</span><span class=\"desc\">{sub_txt}</span></div>
              <div class=\"right\">{bubble}{more_btn}</div>
            </div>
            """
        html = f"""
        <!DOCTYPE html>
        <html lang=\"zh-CN\">
        <head>
            <meta charset=\"UTF-8\"> 
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1, maximum-scale=1\">
            <title>Bubble</title>
            <!-- driver.js 样式：优先内嵌本地版本，失败则使用 CDN 兜底 -->
            <style id=\"driverjs-css\">{self._get_driver_css()}</style>
            <style>
                :root {{ --bg:#fafafa; --card:#fff; --border:#eaeaea; --text:#111; --muted:#666; --accent:#111; --radius:12px; --rightW:64px; }}
                * {{ box-sizing: border-box; }}
                body {{ margin:0; padding:56px 14px 14px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'Noto Sans',sans-serif; background:var(--bg); color:var(--text); overflow-x:hidden; }}
                /* 容器宽度：在小窗口时保留左右留空；去掉过大的最小宽度限制，最大≈888 */
                .list {{ width: calc(100% - 40px); max-width: 888px; margin:0 auto; display:flex; flex-direction:column; gap:10px; }}
                /* 卡片占满容器宽度，限定最小高度；高度/内边距随窗口高度线性放大（无阈值跳变） */
                .hrow {{ position:relative; overflow:hidden; display:flex; align-items:center; justify-content:flex-start; background:var(--card); border:1px solid var(--border); border-radius:12px; padding: calc(12px * var(--vhScale, 1)) 14px; padding-right: calc(14px + var(--rightW)); cursor:pointer; transition: box-shadow .18s ease, border-color .18s ease; width:100%; margin:0 auto; min-height: calc(48px * var(--vhScale, 1)); will-change: box-shadow; backface-visibility:hidden; pointer-events:auto; box-sizing:border-box; }}
                .hrow:hover {{ box-shadow:0 10px 26px rgba(0,0,0,.08); }}
                .hrow.active {{ border-color:#111; box-shadow:0 0 0 2px rgba(17,17,17,.18); }}
                .hrow .title {{ font-size:14px; font-weight:600; display:flex; align-items:center; gap:10px; flex:1; min-width:0; }}
                .hrow .title .icon {{ width:16px; height:16px; border-radius:4px; object-fit:cover; }}
                .hrow .title .name {{ display:inline-block; max-width:46%; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
                .hrow .title .desc {{ margin-left:10px; font-weight:500; font-size:12px; color:#6b7280; opacity:.95; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; min-width:0; text-align:center; }}
                .hrow .right {{ position:absolute; right:14px; top:50%; transform:translateY(-50%); width:var(--rightW); display:flex; align-items:center; gap:6px; justify-content:flex-end; overflow:hidden; }}
                .hrow .more {{ display:inline-flex; align-items:center; justify-content:center; width:18px; height:18px; border-radius:999px; border:1px solid var(--border); background:#fff; cursor:pointer; font-size:14px; line-height:1; }}
                .hrow .bubble {{ display:inline-flex; align-items:center; justify-content:center; width:auto; min-width:18px; height:18px; padding:0 6px; border-radius:999px; background:#111; color:#fff; font-size:10px; font-weight:600; }}
                /* 在超小宽度下略微收窄容器并减小左右内边距，确保右侧留空 */
                @media (max-width: 420px) {{
                    body {{ padding:56px 12px 12px; }}
                    .list {{ width: calc(100% - 36px); }}
                }}
                .hidden {{ visibility:hidden; opacity:0; }}
                .ripple {{ position:absolute; border-radius:50%; transform:scale(0); background:rgba(0,0,0,.12); animation:ripple .45s ease-out; pointer-events:none; }}
                @keyframes ripple {{ to {{ transform:scale(1); opacity:0; }} }}
                .menu {{ position:absolute; background:#fff; border:1px solid var(--border); border-radius:8px; box-shadow:0 12px 28px rgba(0,0,0,.16); padding:6px; display:none; }}
                .menu .item {{ font-size:12px; padding:6px 10px; border-radius:6px; cursor:pointer; }}
                .menu .item:hover {{ background:#f5f5f5; }}
                .popover {{ position:absolute; background:#fff; border:1px solid var(--border); border-radius:10px; box-shadow:0 12px 28px rgba(0,0,0,.16); padding:8px; display:none; min-width:140px; }}
                .pop-title {{ font-size:12px; color:#444; margin:0 0 6px; }}
                .pop-item {{ display:flex; align-items:center; justify-content:space-between; padding:4px 6px; border-radius:6px; }}
                .pop-item:hover {{ background:#f7f7f7; }}
                .pop-del {{ width:18px; height:18px; border-radius:999px; background:#ef4444; color:#fff; display:inline-flex; align-items:center; justify-content:center; font-weight:700; cursor:pointer; }}

                /* DaisyUI Skeleton */
                .skeleton {{ position: relative; overflow: hidden; background: #e5e7eb; border-radius: 8px; }}
                .skeleton::after {{ content: ""; position: absolute; inset: 0; transform: translateX(-100%); background: linear-gradient(90deg, transparent, rgba(255,255,255,0.55), transparent); animation: sk-shine 1.2s infinite; }}
                @keyframes sk-shine {{ 100% {{ transform: translateX(100%); }} }}
                /* 显示品牌区，确保与打包一致 */
                /* driver.js 样式美化 + 控件精简（兼容旧版选择器 #driver-popover-item 与新版 .driver-popover） */
                .driver-popover, div#driver-popover-item {{ border-radius: 12px !important; box-shadow: 0 12px 28px rgba(0,0,0,.18) !important; border:1px solid var(--border) !important; text-align:center !important; }}
                /* 有选择性地隐藏 prev/close（不要隐藏所有按钮，避免气泡消失） */
                .driver-popover .driver-prev-btn,
                .driver-popover .driver-close-btn,
                div#driver-popover-item .driver-popover-footer .driver-prev-btn,
                div#driver-popover-item .driver-popover-footer .driver-close-btn {{ display: none !important; }}
                /* 只保留 next/done 并居中 */
                .driver-popover .driver-next-btn, .driver-popover .driver-done-btn,
                div#driver-popover-item .driver-popover-footer .driver-next-btn, div#driver-popover-item .driver-popover-footer .driver-done-btn {{
                    background: #111 !important; color: #fff !important; border: 1px solid #111 !important; border-radius: 8px !important;
                    box-shadow: 0 4px 10px rgba(0,0,0,.12) !important; transition: transform .06s ease, box-shadow .12s ease, background .12s ease;
                    display: inline-flex !important; margin: 0 auto !important; float: none !important;
                }}
                .driver-popover .driver-next-btn:hover, .driver-popover .driver-done-btn:hover,
                div#driver-popover-item .driver-popover-footer .driver-next-btn:hover, div#driver-popover-item .driver-popover-footer .driver-done-btn:hover {{ background:#000 !important; }}
                .driver-popover .driver-next-btn:active, .driver-popover .driver-done-btn:active,
                div#driver-popover-item .driver-popover-footer .driver-next-btn:active, div#driver-popover-item .driver-popover-footer .driver-done-btn:active {{ transform: translateY(1px) scale(.98); box-shadow: 0 2px 6px rgba(0,0,0,.12) !important; }}
                /* 居中 footer */
                div#driver-popover-item .driver-popover-footer {{ text-align:center !important; }}
                /* 让周围更暗、突出高亮区域，并设置高亮圆角 */
                div#driver-page-overlay {{ opacity: .65 !important; background: #000 !important; }}
                div#driver-highlighted-element-stage {{ border-radius: 12px !important; box-shadow: 0 10px 30px rgba(0,0,0,.22) !important; }}
            </style>
        </head>
        <body>
            <div class=\"list\">{rows}</div>
            <div id=\"menu\" class=\"menu\"><div class=\"item\" data-action=\"duplicate\">重复添加</div></div>
            <div id=\"popover\" class=\"popover\"></div>
        """
        # 注入脚本：先写入公用工具与事件，再加入导览逻辑（依赖变量）
        html += """
            <script>
                // 注：统一采用内置简易导览（不加载 driver.js），避免 DOM 差异引入歧义
                // 让卡片高度随窗口高度线性缩放（无阈值跳变）
                (function(){
                    const root = document.documentElement;
                    if (!root.style.getPropertyValue('--vhBase')) {
                        root.style.setProperty('--vhBase', String(window.innerHeight||600));
                    }
                    function applyScale(){
                        var base = parseFloat(getComputedStyle(root).getPropertyValue('--vhBase')) || (window.innerHeight||600);
                        var s = (window.innerHeight||base) / base;
                        if (!isFinite(s) || s <= 0) s = 1;
                        // 限制最大放大倍数（更大：1.8），避免过高造成滚动
                        s = Math.max(1, Math.min(1.8, s));
                        root.style.setProperty('--vhScale', s.toFixed(4));
                    }
                    applyScale();
                    window.addEventListener('resize', applyScale, {passive:true});
                })();
                const $ = (s, r=document)=>r.querySelector(s);
                const $$ = (s, r=document)=>Array.from(r.querySelectorAll(s));
                const post = (obj)=>{ if (window.webkit&&window.webkit.messageHandlers&&window.webkit.messageHandlers.aiAction) window.webkit.messageHandlers.aiAction.postMessage(obj); };
                const menu = $('#menu');
                const pop = $('#popover');
                $$('.hrow').forEach(row=>{
                    // Ripple on mousedown
                    row.addEventListener('mousedown', e=>{
                        const rect = row.getBoundingClientRect();
                        const ripple = document.createElement('span');
                        const d = Math.max(rect.width, rect.height) * 1.2;
                        ripple.className = 'ripple';
                        ripple.style.width = ripple.style.height = d + 'px';
                        ripple.style.left = (e.clientX - rect.left - d/2) + 'px';
                        ripple.style.top = (e.clientY - rect.top - d/2) + 'px';
                        row.appendChild(ripple);
                        ripple.addEventListener('animationend', ()=> ripple.remove());
                    }, {passive:true});
                    row.addEventListener('click', e=>{
                        if (e.target.classList.contains('more') || e.target.closest('button.more')) return;
                        const pid = row.dataset.pid;
                        // 先本地过渡高亮/取消，保持高度不变
                        if (row.classList.contains('active')) {
                            row.classList.remove('active');
                            // 同步右侧控件（保留占位），避免移位
                            const btn = row.querySelector('button.more'); if (btn) btn.classList.add('hidden');
                            const b = row.querySelector('.bubble'); if (b) { b.textContent = '0'; b.classList.add('hidden'); }
                            setTimeout(()=>post({action:'removePlatform', platformId: pid}), 120);
                        } else {
                            row.classList.add('active');
                            const btn = row.querySelector('button.more'); if (btn) btn.classList.remove('hidden');
                            setTimeout(()=>post({action:'addPlatform', platformId: pid}), 120);
                        }
                    });
                    const btn = row.querySelector('button.more');
                    if (btn) {
                        btn.addEventListener('click', e=>{
                            e.stopPropagation();
                            const pid = row.dataset.pid;
                            // 点击加号：直接新增页面，并即时+1显示
                            post({action:'addWindow', platformId: pid});
                            try {
                                const b = row.querySelector('.bubble');
                                if (b) {
                                    const raw = (b.textContent||'0').trim();
                                    const cur = raw.endsWith('+') ? 9 : Math.max(0, parseInt(raw||'0', 10));
                                    const next = cur + 1;
                                    b.textContent = next > 9 ? '9+' : String(next);
                                    b.classList.remove('hidden');
                                }
                            } catch(_e){}
                        });
                    }
                    const bubble = row.querySelector('.bubble');
                    if (bubble) {
                        bubble.addEventListener('click', e=>{
                            e.stopPropagation();
                            const rect = bubble.getBoundingClientRect();
                            const windows = JSON.parse(row.dataset.windows || '[]');
                            let html = '<div class="pop-title">多页面</div>';
                            windows.forEach(w=>{ html += `<div class=\"pop-item\"><span>#${w.idx}</span><span class=\"pop-del\" data-wid=\"${w.id}\">×</span></div>`; });
                            pop.innerHTML = html; pop.style.display='block';
                            pop.style.left = (rect.left + window.scrollX - 20) + 'px';
                            pop.style.top = (rect.bottom + window.scrollY + 6) + 'px';
                            pop.dataset.pid = row.dataset.pid;
                        });
                    }
                });
                menu.addEventListener('click', e=>{ const it = e.target.closest('.item'); if (!it) return; const pid = menu.dataset.pid; menu.style.display='none'; if (it.dataset.action==='duplicate' || it.dataset.action==='new') { post({action:'addWindow', platformId: pid}); } });
                pop.addEventListener('click', e=>{ const del = e.target.closest('.pop-del'); if (!del) return; const pid = pop.dataset.pid; const wid = del.dataset.wid; pop.style.display='none'; post({action:'removeWindow', platformId: pid, windowId: wid}); });
                document.addEventListener('click', ()=>{ menu.style.display='none'; pop.style.display='none'; });
                // 顶部下拉锚点（用于导览高亮），放在页面顶部中间附近
                (function(){
                    var anchor = document.createElement('div');
                    anchor.id = 'top-dropdown-anchor';
                    anchor.style.position = 'fixed';
                    anchor.style.top = '10px';
                    anchor.style.left = '50%';
                    anchor.style.transform = 'translateX(-50%)';
                    anchor.style.width = '24px';
                    anchor.style.height = '18px';
                    anchor.style.pointerEvents = 'none';
                    anchor.style.zIndex = '1';
                    document.body.appendChild(anchor);
                    // 居中提示锚
                    var center = document.createElement('div');
                    center.id = 'center-anchor';
                    center.style.position = 'fixed';
                    center.style.left = '50%';
                    center.style.top = '50%';
                    center.style.transform = 'translate(-50%, -50%)';
                    center.style.width = '10px';
                    center.style.height = '10px';
                    center.style.pointerEvents = 'none';
                    center.style.zIndex = '1';
                    document.body.appendChild(center);
                })();
            </script>
        </body>
        </html>
        """
        # 追加导览逻辑脚本，注入布尔与示例平台 ID
        try:
            _show_tour_js = 'true' if self.should_show_homepage_tour() else 'false'
        except Exception:
            _show_tour_js = 'false'
        try:
            _force_tour_js = 'true' if self.consume_force_homepage_tour() else 'false'
        except Exception:
            _force_tour_js = 'false'
        _first_pid_js = json.dumps(tour_first_pid)
        # i18n strings for tour (with fallbacks)
        _i18n = {
            'step1_title': _t('tour.step1.title'),
            'step1_desc': _t('tour.step1.desc'),
            'step2_title': _t('tour.step2.title'),
            'step2_desc': _t('tour.step2.desc'),
            'practice': _t('tour.practice'),
            'done': _t('tour.done'),
        }
        import json as _json
        _i18n_js = _json.dumps(_i18n, ensure_ascii=False)
        html += f"""
        <script>
            // 一次性主页引导（统一采用内置简易导览，避免 driver.js 版本差异）
            (function(){{
                var SHOW_TOUR = {_show_tour_js}; // 由原生计算的开关
                var FORCE_TOUR = {_force_tour_js}; // 调试强制开关（忽略本地完成标志）
                var FIRST_PID = {_first_pid_js};  // 示例平台 ID，用于定位元素
                var I18N = {_i18n_js};
                var USE_SIMPLE_TOUR = true; // 始终使用内置简易导览，统一视觉与动效
                try {{
                    var doneLocal = (window.localStorage && localStorage.getItem('bubble_hp_tour_done') === '1');
                }} catch(_e) {{ var doneLocal = false; }}
                if ((!SHOW_TOUR && !FORCE_TOUR) || (!FORCE_TOUR && doneLocal)) return;

                // 简易导览（唯一实现）
                function startSimpleTour(){{
                    try {{
                        // 修正首卡片 ID，确保存在
                        (function(){{
                            var guess = document.querySelector('#row-' + FIRST_PID) || document.querySelector('.hrow');
                            if (guess) {{
                                var pid = (guess.getAttribute('data-pid')||FIRST_PID)||'';
                                if (!guess.id) guess.id = 'row-' + pid;
                                FIRST_PID = pid;
                            }}
                        }})();
                        var steps = [
                            {{ sel: '#row-' + FIRST_PID, title: (I18N.step1_title||'添加你喜欢的AI'), desc: (I18N.step1_desc||'点击AI卡片可启用平台'), pos: 'bottom', requireClick: true }},
                            {{ sel: '#top-dropdown-anchor', title: (I18N.step2_title||'切换窗口'), desc: (I18N.step2_desc||'点击顶部下拉框，选择该平台页面'), pos: 'bottom' }}
                        ];
                        var overlay = document.createElement('div');
                        overlay.id = '__bb_tour';
                        overlay.style.position = 'fixed';
                        overlay.style.inset = '0';
                        overlay.style.background = 'transparent';
                        overlay.style.zIndex = '9998';
                        // 不拦截任何点击，避免影响正常交互
                        overlay.style.pointerEvents = 'none';
                        document.body.appendChild(overlay);

                        // 使用矩形高亮（盒阴影覆盖全屏，仅矩形区域透出）
                        var spot = document.createElement('div');
                        spot.id = '__bb_spot';
                        spot.style.position = 'fixed';
                        spot.style.left = '0px';
                        spot.style.top = '0px';
                        spot.style.width = '0px';
                        spot.style.height = '0px';
                        spot.style.boxShadow = '0 0 0 9999px rgba(0,0,0,0.68)';
                        spot.style.borderRadius = '12px';
                        spot.style.pointerEvents = 'none';
                        spot.style.transition = 'all .22s ease';
                        spot.style.zIndex = '9998';
                        document.body.appendChild(spot);

                        var tip = document.createElement('div');
                        tip.style.position = 'fixed';
                        tip.style.maxWidth = '300px';
                        tip.style.background = '#fff';
                        tip.style.color = '#111';
                        tip.style.borderRadius = '12px';
                        tip.style.boxShadow = '0 12px 28px rgba(0,0,0,.18)';
                        tip.style.padding = '12px';
                        tip.style.zIndex = '9999';
                        tip.style.fontSize = '13px';
                        tip.style.opacity = '0';
                        tip.style.transform = 'translateY(4px) scale(.98)';
                        tip.style.transition = 'opacity .2s ease, transform .2s ease';
                        tip.innerHTML = '<div id="__bb_icon" style="width:28px;height:28px;margin:0 auto 6px;opacity:.95"></div>'+
                                        '<div id="__bb_t" style="font-weight:700;margin-bottom:6px"></div>'+
                                        '<div id="__bb_d" style="opacity:.9"></div>'+
                                        '<div style="margin-top:10px;text-align:center"><button id="__bb_next" style="background:#111;color:#fff;border:1px solid #111;border-radius:8px;padding:6px 12px;box-shadow:0 4px 10px rgba(0,0,0,.12);">下一步</button></div>';
                        document.body.appendChild(tip);
                        var iconEl = tip.querySelector('#__bb_icon');
                        var titleEl = tip.querySelector('#__bb_t');
                        var bodyEl = tip.querySelector('#__bb_d');
                        var nextBtn = tip.querySelector('#__bb_next');

                        function iconFor(idx){{
                            // Inline SVG icons for steps
                            if (idx === 0) {{
                                return '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="4" fill="#111"/><path d="M12 7v10M7 12h10" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>';
                            }} else {{
                                return '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="4" fill="#111"/><path d="M7 9l5 5 5-5" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
                            }}
                        }}

                        function placeNear(el, pos){{
                            var r = (el && el.getBoundingClientRect ? el.getBoundingClientRect() : {{left:0,top:0,width:0,height:0}});
                            // tip/overlay 使用 fixed 定位，直接采用视口坐标，无需叠加 scroll 偏移
                            var x = r.left, y = r.top;
                            tip.style.transform = '';
                            if (pos === 'right') {{ tip.style.left = (x + r.width + 12) + 'px'; tip.style.top = (y + 4) + 'px'; }}
                            else if (pos === 'bottom') {{ tip.style.left = (x + r.width/2 - 120) + 'px'; tip.style.top = (y + r.height + 12) + 'px'; }}
                            else if (pos === 'center' || pos === 'mid-center') {{ tip.style.left = '50%'; tip.style.top = '50%'; tip.style.transform = 'translate(-50%, -50%)'; }}
                            else {{ tip.style.left = (x + 8) + 'px'; tip.style.top = (y + 8) + 'px'; }}
                        }}

                        // 更新矩形高亮位置/尺寸（紧贴元素，轻微内外边距）
                        function spotlight(el){{
                            try {{
                                if (!el) {{ spot.style.width = '0px'; spot.style.height = '0px'; return; }}
                                var r = el.getBoundingClientRect();
                                var pad = 6; // 紧凑聚焦
                                spot.style.left = Math.max(0, r.left - pad) + 'px';
                                spot.style.top = Math.max(0, r.top - pad) + 'px';
                                spot.style.width = (r.width + pad*2) + 'px';
                                spot.style.height = (r.height + pad*2) + 'px';
                                var br = window.getComputedStyle(el).borderRadius || '12px';
                                spot.style.borderRadius = br;
                            }} catch(_e) {{}}
                        }}

                        function highlight(el){{
                            if (!el) return;
                            el.__bb_old_boxShadow = el.style.boxShadow;
                            el.__bb_old_pos = el.style.position;
                            el.__bb_old_radius = el.style.borderRadius;
                            if (getComputedStyle(el).position === 'static') el.style.position = 'relative';
                            el.style.boxShadow = '0 0 0 3px rgba(255,255,255,0.95), 0 0 0 6px rgba(59,130,246,0.55)';
                            el.style.borderRadius = '12px';
                        }}
                        function unhighlight(el){{ if (el) {{ el.style.boxShadow = el.__bb_old_boxShadow || ''; el.style.position = el.__bb_old_pos || ''; el.style.borderRadius = el.__bb_old_radius || ''; }} }}

                        var idx = -1, currentEl = null, wasHidden = false;
                        function go(n){{
                            if (n < 0) n = 0;
                            if (n >= steps.length) return finish();
                            unhighlight(currentEl);
                            idx = n;
                            var st = steps[idx];
                            // Update content with animation
                            try {{ iconEl.innerHTML = iconFor(idx); }} catch(_e){{}}
                            titleEl.textContent = st.title || '';
                            bodyEl.textContent = st.desc || '';
                            try {{ tip.style.opacity = '1'; tip.style.transform = 'translateY(0) scale(1)'; }} catch(_e){{}}
                            currentEl = document.querySelector(st.sel);
                            if (currentEl) {{ spotlight(currentEl); highlight(currentEl), placeNear(currentEl, st.pos || 'right'); }}
                            else {{ spotlight(null); }}
                            var force = !!st.requireClick;
                            nextBtn.style.display = force ? 'none' : '';
                            try {{ nextBtn.textContent = (idx >= steps.length - 1) ? '完成' : '下一步'; }} catch(_e){{}}
                            var handler = function(ev){{
                                // 让原点击自然冒泡到目标，避免拦截 + 保证功能键可用
                                try {{ currentEl && currentEl.removeEventListener('click', handler, true); }} catch(_e){{}}
                                setTimeout(function(){{ go(idx + 1); }}, 150);
                            }};
                            if (force && currentEl) currentEl.addEventListener('click', handler, true);
                            if (idx === 1) {{
                                // 第二步开始：通知原生等待用户通过下拉框切换到平台页面
                                try {{ if (window.webkit&&window.webkit.messageHandlers&&window.webkit.messageHandlers.aiAction) window.webkit.messageHandlers.aiAction.postMessage({{ action: 'homepageTourStage', stage: 'awaitDropdownSelection' }}); }} catch(_e){{}}
                                // 阻止“下一步”按钮，直到原生接管流程
                                nextBtn.style.display = 'none';
                            }}
                        }}
                        function finish(){{
                            try {{ unhighlight(currentEl); }} catch(_e){{}}
                            try {{ var s = document.getElementById('__bb_spot'); if (s&&s.parentNode) s.parentNode.removeChild(s); }} catch(_e){{}}
                            try {{ if (overlay && overlay.parentNode) overlay.parentNode.removeChild(overlay); }} catch(_e){{}}
                            try {{ if (tip && tip.parentNode) tip.parentNode.removeChild(tip); }} catch(_e){{}}
                            try {{ if (window.localStorage) localStorage.setItem('bubble_hp_tour_done', '1'); }} catch(_e){{}}
                            try {{ if (window.webkit&&window.webkit.messageHandlers&&window.webkit.messageHandlers.aiAction) window.webkit.messageHandlers.aiAction.postMessage({{ action: 'homepageTourDone' }}); }} catch(_e){{}}
                        }}
                        // 按压反馈 + 下一步
                        nextBtn.addEventListener('mousedown', function(){{ nextBtn.style.transform='translateY(1px) scale(.98)'; nextBtn.style.boxShadow='0 2px 6px rgba(0,0,0,.12)'; }});
                        nextBtn.addEventListener('mouseup', function(){{ nextBtn.style.transform=''; nextBtn.style.boxShadow='0 4px 10px rgba(0,0,0,.12)'; }});
                        nextBtn.addEventListener('mouseleave', function(){{ nextBtn.style.transform=''; nextBtn.style.boxShadow='0 4px 10px rgba(0,0,0,.12)'; }});
                        nextBtn.addEventListener('click', function(e){{ e.stopPropagation(); go(idx + 1); }});
                        try {{ var firstEl = document.querySelector('#row-' + FIRST_PID); if (firstEl && firstEl.scrollIntoView) firstEl.scrollIntoView({{ block: 'center', inline: 'nearest' }}); }} catch(_e){{}}
                        go(0);

                        // 提供原生回调：返回主页后展示快捷键提示；需要按两次快捷键（隐藏1次+显示1次）后进入最后一步
                        window.__bb_show_hotkey_tip_old = function(){{
                            try {{
                                var _done = false;
                                var _tip = document.createElement('div');
                                _tip.style.position = 'fixed';
                                _tip.style.left = '50%';
                                _tip.style.bottom = '24px';
                                _tip.style.transform = 'translateX(-50%)';
                                _tip.style.background = 'rgba(0,0,0,0.82)';
                                _tip.style.color = '#fff';
                                _tip.style.padding = '10px 14px';
                                _tip.style.borderRadius = '10px';
                                _tip.style.fontSize = '13px';
                                _tip.style.boxShadow = '0 6px 18px rgba(0,0,0,.25)';
                                _tip.style.zIndex = '9999';
                                _tip.textContent = '现在按下 ⌘G 显示/隐藏 Bubble（按两次以完成练习）';
                                document.body.appendChild(_tip);
                                var toggles = 0;
                                var last = document.visibilityState;
                                function _cleanup(){{ if (_done) return; _done = true; try {{ if (_tip&&_tip.parentNode) _tip.parentNode.removeChild(_tip); }} catch(_e){{}} }}
                                document.addEventListener('visibilitychange', function _v(){{
                                    try {{
                                        var cur = document.visibilityState;
                                        if (cur !== last) {{ toggles += 1; last = cur; }}
                                        if (cur === 'visible' && toggles >= 2) {{
                                            document.removeEventListener('visibilitychange', _v);
                                            _cleanup();
                                            try {{ launchConfetti(); }} catch(_e){{}}
                                            try {{
                                                var tip2 = document.createElement('div');
                                                tip2.style.position = 'fixed';
                                                tip2.style.left = '50%';
                                                tip2.style.bottom = '24px';
                                                tip2.style.transform = 'translateX(-50%)';
                                                tip2.style.background = 'rgba(0,0,0,0.82)';
                                                tip2.style.color = '#fff';
                                                tip2.style.padding = '10px 14px';
                                                tip2.style.borderRadius = '10px';
                                                tip2.style.fontSize = '13px';
                                                tip2.style.boxShadow = '0 6px 18px rgba(0,0,0,.25)';
                                                tip2.style.zIndex = '9999';
                                                tip2.textContent = '恭喜完成显示/隐藏练习！';
                                                document.body.appendChild(tip2);
                                                setTimeout(function(){{ try {{ if (tip2&&tip2.parentNode) tip2.parentNode.removeChild(tip2); }} catch(_e){{}} }}, 2200);
                                            }} catch(_e){{}}
                                            setTimeout(function(){{ try {{ go(idx + 1); }} catch(_e){{}} }}, 240);
                                        }}
                                    }} catch(_e){{}}
                                }});
                                // 超时兜底（只清理提示，不结束导览）
                                setTimeout(_cleanup, 20000);
                            }} catch(_e) {{}}
                        }}
                    }} catch(_e){{}}
                }}

                function launchConfetti(){{
                    try {{
                        var container = document.createElement('div');
                        container.style.position = 'fixed';
                        container.style.left = '0';
                        container.style.top = '0';
                        container.style.width = '100%';
                        container.style.height = '100%';
                        container.style.pointerEvents = 'none';
                        container.style.zIndex = '9999';
                        document.body.appendChild(container);
                        var colors = ['#ff6b6b','#feca57','#54a0ff','#5f27cd','#10ac84','#f368e0'];
                        var pieces = 100;
                        for (var i=0;i<pieces;i++) {{
                            var el = document.createElement('div');
                            el.style.position = 'absolute';
                            el.style.width = (6 + Math.random()*6) + 'px';
                            el.style.height = (8 + Math.random()*8) + 'px';
                            el.style.background = colors[Math.floor(Math.random()*colors.length)];
                            el.style.left = (Math.random()*100) + '%';
                            el.style.top = '-10px';
                            el.style.opacity = '0.9';
                            el.style.transform = 'rotate(' + (Math.random()*360) + 'deg)';
                            el.style.borderRadius = '2px';
                            container.appendChild(el);
                            (function(el){{
                                var x = (Math.random()*2-1) * 40; // horizontal drift
                                var y = 100 + Math.random()*50;   // fall distance vh
                                var r = (Math.random()*360);
                                var d = 2000 + Math.random()*1500;
                                el.animate([
                                    {{ transform: 'translate(0,0) rotate(0deg)' }},
                                    {{ transform: 'translate(' + x + 'px,' + y + 'vh) rotate(' + r + 'deg)' }}
                                ], {{ duration: d, easing: 'ease-out', iterations: 1, fill: 'forwards' }});
                            }})(el);
                        }}
                        setTimeout(function(){{ if (container && container.parentNode) container.parentNode.removeChild(container); }}, 4200);
                    }} catch(_e){{}}
                }}

                var __tries = 0;
                function tryStartTour(){{
                    if (USE_SIMPLE_TOUR) {{ startSimpleTour(); return; }}
                    if (typeof window.Driver !== 'function') {{ __tries++; if (__tries < 15) {{ setTimeout(tryStartTour, 120); return; }} else {{ startSimpleTour(); return; }} }}
                    // 等待首张卡片渲染
                    var firstRow = document.querySelector('#row-' + FIRST_PID) || document.querySelector('.hrow');
                    if (!firstRow) {{ __tries++; if (__tries < 15) {{ setTimeout(tryStartTour, 120); return; }} else {{ startSimpleTour(); return; }} }}
                    try {{
                        var driver = new window.Driver({{
                            animate: true,
                            opacity: 0.6, // 更暗的遮罩，突出高亮
                            padding: 6,
                            allowClose: false, // 移除“跳过”
                            overlayClickNext: false,
                            doneBtnText: '完成',
                            nextBtnText: '下一步',
                            // 去掉“跳过/上一步”文案（按钮通过样式与后续逻辑隐藏）
                            onReset: function(){{
                                // 结束后标记完成
                                try {{ if (window.localStorage) localStorage.setItem('bubble_hp_tour_done', '1'); }} catch(_e){{}}
                                try {{ if (window.webkit&&window.webkit.messageHandlers&&window.webkit.messageHandlers.aiAction) window.webkit.messageHandlers.aiAction.postMessage({{ action: 'homepageTourDone' }}); }} catch(_e){{}}
                            }}
                        }});
                        window._bubbleDriver = driver;

                        // 选中首个可用卡片作为第一步高亮目标（容错 FIRST_PID 缺失）
                        (function(){{
                            var guess = document.querySelector('#row-' + FIRST_PID) || document.querySelector('.hrow');
                            if (guess) {{
                                var pid = (guess.getAttribute('data-pid')||FIRST_PID)||'';
                                if (!guess.id) guess.id = 'row-' + pid;
                                FIRST_PID = pid;
                            }}
                        }})();
                        // 步骤定义：
                        var steps = [];
                        // 1) 点击卡片启用平台（整卡高亮）
                        steps.push({{ element: '#row-' + FIRST_PID, popover: {{ title: '添加你喜欢的AI', description: '点击AI卡片可启用平台', position: 'bottom' }} }});
                        // 2) 顶部下拉框提示（锚点定位，稍向左偏移防止溢出）
                        steps.push({{ element: '#top-dropdown-anchor', popover: {{ title: '切换窗口', description: '在顶部下拉框中切换到该平台页面', position: 'bottom' }} }});
                        // 3) 再次点击卡片移除页面/平台
                        steps.push({{ element: '#row-' + FIRST_PID, popover: {{ title: '删除页面', description: '再次点击刚刚的卡片，就可以删除刚刚的页面', position: 'bottom' }} }});
                        // 4) 使用快捷键显示/隐藏（不高亮 body，改用居中锚点）
                        steps.push({{ element: '#center-anchor', popover: {{ title: '试试显示/隐藏', description: '现在按下 ⌘G 显示/隐藏 Bubble（按两次以完成练习）', position: 'mid-center' }} }});
                        // 5) 返回后显示完成步骤，提示开始使用
                        steps.push({{ element: '#center-anchor', popover: {{ title: '恭喜学会显示/隐藏', description: '已完成快捷键练习。点击“完成”开始使用 Bubble。', position: 'mid-center' }} }});

                        // 尝试把第一张卡片滚动到可视区中间，避免遮挡
                        try {{ var firstRow = document.querySelector('#row-' + FIRST_PID); if (firstRow && firstRow.scrollIntoView) firstRow.scrollIntoView({{ block: 'center', inline: 'nearest' }}); }} catch(_e){{}}
                        driver.defineSteps(steps);

                        // 工具：隐藏/显示下一步按钮 + 清理不需要的按钮
                        function setNextVisible(v){{
                            var btn = document.querySelector('#driver-popover-item .driver-popover-footer .driver-next-btn') || document.querySelector('.driver-popover .driver-next-btn');
                            if (btn) btn.style.display = v ? '' : 'none';
                        }}
                        function setCloseVisible(_v){{
                            // 强制隐藏（去除“跳过”）
                            var btn = document.querySelector('#driver-popover-item .driver-popover-footer .driver-close-btn') || document.querySelector('.driver-popover .driver-close-btn');
                            if (btn) btn.style.display = 'none';
                        }}
                        function pruneNavButtons(){{
                            try {{
                                var pop = document.querySelector('.driver-popover') || document.querySelector('#driver-popover-item');
                                if (!pop) return;
                                // 仅隐藏明确的 prev/close 按钮，避免破坏 DOM 结构
                                var toHide = [
                                    '.driver-popover .driver-prev-btn',
                                    '.driver-popover .driver-close-btn',
                                    '#driver-popover-item .driver-popover-footer .driver-prev-btn',
                                    '#driver-popover-item .driver-popover-footer .driver-close-btn'
                                ];
                                toHide.forEach(function(sel){{ document.querySelectorAll(sel).forEach(function(el){{ el.style.display='none'; el.style.visibility='hidden'; }}); }});
                                // 只保留 next/done，并居中
                                var footer = pop.querySelector('.driver-buttons') || pop.querySelector('.driver-popover-footer') || pop;
                                var next = footer.querySelector('.driver-next-btn') || document.querySelector('#driver-popover-item .driver-popover-footer .driver-next-btn');
                                var done = footer.querySelector('.driver-done-btn') || document.querySelector('#driver-popover-item .driver-popover-footer .driver-done-btn');
                                var idx = (window._bubbleDriver && window._bubbleDriver.getActiveIndex) ? window._bubbleDriver.getActiveIndex() : null;
                                var isLast = (idx === 4);
                                if (next) {{
                                    next.style.display = isLast ? 'none' : 'inline-flex';
                                    next.style.margin = '0 auto';
                                    next.style.float = 'none';
                                    try {{ next.textContent = '下一步'; }} catch(_e){{}}
                                }}
                                if (done) {{
                                    done.style.display = 'inline-flex';
                                    done.style.margin = '0 auto';
                                    done.style.float = 'none';
                                    try {{ done.textContent = isLast ? '完成' : '下一步'; }} catch(_e){{}}
                                }}
                            }} catch(_e){{}}
                        }}

                        // 监听高亮变化以绑定卡片点击（第一步和第三步强制点击卡片推进）
                        function onStepChanged(){{
                            var idx = driver.getActiveIndex ? driver.getActiveIndex() : null;
                            var node = driver.getHighlightedElement && driver.getHighlightedElement().getNode ? driver.getHighlightedElement().getNode() : null;
                            // 默认允许下一步；并移除“跳过/上一步”按钮
                            setNextVisible(true);
                            setCloseVisible(false);
                            (function(){{
                                var all = document.querySelectorAll('.driver-popover button');
                                all.forEach(function(b){{
                                    var cls=(b.className||'')+'';
                                    if (cls.indexOf('driver-next-btn')===-1 && cls.indexOf('driver-done-btn')===-1) {{ b.style.display='none'; }}
                                }});
                                ['.driver-popover .driver-prev-btn', '.driver-popover .driver-close-btn', '.driver-popover .driver-cancel-btn', '.driver-popover .driver-skip-btn'].forEach(function(sel){{ var el=document.querySelector(sel); if (el) el.style.display='none'; }});
                                try {{ var anchorEl = document.getElementById('top-dropdown-anchor'); if (anchorEl) anchorEl.style.display = (idx === 1 ? 'block' : 'none'); }} catch(_e){{}}
                            }})();
                            // 为 driver 弹窗添加轻微淡入动效与图标（前两步）
                            try {{
                                var pop = document.querySelector('.driver-popover') || document.querySelector('#driver-popover-item');
                                if (pop) {{
                                    pop.style.transition = 'opacity .18s ease, transform .18s ease';
                                    pop.style.opacity = '0.98';
                                    pop.style.transform = 'translateY(-2px)';
                                    setTimeout(function(){{ try {{ pop.style.opacity = '1'; pop.style.transform = 'translateY(0)'; }} catch(_e){{}} }}, 0);
                                    if (idx === 0 || idx === 1) {{
                                        var title = pop.querySelector('.driver-popover-title') || pop.querySelector('.driver-title');
                                        if (title) {{
                                            var svg = (idx===0)
                                                ? '<svg style="vertical-align:middle;margin-right:6px" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="4" fill="#111"/><path d="M12 7v10M7 12h10" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg>'
                                                : '<svg style="vertical-align:middle;margin-right:6px" width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="4" fill="#111"/><path d="M7 9l5 5 5-5" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
                                            try {{ title.innerHTML = svg + (title.textContent||''); }} catch(_e){{}}
                                        }}
                                    }}
                                }}
                            }} catch(_e){{}}
                            // 第二步微调位置，避免溢出到右侧
                            pruneNavButtons();
                            if (idx === 1) {{ var pop = document.querySelector('.driver-popover') || document.querySelector('#driver-popover-item'); if (pop) {{ var left = pop.style.left; try {{ var v = parseFloat(left)||0; pop.style.left = (v - 40) + 'px'; }} catch(_e) {{ pop.style.marginLeft='-40px'; }} }} }} else {{ var pop2 = document.querySelector('.driver-popover') || document.querySelector('#driver-popover-item'); if (pop2) {{ pop2.style.marginLeft='0'; }} }}
                            // 顶部锚点仅在第二步存在；其它步骤把它移出视口防误判
                            try {{
                                var a=document.getElementById('top-dropdown-anchor');
                                if (a) {{
                                    if (idx === 1) {{ a.style.display='block'; }}
                                    else {{ a.style.display='none'; a.style.left='-9999px'; a.style.top='-9999px'; a.style.width='0'; a.style.height='0'; }}
                                }}
                            }} catch(_e){{}}
                            // Driver 路径：第二步开始，通知原生等待通过下拉进入聊天页；并隐藏“下一步”按钮
                            if (idx === 1) {{
                                try {{ if (window.webkit&&window.webkit.messageHandlers&&window.webkit.messageHandlers.aiAction) window.webkit.messageHandlers.aiAction.postMessage({{ action: 'homepageTourStage', stage: 'awaitDropdownSelection' }}); }} catch(_e){{}}
                                setNextVisible(false);
                            }}
                            if (idx === 0 && node && node.id === ('row-' + FIRST_PID)) {{
                                // 第一步：点击卡片即可前进（不拦截事件，避免阻断＋/删除等交互）
                                setNextVisible(true);
                                setCloseVisible(false);
                                var handler = function(ev){{
                                    try {{ node.removeEventListener('click', handler, true); }} catch(_e){{}}
                                    setTimeout(function(){{ driver.moveNext(); }}, 220);
                                }};
                                node.addEventListener('click', handler, true);
                            }} else if (idx === 2 && node && node.id === ('row-' + FIRST_PID)) {{
                                // 第三步：再次点击卡片即可前进（同样不拦截）
                                setNextVisible(true);
                                setCloseVisible(false);
                                var handler2 = function(ev){{
                                    try {{ node.removeEventListener('click', handler2, true); }} catch(_e){{}}
                                    setTimeout(function(){{ driver.moveNext(); }}, 220);
                                }};
                                node.addEventListener('click', handler2, true);
                            }} else if (idx === 3) {{
                                // 第四步：等待可见性变化（隐藏->显示），要求按两次快捷键（隐藏1次+显示1次）
                                setNextVisible(false);
                                // 隐藏 Driver 自身的高亮与遮罩，只保留自定义白色气泡
                                try {{
                                    var ov = document.querySelector('.driver-overlay'); if (ov) ov.style.display = 'none';
                                    var pop = document.querySelector('.driver-popover') || document.querySelector('#driver-popover-item'); if (pop) pop.style.display = 'none';
                                }} catch(_e){{}}
                                var toggles = 0;
                                var last = document.visibilityState;
                                var visHandler = function(){{
                                    try {{
                                        var cur = document.visibilityState;
                                        if (cur !== last) {{ toggles += 1; last = cur; }}
                                        // 当返回可见且累计发生两次状态切换（一次按键隐藏 + 一次按键显示）
                                        if (cur === 'visible' && toggles >= 2) {{
                                            document.removeEventListener('visibilitychange', visHandler);
                                            // 庆祝动画 + 轻提示，然后进入最后“完成”步骤
                                            launchConfetti();
                                            try {{
                                                var tip = document.createElement('div');
                                                tip.style.position = 'fixed';
                                                tip.style.bottom = '20px';
                                                tip.style.left = '50%';
                                                tip.style.transform = 'translateX(-50%)';
                                                tip.style.background = 'rgba(0,0,0,0.82)';
                                                tip.style.color = '#fff';
                                                tip.style.padding = '10px 14px';
                                                tip.style.borderRadius = '10px';
                                                tip.style.fontSize = '13px';
                                                tip.style.boxShadow = '0 6px 18px rgba(0,0,0,.25)';
                                                tip.style.zIndex = '9999';
                                                tip.textContent = '恭喜完成显示/隐藏练习！';
                                                document.body.appendChild(tip);
                                                setTimeout(function(){{ if (tip && tip.parentNode) tip.parentNode.removeChild(tip); }}, 2600);
                                            }} catch(_e){{}}
                                            setTimeout(function(){{ driver.moveNext(); }}, 220);
                                        }}
                                    }} catch(_e){{}}
                                }};
                                document.addEventListener('visibilitychange', visHandler);
                            }} else if (idx === 4) {{
                                // 第五步：显示“完成”按钮
                                setNextVisible(true); // 由 pruneNavButtons 决定仅显示 Done
                                setCloseVisible(false);
                            }}
                        }}

                        driver.start(0);
                        // 初次渲染后触发一次
                        setTimeout(function(){{ onStepChanged(); pruneNavButtons(); }}, 50);
                        // 监听后续每次高亮变化
                        var obs = new MutationObserver(function(){{ setTimeout(function(){{ onStepChanged(); pruneNavButtons(); }}, 30); }});
                        var pop = document.querySelector('.driver-popover') || document.querySelector('#driver-popover-item');
                        if (pop) obs.observe(pop, {{ childList: true, subtree: true, attributes: true }});
                    }} catch(_e){{}}
                }}
                // 等待页面渲染完成后启动
                window.requestAnimationFrame ? requestAnimationFrame(function(){{ setTimeout(tryStartTour, 80); }}) : setTimeout(tryStartTour, 120);
            }})();
        </script>
        <script>
            // 全局：返回主页后用于展示快捷键提示（双次显示/隐藏），适配 Driver 与简易导览两种路径
            (function(){{
                // 统一覆盖为新版白色居中气泡版本
                window.__bb_show_hotkey_tip = function(hk){{
                    try {{
                        var _done = false;
                        // 遮罩层（变暗背景，突出中间气泡）
                        var _mask = document.createElement('div');
                        _mask.style.position = 'fixed';
                        _mask.style.inset = '0';
                        _mask.style.background = 'rgba(0,0,0,0.60)';
                        _mask.style.zIndex = '9998';
                        _mask.style.opacity = '0';
                        _mask.style.transition = 'opacity .25s ease';
                        // 捕获点击，避免误触页面
                        _mask.style.pointerEvents = 'auto';
                        document.body.appendChild(_mask);

                        // 白色提示气泡（置中）
                        var _tip = document.createElement('div');
                        _tip.style.position = 'fixed';
                        _tip.style.left = '50%';
                        _tip.style.top = '42%';
                        _tip.style.transform = 'translate(-50%, -46%) scale(.98)';
                        _tip.style.background = '#fff';
                        _tip.style.color = '#111';
                        _tip.style.padding = '16px 18px';
                        _tip.style.borderRadius = '12px';
                        _tip.style.fontSize = '15px';
                        _tip.style.fontWeight = '600';
                        _tip.style.fontFamily = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,'PingFang SC','Hiragino Sans GB','Noto Sans','Microsoft YaHei',sans-serif";
                        _tip.style.boxShadow = '0 18px 36px rgba(0,0,0,0.26)';
                        _tip.style.zIndex = '9999';
                        _tip.style.textAlign = 'center';
                        _tip.style.opacity = '0';
                        _tip.style.transition = 'opacity .25s ease, transform .25s ease';
                        var hotkey = (typeof hk === 'string' && hk.trim()) ? hk : '⌘+G';
                        var _practice = (I18N.practice||'按“{{hotkey}}”能够隐藏界面，按两下试试吧！').replace('{{hotkey}}', hotkey);
                        _tip.innerHTML = '<div style="width:28px;height:28px;margin:0 auto 8px">'+
                                         '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'+
                                         '<rect x="3" y="6" width="18" height="12" rx="2" fill="#111"/>'+
                                         '<rect x="6" y="9" width="3" height="2" fill="#fff"/>'+
                                         '<rect x="10" y="9" width="3" height="2" fill="#fff"/>'+
                                         '<rect x="14" y="9" width="3" height="2" fill="#fff"/>'+
                                         '<rect x="6" y="12" width="11" height="2" fill="#fff"/>'+
                                         '</svg>'+
                                         '</div>'+
                                         '<div style="line-height:1.5">'+ _practice +'</div>';
                        document.body.appendChild(_tip);
                        requestAnimationFrame(function(){{
                            try {{ _mask.style.opacity = '1'; }} catch(_e){{}}
                            try {{ _tip.style.opacity = '1'; _tip.style.transform = 'translate(-50%, -48%) scale(1)'; }} catch(_e){{}}
                        }});
                        var toggles = 0;
                        var last = document.visibilityState;
                        function _cleanup(){{
                            if (_done) return; _done = true; // 标记避免重复
                            try {{ _tip.style.opacity = '0'; _tip.style.transform = 'translate(-50%, -44%) scale(.98)'; }} catch(_e){{}}
                            try {{ _mask.style.opacity = '0'; }} catch(_e){{}}
                            setTimeout(function(){{
                                try {{ if (_tip&&_tip.parentNode) _tip.parentNode.removeChild(_tip); }} catch(_e){{}}
                                try {{ if (_mask&&_mask.parentNode) _mask.parentNode.removeChild(_mask); }} catch(_e){{}}
                            }}, 250);
                        }}
                        document.addEventListener('visibilitychange', function _v(){{
                            try {{
                                var cur = document.visibilityState;
                                if (cur !== last) {{ toggles += 1; last = cur; }}
                                if (cur === 'visible' && toggles >= 2) {{
                                    document.removeEventListener('visibilitychange', _v);
                                    // 庆祝 + 修改白色气泡文案，停留 3 秒后关闭
                                    try {{ launchConfetti && launchConfetti(); }} catch(_e){{}}
                                    try {{
                                        _tip.innerHTML = '<div style="width:28px;height:28px;margin:0 auto 8px">'+
                                            '<svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="4" fill="#111"/><path d="M6 12l4 4 8-8" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'+
                                            '</div>'+
                                            '<div style="line-height:1.5">'+ (I18N.done||'你学会使用 Bubble 啦，享用吧！') +'</div>';
                                    }} catch(_e){{}}
                                    setTimeout(function(){{
                                        _cleanup();
                                        // 完成引导
                                        try {{
                                            if (window._bubbleDriver && typeof window._bubbleDriver.reset === 'function') {{
                                                window._bubbleDriver.reset();
                                            }} else {{
                                                try {{ if (window.localStorage) localStorage.setItem('bubble_hp_tour_done', '1'); }} catch(_e){{}}
                                                try {{ if (window.webkit&&window.webkit.messageHandlers&&window.webkit.messageHandlers.aiAction) window.webkit.messageHandlers.aiAction.postMessage({{ action: 'homepageTourDone' }}); }} catch(_e){{}}
                                            }}
                                        }} catch(_e){{}}
                                    }}, 3000);
                                }}
                            }} catch(_e){{}}
                        }});
                        // 不设置超时：必须完成两次切换才会关闭
                    }} catch(_e) {{}}
                }};
            }})();
        </script>
        """
        return html
    
    def _show_first_launch_guide(self) -> str:
        """
        显示首次启动指导
        
        Returns:
            str: 要加载的HTML内容或URL
        """
        # 返回首次启动引导页面的HTML内容
        # 顶部 logo：优先使用 data URL，兜底使用表情符号
        _first_logo_html = (
            f'<img style="width:56px;height:56px;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,.15)" src="{self.logo_data_url}" alt="Bubble" />'
            if getattr(self, 'logo_data_url', None) else
            '<div class="logo">🫧</div>'
        )
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{_t('home.welcome')}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 56px 20px 20px; /* 顶部为悬浮栏让出空间 */
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    max-width: 500px;
                    text-align: center;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .logo {{
                    font-size: 48px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 10px;
                }}
                p {{
                    color: #666;
                    margin-bottom: 30px;
                    line-height: 1.6;
                }}
                .ai-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 30px 0;
                }}
                .ai-option {{
                    background: #f8f9fa;
                    border: 2px solid #e9ecef;
                    border-radius: 12px;
                    padding: 20px;
                    cursor: pointer;
                    transition: transform .18s ease, box-shadow .18s ease, background .18s ease, color .18s ease;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
                    will-change: transform, box-shadow;
                }}
                .ai-option:hover {{ background: #667eea; color: white; transform: translateY(-2px) scale(1.02); box-shadow: 0 10px 24px rgba(102,126,234,0.35); }}
                .ai-option:active {{ transform: scale(.96); box-shadow: 0 4px 12px rgba(0,0,0,0.18); }}
                .ai-name {{
                    font-weight: bold;
                    font-size: 16px;
                    margin-bottom: 5px;
                }}
                .ai-desc {{
                    font-size: 12px;
                    opacity: 0.8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {_first_logo_html}
                <h1>{_t('home.welcome')}</h1>
                <p>您的智能AI助手已准备就绪！<br>请选择您最常使用的AI平台开始体验：</p>
                
                <div class="ai-grid">
                    {self._generate_ai_options_html()}
                </div>
                
                <p style="font-size: 12px; color: #999; margin-top: 20px;">
                    您可以稍后在设置中添加或管理更多AI平台
                </p>
            </div>
            
            <script>
                function selectAI(platformId, platformName) {{
                    // 通知原生应用选择了AI
                    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.aiSelection) {{
                        window.webkit.messageHandlers.aiSelection.postMessage({{
                            action: 'selectDefaultAI',
                            platformId: platformId,
                            platformName: platformName
                        }});
                    }}
                }}
            </script>
        </body>
        </html>
        """
        return html_content
    
    def _show_platform_management(self) -> str:
        """旧版（网格）主页已弃用，统一返回行样式主页。"""
        return self._show_platform_management_rows()

    def _show_platform_management_compact(self) -> str:
        """已弃用：返回行样式主页以保持一致。"""
        return self._show_platform_management_rows()

    # 旧版主页渲染方法（紧凑/网格/首次引导）已删除，统一由 _show_platform_management_rows 提供新版 UI。
