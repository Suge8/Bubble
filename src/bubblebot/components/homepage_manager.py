"""
主页管理器 (Homepage Manager)

该模块负责管理BubbleBot应用的主页功能，包括：
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
                data = pkgutil.get_data('bubblebot', name)
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
        - 开发模式回退到文件系统路径（src/bubblebot/logo/...）
        """
        enabled = self.get_enabled_platforms()
        available = self.get_available_platforms()
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
                data = pkgutil.get_data('bubblebot', f'assets/icons/{pid}.png')
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
            <div class=\"hrow{' active' if is_on else ''}\" data-pid=\"{pid}\" data-windows='{_json.dumps(wl)}'>
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
            <style>
                :root {{ --bg:#fafafa; --card:#fff; --border:#eaeaea; --text:#111; --muted:#666; --accent:#111; --radius:12px; --rightW:40px; }}
                * {{ box-sizing: border-box; }}
                body {{ margin:0; padding:56px 14px 14px; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,'Noto Sans',sans-serif; background:var(--bg); color:var(--text); overflow-x:hidden; }}
                /* 容器宽度：随窗口增大而增宽，左右边距始终相等；最小=360+28，最大≈860 */
                .list {{ width: clamp(388px, calc(100% - 28px), 888px); margin:0 auto; display:flex; flex-direction:column; gap:10px; }}
                /* 卡片占满容器宽度，限定最小高度；高度/内边距随窗口高度线性放大（无阈值跳变） */
                .hrow {{ position:relative; overflow:hidden; display:flex; align-items:center; justify-content:flex-start; background:var(--card); border:1px solid var(--border); border-radius:12px; padding: calc(12px * var(--vhScale, 1)) 14px; padding-right: calc(14px + var(--rightW)); cursor:pointer; transition: box-shadow .18s ease, border-color .18s ease; width:100%; margin:0 auto; min-height: calc(48px * var(--vhScale, 1)); will-change: box-shadow; backface-visibility:hidden; pointer-events:auto; box-sizing:border-box; }}
                .hrow:hover {{ box-shadow:0 10px 26px rgba(0,0,0,.08); }}
                .hrow.active {{ border-color:#111; box-shadow:0 0 0 2px rgba(17,17,17,.18); }}
                .hrow .title {{ font-size:14px; font-weight:600; display:flex; align-items:center; gap:10px; flex:1; min-width:0; }}
                .hrow .title .icon {{ width:16px; height:16px; border-radius:4px; object-fit:cover; }}
                .hrow .title .name {{ display:inline-block; max-width:46%; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
                .hrow .title .desc {{ margin-left:10px; font-weight:500; font-size:12px; color:#6b7280; opacity:.95; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; flex:1; min-width:0; text-align:center; }}
                .hrow .right {{ position:absolute; right:14px; top:50%; transform:translateY(-50%); width:var(--rightW); display:flex; align-items:center; gap:2px; justify-content:flex-end; overflow:hidden; }}
                .hrow .more {{ display:inline-flex; align-items:center; justify-content:center; width:12px; height:12px; border-radius:999px; border:1px solid var(--border); background:#fff; cursor:pointer; font-size:12px; line-height:1; }}
                .hrow .bubble {{ display:inline-flex; align-items:center; justify-content:center; width:auto; min-width:10px; height:10px; padding:0 3px; border-radius:999px; background:#111; color:#fff; font-size:7px; }}
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
            </style>
        </head>
        <body>
            <div class=\"list\">{rows}</div>
            <div id=\"menu\" class=\"menu\"><div class=\"item\" data-action=\"duplicate\">重复添加</div></div>
            <div id=\"popover\" class=\"popover\"></div>
        """
        html += """
            <script>
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
            </script>
        </body>
        </html>
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
