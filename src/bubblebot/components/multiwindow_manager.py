"""
多窗口管理器

实现BubbleBot的多窗口管理功能，支持最多5个窗口的创建、切换、销毁管理。
集成现有的AppWindow类逻辑，支持多平台多窗口并行运行。
"""

import objc
from AppKit import *
from WebKit import *
from Quartz import *
from Foundation import NSObject, NSURL, NSURLRequest
from typing import Dict, List, Optional, Tuple
import os
import uuid
from datetime import datetime

# 导入数据模型
from ..models.ai_window import AIWindow, WindowState, WindowType, WindowGeometry, WindowManager
from ..models.platform_config import PlatformConfig, AIServiceConfig
from ..constants import (
    APP_TITLE,
    CORNER_RADIUS,
    DRAG_AREA_HEIGHT,
    FRAME_SAVE_NAME,
    STATUS_ITEM_CONTEXT,
)


class MultiWindowAppWindow(NSWindow):
    """
    多窗口应用窗口类
    
    扩展原有AppWindow功能，支持多窗口实例管理。
    每个窗口实例都有独立的配置和状态。
    """
    
    def initWithContentRect_styleMask_backing_defer_windowId_(
        self, contentRect, styleMask, backing, defer, window_id
    ):
        """初始化多窗口实例"""
        self = objc.super(MultiWindowAppWindow, self).initWithContentRect_styleMask_backing_defer_(
            contentRect, styleMask, backing, defer
        )
        if self:
            self.window_id = window_id
            self.platform_id = None
            self.ai_window_data = None
        return self
    
    def canBecomeKeyWindow(self):
        """允许成为主要窗口"""
        return True
    
    def keyDown_(self, event):
        """处理键盘事件"""
        delegate = self.delegate()
        if delegate and hasattr(delegate, 'keyDown_'):
            delegate.keyDown_(event)
        else:
            objc.super(MultiWindowAppWindow, self).keyDown_(event)
    
    def setWindowData_(self, ai_window):
        """设置窗口数据"""
        self.ai_window_data = ai_window
        self.platform_id = ai_window.platform_id
    
    def getWindowData(self):
        """获取窗口数据"""
        return self.ai_window_data


class MultiWindowDragArea(NSView):
    """
    多窗口拖拽区域类
    
    为每个窗口提供独立的拖拽功能和控制按钮。
    """
    
    def initWithFrame_windowManager_(self, frame, window_manager):
        """初始化拖拽区域"""
        self = objc.super(MultiWindowDragArea, self).initWithFrame_(frame)
        if self:
            self.setWantsLayer_(True)
            self.window_manager = window_manager
        return self
    
    def setBackgroundColor_(self, color):
        """设置背景颜色"""
        self.layer().setBackgroundColor_(color.CGColor())
    
    def mouseDown_(self, event):
        """处理鼠标拖拽事件"""
        self.window().performWindowDragWithEvent_(event)


