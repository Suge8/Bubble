"""
导航控制器 (Navigation Controller)

该模块负责管理BubbleBot应用的页面导航功能，包括：
- 主页与聊天页面之间的导航
- 返回按钮的显示和处理
- 页面状态的管理和切换
- 窗口间的无缝切换

导航控制器与主页管理器和窗口管理器协作，提供流畅的用户体验。
"""

from typing import Optional, Callable, Dict, Any
import objc
from Foundation import NSObject, NSDate
from AppKit import NSApp


class NavigationController(NSObject):
    """
    导航控制器类
    
    负责管理应用内的页面导航，包括主页显示、聊天页面切换、
    返回按钮处理等功能。
    """
    
    def init(self, app_delegate=None):
        """初始化导航控制器"""
        self = objc.super(NavigationController, self).init()
        if self is None:
            return None
        self.app_delegate = app_delegate
        self.current_page = "homepage"  # 当前页面状态: homepage, chat
        self.current_platform = None   # 当前选中的AI平台
        self.current_window_id = None  # 当前窗口ID
        self.navigation_history = []   # 导航历史栈
        self.page_change_listeners = []  # 页面变化监听器
        
        # 页面状态管理
        self.page_states = {
            "homepage": {
                "title": "Bubble",
                "show_back_button": False,
                "show_ai_selector": False,
                "content_type": "homepage"
            },
            "chat": {
                "title": "Bubble - Chat", 
                "show_back_button": True,
                "show_ai_selector": True,
                "content_type": "webview"
            }
        }
        return self

    def on_language_changed(self):
        """Handle language change at runtime.
        Currently titles are static; this hook ensures UI gets a chance to refresh.
        """
        try:
            # Re-apply UI elements (back button, selector), and window title
            self.update_ui_elements()
            if self.app_delegate and hasattr(self.app_delegate, 'handle_navigation_change'):
                self.app_delegate.handle_navigation_change(self.current_page, self.current_platform)
        except Exception as e:
            print(f"语言切换后刷新导航失败: {e}")
    
    def set_app_delegate(self, app_delegate):
        """设置应用委托"""
        self.app_delegate = app_delegate
    
    def add_page_change_listener(self, listener: Callable[[str, str], None]):
        """
        添加页面变化监听器
        
        Args:
            listener: 监听函数，接收 (from_page, to_page) 参数
        """
        if listener not in self.page_change_listeners:
            self.page_change_listeners.append(listener)
    
    def remove_page_change_listener(self, listener: Callable[[str, str], None]):
        """移除页面变化监听器"""
        if listener in self.page_change_listeners:
            self.page_change_listeners.remove(listener)
    
    def _notify_page_change(self, from_page: str, to_page: str):
        """通知页面变化"""
        for listener in self.page_change_listeners:
            try:
                listener(from_page, to_page)
            except Exception as e:
                print(f"页面变化监听器错误: {e}")
    
    def navigate_to_homepage(self, save_current: bool = True):
        """
        导航到主页
        
        Args:
            save_current: 是否保存当前页面到历史记录
        """
        previous_page = self.current_page
        
        if save_current and self.current_page != "homepage":
            self.navigation_history.append({
                "page": self.current_page,
                "platform": self.current_platform,
                "window_id": self.current_window_id,
                "timestamp": NSDate.date()
            })
        
        self.current_page = "homepage"
        self.current_platform = None
        self.current_window_id = None
        
        # 通知应用委托更新UI
        if self.app_delegate and hasattr(self.app_delegate, 'handle_navigation_change'):
            self.app_delegate.handle_navigation_change("homepage", None)

        # 更新顶栏/返回按钮等
        self.update_ui_elements()

        # 通知页面变化监听器
        self._notify_page_change(previous_page, "homepage")
        
        print("导航到主页")
    
    def navigate_to_chat(self, platform_id: str, window_id: Optional[str] = None, save_current: bool = True):
        """
        导航到聊天页面
        
        Args:
            platform_id: AI平台标识符
            window_id: 窗口ID（可选）
            save_current: 是否保存当前页面到历史记录
        """
        previous_page = self.current_page
        
        if save_current and self.current_page != "chat":
            self.navigation_history.append({
                "page": self.current_page,
                "platform": self.current_platform,
                "window_id": self.current_window_id,
                "timestamp": NSDate.date()
            })
        
        self.current_page = "chat"
        self.current_platform = platform_id
        self.current_window_id = window_id
        
        # 通知应用委托更新UI
        if self.app_delegate and hasattr(self.app_delegate, 'handle_navigation_change'):
            self.app_delegate.handle_navigation_change("chat", platform_id, window_id)

        # 更新顶栏/返回按钮等
        self.update_ui_elements()

        # 通知页面变化监听器
        self._notify_page_change(previous_page, "chat")
        
        print(f"导航到聊天页面: {platform_id}")
    
    def go_back(self) -> bool:
        """
        返回上一页
        
        Returns:
            bool: 是否成功返回
        """
        if not self.navigation_history:
            # 如果没有历史记录，默认返回主页
            if self.current_page != "homepage":
                self.navigate_to_homepage(save_current=False)
                return True
            return False
        
        # 从历史记录中获取上一页
        last_page = self.navigation_history.pop()
        
        if last_page["page"] == "homepage":
            self.navigate_to_homepage(save_current=False)
        elif last_page["page"] == "chat":
            self.navigate_to_chat(
                last_page["platform"], 
                last_page.get("window_id"),
                save_current=False
            )
        
        return True
    
    def can_go_back(self) -> bool:
        """检查是否可以返回"""
        return len(self.navigation_history) > 0 or self.current_page != "homepage"
    
    def clear_history(self):
        """清空导航历史"""
        self.navigation_history = []
    
    def get_current_page_state(self) -> Dict[str, Any]:
        """获取当前页面状态"""
        page_state = self.page_states.get(self.current_page, {}).copy()
        page_state.update({
            "current_platform": self.current_platform,
            "current_window_id": self.current_window_id,
            "can_go_back": self.can_go_back()
        })
        return page_state
    
    def should_show_back_button(self) -> bool:
        """判断是否应该显示返回按钮"""
        return self.current_page == "chat" or self.can_go_back()
    
    def should_show_ai_selector(self) -> bool:
        """主页与聊天页均显示下拉框（主页时选中“主页”项）。"""
        return self.current_page in ("homepage", "chat")
    
    def get_page_title(self) -> str:
        """获取当前页面标题（本地化）"""
        try:
            from ..i18n import t as _t
        except Exception:
            def _t(k, **kwargs):
                return "Bubble" if k == 'app.name' else ("Chat" if k == 'nav.chat' else k)
        if self.current_page == "homepage":
            return _t('app.name')
        if self.current_page == "chat":
            base = _t('app.name')
            chat_label = _t('nav.chat')
            if self.current_platform:
                platform_name = self._get_platform_display_name(self.current_platform)
                return f"{base} - {chat_label}: {platform_name}"
            return f"{base} - {chat_label}"
        return _t('app.name')
    
    def _get_platform_display_name(self, platform_id: str) -> str:
        """获取平台显示名称（i18n 简称）"""
        try:
            from ..i18n import t as _t
            return _t(f'platform.{platform_id}', default=platform_id.title())
        except Exception:
            return platform_id.title()
    
    def handle_ai_selector_change(self, platform_id: str, window_id: Optional[str] = None):
        """
        处理AI选择器变化
        
        Args:
            platform_id: 选中的AI平台ID
            window_id: 窗口ID（可选）
        """
        if self.current_page == "chat":
            # 在聊天页面切换AI，不保存到历史记录
            self.navigate_to_chat(platform_id, window_id, save_current=False)
        else:
            # 从其他页面切换到聊天页面
            self.navigate_to_chat(platform_id, window_id, save_current=True)
    
    def handle_homepage_ai_selection(self, platform_id: str):
        """
        处理主页AI选择
        
        Args:
            platform_id: 选中的AI平台ID
        """
        # 从主页选择AI，导航到聊天页面
        self.navigate_to_chat(platform_id, save_current=True)
    
    def get_navigation_context(self) -> Dict[str, Any]:
        """
        获取导航上下文信息
        
        Returns:
            dict: 包含当前导航状态的字典
        """
        return {
            "current_page": self.current_page,
            "current_platform": self.current_platform,
            "current_window_id": self.current_window_id,
            "can_go_back": self.can_go_back(),
            "history_depth": len(self.navigation_history),
            "page_state": self.get_current_page_state(),
            "page_title": self.get_page_title()
        }
    
    def handle_window_close_request(self) -> bool:
        """
        处理窗口关闭请求
        
        Returns:
            bool: 是否应该关闭窗口（True）或返回主页（False）
        """
        if self.current_page == "homepage":
            # 在主页时，关闭窗口
            return True
        else:
            # 在其他页面时，返回主页而不是关闭
            self.navigate_to_homepage(save_current=False)
            return False
    
    def reset_navigation(self):
        """重置导航状态"""
        self.current_page = "homepage"
        self.current_platform = None
        self.current_window_id = None
        self.clear_history()
        
        print("导航状态已重置")
    
    def get_javascript_bridge_methods(self) -> Dict[str, Callable]:
        """
        获取JavaScript桥接方法
        
        Returns:
            dict: 可以暴露给WebView的方法字典
        """
        return {
            "navigateToHomepage": lambda: self.navigate_to_homepage(),
            "navigateToChat": lambda platform_id, window_id=None: self.navigate_to_chat(platform_id, window_id),
            "goBack": lambda: self.go_back(),
            "canGoBack": lambda: self.can_go_back(),
            "getCurrentPage": lambda: self.current_page,
            "getCurrentPlatform": lambda: self.current_platform,
            "getNavigationContext": lambda: self.get_navigation_context(),
            "handleAISelection": lambda platform_id, window_id=None: self.handle_ai_selector_change(platform_id, window_id)
        }
    
    def inject_navigation_javascript(self) -> str:
        """
        生成要注入到WebView中的JavaScript代码
        
        Returns:
            str: JavaScript代码字符串
        """
        return """
        // BubbleBot导航JavaScript桥接
        window.BubbleBotNavigation = {
            // 导航到主页
            navigateToHomepage: function() {
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.navigationAction) {
                    window.webkit.messageHandlers.navigationAction.postMessage({
                        action: 'navigateToHomepage'
                    });
                }
            },
            
            // 导航到聊天页面
            navigateToChat: function(platformId, windowId) {
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.navigationAction) {
                    window.webkit.messageHandlers.navigationAction.postMessage({
                        action: 'navigateToChat',
                        platformId: platformId,
                        windowId: windowId
                    });
                }
            },
            
            // 返回上一页
            goBack: function() {
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.navigationAction) {
                    window.webkit.messageHandlers.navigationAction.postMessage({
                        action: 'goBack'
                    });
                }
            },
            
            // 检查是否可以返回
            canGoBack: function() {
                // 这个需要同步返回，所以需要在注入时动态设置
                return %s;
            },
            
            // 获取当前页面
            getCurrentPage: function() {
                return '%s';
            },
            
            // 获取当前平台
            getCurrentPlatform: function() {
                return '%s';
            },
            
            // 处理AI选择
            handleAISelection: function(platformId, windowId) {
                if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.navigationAction) {
                    window.webkit.messageHandlers.navigationAction.postMessage({
                        action: 'handleAISelection',
                        platformId: platformId,
                        windowId: windowId
                    });
                }
            }
        };
        
        // 添加返回按钮点击事件监听
        document.addEventListener('DOMContentLoaded', function() {
            // 查找返回按钮并添加事件监听
            const backButtons = document.querySelectorAll('[data-action="back"], .back-button, #back-button');
            backButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    e.preventDefault();
                    window.BubbleBotNavigation.goBack();
                });
            });
        });
        """ % (
            "true" if self.can_go_back() else "false",
            self.current_page,
            self.current_platform or "null"
        )
    
    def update_ui_elements(self):
        """更新UI元素状态"""
        if not self.app_delegate:
            return
        
        # 更新返回按钮显示状态
        if hasattr(self.app_delegate, 'update_back_button_visibility'):
            self.app_delegate.update_back_button_visibility(self.should_show_back_button())
        
        # 更新AI选择器/主页标签显示状态
        if hasattr(self.app_delegate, 'update_ai_selector_visibility'):
            self.app_delegate.update_ai_selector_visibility(self.should_show_ai_selector())
        try:
            show_selector = self.should_show_ai_selector()
            if hasattr(self.app_delegate, 'selector_bg') and self.app_delegate.selector_bg:
                self.app_delegate.selector_bg.setHidden_(not show_selector)
            # 顶栏品牌仅在主页显示
            if hasattr(self.app_delegate, 'brand_logo') and self.app_delegate.brand_logo:
                self.app_delegate.brand_logo.setHidden_(self.current_page != 'homepage')
            if hasattr(self.app_delegate, 'brand_label') and self.app_delegate.brand_label:
                self.app_delegate.brand_label.setHidden_(self.current_page != 'homepage')
        except Exception:
            pass
        
        # 更新窗口标题
        if hasattr(self.app_delegate, 'update_window_title'):
            self.app_delegate.update_window_title(self.get_page_title())
        
        print(f"UI元素已更新 - 页面: {self.current_page}, 平台: {self.current_platform}")