class MultiWindowManager(NSObject):
    """
    多窗口管理器主类
    
    负责管理所有AI窗口实例的生命周期，包括创建、销毁、切换、状态管理等功能。
    默认不限制窗口数量，每个窗口可以是不同的AI平台。
    对外提供页面计数变更回调以便上层做 UI 提示。
    """
    
    def init(self):
        """初始化多窗口管理器"""
        self = objc.super(MultiWindowManager, self).init()
        if self:
            # 初始化组件
            self.window_manager = WindowManager()
            self.platform_config = PlatformConfig()
            
            # NSWindow实例映射
            self.ns_windows = {}  # window_id -> NSWindow instance
            self.webviews = {}    # window_id -> WebView instance
            self.drag_areas = {}  # window_id -> DragArea instance
            
            # 活动窗口跟踪
            self.active_ns_window = None
            
            # 页面计数变化回调：Optional[Callable[[int,int], None]]
            self.on_page_count_changed = None
            
            # 窗口配置
            self.default_window_size = (550, 580)
            self.default_window_position = (500, 200)
            self.window_offset = 30  # 新窗口偏移量
            
            # 用户代理
            self.safari_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
            
        return self
    
    # MARK: - 核心窗口管理方法
    
    def createWindowForPlatform_(self, platform_id):
        """
        为指定平台创建新窗口
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            str: 窗口ID，如果创建失败返回None
        """
        # 记录创建前页面总数（使用 WindowManager 数据更准确）
        old_count = len(self.window_manager.windows)
        # 检查是否可以创建新窗口（默认不限制，除非外部设置了上限）
        if not self.window_manager.can_create_window(platform_id):
            print(f"无法创建新窗口（达到限制或外部约束）: {platform_id}")
            return None
        
        # 获取平台配置
        platform_config = self.platform_config.get_platform(platform_id)
        if not platform_config:
            print(f"未找到平台配置: {platform_id}")
            return None
        
        # 计算新窗口位置
        window_position = self._calculate_new_window_position()
        
        # 创建AI窗口数据模型
        geometry = WindowGeometry(
            x=window_position[0],
            y=window_position[1],
            width=self.default_window_size[0],
            height=self.default_window_size[1]
        )
        
        ai_window = self.window_manager.create_window(
            platform_id=platform_id,
            window_type=WindowType.MAIN,
            geometry=geometry
        )
        
        if not ai_window:
            print("创建AI窗口数据失败")
            return None
        
        # 创建NSWindow实例
        if not self._create_ns_window(ai_window, platform_config):
            # 如果NSWindow创建失败，清理AI窗口数据
            self.window_manager.remove_window(ai_window.window_id)
            return None
        
        # 更新窗口状态
        ai_window.activate()
        self.window_manager.set_active_window(ai_window.window_id)
        
        print(f"成功创建窗口: {ai_window.window_id} for platform: {platform_id}")
        # 触发页面计数变更回调
        try:
            new_count = len(self.window_manager.windows)
            cb = getattr(self, 'on_page_count_changed', None)
            if callable(cb):
                cb(old_count, new_count)
        except Exception:
            pass
        return ai_window.window_id
    
    def closeWindow_(self, window_id):
        """
        关闭指定窗口
        
        Args:
            window_id: 窗口标识符
            
        Returns:
            bool: 关闭是否成功
        """
        if window_id not in self.ns_windows:
            return False
        
        # 关闭NSWindow
        ns_window = self.ns_windows[window_id]
        ns_window.close()
        
        # 关闭前记录页面总数
        old_count = len(self.window_manager.windows)
        # 清理资源
        self._cleanup_window_resources(window_id)
        
        # 移除AI窗口数据
        self.window_manager.remove_window(window_id)
        
        # 如果关闭的是活动窗口，切换到下一个窗口
        if self.active_ns_window == ns_window:
            self._switch_to_next_window()
        
        print(f"窗口已关闭: {window_id}")
        # 触发页面计数变更回调
        try:
            new_count = len(self.window_manager.windows)
            cb = getattr(self, 'on_page_count_changed', None)
            if callable(cb):
                cb(old_count, new_count)
        except Exception:
            pass
        return True
    
    # Pythonic 别名（不参与 ObjC 选择子转换）
    def close_window(self, window_id):
        return self.closeWindow_(window_id)

    # Pythonic：切换窗口（内部转调 ObjC 方法）
    def switch_to_window(self, window_id):
        """
        切换到指定窗口
        
        Args:
            window_id: 窗口标识符
            
        Returns:
            bool: 切换是否成功
        """
        return self.switchToWindow_(window_id)
    
    # 兼容旧命名（CamelCase）：转调到新方法
    def switchToWindow_(self, window_id):
        """ObjC 风格选择子，实现实际切换逻辑。"""
        if window_id not in self.ns_windows:
            return False
        target_window = self.ns_windows[window_id]
        NSApp.activateIgnoringOtherApps_(True)
        target_window.orderFront_(None)
        target_window.makeKeyAndOrderFront_(None)
        self.active_ns_window = target_window
        self.window_manager.set_active_window(window_id)
        print(f"切换到窗口: {window_id}")
        return True
    
    def get_active_window_id(self):
        """获取当前活动窗口ID"""
        return self.window_manager.active_window_id
    
    def get_platform_windows(self, platform_id):
        """获取指定平台的所有窗口"""
        return self.window_manager.get_platform_windows(platform_id)
    
    def get_all_windows(self):
        """获取所有窗口"""
        return self.window_manager.get_all_windows()
    
    # MARK: - 私有辅助方法
    
    def _create_ns_window(self, ai_window, platform_config):
        """
        创建NSWindow实例
        
        Args:
            ai_window: AI窗口数据
            platform_config: 平台配置
            
        Returns:
            bool: 创建是否成功
        """
        try:
            # 创建无边框、可调整大小的浮动窗口
            content_rect = NSMakeRect(
                ai_window.geometry.x,
                ai_window.geometry.y,
                ai_window.geometry.width,
                ai_window.geometry.height
            )
            
            ns_window = MultiWindowAppWindow.alloc().initWithContentRect_styleMask_backing_defer_windowId_(
                content_rect,
                NSBorderlessWindowMask | NSResizableWindowMask,
                NSBackingStoreBuffered,
                False,
                ai_window.window_id
            )
            
            # 设置窗口属性
            ns_window.setLevel_(NSFloatingWindowLevel)
            ns_window.setCollectionBehavior_(
                NSWindowCollectionBehaviorCanJoinAllSpaces |
                NSWindowCollectionBehaviorStationary
            )
            
            # 设置窗口数据
            ns_window.setWindowData_(ai_window)
            
            # 设置透明属性
            ns_window.setOpaque_(False)
            ns_window.setBackgroundColor_(NSColor.clearColor())
            
            # 防止出现在截图中
            ns_window.setSharingType_(NSWindowSharingNone)
            
            # 设置窗口标题
            window_title = f"{platform_config.display_name} - {ai_window.window_id[:8]}"
            ns_window.setTitle_(window_title)
            ai_window.update_title(window_title)
            
            # 创建内容视图
            if not self._setup_window_content(ns_window, ai_window, platform_config):
                return False
            
            # 保存窗口引用
            self.ns_windows[ai_window.window_id] = ns_window
            
            # 显示窗口
            ns_window.orderFront_(None)
            ns_window.makeKeyAndOrderFront_(None)
            
            return True
            
        except Exception as e:
            print(f"创建NSWindow失败: {e}")
            return False
    
    def _setup_window_content(self, ns_window, ai_window, platform_config):
        """
        设置窗口内容
        
        Args:
            ns_window: NSWindow实例
            ai_window: AI窗口数据
            platform_config: 平台配置
            
        Returns:
            bool: 设置是否成功
        """
        try:
            # 创建内容视图
            content_view = NSView.alloc().initWithFrame_(ns_window.contentView().bounds())
            content_view.setWantsLayer_(True)
            content_view.layer().setCornerRadius_(CORNER_RADIUS)
            content_view.layer().setBackgroundColor_(NSColor.whiteColor().CGColor())
            ns_window.setContentView_(content_view)
            
            # 创建拖拽区域
            content_bounds = content_view.bounds()
            drag_area = MultiWindowDragArea.alloc().initWithFrame_windowManager_(
                NSMakeRect(0, content_bounds.size.height - DRAG_AREA_HEIGHT, 
                          content_bounds.size.width, DRAG_AREA_HEIGHT),
                self
            )
            content_view.addSubview_(drag_area)
            self.drag_areas[ai_window.window_id] = drag_area
            
            # 添加窗口控制按钮
            self._add_window_controls(drag_area, ai_window, content_bounds)
            
            # 创建WebView
            if not self._create_webview(ns_window, ai_window, platform_config, content_view, content_bounds):
                return False
            
            return True
            
        except Exception as e:
            print(f"设置窗口内容失败: {e}")
            return False
    
    def _add_window_controls(self, drag_area, ai_window, content_bounds):
        """
        添加窗口控制按钮
        
        Args:
            drag_area: 拖拽区域
            ai_window: AI窗口数据
            content_bounds: 内容边界
        """
        # 关闭按钮
        try:
            from ..app import PointerButton
            close_button = PointerButton.alloc().initWithFrame_(NSMakeRect(5, 5, 20, 20))
        except Exception:
            close_button = NSButton.alloc().initWithFrame_(NSMakeRect(5, 5, 20, 20))
        close_button.setBordered_(False)
        close_button.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("xmark.circle.fill", None))
        close_button.setTarget_(self)
        close_button.setAction_("closeWindowAction:")
        close_button.window_id = ai_window.window_id
        drag_area.addSubview_(close_button)
        
        # 最小化按钮
        try:
            from ..app import PointerButton
            minimize_button = PointerButton.alloc().initWithFrame_(NSMakeRect(30, 5, 20, 20))
        except Exception:
            minimize_button = NSButton.alloc().initWithFrame_(NSMakeRect(30, 5, 20, 20))
        minimize_button.setBordered_(False)
        minimize_button.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("minus.circle.fill", None))
        minimize_button.setTarget_(self)
        minimize_button.setAction_("minimizeWindowAction:")
        minimize_button.window_id = ai_window.window_id
        drag_area.addSubview_(minimize_button)
        
        # 平台标签
        platform_label = NSTextField.alloc().initWithFrame_(NSMakeRect(60, 5, 100, 20))
        platform_label.setEditable_(False)
        platform_label.setBordered_(False)
        platform_label.setBackgroundColor_(NSColor.clearColor())
        platform_label.setStringValue_(ai_window.platform_id.upper())
        platform_label.setFont_(NSFont.systemFontOfSize_(12))
        drag_area.addSubview_(platform_label)
        
        # 透明度控制按钮
        try:
            from ..app import PointerButton
            decrease_btn = PointerButton.alloc().initWithFrame_(NSMakeRect(content_bounds.size.width - 60, 5, 20, 20))
        except Exception:
            decrease_btn = NSButton.alloc().initWithFrame_(NSMakeRect(content_bounds.size.width - 60, 5, 20, 20))
        decrease_btn.setBordered_(False)
        decrease_btn.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("minus.circle", None))
        decrease_btn.setTarget_(self)
        decrease_btn.setAction_("decreaseTransparencyAction:")
        decrease_btn.window_id = ai_window.window_id
        decrease_btn.setAutoresizingMask_(NSViewMinXMargin)
        drag_area.addSubview_(decrease_btn)
        
        try:
            from ..app import PointerButton
            increase_btn = PointerButton.alloc().initWithFrame_(NSMakeRect(content_bounds.size.width - 30, 5, 20, 20))
        except Exception:
            increase_btn = NSButton.alloc().initWithFrame_(NSMakeRect(content_bounds.size.width - 30, 5, 20, 20))
        increase_btn.setBordered_(False)
        increase_btn.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("plus.circle", None))
        increase_btn.setTarget_(self)
        increase_btn.setAction_("increaseTransparencyAction:")
        increase_btn.window_id = ai_window.window_id
        increase_btn.setAutoresizingMask_(NSViewMinXMargin)
        drag_area.addSubview_(increase_btn)
    
    def _create_webview(self, ns_window, ai_window, platform_config, content_view, content_bounds):
        """
        创建WebView
        
        Args:
            ns_window: NSWindow实例
            ai_window: AI窗口数据
            platform_config: 平台配置
            content_view: 内容视图
            content_bounds: 内容边界
            
        Returns:
            bool: 创建是否成功
        """
        try:
            # 创建WebView配置
            config = WKWebViewConfiguration.alloc().init()
            config.preferences().setJavaScriptCanOpenWindowsAutomatically_(True)
            
            # 创建WebView
            webview = WKWebView.alloc().initWithFrame_configuration_(
                NSMakeRect(0, 0, content_bounds.size.width, 
                          content_bounds.size.height - DRAG_AREA_HEIGHT),
                config
            )
            
            # 设置WebView属性
            webview.setUIDelegate_(self)
            webview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            webview.setCustomUserAgent_(self.safari_user_agent)
            
            # 添加到内容视图
            content_view.addSubview_(webview)
            
            # 保存WebView引用
            self.webviews[ai_window.window_id] = webview
            
            # 加载平台URL
            ai_window.update_url(platform_config.url)
            url = NSURL.URLWithString_(platform_config.url)
            request = NSURLRequest.requestWithURL_(url)
            webview.loadRequest_(request)
            
            return True
            
        except Exception as e:
            print(f"创建WebView失败: {e}")
            return False
    
    def _calculate_new_window_position(self):
        """
        计算新窗口的位置
        
        Returns:
            tuple: (x, y) 坐标
        """
        # 获取现有窗口数量
        window_count = len(self.ns_windows)
        
        # 基础位置
        base_x, base_y = self.default_window_position
        
        # 计算偏移
        offset = window_count * self.window_offset
        
        return (base_x + offset, base_y + offset)
    
    def _cleanup_window_resources(self, window_id):
        """
        清理窗口资源
        
        Args:
            window_id: 窗口ID
        """
        # 清理NSWindow引用
        if window_id in self.ns_windows:
            del self.ns_windows[window_id]
        
        # 清理WebView引用
        if window_id in self.webviews:
            del self.webviews[window_id]
        
        # 清理拖拽区域引用
        if window_id in self.drag_areas:
            del self.drag_areas[window_id]
    
    def _switch_to_next_window(self):
        """切换到下一个可用窗口"""
        available_windows = list(self.ns_windows.values())
        if available_windows:
            next_window = available_windows[0]
            window_id = next_window.window_id
            self.switch_to_window(window_id)
        else:
            self.active_ns_window = None
    
    # MARK: - 窗口控制动作方法
    
    def closeWindowAction_(self, sender):
        """关闭窗口动作"""
        window_id = getattr(sender, 'window_id', None)
        if window_id:
            self.close_window(window_id)
    
    def minimizeWindowAction_(self, sender):
        """最小化窗口动作"""
        window_id = getattr(sender, 'window_id', None)
        if window_id and window_id in self.ns_windows:
            ns_window = self.ns_windows[window_id]
            ns_window.miniaturize_(sender)
            
            # 更新AI窗口状态
            ai_window = self.window_manager.get_window(window_id)
            if ai_window:
                ai_window.minimize()
    
    def increaseTransparencyAction_(self, sender):
        """增加透明度动作"""
        window_id = getattr(sender, 'window_id', None)
        if window_id and window_id in self.ns_windows:
            ns_window = self.ns_windows[window_id]
            current = ns_window.alphaValue()
            new_alpha = min(current + 0.1, 1.0)
            ns_window.setAlphaValue_(new_alpha)
    
    def decreaseTransparencyAction_(self, sender):
        """减少透明度动作"""
        window_id = getattr(sender, 'window_id', None)
        if window_id and window_id in self.ns_windows:
            ns_window = self.ns_windows[window_id]
            current = ns_window.alphaValue()
            new_alpha = max(current - 0.1, 0.2)
            ns_window.setAlphaValue_(new_alpha)
    
    # MARK: - WebView委托方法
    
    def webView_requestMediaCapturePermissionForOrigin_initiatedByFrame_type_decisionListener_(
        self, webView, origin, frame, mediaType, listener
    ):
        """自动授予媒体捕获权限"""
        listener.grant()
    
    # MARK: - 窗口委托方法
    
    def windowDidResize_(self, notification):
        """窗口大小改变时的处理"""
        ns_window = notification.object()
        window_id = getattr(ns_window, 'window_id', None)
        
        if window_id and window_id in self.drag_areas and window_id in self.webviews:
            # 更新拖拽区域和WebView的布局
            bounds = ns_window.contentView().bounds()
            w, h = bounds.size.width, bounds.size.height
            
            drag_area = self.drag_areas[window_id]
            webview = self.webviews[window_id]
            
            drag_area.setFrame_(NSMakeRect(0, h - DRAG_AREA_HEIGHT, w, DRAG_AREA_HEIGHT))
            webview.setFrame_(NSMakeRect(0, 0, w, h - DRAG_AREA_HEIGHT))
            
            # 更新AI窗口几何信息
            ai_window = self.window_manager.get_window(window_id)
            if ai_window:
                frame = ns_window.frame()
                ai_window.update_geometry(
                    int(frame.origin.x),
                    int(frame.origin.y),
                    int(frame.size.width),
                    int(frame.size.height)
                )
    
    # MARK: - 公共接口方法
    
    def get_window_count(self):
        """获取当前窗口总数"""
        return len(self.ns_windows)
    
    def get_platform_window_count(self, platform_id):
        """获取指定平台的窗口数量"""
        return self.window_manager.get_platform_window_count(platform_id)
    
    def canCreateWindowForPlatform_(self, platform_id):
        """检查是否可以为指定平台创建窗口"""
        return self.window_manager.can_create_window(platform_id)
    
    def closeAllPlatformWindows_(self, platform_id):
        """关闭指定平台的所有窗口"""
        platform_windows = self.window_manager.get_platform_windows(platform_id)
        closed_count = 0
        
        for ai_window in platform_windows:
            if self.close_window(ai_window.window_id):
                closed_count += 1
        
        return closed_count
    
    def hide_all_windows(self):
        """隐藏所有窗口"""
        for ns_window in self.ns_windows.values():
            ns_window.orderOut_(None)
    
    def show_all_windows(self):
        """显示所有窗口"""
        for ns_window in self.ns_windows.values():
            ns_window.orderFront_(None)
    
    def getWindowListForPlatform_(self, platform_id):
        """获取指定平台的窗口列表信息"""
        platform_windows = self.window_manager.get_platform_windows(platform_id)
        window_list = []
        
        for ai_window in platform_windows:
            window_info = {
                'window_id': ai_window.window_id,
                'title': ai_window.title,
                'state': ai_window.state.value,
                'url': ai_window.url,
                'created_at': ai_window.created_at.isoformat(),
                'is_active': ai_window.window_id == self.window_manager.active_window_id
            }
            window_list.append(window_info)
        
        return window_list
