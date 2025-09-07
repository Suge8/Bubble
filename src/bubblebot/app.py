

# Python libraries
import os
import sys
import signal

import objc
from AppKit import *
from AppKit import NSCursor
from AppKit import NSWindowSharingNone
from WebKit import *
from Quartz import *
from AVFoundation import AVCaptureDevice, AVMediaTypeAudio
# Accessibility prompt import with fallback
try:
    from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
except ImportError:
    AXIsProcessTrustedWithOptions = None
    kAXTrustedCheckOptionPrompt = None
from Foundation import NSObject, NSURL, NSURLRequest, NSDate, NSTimer, NSBundle, NSNumber, NSData
from CoreFoundation import kCFRunLoopCommonModes

# Quiet verbose logs unless BB_DEBUG=1 (keep only essentials)
import builtins as _builtins
_orig_print = _builtins.print
def _filtered_print(*args, **kwargs):
    if os.environ.get('BB_DEBUG') == '1':
        return _orig_print(*args, **kwargs)
    if not args:
        return
    first = str(args[0])
    essentials = (
        '主页已加载',
        'AI服务已加载',
        '导航失败',
        '不支持的AI平台',
        'ERROR',
        'WARNING'
    )
    if any(key in first for key in essentials):
        return _orig_print(*args, **kwargs)
    # silence everything else
    return
print = _filtered_print

# Local libraries
from .constants import (
    APP_TITLE,
    CORNER_RADIUS,
    DRAG_AREA_HEIGHT,
    LOGO_BLACK_PATH,
    LOGO_WHITE_PATH,
    FRAME_SAVE_NAME,
    STATUS_ITEM_CONTEXT,
    WEBSITE,
)
from .listener import (
    global_show_hide_listener,
    load_custom_launcher_trigger,
    set_custom_launcher_trigger,
    SPECIAL_KEY_NAMES,
)
from .components.platform_manager import PlatformManager
from .components.config_manager import ConfigManager
from .i18n import t as _t, set_language as _set_lang, get_language as _get_lang
from .constants import LAUNCHER_TRIGGER


# Add AI service endpoints
AI_SERVICES = {
    "Grok": "https://grok.com",
    "Gemini": "https://gemini.google.com",
    "ChatGPT": "https://chat.openai.com",
    "Claude": "https://claude.ai/chat",
    "DeepSeek": "https://chat.deepseek.com",
}

# Custom window (contains entire application).
class AppWindow(NSWindow):

    def initWithContentRect_styleMask_backing_defer_(self, contentRect, styleMask, backing, defer):
        """初始化窗口实例"""
        self = objc.super(AppWindow, self).initWithContentRect_styleMask_backing_defer_(
            contentRect, styleMask, backing, defer
        )
        if self:
            # 多实例支持属性
            self.window_id = None
            self.platform_id = None
            self.window_instance_data = None
        return self

    def setWindowInstanceData_windowId_platformId_(self, instance_data, window_id, platform_id):
        """设置窗口实例数据"""
        self.window_instance_data = instance_data
        self.window_id = window_id
        self.platform_id = platform_id

    def getWindowInstanceData(self):
        """获取窗口实例数据"""
        return self.window_instance_data

    def getWindowId(self):
        """获取窗口ID"""
        return self.window_id

    def getPlatformId(self):
        """获取平台ID"""
        return self.platform_id

    # Explicitly allow key window status
    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return True
    
    def acceptsFirstResponder(self):
        return True

    # Required to capture "Command+..." sequences.
    def keyDown_(self, event):
        delegate = self.delegate()
        if delegate and hasattr(delegate, 'keyDown_'):
            delegate.keyDown_(event)
        else:
            # Fallback to default handling
            objc.super(AppWindow, self).keyDown_(event)


class ClickThroughView(NSView):
    """A view that never intercepts mouse events (click-through)."""
    def hitTest_(self, point):
        return None


class TopBarView(NSView):
    """Custom top bar used for dragging the window and hosting the AI selector."""
    def mouseDown_(self, event):
        if self.window():
            # 支持按压后拖动整个窗口
            self.window().performWindowDragWithEvent_(event)

    def hitTest_(self, point):
        """允许在空白区域命中自身以便拖动；控件区域仍命中控件。"""
        v = objc.super(TopBarView, self).hitTest_(point)
        return v


class PointerButton(NSButton):
    def initWithFrame_(self, frame):
        self = objc.super(PointerButton, self).initWithFrame_(frame)
        if self is None:
            return None
        try:
            self.setWantsLayer_(True)
            self.layer().setCornerRadius_(8.0)
            self.layer().setMasksToBounds_(True)
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.05).CGColor())
            self.layer().setShadowColor_(NSColor.blackColor().CGColor())
            self.layer().setShadowOpacity_(0.0)
            self.layer().setShadowRadius_(6.0)
            self.layer().setShadowOffset_(NSMakeSize(0, -1))
        except Exception:
            pass
        self._tracking_area = None
        return self

    def resetCursorRects(self):
        try:
            self.discardCursorRects()
            self.addCursorRect_cursor_(self.bounds(), NSCursor.pointingHandCursor())
        except Exception:
            pass

    def updateTrackingAreas(self):
        try:
            if self._tracking_area is not None:
                self.removeTrackingArea_(self._tracking_area)
            opts = NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect
            self._tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(self.bounds(), opts, self, None)
            self.addTrackingArea_(self._tracking_area)
        except Exception:
            pass
        objc.super(PointerButton, self).updateTrackingAreas()

    def _animate_layer(self, key, from_value, to_value, duration=0.18):
        # 去除依赖后不再执行显式动画，直接快速切换由 NSView 呈现
        return

    def mouseEntered_(self, event):
        try:
            self._animate_layer("transform.scale", None, 1.03)
            self._animate_layer("shadowOpacity", None, 0.28)
            # 轻微提亮背景
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.10).CGColor())
        except Exception:
            pass

    def mouseExited_(self, event):
        try:
            self._animate_layer("transform.scale", None, 1.0)
            self._animate_layer("shadowOpacity", None, 0.0)
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.05).CGColor())
            self._bg_set(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.90).CGColor(), 0.15)
        except Exception:
            pass

    def mouseDown_(self, event):
        try:
            self._animate_layer("transform.scale", None, 0.98, 0.12)
            self._animate_layer("shadowOpacity", None, 0.35, 0.12)
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.14).CGColor())
        except Exception:
            pass
        objc.super(PointerButton, self).mouseDown_(event)

    def mouseUp_(self, event):
        try:
            self._animate_layer("transform.scale", None, 1.02, 0.12)
            self._animate_layer("shadowOpacity", None, 0.25, 0.12)
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.10).CGColor())
        except Exception:
            pass
        objc.super(PointerButton, self).mouseUp_(event)


class PointerPopUpButton(NSPopUpButton):
    def initWithFrame_pullsDown_(self, frame, pullsDown):
        self = objc.super(PointerPopUpButton, self).initWithFrame_pullsDown_(frame, pullsDown)
        if self is None:
            return None
        try:
            self.setWantsLayer_(True)
            self.layer().setCornerRadius_(8.0)
            self.layer().setMasksToBounds_(True)
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.05).CGColor())
            self.layer().setShadowColor_(NSColor.blackColor().CGColor())
            self.layer().setShadowOpacity_(0.0)
            self.layer().setShadowRadius_(6.0)
            self.layer().setShadowOffset_(NSMakeSize(0, -1))
        except Exception:
            pass
        self._tracking_area = None
        return self

    def resetCursorRects(self):
        try:
            self.discardCursorRects()
            self.addCursorRect_cursor_(self.bounds(), NSCursor.pointingHandCursor())
        except Exception:
            pass

class BackPointerButton(PointerButton):
    def setBackgroundView_(self, view):
        self._bg_view = view

    def _bg_set(self, color=None, shadow=None):
        try:
            if not hasattr(self, '_bg_view') or not self._bg_view:
                return
            self._bg_view.setWantsLayer_(True)
            if color is not None:
                self._bg_view.layer().setBackgroundColor_(color)
            if shadow is not None:
                self._bg_view.layer().setShadowOpacity_(shadow)
        except Exception:
            pass

    def mouseEntered_(self, event):
        objc.super(BackPointerButton, self).mouseEntered_(event)
        try:
            # 与下拉框背景一致：白色 + 透明度变化
            self._bg_set(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.95).CGColor(), 0.25)
        except Exception:
            pass

    def mouseExited_(self, event):
        objc.super(BackPointerButton, self).mouseExited_(event)
        try:
            self._bg_set(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.90).CGColor(), 0.15)
        except Exception:
            pass

    def mouseDown_(self, event):
        try:
            self._bg_set(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.85).CGColor(), 0.30)
        except Exception:
            pass
        objc.super(BackPointerButton, self).mouseDown_(event)

    def mouseUp_(self, event):
        objc.super(BackPointerButton, self).mouseUp_(event)
        try:
            self._bg_set(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.92).CGColor(), 0.22)
        except Exception:
            pass

    def updateTrackingAreas(self):
        try:
            if self._tracking_area is not None:
                self.removeTrackingArea_(self._tracking_area)
            opts = NSTrackingMouseEnteredAndExited | NSTrackingActiveAlways | NSTrackingInVisibleRect
            self._tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(self.bounds(), opts, self, None)
            self.addTrackingArea_(self._tracking_area)
        except Exception:
            pass
        # 修复super调用目标错误
        objc.super(BackPointerButton, self).updateTrackingAreas()

    def _animate_layer(self, key, from_value, to_value, duration=0.18):
        return

    def mouseEntered_(self, event):
        try:
            self._animate_layer("transform.scale", None, 1.02)
            self._animate_layer("shadowOpacity", None, 0.22)
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.10).CGColor())
            # 同步圆形背景为白色系（与下拉一致）
            self._bg_set(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.95).CGColor(), 0.25)
        except Exception:
            pass

    def mouseExited_(self, event):
        try:
            self._animate_layer("transform.scale", None, 1.0)
            self._animate_layer("shadowOpacity", None, 0.0)
            self.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.05).CGColor())
        except Exception:
            pass





# The main delegate for running the overlay app.
class AppDelegate(NSObject):
    def init(self):
        """ObjC 风格初始化，确保属性存在（PyObjC 推荐实现）。"""
        self = objc.super(AppDelegate, self).init()
        if self is None:
            return None
        self.homepage_manager = None
        self.navigation_controller = None
        self.platform_manager = None
        self.exit_check_timer = None  # 退出检查定时器
        # 单窗口多页面：同一 NSWindow 内持有多个后台 WKWebView
        self._pages_map = {}
        self._page_meta = {}
        self._active_page_id = None
        # 批量关闭标记：用于一次性关闭大量页面时抑制重复 UI 刷新
        self._batch_closing = False
        # 批量恢复标记：启动时从配置恢复各平台页面，避免反复刷新
        self._batch_restoring = False
        self._restored_pages_done = False

        # 多窗口管理器支持
        self.multiwindow_manager = None
        self.is_multiwindow_mode = False  # 是否启用多窗口模式

        # 传统单窗口相关属性（向后兼容）
        self.window = None
        self.webview = None
        self.ai_selector = None  # 初始化为None，在applicationDidFinishLaunching_中创建
        self.ai_selector_map = {}  # 下拉选项索引 -> {platform_id, window_id}
        self.top_bar = None
        self.back_button = None
        self.selector_bg = None
        self.back_button_bg = None
        self.last_loaded_is_homepage = False
        self.root_view = None
        self.skeleton_view = None
        self.memory_bubble_view = None
        self._memory_bubble_dismissed = False
        self._page_count_last = 0
        # 错误覆盖层（导航失败提示）
        self.error_overlay = None
        self._error_label = None
        self.window_initialized = False
        self._suppress_ai_action = False
        # 抑制下一次骨架屏显示（用于主页刷新等场景）
        self._skeleton_suppress_next = False
        # 抑制直到完成（用于整个主页加载生命周期，避免双事件触发闪烁）
        self._skeleton_suppress_until_finish = False
        # 活动 Toast 引用，便于覆盖/移除
        self._active_toast = None
        return self

    # -------- Language: initial apply and runtime changes --------
    def _apply_initial_language(self):
        try:
            lang = ConfigManager.get_language()
            if not lang:
                lang = ConfigManager.detect_system_language()
                ConfigManager.set_language(lang)
            _set_lang(lang)
            print(f"DEBUG: 应用语言: {lang}")
        except Exception as e:
            print(f"WARNING: 初始化语言失败: {e}")

    def changeLanguage_(self, new_lang):
        """ObjC-bridgeable setter for language changes at runtime."""
        try:
            lang = str(new_lang)
            ConfigManager.set_language(lang)
            _set_lang(lang)
            self._broadcast_language_changed()
        except Exception as e:
            print(f"WARNING: 切换语言失败: {e}")

    def _broadcast_language_changed(self):
        # Refresh status menu labels (if available)
        try:
            self._refresh_status_menu_titles()
        except Exception:
            pass
        # Refresh homepage if showing
        try:
            if self.navigation_controller and self.navigation_controller.current_page == 'homepage':
                if self.homepage_manager and hasattr(self.homepage_manager, 'on_language_changed'):
                    self.homepage_manager.on_language_changed()
                self._load_homepage()
        except Exception:
            pass
        # Notify navigation controller to update UI elements
        try:
            if self.navigation_controller and hasattr(self.navigation_controller, 'on_language_changed'):
                self.navigation_controller.on_language_changed()
        except Exception:
            pass
        # Refresh settings window labels if open
        try:
            if hasattr(self, '_settings_window') and self._settings_window:
                if hasattr(self._settings_window, '_apply_localization'):
                    self._settings_window._apply_localization()
        except Exception:
            pass

    def _i18n_or_default(self, key, default_text, **kwargs):
        try:
            text = _t(key, **kwargs)
            # our t() returns the key string if missing; detect and fallback
            if text == key:
                return default_text
            return text
        except Exception:
            return default_text

    # -------- Toast（页面阈值） --------
    def show_toast(self, text: str, duration: float = 3.0):
        """在当前窗口显示轻量 Toast（内联简易版）。"""
        self._inline_toast(text, duration)

    def dismissToast_(self, timer):
        try:
            toast = timer.userInfo()
            if os.environ.get('BB_NO_EFFECTS') != '1':
                NSAnimationContext.beginGrouping()
                NSAnimationContext.currentContext().setDuration_(0.18)
                toast.animator().setAlphaValue_(0.0)
                NSAnimationContext.endGrouping()
            toast.removeFromSuperview()
        except Exception:
            pass

    def _maybe_show_page_threshold_toast(self, old: int, new: int):
        try:
            # 规则：当总页数首次从 <=4 跨到 >4 时提示一次；
            # 之后减少到 <=5 再次跨过 >5 时再次提示。
            if int(old) <= 4 and int(new) > 4:
                msg = self._i18n_or_default('toast.tooManyPages', '页面较多可能占用内存导致卡顿')
                self._inline_toast(msg, duration=3.0)
            try:
                print(f"DEBUG: page_threshold_check old={old} new={new} trigger={int(old)<=4 and int(new)>4}")
            except Exception:
                pass
        except Exception:
            pass

    def notify_page_count_changed(self, old: int, new: int):
        """供多窗口管理器回调：页面计数变化时的处理。"""
        self._maybe_show_page_threshold_toast(old, new)

    # 简单内联 Toast（与设置页一致）
    def _inline_toast(self, text: str, duration: float = 3.0):
        """将简易 Toast 添加到最可能可见的容器上。

        策略：
        - 多窗口：优先使用所有窗口的 drag_area（顶栏），其次 contentView。
        - 单窗口：使用 root_view 或 window.contentView。
        """
        parents = []
        try:
            if bool(getattr(self, 'is_multiwindow_mode', False)) and getattr(self, 'multiwindow_manager', None):
                mw = self.multiwindow_manager
                # 1) 所有 drag_area（最上层顶栏容器）
                try:
                    for da in list(getattr(mw, 'drag_areas', {}).values()):
                        if da is not None:
                            parents.append(da)
                except Exception:
                    pass
                # 2) 所有 contentView（兜底）
                try:
                    for w in list(getattr(mw, 'ns_windows', {}).values()):
                        try:
                            cv = w.contentView()
                            if cv is not None:
                                parents.append(cv)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        if not parents:
            p = self.root_view if getattr(self, 'root_view', None) is not None else (self.window.contentView() if self.window else None)
            if p is not None:
                parents = [p]
        if not parents:
            return
        for parent in parents:
            try:
                bounds = parent.bounds()
                # 在 drag_area（顶栏）上：右上角；在 contentView 上：上方居中
                is_drag = parent.__class__.__name__.endswith('MultiWindowDragArea')
                tw, th = (260, 36)
                margin = 12
                if is_drag:
                    tx = max(margin, bounds.size.width - tw - margin)
                    ty = (bounds.size.height - th) / 2.0
                else:
                    tx = (bounds.size.width - tw) / 2.0
                    ty = max(margin, bounds.size.height - th - margin)
                toast = NSView.alloc().initWithFrame_(NSMakeRect(tx, ty, tw, th))
                toast.setWantsLayer_(True)
                toast.layer().setCornerRadius_(8.0)
                toast.layer().setBackgroundColor_(NSColor.blackColor().colorWithAlphaComponent_(0.92).CGColor())
                lbl = NSTextField.alloc().initWithFrame_(NSMakeRect(12, 8, tw - 24, th - 16))
                lbl.setBezeled_(False); lbl.setDrawsBackground_(False); lbl.setEditable_(False); lbl.setSelectable_(False)
                try:
                    lbl.setTextColor_(NSColor.whiteColor())
                except Exception:
                    pass
                try:
                    lbl.setFont_(NSFont.systemFontOfSize_(13))
                except Exception:
                    pass
                lbl.setStringValue_(str(text) if text is not None else "")
                toast.addSubview_(lbl)
                toast.setAlphaValue_(0.0)
                try:
                    subs = list(parent.subviews())
                    anchor = subs[-1] if subs else None
                    if hasattr(parent, 'addSubview_positioned_relativeTo_'):
                        parent.addSubview_positioned_relativeTo_(toast, NSWindowAbove, anchor)
                    else:
                        parent.addSubview_(toast)
                except Exception:
                    parent.addSubview_(toast)
                try:
                    if os.environ.get('BB_NO_EFFECTS') != '1':
                        NSAnimationContext.beginGrouping()
                        NSAnimationContext.currentContext().setDuration_(0.18)
                        toast.animator().setAlphaValue_(1.0)
                        NSAnimationContext.endGrouping()
                    else:
                        toast.setAlphaValue_(1.0)
                except Exception:
                    toast.setAlphaValue_(1.0)
                try:
                    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                        float(duration or 3.0), self, 'dismissToast:', toast, False
                    )
                except Exception:
                    try:
                        toast.removeFromSuperview()
                    except Exception:
                        pass
                try:
                    pos = 'drag' if is_drag else 'content'
                    print(f"DEBUG: inline_toast added pos={pos} tx={tx} ty={ty} parent={parent}")
                except Exception:
                    pass
            except Exception:
                pass

    # -------- One-time notice bubble (e.g., config migration) --------
    def _ensure_notice_bubble(self):
        if getattr(self, 'notice_bubble_view', None) is not None:
            return
        try:
            self.notice_bubble_view = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, 360, 24))
            self.notice_bubble_view.setWantsLayer_(True)
            self.notice_bubble_view.layer().setCornerRadius_(12)
            self.notice_bubble_view.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.92).CGColor())
            self.notice_bubble_view.layer().setBorderColor_(NSColor.colorWithCalibratedWhite_alpha_(0.85, 1.0).CGColor())
            self.notice_bubble_view.layer().setBorderWidth_(1.0)
            # Label (store reference)
            self.notice_label = NSTextField.alloc().initWithFrame_(NSMakeRect(10, 3, 300, 18))
            self.notice_label.setBezeled_(False)
            self.notice_label.setDrawsBackground_(False)
            self.notice_label.setEditable_(False)
            self.notice_label.setSelectable_(False)
            self.notice_label.setFont_(NSFont.systemFontOfSize_(11))
            self.notice_label.setStringValue_("")
            self.notice_bubble_view.addSubview_(self.notice_label)
            # Dismiss button (×)
            ndismiss = NSButton.alloc().initWithFrame_(NSMakeRect(320, 2, 20, 20))
            ndismiss.setBordered_(False)
            ndismiss.setTitle_("×")
            ndismiss.setTarget_(self)
            ndismiss.setAction_("dismissNotice:")
            self.notice_bubble_view.addSubview_(ndismiss)
            # position top-right
            tb = self.top_bar
            bx = tb.frame().size.width - 370
            by = (self.top_bar_height - 24) / 2
            self.notice_bubble_view.setFrameOrigin_(NSMakePoint(bx, by))
            tb.addSubview_(self.notice_bubble_view)
            self.notice_bubble_view.setHidden_(True)
        except Exception:
            self.notice_bubble_view = None

    def _show_migration_notice_if_pending(self):
        try:
            from .components.config_manager import ConfigManager as _CM
        except Exception:
            return
        try:
            if not _CM.needs_migration_notice():
                return
            self._ensure_notice_bubble()
            if getattr(self, 'notice_bubble_view', None) is None:
                return
            msg = self._i18n_or_default('notice.configMigrated', 'Settings moved to new Bubble folder. Backup kept.')
            try:
                if getattr(self, 'notice_label', None) is not None:
                    self.notice_label.setStringValue_(msg)
            except Exception:
                pass
            # show
            self.notice_bubble_view.setHidden_(False)
        except Exception:
            pass

    def dismissNotice_(self, sender):
        try:
            if getattr(self, 'notice_bubble_view', None):
                self.notice_bubble_view.setHidden_(True)
            from .components.config_manager import ConfigManager as _CM
            try:
                _CM.mark_migration_notice_shown()
            except Exception:
                pass
        except Exception:
            pass

    def setHomepageManager_(self, manager):
        """设置主页管理器"""
        self.homepage_manager = manager

    def setNavigationController_(self, controller):
        """设置导航控制器"""
        self.navigation_controller = controller

    def setMultiwindowManager_(self, manager):
        """设置多窗口管理器"""
        self.multiwindow_manager = manager
        try:
            # 注册页面计数变化回调，用于阈值 Toast
            if hasattr(self.multiwindow_manager, 'on_page_count_changed'):
                self.multiwindow_manager.on_page_count_changed = self.notify_page_count_changed
            # 同步窗口开关事件到主页与下拉
            if hasattr(self.multiwindow_manager, 'on_window_opened'):
                self.multiwindow_manager.on_window_opened = self._on_multiwin_opened
            if hasattr(self.multiwindow_manager, 'on_window_closed'):
                self.multiwindow_manager.on_window_closed = self._on_multiwin_closed
        except Exception:
            pass
        # 默认启用多窗口模式，保障切换不重载
        try:
            self.enable_multiwindow_mode()
        except Exception:
            pass
        # 当设置多窗口管理器时，更新AI选择器（只有在已初始化的情况下）
        if hasattr(self, 'ai_selector') and self.ai_selector:
            self._populate_ai_selector()

    def setPlatformManager_(self, manager):
        """设置平台管理器"""
        self.platform_manager = manager
        # 添加平台配置变更监听器
        self.platform_manager.add_change_listener(self._on_platform_config_changed)

    def enable_multiwindow_mode(self):
        """启用多窗口模式"""
        self.is_multiwindow_mode = True
        # 更新AI选择器显示样式
        if hasattr(self, 'ai_selector') and self.ai_selector:
            self._populate_ai_selector()
        print("多窗口模式已启用")

    def disable_multiwindow_mode(self):
        """禁用多窗口模式"""
        self.is_multiwindow_mode = False
        # 更新AI选择器显示样式
        if hasattr(self, 'ai_selector') and self.ai_selector:
            self._populate_ai_selector()
        print("多窗口模式已禁用")

    def get_current_window_id(self):
        """获取当前活动窗口ID"""
        if self.is_multiwindow_mode and self.multiwindow_manager:
            return self.multiwindow_manager.get_active_window_id()
        elif self.window and hasattr(self.window, 'getWindowId'):
            return self.window.getWindowId()
        return None

    def handleWindowDragEvent_forWindowId_(self, event, window_id):
        """处理窗口拖拽事件（由DragArea调用）"""
        if self.is_multiwindow_mode and self.multiwindow_manager:
            # 多窗口模式：切换到指定窗口并执行拖拽
            self.multiwindow_manager.switch_to_window(window_id)

        # 执行窗口拖拽
        window = event.window()
        if window:
            window.performWindowDragWithEvent_(event)

    def applicationWillTerminate_(self, notification):
        """应用将要终止时的清理工作"""
        print("BubbleBot 正在退出...")

        # 清理事件监听器
        if hasattr(self, 'eventTap') and self.eventTap:
            try:
                from Quartz import CGEventTapEnable
                CGEventTapEnable(self.eventTap, False)
            except:
                pass

        # 清理本地鼠标监听器
        if hasattr(self, 'local_mouse_monitor') and self.local_mouse_monitor:
            try:
                NSEvent.removeMonitor_(self.local_mouse_monitor)
            except:
                pass

        # 清理多窗口管理器
        if self.multiwindow_manager:
            try:
                self.multiwindow_manager.cleanup()
            except:
                pass

        print("BubbleBot 清理完成")
        
        # 强制退出，确保不会卡住
        import os
        import threading
        def force_exit():
            import time
            time.sleep(1)  # 给清理一点时间
            os._exit(0)
        
        threading.Thread(target=force_exit, daemon=True).start()

        # 清理外观观察者，防止退出阶段 KVO/通知触发崩溃
        try:
            if getattr(self, 'status_item', None) is not None:
                btn = self.status_item.button()
                if btn is not None:
                    try:
                        btn.removeObserver_forKeyPath_(self, "effectiveAppearance")
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self)
        except Exception:
            pass
    
    def checkExitStatus_(self, timer):
        """定期检查是否需要退出"""
        try:
            # 导入main模块的退出标志
            from . import main
            if hasattr(main, 'exit_requested') and main.exit_requested:
                print("DEBUG: 检测到退出请求，正在关闭应用...")
                if self.exit_check_timer:
                    self.exit_check_timer.invalidate()
                    self.exit_check_timer = None
                NSApp.terminate_(None)
        except Exception as e:
            print(f"DEBUG: 检查退出状态异常: {e}")

    def ensureActive_(self, timer):
        """不再强制置顶，保留为空壳以兼容旧选择子。"""
        if hasattr(self, 'activation_timer') and self.activation_timer:
            try:
                self.activation_timer.invalidate()
            except Exception:
                pass
            self.activation_timer = None
    # The main application setup.
    def applicationDidFinishLaunching_(self, notification):
        print("AppDelegate.applicationDidFinishLaunching_ 被调用")
        # Migrate config path from BubbleBot -> Bubble (Task 0.2)
        try:
            ConfigManager.migrate_config_if_needed()
        except Exception as _e:
            pass
        # Apply language as early as possible so UI strings use the right locale
        self._apply_initial_language()
        # 省略环境日志
        
        # 设置应用图标（初次设置 + 延迟再应用，确保 Dock 已就绪后刷新）
        print("DEBUG: 设置应用图标...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self._icon_icns_path = os.path.join(script_dir, "logo/icon.icns")
        # Prefer the highest resolution PNG for crisp Dock icon when setting at runtime
        hi_png = os.path.join(script_dir, "logo/icon.iconset/icon_512x512@2x.png")
        lo_png = os.path.join(script_dir, "logo/icon.iconset/icon_512x512.png")
        self._icon_png_path = hi_png if os.path.exists(hi_png) else lo_png
        self._applyDockIconOnce()

        # Check for accessibility permissions (简化版本，不阻塞)
        print("DEBUG: 检查辅助功能权限...")
        if AXIsProcessTrustedWithOptions is not None:
            # 不显示权限请求对话框，只检查状态（传 None 更安全，避免桥接空 dict 崩溃）
            try:
                is_trusted = AXIsProcessTrustedWithOptions(None)
            except Exception as e:
                print(f"WARNING: AXIsProcessTrustedWithOptions 检查失败：{e}")
                is_trusted = False
            if not is_trusted:
                print("WARNING: 辅助功能权限未授予，某些功能可能受限")
                print("请在系统设置 > 隐私与安全性 > 辅助功能 中添加 Bubble 并启用")
            else:
                print("DEBUG: 辅助功能权限已授予")
        else:
            print("DEBUG: 无法检查辅助功能权限（API不可用）")

        # Placeholders for event tap and its run loop source
        self.eventTap = None
        self.eventTapSource = None

        # 设置为普通应用，确保窗口可见
        print("DEBUG: 设置应用激活策略为 NSApplicationActivationPolicyRegular")
        current_policy = NSApp.activationPolicy()
        print(f"DEBUG: 当前激活策略: {current_policy}")
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        new_policy = NSApp.activationPolicy()
        print(f"DEBUG: 新激活策略: {new_policy}")
        if new_policy != NSApplicationActivationPolicyRegular:
            print("WARNING: 激活策略设置失败！")
        # Dock tile 可能尚未附着，稍后再次刷新一次图标，避免首次设置被忽略
        try:
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.25, self, 'reapplyDockIcon:', None, False
            )
        except Exception as _e:
            pass

        # 激活应用；窗口创建放到事件循环开始后（避免白屏/生命周期不同步）
        try:
            NSApp.activateIgnoringOtherApps_(True)
        except Exception:
            pass
        # 安装一个空转计时器，帮助 Python 及时处理 Ctrl+C 信号
        try:
            self._keepalive_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.25, self, 'keepAlive:', None, True
            )
        except Exception:
            self._keepalive_timer = None
        try:
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.05, self, 'initializeWindow:', None, False
            )
        except Exception:
            # 兜底直接调用（一般不会触发）
            try:
                self.performSelector_withObject_afterDelay_('initializeWindow:', None, 0.01)
            except Exception:
                pass

    def initializeWindow_(self, _):
        try:
            if not getattr(self, 'window_initialized', False):
                self.applicationDidBecomeActive_(None)
        except Exception:
            pass

    def keepAlive_(self, _):
        # 空方法：仅用于唤醒解释器，确保 SIGINT 能被及时处理
        return

    # 确保 Dock 图标实际刷新：首次设置与延迟/激活后再设置
    def _applyDockIconOnce(self):
        try:
            # 打包后（.app）优先使用 icns；开发模式优先使用 PNG+圆角，确保 Dock 立刻显示圆角
            applied = False
            is_packaged = False
            try:
                bundle = NSBundle.mainBundle()
                bp = str(bundle.bundlePath()) if bundle else ''
                is_packaged = bool(bp and bp.endswith('.app')) or bool(getattr(sys, 'frozen', False))
            except Exception:
                is_packaged = False

            force_png = os.environ.get('BB_FORCE_PNG_ICON') == '1'

            if not is_packaged or force_png:
                # 开发模式/强制：使用高分辨率 PNG 并主动圆角
                if hasattr(self, '_icon_png_path') and self._icon_png_path and os.path.exists(self._icon_png_path):
                    img = NSImage.alloc().initWithContentsOfFile_(self._icon_png_path)
                    if img:
                        try:
                            sz = img.size()
                            radius = max(6.0, min(sz.width, sz.height) * 0.20)
                        except Exception:
                            radius = 96.0
                        rounded = self._rounded_nsimage(img, radius)
                        NSApp.setApplicationIconImage_(rounded or img)
                        applied = True
                        print(f"DEBUG: 开发模式，Dock 图标采用 PNG 圆角: {self._icon_png_path}")

            if not applied:
                # 打包模式默认：icns（系统标准遮罩），若缺失则回退 PNG 圆角
                if hasattr(self, '_icon_icns_path') and self._icon_icns_path and os.path.exists(self._icon_icns_path):
                    icns = NSImage.alloc().initWithContentsOfFile_(self._icon_icns_path)
                    if icns:
                        NSApp.setApplicationIconImage_(icns)
                        applied = True
                        print(f"DEBUG: Dock 图标已从 ICNS 应用: {self._icon_icns_path}")
                if not applied and hasattr(self, '_icon_png_path') and self._icon_png_path and os.path.exists(self._icon_png_path):
                    img = NSImage.alloc().initWithContentsOfFile_(self._icon_png_path)
                    if img:
                        try:
                            sz = img.size()
                            radius = max(6.0, min(sz.width, sz.height) * 0.20)
                        except Exception:
                            radius = 96.0
                        rounded = self._rounded_nsimage(img, radius)
                        NSApp.setApplicationIconImage_(rounded or img)
                        applied = True
                        print(f"WARNING: Dock 图标已从 PNG 应用（圆角已处理）: {self._icon_png_path}")
            # 触发 Dock 刷新（可选）
            try:
                NSApp.dockTile().display()
            except Exception:
                pass
        except Exception as e:
            print(f"WARNING: 重新应用 Dock 图标失败: {e}")

    def reapplyDockIcon_(self, timer):
        self._applyDockIconOnce()
        print("DEBUG: 已执行延迟的 Dock 图标刷新")

    def applicationDidBecomeActive_(self, notification):
        # 防止重复创建
        if getattr(self, 'window_initialized', False):
            return
        self.window_initialized = True
        # 再次确保 Dock 图标为自定义圆角版本
        self._applyDockIconOnce()

        print("开始创建窗口...")
        # Create a borderless, floating, resizable window
        print("创建主窗口...")
        window_rect = NSMakeRect(500, 200, 550, 580)
        print(f"DEBUG: 窗口位置和大小: {window_rect}")
        
        # 使用标准窗口样式并隐藏系统标题栏，改为全尺寸内容视图
        window_style = (
            NSWindowStyleMaskTitled
            | NSWindowStyleMaskClosable
            | NSWindowStyleMaskResizable
            | NSWindowStyleMaskMiniaturizable
            | NSWindowStyleMaskFullSizeContentView
        )
        print(f"DEBUG: 窗口样式掩码: {window_style} (无边框窗口样式)")
        
        self.window = AppWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            window_rect,
            window_style,
            NSBackingStoreBuffered,
            False
        )
        
        print(f"窗口创建完成: {self.window}")
        if self.window is None:
            print("ERROR: 窗口创建失败!")
            return
            
        # 设置窗口标题并隐藏系统标题栏（去掉顶部边框）
        self.window.setTitle_(APP_TITLE)
        try:
            self.window.setTitleVisibility_(NSWindowTitleHidden)
            self.window.setTitlebarAppearsTransparent_(True)
        except Exception:
            pass
        
        # 确保窗口能够接收鼠标事件和键盘输入
        self.window.setIgnoresMouseEvents_(False)  # 确保不忽略鼠标事件
        self.window.setAcceptsMouseMovedEvents_(True)  # 接受鼠标移动事件
        try:
            # 允许通过背景拖动窗口（配合自定义顶栏）
            self.window.setMovableByWindowBackground_(True)
        except Exception:
            pass
        
        # 添加调试信息
        print(f"DEBUG: 窗口事件设置完成:")
        print(f"  - 忽略鼠标事件: {self.window.ignoresMouseEvents()}")
        print(f"  - 接受鼠标移动: {self.window.acceptsMouseMovedEvents()}")

        # 验证窗口基本属性
        print(f"DEBUG: 窗口是否可以成为关键窗口: {self.window.canBecomeKeyWindow()}")
        print(f"DEBUG: 窗口是否不透明: {self.window.isOpaque()}")
        print(f"DEBUG: 窗口背景颜色: {self.window.backgroundColor()}")

        # 为主窗口设置默认实例数据（向后兼容）
        default_window_id = "main-window"
        default_platform_id = "default"
        if hasattr(self.window, 'setWindowInstanceData_windowId_platformId_'):
            self.window.setWindowInstanceData_windowId_platformId_(None, default_window_id, default_platform_id)
            
        # 置顶窗口，保证始终在最前
        try:
            self.window.setLevel_(NSFloatingWindowLevel)
            print(f"DEBUG: 窗口级别设置为: {NSFloatingWindowLevel} (置顶)")
        except Exception:
            # 退化为普通层级
            self.window.setLevel_(NSNormalWindowLevel)
            print(f"DEBUG: 窗口级别设置为: {NSNormalWindowLevel} (普通窗口，置顶失败)")
        
        # 如果需要置顶，使用更温和的方式
        self.window.orderFront_(None)  # 将窗口置前
        
        # 设置窗口集合行为，允许正常交互
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorManaged
        )
        # Save the last position and size
        self.window.setFrameAutosaveName_(FRAME_SAVE_NAME)
        # Create the webview for the main application.
        print("创建 WebView 配置...")
        config = WKWebViewConfiguration.alloc().init()
        config.preferences().setJavaScriptCanOpenWindowsAutomatically_(True)
        # Initialize the WebView with a frame
        print("创建 WebView...")
        webview_frame = ((0, 0), (800, 600))  # Frame: origin (0,0), size (800x600)
        print(f"DEBUG: WebView 框架: {webview_frame}")
        self.webview = WKWebView.alloc().initWithFrame_configuration_(
            webview_frame,
            config
        )
        print(f"WebView 创建完成: {self.webview}")
        if self.webview is None:
            print("ERROR: WebView 创建失败!")
            return
        # 设置 WebView 配置，确保能够处理用户交互
        self.webview.setUIDelegate_(self)
        self.webview.setNavigationDelegate_(self)  # 添加导航委托
        self.webview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)  # Resizes with window
        
        # 确保 WebView 能够接收焦点和交互
        self.webview.setAcceptsTouchEvents_(True)
        try:
            # 在部分系统上启用该选项会导致 WKWebView 白屏，关闭更稳定
            self.webview.setCanDrawSubviewsIntoLayer_(False)
        except Exception:
            pass
        try:
            # 使用不透明背景以避免透明链路造成白屏
            self.webview.setOpaque_(True)
        except Exception:
            pass
        try:
            # 确保 WebView 绘制背景，避免透明链条导致白屏
            self.webview.setValue_forKey_(True, "drawsBackground")
        except Exception:
            pass
        # Set a custom user agent
        safari_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
        self.webview.setCustomUserAgent_(safari_user_agent)
        # 设置窗口属性：使用不透明窗口，避免透明链路导致的白屏
        self.window.setOpaque_(True)
        try:
            self.window.setBackgroundColor_(NSColor.windowBackgroundColor())
        except Exception:
            pass
        self.window.setHasShadow_(True)
        print("DEBUG: 窗口设为不透明并使用系统背景色")
        # Prevent overlay from appearing in screenshots or screen recordings
        self.window.setSharingType_(NSWindowSharingNone)

        # 隐藏系统交通灯按钮，完全自定义顶部栏
        try:
            for btnKind in (NSWindowCloseButton, NSWindowMiniaturizeButton, NSWindowZoomButton):
                btn = self.window.standardWindowButton_(btnKind)
                if btn:
                    btn.setHidden_(True)
        except Exception:
            pass

        # 创建根视图，包含自定义顶部栏 + WebView
        content_bounds = self.window.contentView().bounds()
        root_view = NSView.alloc().initWithFrame_(content_bounds)
        root_view.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        # 增大圆角并绘制背景，窗口本身改为透明
        root_view.setWantsLayer_(True)
        try:
            from .constants import CORNER_RADIUS
            root_view.layer().setCornerRadius_(float(CORNER_RADIUS))
            root_view.layer().setMasksToBounds_(True)
            root_view.layer().setBackgroundColor_(NSColor.windowBackgroundColor().CGColor())
        except Exception:
            pass
        self.window.setContentView_(root_view)
        self.root_view = root_view

        # 顶部栏（用作拖拽区域和平台选择器容器）
        self.top_bar_height = 36
        self.top_bar = TopBarView.alloc().initWithFrame_(
            NSMakeRect(0, content_bounds.size.height - self.top_bar_height, content_bounds.size.width, self.top_bar_height)
        )
        self.top_bar.setWantsLayer_(True)
        try:
            self.top_bar.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
        except Exception:
            pass
        self.top_bar.setAutoresizingMask_(NSViewWidthSizable | NSViewMinYMargin)
        root_view.addSubview_(self.top_bar)

        # 左上角品牌：彩色圆角 Logo + 更好看的字体（打包与开发一致加载）
        try:
            brand_h = 28
            by = (self.top_bar_height - brand_h) / 2
            bx = 10
            script_dir2 = os.path.dirname(os.path.abspath(__file__))
            brand_img = None
            # 1) NSBundle 资源（py2app 打包后优先）
            try:
                bundle = NSBundle.mainBundle()
                for base in ("icon_64x64@2x", "icon_64x64", "icon_32x32@2x", "icon_32x32"):
                    p = bundle.pathForResource_ofType_inDirectory_(base, "png", "logo/icon.iconset")
                    if p:
                        tmp = NSImage.alloc().initWithContentsOfFile_(p)
                        if tmp is not None:
                            brand_img = tmp
                            break
            except Exception:
                pass
            # 2) pkgutil（zip-safe，打包为 zip 的情况）
            if brand_img is None:
                try:
                    import pkgutil
                    for name in (
                        "logo/icon.iconset/icon_64x64@2x.png",
                        "logo/icon.iconset/icon_64x64.png",
                        "logo/icon.iconset/icon_32x32@2x.png",
                        "logo/icon.iconset/icon_32x32.png",
                    ):
                        data = pkgutil.get_data('bubblebot', name)
                        if data:
                            nsdata = NSData.dataWithBytes_length_(data, len(data))
                            tmp = NSImage.alloc().initWithData_(nsdata)
                            if tmp is not None:
                                brand_img = tmp
                                break
                except Exception:
                    pass
            # 3) 文件系统（开发模式兜底）
            if brand_img is None:
                color_candidates = [
                    os.path.join(script_dir2, "logo/icon.iconset/icon_64x64@2x.png"),
                    os.path.join(script_dir2, "logo/icon.iconset/icon_64x64.png"),
                    os.path.join(script_dir2, "logo/icon.iconset/icon_32x32@2x.png"),
                    os.path.join(script_dir2, "logo/icon.iconset/icon_32x32.png"),
                ]
                logo_path = next((p for p in color_candidates if os.path.exists(p)), os.path.join(script_dir2, LOGO_BLACK_PATH))
                brand_img = NSImage.alloc().initWithContentsOfFile_(logo_path)
            self.brand_logo = NSImageView.alloc().initWithFrame_(NSMakeRect(bx, by, brand_h, brand_h))
            if brand_img:
                try:
                    brand_img.setSize_(NSSize(brand_h, brand_h))
                except Exception:
                    pass
                self.brand_logo.setImage_(brand_img)
            try:
                self.brand_logo.setWantsLayer_(True)
                self.brand_logo.layer().setCornerRadius_(8.0)
                self.brand_logo.layer().setMasksToBounds_(True)
            except Exception:
                pass
            self.brand_logo.setAutoresizingMask_(NSViewMaxXMargin | NSViewMinYMargin)
            self.top_bar.addSubview_(self.brand_logo)

            # 更美观的品牌文字（字距、对齐到 logo 中线）
            label_h = 18.0
            ly = (self.top_bar_height - label_h) / 2.0 + 0.5
            self.brand_label = NSTextField.alloc().initWithFrame_(NSMakeRect(bx+brand_h+8, ly, 160, label_h))
            self.brand_label.setBezeled_(False)
            self.brand_label.setEditable_(False)
            self.brand_label.setSelectable_(False)
            self.brand_label.setDrawsBackground_(False)
            cute = self._get_cute_bold_font(15) or NSFont.boldSystemFontOfSize_(15)
            try:
                from AppKit import NSAttributedString, NSFontAttributeName, NSKernAttributeName, NSForegroundColorAttributeName
                attrs = {NSFontAttributeName: cute, NSKernAttributeName: 0.4, NSForegroundColorAttributeName: NSColor.labelColor()}
                self.brand_label.setAttributedStringValue_(NSAttributedString.alloc().initWithString_attributes_("Bubble", attrs))
            except Exception:
                # 兜底：不支持属性时用普通字符串
                self.brand_label.setStringValue_("Bubble")
                self.brand_label.setFont_(cute)
                try:
                    self.brand_label.setTextColor_(NSColor.labelColor())
                except Exception:
                    pass
            self.brand_label.setAutoresizingMask_(NSViewMaxXMargin | NSViewMinYMargin)
            self.top_bar.addSubview_(self.brand_label)
        except Exception:
            pass

        # 返回按钮（左侧，默认主页隐藏）
        self.back_button = BackPointerButton.alloc().initWithFrame_(NSMakeRect(10, content_bounds.size.height - self.top_bar_height + 4, 28, 28))
        img = None
        try:
            img = NSImage.imageWithSystemSymbolName_accessibilityDescription_("chevron.left", None)
        except Exception:
            img = None
        if img is not None:
            # 使用更细的符号配置
            try:
                from AppKit import NSImageSymbolConfiguration, NSFontWeightRegular, NSImageSymbolScaleSmall
                cfg = NSImageSymbolConfiguration.configurationWithPointSize_weight_scale_(18.0, NSFontWeightRegular, NSImageSymbolScaleSmall)
                img_cfg = img.imageWithSymbolConfiguration_(cfg)
                if img_cfg:
                    img = img_cfg
            except Exception:
                pass
            self.back_button.setImage_(img)
            try:
                self.back_button.setImageScaling_(NSImageScaleProportionallyDown)
            except Exception:
                pass
        else:
            self.back_button.setTitle_("←")
        self.back_button.setBordered_(False)
        try:
            self.back_button.setContentTintColor_(NSColor.labelColor())
        except Exception:
            pass
        try:
            self.back_button.setToolTip_(self._i18n_or_default('tooltip.back', 'Back'))
        except Exception:
            pass
        self.back_button.setTarget_(self)
        self.back_button.setAction_("navigateBack:")
        # 主页默认不显示返回按钮；进入平台页时显示
        self.back_button.setHidden_(True)
        self.back_button.setAutoresizingMask_(NSViewMaxXMargin | NSViewMinYMargin)
        self.top_bar.addSubview_(self.back_button)

        # 不再添加左侧“主页指示器”，主页显示通过下拉项完成

        # 创建 AI 选择器（相对顶栏居中）
        selector_width = 108  # 更短
        selector_height = 22  # 更小
        selector_x = (self.top_bar.frame().size.width - selector_width) / 2
        selector_y = (self.top_bar_height - selector_height) / 2

        # 恢复下拉框的美观背景容器（圆角、细边、浅色）
        self.selector_bg = ClickThroughView.alloc().initWithFrame_(NSMakeRect(selector_x-6, selector_y-3, selector_width+12, selector_height+6))
        self.selector_bg.setWantsLayer_(True)
        try:
            self.selector_bg.layer().setCornerRadius_(8)
            self.selector_bg.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.9).CGColor())
            self.selector_bg.layer().setBorderColor_(NSColor.colorWithCalibratedWhite_alpha_(0.85, 1.0).CGColor())
            self.selector_bg.layer().setBorderWidth_(1.0)
            self.selector_bg.layer().setShadowColor_(NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.2).CGColor())
            self.selector_bg.layer().setShadowOpacity_(0.2)
            self.selector_bg.layer().setShadowRadius_(4.0)
            self.selector_bg.layer().setShadowOffset_(NSMakeSize(0, -1))
        except Exception:
            pass
        self.selector_bg.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin)
        self.top_bar.addSubview_(self.selector_bg)
        self.ai_selector = PointerPopUpButton.alloc().initWithFrame_pullsDown_(
            NSMakeRect(selector_x, selector_y, selector_width, selector_height), False
        )
        self.ai_selector.setTarget_(self)
        self.ai_selector.setAction_("aiServiceChanged:")
        self.ai_selector.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin)
        try:
            self.ai_selector.cell().setBezelStyle_(NSBezelStyleRounded)
            self.ai_selector.setBordered_(False)
            # 紧凑字体，并居中对齐
            cute = self._get_cute_bold_font(13)
            if cute is not None:
                self.ai_selector.setFont_(cute)
            else:
                self.ai_selector.setFont_(NSFont.boldSystemFontOfSize_(13))
            from AppKit import NSTextAlignmentCenter
            try:
                self.ai_selector.cell().setAlignment_(NSTextAlignmentCenter)
            except Exception:
                pass
        except Exception:
            pass
        self.top_bar.addSubview_(self.ai_selector)
        
        # 旧版“内存提示气泡”已移除，改为阈值 Toast（4→5 时提示一次）
        # 显示一次性迁移提示（如需要）
        try:
            self._show_migration_notice_if_pending()
        except Exception:
            pass
        
        # 不再添加覆盖下拉的“主页标签”
        # 美化下拉菜单项居中（避免安装菜单委托造成不稳定）
        try:
            self._style_popup_menu_items()
        except Exception:
            pass
        # 定位返回按钮与其圆形背景到下拉框左侧
        try:
            diameter = selector_height
            bx = selector_x - diameter - 8
            by = (self.top_bar_height - diameter) / 2
            self.back_button.setFrame_(NSMakeRect(bx, by, diameter, diameter))
            # 创建圆形背景，置于按钮下方
            if not hasattr(self, 'back_button_bg') or self.back_button_bg is None:
                self.back_button_bg = NSView.alloc().initWithFrame_(NSMakeRect(bx, by, diameter, diameter))
                self.back_button_bg.setWantsLayer_(True)
                self.back_button_bg.layer().setCornerRadius_(diameter/2)
                # 与下拉框背景一致（白色+透明度）
                self.back_button_bg.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.90).CGColor())
                self.back_button_bg.layer().setBorderColor_(NSColor.colorWithCalibratedWhite_alpha_(0.85, 1.0).CGColor())
                self.back_button_bg.layer().setBorderWidth_(1.0)
                try:
                    self.back_button_bg.layer().setShadowOpacity_(0.15)
                    self.back_button_bg.layer().setShadowRadius_(3.0)
                except Exception:
                    pass
                self.top_bar.addSubview_positioned_relativeTo_(self.back_button_bg, NSWindowBelow, self.back_button)
                # 与选择器背景一致，但在主页默认隐藏
                self.back_button_bg.setHidden_(True)
            else:
                self.back_button_bg.setFrame_(NSMakeRect(bx, by, diameter, diameter))
            try:
                if hasattr(self.back_button, 'setBackgroundView_'):
                    self.back_button.setBackgroundView_(self.back_button_bg)
            except Exception:
                pass
        except Exception:
            pass
        
        # 预判首次内容：是否加载主页，用于正确填充下拉（主页需首项为“主页”）
        print("准备加载内容...")
        load_home = False
        if self.homepage_manager:
            try:
                if self.homepage_manager.is_first_launch() or self.homepage_manager.should_show_homepage_on_startup():
                    load_home = True
            except Exception as e:
                print(f"主页显示判断失败，回退到主页: {e}")
                load_home = True
        # 填充平台项（主页时首项为“主页”）
        self._populate_ai_selector(include_home_first=load_home)
        # 旧版“内存提示气泡”已移除

        # WebView 全高（顶栏悬浮覆盖，不挤压内容）
        webview_frame = NSMakeRect(
            0,
            0,
            content_bounds.size.width,
            content_bounds.size.height
        )
        self.webview.setFrame_(webview_frame)
        root_view.addSubview_(self.webview)
        # 确保顶栏位于 WebView 之上
        if hasattr(root_view, 'addSubview_positioned_relativeTo_'):
            self.top_bar.removeFromSuperview()
            root_view.addSubview_positioned_relativeTo_(self.top_bar, NSWindowAbove, self.webview)
        self.webview.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        
        # 让 WebView 成为第一响应者
        self.window.makeFirstResponder_(self.webview)

        # 预创建骨架屏视图（用于页面加载中展示）
        self._ensure_skeleton_view()

        # 图标使用随包资源（assets/icons），不依赖联网与运行时生成

        # Set up script message handler for background color changes
        configuration = self.webview.configuration()
        user_content_controller = configuration.userContentController()

        # 设置主页和导航相关的消息处理器
        user_content_controller.addScriptMessageHandler_name_(self, "aiSelection")  # 处理AI选择
        user_content_controller.addScriptMessageHandler_name_(self, "aiAction")    # 处理AI操作
        user_content_controller.addScriptMessageHandler_name_(self, "navigationAction")  # 处理导航操作
        user_content_controller.addScriptMessageHandler_name_(self, "backgroundColorHandler")

        # Contat the target website.
        # 根据上面的预判加载对应页面
        if load_home:
            print("加载主页...")
            self._load_homepage()
            # 启动后在后台恢复历史页面（不干扰主页）
            try:
                NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    0.08, self, 'restorePagesIfAny:', None, False
                )
            except Exception:
                pass
        else:
            # 启动时直接进入默认AI平台
            startup_platform = None
            try:
                if self.homepage_manager:
                    startup_platform = self.homepage_manager.get_default_ai()
            except Exception:
                startup_platform = None
            if not startup_platform and self.platform_manager:
                try:
                    dp = self.platform_manager.get_default_platform()
                    if dp:
                        startup_platform = dp.platform_id
                except Exception:
                    startup_platform = None
            if not startup_platform:
                # 兜底为 ChatGPT
                startup_platform = 'openai'

            # 更新导航并加载对应平台
            try:
                if self.navigation_controller:
                    self.navigation_controller.handle_ai_selector_change(startup_platform, None)
                self._load_ai_service(startup_platform)
                # 精确选中对应下拉项
                self._select_ai_item(startup_platform)
            except Exception as _e:
                print(f"DEBUG: 启动平台加载异常: {_e}")
            # 无论是否直接进入平台页，后台恢复历史页面
            try:
                NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    0.08, self, 'restorePagesIfAny:', None, False
                )
            except Exception:
                pass
        # 旧版“内存提示气泡”已移除
        # Inject JavaScript to monitor background color changes
        script = """
            function sendBackgroundColor() {
                var bgColor = window.getComputedStyle(document.body).backgroundColor;
                window.webkit.messageHandlers.backgroundColorHandler.postMessage(bgColor);
            }
            window.addEventListener('load', sendBackgroundColor);
            new MutationObserver(sendBackgroundColor).observe(document.body, { attributes: true, attributeFilter: ['style'] });
        """
        user_script = WKUserScript.alloc().initWithSource_injectionTime_forMainFrameOnly_(script, WKUserScriptInjectionTimeAtDocumentEnd, True)
        user_content_controller.addUserScript_(user_script)
        # Create status bar item with logo
        # Use variable length to let the system size appropriately
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)

        # Robust icon loader that works both in source tree and py2app bundle
        def _load_nsimage(rel_path, name_hint=None):
            # 1) Try NSBundle Resources (works when setup.py copies "logo" dir)
            try:
                bundle = NSBundle.mainBundle()
                # Allow path like "logo/logo_white.png" or just name+type
                if name_hint and "." in name_hint:
                    base, ext = name_hint.rsplit(".", 1)
                else:
                    base, ext = None, None
                # Precise lookup in subdirectory
                path = None
                try:
                    path = bundle.pathForResource_ofType_inDirectory_(base or None, ext or None, "logo") if base and ext else None
                except Exception:
                    path = None
                if not path:
                    # Fallback: join resourcePath + rel_path
                    base_dir = bundle.resourcePath()
                    if base_dir:
                        p = os.path.join(str(base_dir), rel_path)
                        if os.path.exists(p):
                            path = p
                if path:
                    img = NSImage.alloc().initWithContentsOfFile_(path)
                    if img is not None:
                        try: img.setTemplate_(False)
                        except Exception: pass
                        try: img.setSize_(NSSize(18, 18))
                        except Exception: pass
                        return img
            except Exception:
                pass

            # 2) Try pkgutil data (zip-safe)
            try:
                import pkgutil
                data = pkgutil.get_data('bubblebot', rel_path)
                if data:
                    nsdata = NSData.dataWithBytes_length_(data, len(data))
                    img = NSImage.alloc().initWithData_(nsdata)
                    if img is not None:
                        try: img.setTemplate_(False)
                        except Exception: pass
                        try: img.setSize_(NSSize(18, 18))
                        except Exception: pass
                        return img
            except Exception:
                pass

            # 3) Try file next to module (dev mode)
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                p = os.path.join(script_dir, rel_path)
                if os.path.exists(p):
                    img = NSImage.alloc().initWithContentsOfFile_(p)
                    if img is not None:
                        try: img.setTemplate_(False)
                        except Exception: pass
                        try: img.setSize_(NSSize(18, 18))
                        except Exception: pass
                        return img
            except Exception:
                pass
            return None

        self.logo_white = _load_nsimage(LOGO_WHITE_PATH, name_hint="logo_white.png")
        self.logo_black = _load_nsimage(LOGO_BLACK_PATH, name_hint="logo_black.png")
        if not self.logo_white or not self.logo_black:
            print("WARNING: status bar icon images failed to load")
        # 生成圆角版本图标用于状态栏（更精致）
        # Keep originals as template images; we will round at runtime to enforce silhouette
        self.logo_white_rounded = None
        self.logo_black_rounded = None
        try:
            print(f"DEBUG: 状态栏图标属性: white_isTemplate={getattr(self.logo_white, 'isTemplate', lambda: None)()} size={self.logo_white.size()} black_isTemplate={getattr(self.logo_black, 'isTemplate', lambda: None)()} size={self.logo_black.size()}")
        except Exception:
            pass
        # Set the initial logo image based on the current appearance
        try:
            self.updateStatusItemImage()
        except Exception:
            pass
        # Observe system appearance changes (KVO on status item button)
        try:
            btn = self.status_item.button()
            if btn is not None:
                btn.addObserver_forKeyPath_options_context_(
                    self, "effectiveAppearance", NSKeyValueObservingOptionNew, STATUS_ITEM_CONTEXT
                )
        except Exception:
            pass
        # Also observe application-level appearance changes as a fallback
        try:
            try:
                from AppKit import NSApplicationDidChangeEffectiveAppearanceNotification as _APP_APPEARANCE_CHANGED
            except Exception:
                _APP_APPEARANCE_CHANGED = "NSApplicationDidChangeEffectiveAppearanceNotification"
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self, 'appearanceDidChange:', _APP_APPEARANCE_CHANGED, None
            )
        except Exception:
            pass
        # Create simplified status bar menu (hint + Settings… + Quit)
        menu = NSMenu.alloc().init()
        menu.setDelegate_(self)
        # Hint item (disabled)
        self.menu_hint_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("", None, "")
        self.menu_hint_item.setEnabled_(False)
        menu.addItem_(self.menu_hint_item)
        menu.addItem_(NSMenuItem.separatorItem())
        # Settings…
        self.menu_settings_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Settings…", "showSettings:", "")
        self.menu_settings_item.setTarget_(self)
        self.menu_settings_item.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("gearshape", None))
        menu.addItem_(self.menu_settings_item)
        menu.addItem_(NSMenuItem.separatorItem())
        # Quit
        self.menu_quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "q")
        self.menu_quit_item.setTarget_(NSApp)
        self.menu_quit_item.setImage_(NSImage.imageWithSystemSymbolName_accessibilityDescription_("power", None))
        menu.addItem_(self.menu_quit_item)

        # Set the menu for the status item and localize/refresh
        self.status_item.setMenu_(menu)
        try:
            self._refresh_status_menu_titles()
        except Exception:
            pass

    def _format_launcher_hotkey(self) -> str:
        try:
            flags_val = LAUNCHER_TRIGGER.get('flags')
            key_val = LAUNCHER_TRIGGER.get('key')
            if flags_val in (None, 0) and key_val in (None, 0):
                return '—'
            flags = int(flags_val or 0)
            key = int(key_val or 0)
        except Exception:
            flags, key = 0, 0
        parts = []
        try:
            # Prefer NSEvent masks if available in this scope
            from Quartz import NSCommandKeyMask, NSAlternateKeyMask, NSShiftKeyMask, NSControlKeyMask
            if flags & NSCommandKeyMask:
                parts.append('⌘')
            if flags & NSAlternateKeyMask:
                parts.append('⌥')
            if flags & NSShiftKeyMask:
                parts.append('⇧')
            if flags & NSControlKeyMask:
                parts.append('⌃')
        except Exception:
            pass
        # Key mapping (best-effort; includes common letters)
        keymap = {
            0: 'a', 1: 's', 2: 'd', 3: 'f', 4: 'h', 5: 'g', 6: 'z', 7: 'x', 8: 'c', 9: 'v',
            11: 'b', 12: 'q', 13: 'w', 14: 'e', 15: 'r', 16: 'y', 17: 't', 31: 'o', 32: 'u',
            34: 'i', 35: 'p', 37: 'l', 38: 'j', 40: 'k', 45: 'n', 46: 'm', 49: 'Space', 36: 'Return', 53: 'Esc'
        }
        keyname = keymap.get(key)
        if not keyname:
            try:
                keyname = SPECIAL_KEY_NAMES.get(key)
            except Exception:
                keyname = None
        if not keyname:
            keyname = str(key)
        parts.append(keyname)
        return '+'.join(parts)

    def _refresh_status_menu_titles(self):
        # Update simplified menu text to current language
        try:
            hotkey = self._format_launcher_hotkey()
            if getattr(self, 'menu_hint_item', None) is not None:
                self.menu_hint_item.setTitle_(self._i18n_or_default('menu.showHideHint', 'Press {hotkey} to Show/Hide', hotkey=hotkey))
            if getattr(self, 'menu_settings_item', None) is not None:
                self.menu_settings_item.setTitle_(self._i18n_or_default('menu.settings', 'Settings…'))
            if getattr(self, 'menu_quit_item', None) is not None:
                self.menu_quit_item.setTitle_(self._i18n_or_default('menu.quit', 'Quit'))
        except Exception:
            pass
        # Heavy initialization (observers, event tap) should run only once.
        if getattr(self, '_status_menu_initialized', False):
            return
        # Add resize observer（用于自适应顶部栏与选择器位置）
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, 'windowDidResize:', NSWindowDidResizeNotification, self.window
        )
        
        # 可选：允许通过环境变量跳过事件监听器和麦克风授权提示，排除干扰
        skip_tap = os.environ.get('BB_NO_TAP') == '1'
        skip_mic = os.environ.get('BB_NO_MIC_PROMPT') == '1'

        if not skip_tap:
            # Create and store the event tap for key-down events
            self.eventTap = CGEventTapCreate(
                kCGHIDEventTap,
                kCGHeadInsertEventTap,
                kCGEventTapOptionDefault,
                CGEventMaskBit(kCGEventKeyDown) | CGEventMaskBit(kCGEventKeyUp),
                global_show_hide_listener(self),
                None
            )
            # Prompt for Accessibility if API is available
            if AXIsProcessTrustedWithOptions and kAXTrustedCheckOptionPrompt:
                AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
        else:
            self.eventTap = None
            print("DEBUG: 已按环境变量 BB_NO_TAP 跳过事件监听器创建")

        if not skip_mic:
            # Prompt for microphone permission when running via Python
            AVCaptureDevice.requestAccessForMediaType_completionHandler_(
                AVMediaTypeAudio,
                lambda granted: (print("DEBUG: Microphone access granted:", granted) if os.environ.get('BB_DEBUG') == '1' else None)
            )
        else:
            print("DEBUG: 已按环境变量 BB_NO_MIC_PROMPT 跳过麦克风授权提示")

        if self.eventTap:
            print("DEBUG: 事件监听器创建成功")
            # Create and add the run loop source
            self.eventTapSource = CFMachPortCreateRunLoopSource(None, self.eventTap, 0)
            print(f"DEBUG: 事件监听器源创建完成: {self.eventTapSource}")
            CFRunLoopAddSource(CFRunLoopGetCurrent(), self.eventTapSource, kCFRunLoopCommonModes)
            print("DEBUG: 事件监听器源已添加到运行循环")
            CGEventTapEnable(self.eventTap, True)
            print(f"DEBUG: 事件监听器已启用: {CGEventTapIsEnabled(self.eventTap)}")
        elif not skip_tap:
            print("ERROR: 事件监听器创建失败！请检查 Accessibility 权限")
            print("请在 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能 中授予权限")
        # Load the custom launch trigger if the user set it.
        load_custom_launcher_trigger()
        # Set the delegate of the window to this parent application.
        self.window.setDelegate_(self)

        # 添加调试信息
        print("窗口初始化完成，准备显示窗口...")

        # 详细检查窗口状态
        print(f"DEBUG: 窗口创建前状态检查:")
        print(f"  - 窗口对象: {self.window}")
        print(f"  - 窗口是否为nil: {self.window is None}")
        print(f"  - 窗口样式掩码: {self.window.styleMask()}")
        print(f"  - 窗口级别: {self.window.level()}")
        print(f"  - 窗口透明度: {self.window.alphaValue()}")
        print(f"  - 窗口是否不透明: {self.window.isOpaque()}")
        print(f"  - 窗口背景颜色: {self.window.backgroundColor()}")
        print(f"  - 窗口框架: {self.window.frame()}")

        # 检查屏幕信息
        screen = NSScreen.mainScreen()
        print(f"DEBUG: 主屏幕信息:")
        print(f"  - 屏幕框架: {screen.frame()}")
        print(f"  - 可见框架: {screen.visibleFrame()}")

        # Make sure this window is shown and focused.
        print("DEBUG: 调用 showWindow_...")
        self.showWindow_(None)
        # 如 App 未激活，仅在首次启动时激活一次，避免 Dock 反复弹跳
        if not NSApp.isActive():
            NSApp.activateIgnoringOtherApps_(True)
        # 窗口前置
        self.window.makeKeyAndOrderFront_(None)
        print("DEBUG: 已前置并设为关键窗口")

        # 再次检查窗口状态
        print(f"DEBUG: 显示后窗口状态:")
        print(f"  - 窗口是否可见: {self.window.isVisible()}")
        print(f"  - 窗口是否为关键窗口: {self.window.isKeyWindow()}")
        print(f"  - 窗口是否为主要窗口: {self.window.isMainWindow()}")
        print(f"  - 应用是否激活: {NSApp.isActive()}")
        print(f"  - 应用激活策略: {NSApp.activationPolicy()}")
        
        # 不再使用退出轮询/激活保活，避免干扰交互
        self.activation_timer = None
        # Mark initialized to avoid repeating heavy setup on subsequent refreshes
        self._status_menu_initialized = True

    # Logic to show the overlay, make it the key window, and focus on the typing area.
    def showWindow_(self, sender):

        # 仅在应用未激活或窗口非关键时置前
        if not NSApp.isActive() or not self.window.isKeyWindow():
            NSApp.activateIgnoringOtherApps_(True)
            self.window.orderFront_(None)
            self.window.makeKeyAndOrderFront_(None)
        # Debug log（默认不打印，只有 BB_DEBUG=1 才显示）
        print("DEBUG: ShowWindow_ called via", sender)
        print(f"DEBUG: 窗口状态: visible={self.window.isVisible()}, key={self.window.isKeyWindow()}")

        # 检查窗口样式和透明度问题
        print(f"DEBUG: 窗口样式检查:")
        print(f"  - 样式掩码: {self.window.styleMask()}")
        print(f"  - 是否有边框: {bool(self.window.styleMask() & NSBorderlessWindowMask)}")
        print(f"  - 是否可调整大小: {bool(self.window.styleMask() & NSResizableWindowMask)}")
        print(f"  - 窗口级别: {self.window.level()}")
        print(f"  - 窗口透明度: {self.window.alphaValue()}")
        print(f"  - 窗口是否不透明: {self.window.isOpaque()}")
        print(f"  - 背景颜色: {self.window.backgroundColor()}")
        print(f"  - 内容视图背景颜色: {self.window.contentView().layer().backgroundColor() if self.window.contentView().layer() else 'None'}")

        # 检查窗口位置
        frame = self.window.frame()
        print(f"DEBUG: 窗口位置检查:")
        print(f"  - 窗口框架: {frame}")
        print(f"  - 窗口原点: {frame.origin}")
        print(f"  - 窗口大小: {frame.size}")

        # 检查屏幕边界
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        visible_frame = screen.visibleFrame()
        print(f"  - 屏幕框架: {screen_frame}")
        print(f"  - 可见框架: {visible_frame}")

        # 检查窗口是否在屏幕范围内
        if frame.origin.x < 0 or frame.origin.y < 0:
            print("WARNING: 窗口原点在屏幕外!")
        if frame.origin.x + frame.size.width > screen_frame.size.width:
            print("WARNING: 窗口右边缘超出屏幕!")
        if frame.origin.y + frame.size.height > screen_frame.size.height:
            print("WARNING: 窗口下边缘超出屏幕!")

        # 如果已经激活且是关键窗口，不再反复置前

        print(f"DEBUG: 显示后窗口状态: visible={self.window.isVisible()}, key={self.window.isKeyWindow()}")

        # 检查窗口是否真的在屏幕上
        if self.window.isVisible():
            print("DEBUG: 窗口报告为可见")
        else:
            print("ERROR: 窗口报告为不可见!")

        if self.window.isKeyWindow():
            print("DEBUG: 窗口是关键窗口")
        else:
            print("DEBUG: 窗口不是关键窗口")

        # 检查应用激活状态
        print(f"DEBUG: 应用状态:")
        print(f"  - 应用是否激活: {NSApp.isActive()}")
        print(f"  - 应用激活策略: {NSApp.activationPolicy()}")
        print(f"  - 应用是否隐藏: {NSApp.isHidden()}")

        # Re-enable event tap when showing overlay
        if self.eventTap:
            CGEventTapEnable(self.eventTap, True)
        # 如页面存在可聚焦区域，可在需要时聚焦
        # Debug helper: show hotkey window automatically for tests
        try:
            import os as _os
            if _os.environ.get('BB_DEBUG_HOTKEY') == '1' and not getattr(self, '_debug_hotkey_shown', False):
                self._debug_hotkey_shown = True
                from Foundation import NSTimer
                NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                    0.6, self, 'setTrigger:', None, False
                )
        except Exception:
            pass

    # Hide the overlay and allow focus to return to the next visible application.
    def hideWindow_(self, sender):
        # 仅隐藏窗口而不隐藏整个应用，避免 Dock 弹跳/状态栏不可点击
        try:
            if self.window and self.window.isVisible():
                self.window.orderOut_(None)
        except Exception:
            pass

    # Go to the default landing website for the overlay (in case accidentally navigated away).
    def goToWebsite_(self, sender):
        url = NSURL.URLWithString_(WEBSITE)
        request = NSURLRequest.requestWithURL_(url)
        self.webview.loadRequest_(request)

    # Clear the webview cache data (in case cookies cause errors).
    def clearWebViewData_(self, sender):
        dataStore = self.webview.configuration().websiteDataStore()
        dataTypes = WKWebsiteDataStore.allWebsiteDataTypes()
        dataStore.removeDataOfTypes_modifiedSince_completionHandler_(
            dataTypes,
            NSDate.distantPast(),
            lambda: print("Data cleared")
        )

    # Legacy Autolauncher actions removed (3.1): install_/uninstall_ no longer present

    # 创建圆角图像（用于 Dock PNG 兜底和状态栏图标美化）
    def _rounded_nsimage(self, image, radius):
        try:
            if image is None:
                return None
            size = image.size()
            new_img = NSImage.alloc().initWithSize_(size)
            new_img.lockFocus()
            rect = NSMakeRect(0, 0, size.width, size.height)
            try:
                path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, radius, radius)
                path.addClip()
            except Exception:
                pass
            image.drawInRect_fromRect_operation_fraction_(rect, NSZeroRect, NSCompositingOperationSourceOver, 1.0)
            new_img.unlockFocus()
            try:
                new_img.setTemplate_(False)
            except Exception:
                pass
            return new_img
        except Exception:
            return image

    

    # Handle the 'Set Trigger' menu item click.
    def setTrigger_(self, sender):
        set_custom_launcher_trigger(self)

    # Settings window
    def showSettings_(self, sender):
        try:
            if not hasattr(self, '_settings_window') or self._settings_window is None:
                from .components.settings_window import SettingsWindow
                self._settings_window = SettingsWindow.alloc().initWithAppDelegate_(self)
            self._settings_window.show()
        except Exception as e:
            print(f"WARNING: 无法打开设置窗口: {e}")

    # Refresh hint when menu opens (hotkey may have changed)
    def menuWillOpen_(self, menu):
        try:
            self._refresh_status_menu_titles()
        except Exception:
            pass

    # For capturing key commands while the key window (in focus).
    def keyDown_(self, event):
        modifiers = event.modifierFlags()
        key_command = modifiers & NSCommandKeyMask
        key_alt = modifiers & NSAlternateKeyMask
        key_shift = modifiers & NSShiftKeyMask
        key_control = modifiers & NSControlKeyMask
        key = event.charactersIgnoringModifiers()
        
        # 检查 Ctrl+C 组合键
        if key_control and key == 'c':
            print("检测到 Ctrl+C，退出应用...")
            NSApp.terminate_(None)
            return
            
        # Command (NOT alt)
        if (key_command or key_control) and (not key_alt):
            # Select all
            if key == 'a':
                self.window.firstResponder().selectAll_(None)
            # Copy
            elif key == 'c':
                self.window.firstResponder().copy_(None)
            # Cut
            elif key == 'x':
                self.window.firstResponder().cut_(None)
            # Paste
            elif key == 'v':
                self.window.firstResponder().paste_(None)
            # Hide
            elif key == 'h':
                self.hideWindow_(None)
            # Quit
            elif key == 'q':
                print("检测到 Cmd+Q，退出应用...")
                NSApp.terminate_(None)
            # # Undo (causes crash for some reason)
            # elif key == 'z':
            #     self.window.firstResponder().undo_(None)

    

    # Handler for setting the background color based on the web page background color.
    def userContentController_didReceiveScriptMessage_(self, userContentController, message):
        try:
            name = message.name()
            body = message.body()
            data = body
            # 尝试将来自 JS 的 NSDictionary 安全转为 Python dict
            try:
                if data is not None and not isinstance(data, dict):
                    # 部分 PyObjC 版本返回的是 NSDictionary，dict() 可直接转换
                    data = dict(data)
            except Exception:
                pass

            if name == "backgroundColorHandler":
                return

            if name == "aiSelection":
                # 处理AI选择消息
                if isinstance(data, dict) and data.get("action") == "selectDefaultAI":
                    platform_id = data.get("platformId")
                    if self.homepage_manager:
                        self.homepage_manager.set_default_ai(platform_id)
                    if self.navigation_controller:
                        self.navigation_controller.handle_homepage_ai_selection(platform_id)
                    self._load_ai_service(platform_id)
                return

            if name == "aiAction":
                # 处理AI操作消息
                action = data.get("action") if isinstance(data, dict) else None
                platform_id = data.get("platformId") if isinstance(data, dict) else None
                if action == "openAI" and self.navigation_controller:
                    if self.is_multiwindow_mode:
                        # 单窗口多页面：统一走导航控制器，避免手动切换导致 UI 不同步
                        try:
                            # 优先最近创建/使用的一个
                            ordered = []
                            try:
                                ordered = sorted(
                                    [(wid, meta) for wid, meta in self._page_meta.items() if meta.get('platform_id') == platform_id],
                                    key=lambda kv: kv[1].get('created_at') or 0
                                )
                            except Exception:
                                ordered = []
                            target_id = ordered[-1][0] if ordered else None
                            self.navigation_controller.handle_ai_selector_change(platform_id, target_id)
                        except Exception:
                            pass
                        return
                    # 单窗口模式：保持原行为
                    target_window_id = None
                    try:
                        win_map = self.homepage_manager.get_platform_windows(platform_id)
                        if win_map:
                            items = list(win_map.items())
                            try:
                                items.sort(key=lambda kv: kv[1].get('createdAt', ''))
                            except Exception:
                                pass
                            target_window_id = items[-1][0]
                        else:
                            from uuid import uuid4
                            if self.homepage_manager.can_add_window():
                                old_cnt = 0
                                try:
                                    old_cnt = int(self.homepage_manager.get_total_window_count())
                                except Exception:
                                    old_cnt = 0
                                new_id = str(uuid4())
                                self.homepage_manager.add_platform_window(platform_id, new_id, { 'createdAt': str(NSDate.date()) })
                                try:
                                    new_cnt = int(self.homepage_manager.get_total_window_count())
                                except Exception:
                                    new_cnt = old_cnt
                                self._maybe_show_page_threshold_toast(old_cnt, new_cnt)
                                target_window_id = new_id
                    except Exception:
                        pass
                    self.navigation_controller.handle_ai_selector_change(platform_id, target_window_id)
                    self._load_ai_service(platform_id)
                    self._populate_ai_selector()
                    try:
                        for i in range(self.ai_selector.numberOfItems()):
                            rep = self.ai_selector_map.get(i) if hasattr(self, 'ai_selector_map') else None
                            if rep and rep.get('platform_id') == platform_id and rep.get('window_id') == target_window_id:
                                self.ai_selector.selectItemAtIndex_(i)
                                break
                    except Exception:
                        pass
                    self.update_back_button_visibility(True)
                    return
                if action == "setDefault" and self.homepage_manager:
                    self.homepage_manager.set_default_ai(platform_id)
                    self._refresh_homepage()
                    # 保持下拉框与主页一致
                    try:
                        self._set_ai_selector_to_home()
                    except Exception:
                        pass
                    return
                if action == "removePlatform" and self.homepage_manager:
                    # 取消选中平台：在多页面模式下需要关闭该平台的所有后台页面，保持下拉与实际页面同步
                    if self.is_multiwindow_mode:
                        try:
                            # 批量关闭，避免重复刷新下拉
                            self._batch_closing = True
                            targets = [wid for wid, meta in list(self._page_meta.items()) if meta.get('platform_id') == platform_id]
                            for wid in targets:
                                try:
                                    self._pages_close(wid)
                                except Exception:
                                    pass
                        finally:
                            self._batch_closing = False
                        # 关闭完成后，移除平台使其处于未启用状态
                        try:
                            self.homepage_manager.remove_platform(platform_id)
                        except Exception:
                            pass
                        # 无刷新更新行状态、下拉与气泡
                        self._update_homepage_platform_active(platform_id, False)
                        try:
                            self._populate_ai_selector(include_home_first=True)
                        except Exception:
                            pass
                        try:
                            self._update_homepage_window_count(platform_id)
                        except Exception:
                            pass
                        return
                    # 非多页面模式：仅更新配置与 UI
                    self.homepage_manager.remove_platform(platform_id)
                    self._update_homepage_platform_active(platform_id, False)
                    try:
                        self._set_ai_selector_to_home()
                    except Exception:
                        pass
                    return
                if action == "addPlatform" and self.homepage_manager:
                    # 启用平台：多页面模式下首次高亮即创建第1个后台页面
                    self.homepage_manager.add_platform(platform_id)
                    if self.is_multiwindow_mode:
                        try:
                            # 若该平台暂无任何页面（运行时或配置中都没有），则后台创建一个
                            runtime_exists = any((meta.get('platform_id') == platform_id) for meta in self._page_meta.values())
                            config_exists = False
                            try:
                                config_exists = bool(self.homepage_manager.get_platform_windows(platform_id))
                            except Exception:
                                config_exists = False
                            if not (runtime_exists or config_exists):
                                self._pages_create(platform_id, background=True)
                        except Exception:
                            pass
                        # 同步主页行与下拉
                        self._update_homepage_platform_active(platform_id, True)
                        self._update_homepage_window_count(platform_id)
                        try:
                            self._populate_ai_selector(include_home_first=True)
                        except Exception:
                            pass
                        return
                    # 非多页面模式：保持旧逻辑，自动创建一个页面记录
                    try:
                        old_cnt = int(self.homepage_manager.get_total_window_count())
                    except Exception:
                        old_cnt = 0
                    try:
                        cur_map = self.homepage_manager.get_platform_windows(platform_id) or {}
                        if not cur_map:
                            from uuid import uuid4
                            new_id = str(uuid4())
                            self.homepage_manager.add_platform_window(platform_id, new_id, { 'createdAt': str(NSDate.date()) })
                    except Exception:
                        pass
                    self._update_homepage_platform_active(platform_id, True)
                    self._update_homepage_window_count(platform_id)
                    try:
                        self._set_ai_selector_to_home()
                    except Exception:
                        pass
                    try:
                        new_cnt = int(self.homepage_manager.get_total_window_count())
                    except Exception:
                        new_cnt = old_cnt
                    try:
                        self.notify_page_count_changed(old_cnt, new_cnt)
                    except Exception:
                        pass
                    return
                if action == "addWindow" and self.homepage_manager:
                    # 新增页面：单窗口多页面后台创建并加载（不前置）
                    if self.is_multiwindow_mode:
                        self._pages_create(platform_id, background=True)
                    else:
                        from uuid import uuid4
                        new_id = str(uuid4())
                        try:
                            old_cnt = int(self.homepage_manager.get_total_window_count())
                        except Exception:
                            old_cnt = 0
                        try:
                            _platform_before = self.homepage_manager.get_platform_windows(platform_id) or {}
                            old_platform_cnt = int(len(_platform_before))
                        except Exception:
                            old_platform_cnt = 0
                        ok = self.homepage_manager.add_platform_window(platform_id, new_id, { 'createdAt': str(NSDate.date()) })
                        if ok:
                            self._update_homepage_window_count(platform_id)
                            try:
                                self._set_ai_selector_to_home()
                            except Exception:
                                pass
                            try:
                                new_cnt = int(self.homepage_manager.get_total_window_count())
                            except Exception:
                                new_cnt = old_cnt
                            try:
                                self.notify_page_count_changed(old_cnt, new_cnt)
                            except Exception:
                                pass
                    return
                if action == "removeWindow" and self.homepage_manager:
                    wid = data.get('windowId') if isinstance(data, dict) else None
                    if platform_id and wid:
                        if self.is_multiwindow_mode:
                            self._pages_close(wid)
                        else:
                            try:
                                old_cnt = int(self.homepage_manager.get_total_window_count())
                            except Exception:
                                old_cnt = 0
                            ok = self.homepage_manager.remove_platform_window(platform_id, wid)
                            if ok:
                                self._update_homepage_window_count(platform_id)
                                try:
                                    self._set_ai_selector_to_home()
                                except Exception:
                                    pass
                                try:
                                    new_cnt = max(0, int(self.homepage_manager.get_total_window_count()))
                                except Exception:
                                    new_cnt = old_cnt
                                try:
                                    self.notify_page_count_changed(old_cnt, new_cnt)
                                except Exception:
                                    pass
                    return

            if name == "navigationAction":
                # 处理导航操作消息
                action = data.get("action") if isinstance(data, dict) else None
                if action == "navigateToHomepage" and self.navigation_controller:
                    self.navigation_controller.navigate_to_homepage()
                    self._load_homepage()
                elif action == "goBack" and self.navigation_controller:
                    if self.navigation_controller.can_go_back():
                        self.navigation_controller.go_back()
                        if self.navigation_controller.current_page == "homepage":
                            self._load_homepage()
                        else:
                            self._load_ai_service(self.navigation_controller.current_platform)
                elif action == "handleAISelection" and self.navigation_controller:
                    platform_id = data.get("platformId") if isinstance(data, dict) else None
                    window_id = data.get("windowId") if isinstance(data, dict) else None
                    self.navigation_controller.handle_ai_selector_change(platform_id, window_id)
                    self._load_ai_service(platform_id)
                return
        except Exception as e:
            print(f"WKScriptMessage 处理异常: {e}")

    # Logic for checking what color the logo in the status bar should be, and setting appropriate logo.
    def updateStatusItemImage(self):
        try:
            dark = self._is_dark_appearance()
        except Exception:
            dark = False
        # Choose the best-available image for current appearance with fallback
        img = None
        try:
            img = self.logo_white if dark else self.logo_black
            if img is None:
                img = self.logo_black if self.logo_black is not None else self.logo_white
        except Exception:
            img = None
        if img is None:
            print("WARNING: status bar icon missing for appearance", "dark" if dark else "light")
            return
        try:
            btn = self.status_item.button() if getattr(self, 'status_item', None) is not None else None
            if btn is not None:
                try:
                    btn.setWantsLayer_(True)
                except Exception:
                    pass
                btn.setImage_(img)
        except Exception as _e:
            print(f"WARNING: failed to set status bar image: {_e}")

    def _is_dark_appearance(self) -> bool:
        """Robust dark-mode detection.
        Order: status button effectiveAppearance -> NSApp.effectiveAppearance -> name contains 'Dark' -> AppleInterfaceStyle fallback.
        """
        appearance = None
        # Preferred: status item button effective appearance
        try:
            if getattr(self, 'status_item', None) is not None:
                btn = self.status_item.button()
                if btn is not None and hasattr(btn, 'effectiveAppearance'):
                    appearance = btn.effectiveAppearance()
        except Exception:
            appearance = None
        # Fallback: application appearance
        if appearance is None:
            try:
                appearance = NSApp.effectiveAppearance()
            except Exception:
                appearance = None
        # Try bestMatch API when available
        if appearance is not None:
            try:
                try:
                    names = [NSAppearanceNameAqua, NSAppearanceNameDarkAqua]
                except Exception:
                    names = ["NSAppearanceNameAqua", "NSAppearanceNameDarkAqua"]
                name = appearance.bestMatchFromAppearancesWithNames_(names)
                if name:
                    s = str(name)
                    return s.endswith("DarkAqua") or ('Dark' in s)
            except Exception:
                pass
            # Fallback: direct name()
            try:
                nm = appearance.name()
                if nm:
                    s = str(nm)
                    return ('Dark' in s) or ('dark' in s)
            except Exception:
                pass
        # Legacy fallback: AppleInterfaceStyle == 'Dark'
        try:
            from Foundation import NSUserDefaults
            val = NSUserDefaults.standardUserDefaults().stringForKey_("AppleInterfaceStyle")
            return str(val) == 'Dark'
        except Exception:
            pass
        return False

    # Observer that is triggered whenever the color of the status bar logo might need to be updated.
    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, object, change, context):
        if context == STATUS_ITEM_CONTEXT and keyPath == "effectiveAppearance":
            try:
                self.updateStatusItemImage()
            except Exception:
                pass

    # 返回按钮点击
    def navigateBack_(self, sender):
        try:
            if self.navigation_controller and self.navigation_controller.can_go_back():
                self.navigation_controller.go_back()
            else:
                if self.navigation_controller:
                    self.navigation_controller.navigate_to_homepage(save_current=False)
                else:
                    self._load_homepage()
        except Exception as e:
            print(f"DEBUG: navigateBack_ 异常: {e}")

    # 窗口尺寸变化时，调整顶部栏与选择器位置
    def windowDidResize_(self, notification):
        try:
            content_bounds = self.window.contentView().bounds()
            if hasattr(self, 'top_bar') and self.top_bar:
                self.top_bar.setFrame_(NSMakeRect(0, content_bounds.size.height - self.top_bar_height, content_bounds.size.width, self.top_bar_height))
            if hasattr(self, 'ai_selector') and self.ai_selector:
                selector_width = self.ai_selector.frame().size.width
                selector_height = self.ai_selector.frame().size.height
                selector_x = (self.top_bar.frame().size.width - selector_width) / 2
                selector_y = (self.top_bar_height - selector_height) / 2
                self.ai_selector.setFrame_(NSMakeRect(selector_x, selector_y, selector_width, selector_height))
                if hasattr(self, 'selector_bg') and self.selector_bg:
                    self.selector_bg.setFrame_(NSMakeRect(selector_x-6, selector_y-3, selector_width+12, selector_height+6))
            # 无额外主页指示器/标签
                if hasattr(self, 'back_button') and self.back_button:
                    try:
                        diameter = selector_height
                        bx = selector_x - diameter - 8
                        by = (self.top_bar_height - diameter) / 2
                        self.back_button.setFrame_(NSMakeRect(bx, by, diameter, diameter))
                        if hasattr(self, 'back_button_bg') and self.back_button_bg:
                            self.back_button_bg.setFrame_(NSMakeRect(bx, by, diameter, diameter))
                    except Exception:
                        self.back_button.setFrameOrigin_(NSMakePoint(10, content_bounds.size.height - self.top_bar_height + (self.top_bar_height - self.back_button.frame().size.height)/2))
            if self.webview:
                # WebView 保持全高，顶栏悬浮其上
                self.webview.setFrame_(NSMakeRect(0, 0, content_bounds.size.width, content_bounds.size.height))
            # 调整单窗口多页面的 WebView 布局
            try:
                for _wid, _wv in list(getattr(self, '_pages_map', {}).items()):
                    _wv.setFrame_(NSMakeRect(0, 0, content_bounds.size.width, content_bounds.size.height))
                
            except Exception:
                pass
        except Exception as e:
            print(f"DEBUG: windowDidResize_ 异常: {e}")

    # System triggered appearance changes that might affect logo color.
    def appearanceDidChange_(self, notification):
        # Update the logo image when the system appearance changes
        try:
            self.updateStatusItemImage()
        except Exception:
            pass
    # Handler to switch AI service based on dropdown selection
    def aiServiceChanged_(self, sender):
        if getattr(self, '_suppress_ai_action', False):
            return
        # 从内部映射解析平台/窗口，避免 representedObject 跨桥接不稳定
        idx = sender.indexOfSelectedItem()
        entry = None
        try:
            entry = self.ai_selector_map.get(int(idx)) if hasattr(self, 'ai_selector_map') else None
        except Exception:
            entry = None
        platform_id = entry.get('platform_id') if isinstance(entry, dict) else None
        window_id = entry.get('window_id') if isinstance(entry, dict) else None

        if self.is_multiwindow_mode:
            if platform_id:
                # 多页面模式：统一走导航控制器，确保返回键/品牌/下拉正确同步
                try:
                    if self.navigation_controller:
                        self.navigation_controller.handle_ai_selector_change(platform_id, window_id)
                    else:
                        # 兜底：直接切换到指定/现有/新建页面
                        if window_id and window_id in getattr(self, '_pages_map', {}):
                            self._pages_switch(window_id)
                        else:
                            target = None
                            try:
                                ordered = sorted(
                                    [(wid, meta) for wid, meta in self._page_meta.items() if meta.get('platform_id') == platform_id],
                                    key=lambda kv: kv[1].get('created_at') or 0
                                )
                                target = ordered[0][0] if ordered else None
                            except Exception:
                                target = None
                            if target:
                                self._pages_switch(target)
                            else:
                                wid = self._pages_create(platform_id, background=False)
                                if wid:
                                    self._pages_switch(wid)
                except Exception:
                    pass
            return
        else:
            if platform_id:
                # 更新导航状态到聊天页并加载对应服务
                if self.navigation_controller:
                    self.navigation_controller.handle_ai_selector_change(platform_id, window_id)
                else:
                    self._load_ai_service(platform_id)
            else:
                # 不再通过下拉项进入主页，主页请使用返回键
                return

    # -------- 单窗口多页面：核心实现 --------
    def _pages_frame(self):
        try:
            b = self.root_view.bounds()
            return NSMakeRect(0, 0, b.size.width, b.size.height)
        except Exception:
            return NSMakeRect(0, 0, 800, 600)

    def _pages_create(self, platform_id: str, background: bool = True):
        """在同一窗口内创建一个新的 WKWebView 页面，后台加载并加入下拉。返回 window_id 或 None。"""
        try:
            # 记录变更前页面数量（基于 _pages_map）
            try:
                _old_pages_count = int(len(getattr(self, '_pages_map', {})))
            except Exception:
                _old_pages_count = 0
            from uuid import uuid4
            wid = str(uuid4())
            cfg = WKWebViewConfiguration.alloc().init()
            try:
                cfg.preferences().setJavaScriptCanOpenWindowsAutomatically_(True)
            except Exception:
                pass
            wv = WKWebView.alloc().initWithFrame_configuration_(self._pages_frame(), cfg)
            try:
                wv.setUIDelegate_(self)
                wv.setNavigationDelegate_(self)
                wv.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
                wv.setAcceptsTouchEvents_(True)
                wv.setOpaque_(True)
                wv.setValue_forKey_(True, "drawsBackground")
                safari_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
                wv.setCustomUserAgent_(safari_user_agent)
            except Exception:
                pass
            # 添加到 root_view（先隐藏）
            try:
                # 将页面视图放在顶栏之下，确保顶栏始终可见
                if hasattr(self.root_view, 'addSubview_positioned_relativeTo_') and getattr(self, 'top_bar', None) is not None:
                    self.root_view.addSubview_positioned_relativeTo_(wv, NSWindowBelow, self.top_bar)
                else:
                    self.root_view.addSubview_(wv)
                    # 最后再把顶栏移到最上层
                    try:
                        if hasattr(self.root_view, 'addSubview_positioned_relativeTo_') and self.webview is not None:
                            self.top_bar.removeFromSuperview()
                            self.root_view.addSubview_positioned_relativeTo_(self.top_bar, NSWindowAbove, wv)
                    except Exception:
                        pass
            except Exception:
                pass
            try:
                wv.setHidden_(bool(background))
            except Exception:
                pass
            # 记录与加载
            self._pages_map[wid] = wv
            from Foundation import NSDate
            try:
                created_at = NSDate.date()
            except Exception:
                created_at = None
            self._page_meta[wid] = { 'platform_id': platform_id, 'created_at': created_at }
            try:
                url = self._get_platform_url(platform_id)
                if url:
                    nsurl = NSURL.URLWithString_(url)
                    req = NSURLRequest.requestWithURL_(nsurl)
                    wv.loadRequest_(req)
            except Exception:
                pass
            # 实时同步下拉与主页气泡
            try:
                if self.homepage_manager:
                    from Foundation import NSDate as _NSDate
                    self.homepage_manager.add_platform_window(platform_id, wid, { 'createdAt': str(_NSDate.date()) })
                if not getattr(self, '_batch_restoring', False):
                    self._populate_ai_selector(include_home_first=True)
                    self._update_homepage_window_count(platform_id)
                    # 触发页面计数变化回调（用于阈值 toast）
                    try:
                        _new_pages_count = int(len(getattr(self, '_pages_map', {})))
                    except Exception:
                        _new_pages_count = _old_pages_count
                    self.notify_page_count_changed(_old_pages_count, _new_pages_count)
            except Exception:
                pass
            return wid
        except Exception as e:
            print(f"WARNING: _pages_create 失败: {e}")
            return None

    def _pages_create_for_id(self, platform_id: str, window_id: str, background: bool = True):
        """使用指定的 window_id 在当前窗口创建 WKWebView（用于从配置恢复）。"""
        try:
            if not platform_id or not window_id:
                return None
            # 已存在则跳过
            if window_id in self._pages_map:
                return window_id
            # 记录变更前计数
            try:
                _old_pages_count = int(len(getattr(self, '_pages_map', {})))
            except Exception:
                _old_pages_count = 0
            cfg = WKWebViewConfiguration.alloc().init()
            try:
                cfg.preferences().setJavaScriptCanOpenWindowsAutomatically_(True)
            except Exception:
                pass
            wv = WKWebView.alloc().initWithFrame_configuration_(self._pages_frame(), cfg)
            try:
                wv.setUIDelegate_(self)
                wv.setNavigationDelegate_(self)
                wv.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
                wv.setAcceptsTouchEvents_(True)
                wv.setOpaque_(True)
                wv.setValue_forKey_(True, "drawsBackground")
                safari_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
                wv.setCustomUserAgent_(safari_user_agent)
            except Exception:
                pass
            # 添加到 root_view（先隐藏）
            try:
                if hasattr(self.root_view, 'addSubview_positioned_relativeTo_') and getattr(self, 'top_bar', None) is not None:
                    self.root_view.addSubview_positioned_relativeTo_(wv, NSWindowBelow, self.top_bar)
                else:
                    self.root_view.addSubview_(wv)
                    try:
                        if hasattr(self.root_view, 'addSubview_positioned_relativeTo_') and self.webview is not None:
                            self.top_bar.removeFromSuperview()
                            self.root_view.addSubview_positioned_relativeTo_(self.top_bar, NSWindowAbove, wv)
                    except Exception:
                        pass
                wv.setHidden_(bool(background))
            except Exception:
                pass
            # 记录与加载（不写回 HomepageManager）
            self._pages_map[window_id] = wv
            from Foundation import NSDate
            try:
                created_at = NSDate.date()
            except Exception:
                created_at = None
            self._page_meta[window_id] = { 'platform_id': platform_id, 'created_at': created_at }
            try:
                url = self._get_platform_url(platform_id)
                if url:
                    nsurl = NSURL.URLWithString_(url)
                    req = NSURLRequest.requestWithURL_(nsurl)
                    wv.loadRequest_(req)
            except Exception:
                pass
            # 变更后计数提示（恢复阶段只在非批量时提示）
            try:
                if not getattr(self, '_batch_restoring', False):
                    _new_pages_count = int(len(getattr(self, '_pages_map', {})))
                    self.notify_page_count_changed(_old_pages_count, _new_pages_count)
            except Exception:
                pass
            return window_id
        except Exception:
            return None

    def restorePagesIfAny_(self, _timer):
        """定时器回调：从用户配置恢复历史页面到后台。"""
        try:
            if getattr(self, '_restored_pages_done', False):
                return
            if not getattr(self, 'is_multiwindow_mode', False):
                return
            if not getattr(self, 'homepage_manager', None):
                return
            all_windows = {}
            try:
                all_windows = self.homepage_manager.get_all_windows() or {}
            except Exception:
                all_windows = {}
            if not all_windows:
                self._restored_pages_done = True
                return
            # 批量恢复，避免反复刷新下拉
            self._batch_restoring = True
            for pid, win_map in list(all_windows.items()):
                try:
                    for wid in list(win_map.keys()):
                        try:
                            self._pages_create_for_id(pid, wid, background=True)
                        except Exception:
                            pass
                except Exception:
                    pass
            self._batch_restoring = False
            # 统一刷新一次下拉（主页包含“主页”，非主页不包含）
            try:
                self._populate_ai_selector(include_home_first=bool(getattr(self, 'last_loaded_is_homepage', False)))
            except Exception:
                pass
            self._restored_pages_done = True
        except Exception:
            pass

    def _pages_switch(self, window_id: str) -> bool:
        try:
            if window_id not in self._pages_map:
                return False
            # 隐藏主页 WebView
            try:
                if getattr(self, 'webview', None):
                    self.webview.setHidden_(True)
            except Exception:
                pass
            # 隐藏当前页
            if self._active_page_id and self._active_page_id in self._pages_map:
                try:
                    self._pages_map[self._active_page_id].setHidden_(True)
                except Exception:
                    pass
            # 显示目标
            try:
                self._pages_map[window_id].setHidden_(False)
            except Exception:
                pass
            self._active_page_id = window_id
            # 窗口标题与返回键
            try:
                self.update_back_button_visibility(True)
                pid = self._page_meta.get(window_id, {}).get('platform_id')
                base = self._i18n_or_default('app.name', 'Bubble')
                chat = self._i18n_or_default('nav.chat', 'Chat')
                name = self._i18n_or_default(f'platform.{pid}', (pid or 'AI').title()) if pid else 'AI'
                self.update_window_title(f"{base} - {chat}: {name}")
            except Exception:
                pass
            # 保障顶栏与下拉可见
            try:
                self._update_ai_selector_ui(True)
            except Exception:
                pass
            # 进入页面，移除下拉中的“主页”项
            try:
                self.last_loaded_is_homepage = False
                # 批量操作中避免重复刷新
                if not getattr(self, '_batch_closing', False):
                    self._populate_ai_selector(include_home_first=False)
            except Exception:
                pass
            # 下拉选中该页
            try:
                pid = self._page_meta.get(window_id, {}).get('platform_id')
                self._suppress_ai_action = True
                try:
                    self._select_ai_item(pid, window_id)
                finally:
                    self._suppress_ai_action = False
            except Exception:
                pass
            # 若目标页仍在加载中，显示骨架；否则隐藏
            try:
                wv = self._pages_map.get(window_id)
                loading = False
                try:
                    loading = bool(wv.isLoading()) if hasattr(wv, 'isLoading') else False
                except Exception:
                    loading = False
                if loading:
                    self._show_skeleton_overlay()
                else:
                    self._hide_skeleton_overlay()
            except Exception:
                pass
            return True
        except Exception:
            return False

    def _pages_close(self, window_id: str) -> bool:
        try:
            try:
                _old_pages_count = int(len(getattr(self, '_pages_map', {})))
            except Exception:
                _old_pages_count = 0
            meta = self._page_meta.get(window_id) or {}
            pid = meta.get('platform_id')
            wv = self._pages_map.get(window_id)
            if wv is not None:
                try:
                    wv.removeFromSuperview()
                except Exception:
                    pass
            self._pages_map.pop(window_id, None)
            self._page_meta.pop(window_id, None)
            if getattr(self, '_active_page_id', None) == window_id:
                self._active_page_id = None
                # 切到该平台其他页，或回主页
                alt = None
                try:
                    alt = next((wid for wid, mm in self._page_meta.items() if mm.get('platform_id') == pid), None)
                except Exception:
                    alt = None
                if alt:
                    self._pages_switch(alt)
                else:
                    try:
                        self.update_back_button_visibility(False)
                    except Exception:
                        pass
                    try:
                        if getattr(self, 'webview', None):
                            self.webview.setHidden_(False)
                    except Exception:
                        pass
                    try:
                        self._load_homepage()
                    except Exception:
                        pass
            # 同步 UI（支持批量关闭时抑制重复刷新）
            try:
                if self.homepage_manager and pid and window_id:
                    self.homepage_manager.remove_platform_window(pid, window_id)
                if not getattr(self, '_batch_closing', False):
                    self._populate_ai_selector(include_home_first=True)
                    if pid:
                        self._update_homepage_window_count(pid)
                    try:
                        _new_pages_count = int(len(getattr(self, '_pages_map', {})))
                    except Exception:
                        _new_pages_count = max(0, _old_pages_count - 1)
                    self.notify_page_count_changed(_old_pages_count, _new_pages_count)
            except Exception:
                pass
            return True
        except Exception:
            return False

    def _populate_ai_selector(self, include_home_first: bool = False):
        """填充AI选择器下拉框"""
        if not self.ai_selector:
            return

        # 清空现有选项
        self.ai_selector.removeAllItems()
        try:
            self.ai_selector_map = {}
        except Exception:
            pass

        # 首页优先项（仅当在主页时调用时使用）
        if include_home_first:
            self.ai_selector.addItemWithTitle_(_t('nav.home'))
            try:
                # 给“主页”项加屋子图标
                it = self.ai_selector.itemAtIndex_(0)
                if it is not None:
                    try:
                        img = NSImage.imageWithSystemSymbolName_accessibilityDescription_("house.fill", None) or NSImage.imageWithSystemSymbolName_accessibilityDescription_("house", None)
                        if img is not None:
                            try:
                                img.setSize_(NSSize(14, 14))
                            except Exception:
                                pass
                            it.setImage_(img)
                    except Exception:
                        pass
                self.ai_selector_map[0] = {'platform_id': None, 'window_id': None}
            except Exception:
                pass

        # 优先使用单窗口多页面的实时列表；否则回退到 HomepageManager 配置
        if self.is_multiwindow_mode and getattr(self, '_page_meta', None) is not None:
            # 按平台分组 self._page_meta（window_id -> meta）
            grouped = {}
            for wid, meta in self._page_meta.items():
                try:
                    pid = meta.get('platform_id')
                    if not pid:
                        continue
                    grouped.setdefault(pid, []).append((wid, meta))
                except Exception:
                    pass
            for pid, items in grouped.items():
                try:
                    items.sort(key=lambda kv: kv[1].get('created_at') or 0)
                except Exception:
                    pass
                try:
                    base_name = self._i18n_or_default(f'platform.{pid}', pid.title())
                except Exception:
                    base_name = pid.title()
                try:
                    if pid in ("mistral", "perplexity"):
                        base_name = str(base_name).capitalize()
                except Exception:
                    pass
                for idx, (wid, _m) in enumerate(items, start=1):
                    title = base_name if idx == 1 else f"{base_name} {idx}"
                    self._ai_selector_add_item(title, pid, wid)
            if not grouped and self.platform_manager:
                for p in self.platform_manager.get_enabled_platforms():
                    self._ai_selector_add_item(p.display_name, p.platform_id, None)
        else:
            # 获取启用的平台列表及其窗口（来自 HomepageManager）
            enabled = {}
            if self.homepage_manager:
                try:
                    enabled = self.homepage_manager.get_enabled_platforms()  # dict pid -> info
                except Exception:
                    enabled = {}

            if not enabled and self.platform_manager:
                # 退化为平台管理器（无窗口信息）
                for p in self.platform_manager.get_enabled_platforms():
                    self._ai_selector_add_item(p.display_name, p.platform_id, None)
            else:
                # 基于窗口实例填充；同平台多个实例用序号（来自 HomepageManager 的记录）
                for pid, info in enabled.items():
                    try:
                        display_base = self._i18n_or_default(f'platform.{pid}', info.get('display_name', pid.title()))
                    except Exception:
                        display_base = info.get('display_name', pid.title())
                    try:
                        if pid in ("mistral", "perplexity"):
                            display_base = str(display_base).capitalize()
                    except Exception:
                        pass
                    win_map = {}
                    try:
                        win_map = self.homepage_manager.get_platform_windows(pid)
                    except Exception:
                        win_map = {}
                    if not win_map:
                        self._ai_selector_add_item(display_base, pid, None)
                    else:
                        items = list(win_map.items())  # (window_id, info)
                        try:
                            items.sort(key=lambda kv: kv[1].get('createdAt', ''))
                        except Exception:
                            pass
                        for idx, (wid, winfo) in enumerate(items, start=1):
                            title = display_base if idx == 1 else f"{display_base} {idx}"
                            self._ai_selector_add_item(title, pid, wid)

        # 如果最终没有任何选项：放置占位“主页”项，保持顶部栏存在
        if self.ai_selector.numberOfItems() == 0:
            try:
                self.ai_selector.addItemWithTitle_(_t('nav.home'))
                self.ai_selector_map[0] = {'platform_id': None, 'window_id': None}
                self.ai_selector.selectItemAtIndex_(0)
            except Exception:
                pass

        # 设置默认选择（优先保持当前活动页/导航状态的选择）
        # 在填充期间抑制动作回调，避免误触发导航
        desired_platform = None
        desired_window = None
        try:
            if self.is_multiwindow_mode and getattr(self, '_active_page_id', None) in self._page_meta:
                apid = self._active_page_id
                desired_window = apid
                desired_platform = self._page_meta.get(apid, {}).get('platform_id')
            elif getattr(self, 'navigation_controller', None) and self.navigation_controller.current_page == 'chat':
                desired_platform = self.navigation_controller.current_platform
                desired_window = getattr(self.navigation_controller, 'current_window_id', None)
        except Exception:
            desired_platform = desired_platform or None
            desired_window = desired_window or None

        self._suppress_ai_action = True
        try:
            if include_home_first and self.ai_selector.numberOfItems() > 0:
                # 主页：优先选中“主页”项
                self.ai_selector.selectItemAtIndex_(0)
            elif desired_platform:
                # 聊天页：精确选中当前活动页面
                self._select_ai_item(desired_platform, desired_window)
            else:
                # 兜底：按默认平台
                self._set_default_ai_selection()
        finally:
            self._suppress_ai_action = False
        # 确保顶栏可见（有选项时）
        self._update_ai_selector_ui(True)
        # 美化菜单项：居中与可爱加粗字体
        try:
            self._style_popup_menu_items()
        except Exception:
            pass

    def _get_platform_id_from_display_name(self, display_name):
        """从显示名称获取平台ID"""
        # 处理多窗口模式下的格式："Platform Name (2)"
        if "(" in display_name and ")" in display_name:
            display_name = display_name[:display_name.rfind("(")].strip()

        # 在启用的平台中查找（优先 HomepageManager 配置）
        if self.homepage_manager:
            try:
                hp_enabled = self.homepage_manager.get_enabled_platforms()
                for pid, info in hp_enabled.items():
                    if info.get('display_name') == display_name:
                        return pid
            except Exception:
                pass
        for platform in self.platform_manager.get_enabled_platforms():
            if platform.display_name == display_name:
                return platform.platform_id

        # 如果没有找到，尝试传统的AI_SERVICES映射
        service_mapping = {
            "Grok": "grok",
            "Gemini": "gemini",
            "ChatGPT": "openai",
            "Claude": "claude",
            "DeepSeek": "deepseek"
        }
        return service_mapping.get(display_name)

    def _select_ai_item(self, platform_id, window_id=None):
        """根据平台/窗口在下拉框中选中对应项（使用 ai_selector_map，避免标题不一致）。"""
        try:
            if not self.ai_selector or not hasattr(self, 'ai_selector_map'):
                return
            count = int(self.ai_selector.numberOfItems())
            exact_idx = None
            first_platform_idx = None
            for i in range(count):
                entry = self.ai_selector_map.get(i)
                if not isinstance(entry, dict):
                    continue
                pid = entry.get('platform_id')
                wid = entry.get('window_id')
                if pid == platform_id:
                    if first_platform_idx is None:
                        first_platform_idx = i
                    if window_id is not None and wid == window_id:
                        exact_idx = i
                        break
            idx = exact_idx if exact_idx is not None else first_platform_idx
            if idx is not None:
                self.ai_selector.selectItemAtIndex_(int(idx))
        except Exception:
            pass

    def _get_cute_bold_font(self, size):
        """返回一个可爱/圆润风格的粗体字体（带多级兜底）。"""
        try:
            # 优先尝试 SF Pro Rounded 系列（如果系统有）
            for name in (
                "SF Pro Rounded Semibold",
                "SF Pro Rounded Bold",
                "Avenir Next Rounded Demi Bold",
                "Avenir Next Rounded Bold",
                "Helvetica Neue Bold",
            ):
                f = NSFont.fontWithName_size_(name, float(size))
                if f:
                    return f
        except Exception:
            pass
        try:
            return NSFont.boldSystemFontOfSize_(float(size))
        except Exception:
            return None

    def _set_default_ai_selection(self):
        """设置默认的AI选择"""
        if not self.ai_selector:
            return

        # 获取默认平台（优先 HomepageManager），选中其第一项
        default_id = None
        if self.homepage_manager:
            try:
                default_id = self.homepage_manager.get_default_ai()
            except Exception:
                default_id = None
        if not default_id and self.platform_manager:
            dp = self.platform_manager.get_default_platform()
            if dp:
                default_id = dp.platform_id

        if default_id:
            for i in range(self.ai_selector.numberOfItems()):
                try:
                    rep = self.ai_selector_map.get(i)
                    if rep and rep.get('platform_id') == default_id:
                        self.ai_selector.selectItemAtIndex_(i)
                        break
                except Exception:
                    pass
        elif self.ai_selector.numberOfItems() > 0:
            self.ai_selector.selectItemAtIndex_(0)

    def _set_ai_selector_to_home(self):
        """在主页时将下拉框显示为“主页”并列出全部页面实例。"""
        try:
            self._populate_ai_selector(include_home_first=True)
        except Exception as e:
            print(f"DEBUG: _set_ai_selector_to_home 异常: {e}")

    def _style_popup_menu_items(self):
        try:
            if not self.ai_selector:
                return
            menu = self.ai_selector.menu()
            if not menu:
                return
            font = self._get_cute_bold_font(13) or NSFont.boldSystemFontOfSize_(13)
            from AppKit import NSMutableParagraphStyle, NSFontAttributeName, NSParagraphStyleAttributeName, NSTextAlignmentCenter, NSAttributedString
            ps = NSMutableParagraphStyle.alloc().init()
            ps.setAlignment_(NSTextAlignmentCenter)
            items = menu.itemArray() if hasattr(menu, 'itemArray') else [menu.itemAtIndex_(i) for i in range(menu.numberOfItems())]
            for it in items:
                if it is None:
                    continue
                t = it.title()
                try:
                    attr = NSAttributedString.alloc().initWithString_attributes_(t, {NSFontAttributeName: font, NSParagraphStyleAttributeName: ps})
                    it.setAttributedTitle_(attr)
                except Exception:
                    pass
        except Exception:
            pass

    # 取消下拉菜单委托相关逻辑，稳定优先

    def _ai_selector_add_item(self, title, platform_id, window_id):
        """辅助：为下拉框添加带元数据的项，并设置图标。"""
        self.ai_selector.addItemWithTitle_(title)
        index = self.ai_selector.numberOfItems() - 1
        try:
            # 使用 Python 侧映射，避免 representedObject 跨桥接潜在崩溃
            if not hasattr(self, 'ai_selector_map') or self.ai_selector_map is None:
                self.ai_selector_map = {}
            self.ai_selector_map[index] = {
                'platform_id': platform_id,
                'window_id': window_id
            }
        except Exception:
            pass
        # 设置菜单项图标
        try:
            it = self.ai_selector.itemAtIndex_(index)
            if it is not None and platform_id:
                url = self._get_platform_url(platform_id)
                img = self._get_favicon_image(platform_id, url)
                if img is not None:
                    it.setImage_(img)
        except Exception:
            pass

    # --- 多窗口事件回调：同步主页与下拉 ---
    def _on_multiwin_opened(self, ai_window):
        try:
            pid = getattr(ai_window, 'platform_id', None)
            wid = getattr(ai_window, 'window_id', None)
            if self.homepage_manager and pid and wid:
                self.homepage_manager.add_platform_window(pid, wid, { 'createdAt': str(NSDate.date()) })
        except Exception:
            pass
        # 刷新下拉
        try:
            self._populate_ai_selector()
        except Exception:
            pass
        # 刷新主页气泡
        try:
            if pid:
                self._update_homepage_window_count(pid)
        except Exception:
            pass

    def _on_multiwin_closed(self, window_id, platform_id):
        try:
            if self.homepage_manager and platform_id and window_id:
                self.homepage_manager.remove_platform_window(platform_id, window_id)
        except Exception:
            pass
        try:
            self._populate_ai_selector()
        except Exception:
            pass
        try:
            if platform_id:
                self._update_homepage_window_count(platform_id)
        except Exception:
            pass

    def _get_platform_url(self, platform_id):
        # 从 HomepageManager 获取
        try:
            if self.homepage_manager:
                allp = self.homepage_manager.get_available_platforms()
                if platform_id in allp:
                    return allp[platform_id].get('url')
        except Exception:
            pass
        # 从 PlatformManager 获取
        try:
            if self.platform_manager:
                p = self.platform_manager.get_platform(platform_id)
                if p:
                    return p.url
        except Exception:
            pass
        # 兜底映射
        return {
            "openai": "https://chat.openai.com",
            "gemini": "https://gemini.google.com",
            "grok": "https://grok.com",
            "claude": "https://claude.ai/chat",
            "deepseek": "https://chat.deepseek.com",
            "zai": "https://chat.z.ai/",
            "qwen": "https://chat.qwen.ai/",
            "mistral": "https://chat.mistral.ai",
            "perplexity": "https://www.perplexity.ai",
            "kimi": "https://www.kimi.com/",
        }.get(platform_id)

    def _get_favicon_image(self, platform_id, url):
        try:
            cache = getattr(self, '_ai_selector_icon_cache', None)
            if isinstance(cache, dict) and platform_id in cache:
                return cache.get(platform_id)
            # 仅使用随包本地图标（assets/icons/<id>.png）；不做联网与运行时生成
            img = None
            # 1) 尝试读取打包资源 assets/icons/<id>.png
            try:
                bundle = NSBundle.mainBundle()
                base_dir = bundle.resourcePath()
                if base_dir:
                    p = os.path.join(str(base_dir), 'assets', 'icons', f'{platform_id}.png')
                    if os.path.exists(p):
                        img = NSImage.alloc().initWithContentsOfFile_(p)
            except Exception:
                img = None
            # 1b) 开发模式：src/bubblebot/assets/icons
            if img is None:
                try:
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    p = os.path.join(script_dir, 'assets', 'icons', f'{platform_id}.png')
                    if os.path.exists(p):
                        img = NSImage.alloc().initWithContentsOfFile_(p)
                except Exception:
                    img = None
            if img is not None:
                try:
                    img.setSize_(NSSize(16, 16))
                except Exception:
                    pass
                try:
                    self._ai_selector_icon_cache[platform_id] = img
                except Exception:
                    pass
            return img
        except Exception:
            return None

    def _update_ai_selector_ui(self, visible):
        """更新AI选择器显示状态（顶部栏）/内部实现"""
        try:
            # 顶栏保持显示，用于拖拽/返回/主页标签
            if self.ai_selector:
                # 永远显示，不随页面变化隐藏
                self.ai_selector.setHidden_(False)
                # 同步背景容器
                if hasattr(self, 'selector_bg') and self.selector_bg:
                    self.selector_bg.setHidden_(False)
            # WebView 不调整高度（顶栏悬浮覆盖）
        except Exception as e:
            print(f"DEBUG: update_ai_selector_visibility 异常: {e}")

    def _on_platform_config_changed(self, event_type, data):
        """平台配置变更时的回调"""
        # 当平台配置发生变化时，更新AI选择器
        if self.ai_selector:
            self._populate_ai_selector()
        print(f"平台配置变更: {event_type}")
    # Increase overlay transparency
    def increaseTransparency_(self, sender):
        current = self.window.alphaValue()
        new_alpha = min(current + 0.1, 1.0)
        self.window.setAlphaValue_(new_alpha)

    # Decrease overlay transparency
    def decreaseTransparency_(self, sender):
        current = self.window.alphaValue()
        new_alpha = max(current - 0.1, 0.2)
        self.window.setAlphaValue_(new_alpha)

    # Automatically grant microphone permission requests from the webview
    def webView_requestMediaCapturePermissionForOrigin_initiatedByFrame_type_decisionListener_(self, webView, origin, frame, mediaType, listener):
        # Grant all media capture requests (e.g., microphone)
        listener.grant()
    
    # WKNavigationDelegate 方法
    def webView_didCommitNavigation_(self, webView, navigation):
        """导航开始提交时调用"""
        try:
            print("DEBUG: WKWebView didCommitNavigation")
            if getattr(self, '_skeleton_suppress_until_finish', False):
                # 抑制到完成
                pass
            elif getattr(self, '_skeleton_suppress_next', False):
                # 一次性抑制骨架屏
                self._skeleton_suppress_next = False
            else:
                # 仅对当前前台可见页面显示骨架；主页不显示
                if self._should_show_skeleton_for_webview(webView):
                    self._show_skeleton_overlay()
        except Exception:
            pass

    def webView_didStartProvisionalNavigation_(self, webView, navigation):
        """开始加载时显示骨架屏。"""
        try:
            print("DEBUG: WKWebView didStartProvisionalNavigation")
            # 新的加载开始时，隐藏错误提示
            try:
                self._hide_error_overlay()
            except Exception:
                pass
            if getattr(self, '_skeleton_suppress_until_finish', False):
                # 抑制到完成
                pass
            elif getattr(self, '_skeleton_suppress_next', False):
                # 一次性抑制骨架屏
                self._skeleton_suppress_next = False
            else:
                # 仅对当前前台可见页面显示骨架；主页不显示
                if self._should_show_skeleton_for_webview(webView):
                    self._show_skeleton_overlay()
        except Exception:
            pass
    
    def webView_didFinishNavigation_(self, webView, navigation):
        """导航完成时调用，确保页面可交互"""
        print("DEBUG: WKWebView didFinishNavigation")
        # 注入 JavaScript 确保页面元素可点击
        script = """
        // 确保所有元素都可以接收点击事件
        document.body.style.pointerEvents = 'auto';
        var elements = document.querySelectorAll('*');
        for (var i = 0; i < elements.length; i++) {
            if (elements[i].style.pointerEvents === 'none') {
                elements[i].style.pointerEvents = 'auto';
            }
        }
        console.log('页面交互性已恢复');
        """
        webView.evaluateJavaScript_completionHandler_(script, None)
        # 如果是主页，确保内容下移不被顶栏遮挡
        try:
            if self.last_loaded_is_homepage:
                pad = int(self.top_bar_height + 20)
                webView.evaluateJavaScript_completionHandler_(f"document.body && (document.body.style.paddingTop='{pad}px');", None)
        except Exception:
            pass
        # 页面完成后隐藏骨架
        try:
            self._hide_skeleton_overlay()
        except Exception:
            pass
        try:
            # 结束全程抑制
            self._skeleton_suppress_until_finish = False
        except Exception:
            pass
        # 成功加载后隐藏错误提示
        try:
            self._hide_error_overlay()
        except Exception:
            pass
    
    def webView_didFailNavigation_withError_(self, webView, navigation, error):
        """导航失败时调用"""
        print(f"导航失败: {error}")
        try:
            self._hide_skeleton_overlay()
        except Exception:
            pass
        try:
            self._skeleton_suppress_until_finish = False
        except Exception:
            pass
        try:
            msg = getattr(error, 'localizedDescription', None)
            if not msg:
                msg = str(error)
            self._show_error_overlay(msg)
        except Exception:
            pass

    # 早期阶段失败（例如网络中断、证书、DNS）
    def webView_didFailProvisionalNavigation_withError_(self, webView, navigation, error):
        try:
            print(f"导航失败: {error}")
        except Exception:
            pass
        try:
            self._hide_skeleton_overlay()
        except Exception:
            pass
        try:
            self._skeleton_suppress_until_finish = False
        except Exception:
            pass
        try:
            msg = getattr(error, 'localizedDescription', None) or str(error)
            self._show_error_overlay(msg)
        except Exception:
            pass

    def webView_decidePolicyForNavigationAction_decisionHandler_(self, webView, navigationAction, decisionHandler):
        """决定是否允许导航"""
        decisionHandler(1)  # WKNavigationActionPolicyAllow

    # 加载主页
    def _load_homepage(self):
        """加载主页内容"""
        if self.homepage_manager:
            try:
                self._hide_error_overlay()
            except Exception:
                pass
            try:
                self._hide_skeleton_overlay()
            except Exception:
                pass
            # 主页加载不显示骨架屏
            try:
                # 抑制整个加载生命周期，避免 didStart/didCommit 双事件造成闪烁
                self._skeleton_suppress_next = True
                self._skeleton_suppress_until_finish = True
            except Exception:
                pass
            html_content = self.homepage_manager.show_homepage()
            self.webview.loadHTMLString_baseURL_(html_content, None)
            try:
                print(f"DEBUG: 主页HTML长度: {len(html_content)}")
            except Exception:
                pass
            self.last_loaded_is_homepage = True
            # 在主页时无条件将下拉框显示为“主页”，避免混淆
            try:
                self._set_ai_selector_to_home()
            except Exception:
                pass
            # 主页不显示返回按钮
            try:
                self.update_back_button_visibility(False)
            except Exception:
                pass
            # 已禁用联网图标下载：使用离线生成的字母图标，无需预取
            print("主页已加载")

    # 刷新主页
    def _refresh_homepage(self):
        """刷新主页内容"""
        if self.navigation_controller and self.navigation_controller.current_page == "homepage":
            self._load_homepage()

    # ---- 无刷新更新主页行元素（后台加载/不闪烁） ----
    def _js_eval(self, script: str):
        try:
            if self.webview:
                self.webview.evaluateJavaScript_completionHandler_(script, None)
        except Exception:
            pass

    def _update_homepage_platform_active(self, platform_id: str, active: bool):
        """切换某平台的 active 状态 + 显隐右侧按钮（无刷新）。"""
        if not getattr(self, 'last_loaded_is_homepage', False):
            return
        active_js = 'true' if active else 'false'
        inactive_js = 'false' if active else 'true'
        js = f"""
            (function(){{
                const row = document.querySelector('.hrow[data-pid=\"{platform_id}\"]');
                if (!row) return;
                row.classList.toggle('active', {active_js});
                const btn = row.querySelector('button.more');
                try {{
                    const wl = JSON.parse(row.dataset.windows||'[]')||[];
                    const count = Array.isArray(wl) ? wl.length : 0;
                    if (btn) btn.classList.toggle('hidden', !({active_js}));
                }} catch (err) {{ if (btn) btn.classList.toggle('hidden', true); }}
                if (!{active_js}) {{ const b = row.querySelector('.bubble'); if (b) {{ b.textContent='0'; b.classList.add('hidden'); }} }}
            }})();
        """
        self._js_eval(js)

    def _update_homepage_window_count(self, platform_id: str):
        """更新指定平台多页面气泡数量与 data-windows（无刷新）。"""
        if not getattr(self, 'last_loaded_is_homepage', False):
            return
        try:
            win_map = self.homepage_manager.get_platform_windows(platform_id) if self.homepage_manager else {}
        except Exception:
            win_map = {}
        items = list(win_map.items())  # (window_id, info)
        try:
            items.sort(key=lambda kv: kv[1].get('createdAt', ''))
        except Exception:
            pass
        # 构造 [{id, idx}]
        idx_items = []
        for idx, (wid, _) in enumerate(items, start=1):
            idx_items.append({'id': wid, 'idx': idx})
        import json as _json
        js_data = _json.dumps(idx_items)
        count = len(idx_items)
        js = f"""
            (function(){{
                const row = document.querySelector('.hrow[data-pid=\"{platform_id}\"]');
                if (!row) return;
                row.dataset.windows = '{js_data.replace("'", "\\'")}';
                const b = row.querySelector('.bubble');
                if (b) {{ b.textContent = String({count}); if ({count} > 0) b.classList.remove('hidden'); else b.classList.add('hidden'); }}
                const btn = row.querySelector('button.more');
                if (btn) btn.classList.toggle('hidden', !row.classList.contains('active'));
            }})();
        """
        self._js_eval(js)

    # 加载AI服务
    def _load_ai_service(self, platform_id):
        """加载指定AI服务"""
        if not platform_id:
            return

        # 获取AI服务URL
        ai_services = {
            "openai": "https://chat.openai.com",
            "gemini": "https://gemini.google.com",
            "grok": "https://grok.com",
            "claude": "https://claude.ai/chat",
            "deepseek": "https://chat.deepseek.com",
            "zai": "https://chat.z.ai/",
            "qwen": "https://chat.qwen.ai/",
            "mistral": "https://chat.mistral.ai",
            "perplexity": "https://www.perplexity.ai",
            "kimi": "https://www.kimi.com/"
        }

        service_url = ai_services.get(platform_id)
        if service_url:
            url = NSURL.URLWithString_(service_url)
            request = NSURLRequest.requestWithURL_(url)
            # 显示骨架并发起加载
            try:
                self._hide_error_overlay()
            except Exception:
                pass
            try:
                self._show_skeleton_overlay()
            except Exception:
                pass
            self.webview.loadRequest_(request)
            # 确保返回按钮在平台页可见
            try:
                self.update_back_button_visibility(True)
            except Exception:
                pass

            # 更新AI选择器：按平台/窗口精确选中
            self._select_ai_item(platform_id)

            self.last_loaded_is_homepage = False
            print(f"AI服务已加载: {platform_id}")
        else:
            print(f"不支持的AI平台: {platform_id}")

    def _ensure_skeleton_view(self):
        try:
            if self.skeleton_view is not None:
                return
            if not self.root_view:
                return
            # 容器用于持有可能的定时器，避免被回收
            bounds = self.window.contentView().bounds()
            sk = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, bounds.size.width, bounds.size.height))
            sk.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            sk.setWantsLayer_(True)
            try:
                sk.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.98, 1.0).CGColor())
            except Exception:
                pass
            # 占位块（简洁灰色块）
            shimmer_blocks = []
            def add_block(x, y, w, h, radius=10):
                view = NSView.alloc().initWithFrame_(NSMakeRect(x, y, w, h))
                view.setWantsLayer_(True)
                try:
                    view.layer().setCornerRadius_(radius)
                    # 统一灰色占位
                    view.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(0.85, 1.0).CGColor())
                    view.layer().setMasksToBounds_(True)
                except Exception:
                    pass
                sk.addSubview_(view)
                shimmer_blocks.append(view)
            content_h = bounds.size.height
            content_w = bounds.size.width
            # DaisyUI skeleton（circle + two lines + large rect）布局（更分散）
            margin_side = 32
            margin_top = self.top_bar_height + 36
            margin_bottom = 36
            skeleton_w = int(min(360, max(240, content_w * 0.52)))
            x0 = int((content_w - skeleton_w) / 2)
            y_anchor = int(min(content_h - margin_top - 20, (content_h - self.top_bar_height) * 0.64))
            # 第一行：圆形 + 两条文本线
            circle = 64
            gap = 20
            # 圆形（左）
            add_block(x0, y_anchor - circle, circle, circle, circle/2)
            # 右侧两条线
            line_h = 12
            line1_w = 96
            line2_w = 128
            right_x = x0 + circle + gap
            # 垂直居中在圆形内
            line1_y = y_anchor - int(circle/2) + int(line_h/2)
            line2_y = line1_y - (line_h + 8)
            add_block(right_x, line1_y, line1_w, line_h, 6)
            add_block(right_x, line2_y, line2_w, line_h, 6)
            # 第二行：大矩形
            rect_h = 140
            rect_y = line2_y - (gap + 8) - rect_h
            if rect_y < margin_bottom:
                rect_y = margin_bottom
            add_block(x0, rect_y, skeleton_w, rect_h, 10)
            # 可选：底部一条次要线条，拉开层次
            minor_y = rect_y - 18
            if minor_y > margin_bottom:
                add_block(x0 + int(skeleton_w*0.2), minor_y, int(skeleton_w*0.6), 10, 6)
            self.skeleton_view = sk
            self.skeleton_view.setHidden_(True)
            # 放在 webview 上方、顶栏下方
            try:
                self.root_view.addSubview_positioned_relativeTo_(self.skeleton_view, NSWindowAbove, self.webview)
                self.top_bar.removeFromSuperview()
                self.root_view.addSubview_positioned_relativeTo_(self.top_bar, NSWindowAbove, self.skeleton_view)
            except Exception:
                self.root_view.addSubview_(self.skeleton_view)
        except Exception:
            pass

    # ------- 错误覆盖层（导航失败） -------
    def _ensure_error_overlay(self):
        try:
            if self.error_overlay is not None:
                return
            if not self.root_view or not self.window:
                return
            bounds = self.window.contentView().bounds()
            overlay = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, bounds.size.width, bounds.size.height))
            overlay.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            overlay.setHidden_(True)
            overlay.setWantsLayer_(True)
            try:
                overlay.layer().setBackgroundColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.94).CGColor())
            except Exception:
                pass

            # 卡片
            card_w = 360
            card_h = 160
            cx = (bounds.size.width - card_w) / 2
            cy = (bounds.size.height - card_h) / 2
            card = NSView.alloc().initWithFrame_(NSMakeRect(cx, cy, card_w, card_h))
            card.setAutoresizingMask_(NSViewMinXMargin | NSViewMaxXMargin | NSViewMinYMargin | NSViewMaxYMargin)
            card.setWantsLayer_(True)
            try:
                card.layer().setCornerRadius_(12.0)
                card.layer().setBackgroundColor_(NSColor.whiteColor().CGColor())
                card.layer().setBorderColor_(NSColor.colorWithCalibratedWhite_alpha_(0.85, 1.0).CGColor())
                card.layer().setBorderWidth_(1.0)
                card.layer().setShadowOpacity_(0.08)
                card.layer().setShadowRadius_(12.0)
            except Exception:
                pass
            overlay.addSubview_(card)

            # 标题与说明
            title = NSTextField.alloc().initWithFrame_(NSMakeRect(16, card_h - 40, card_w - 32, 22))
            title.setBezeled_(False)
            title.setEditable_(False)
            title.setSelectable_(False)
            title.setDrawsBackground_(False)
            try:
                t = self._i18n_or_default('error.navigationTitle', '无法打开页面')
                cute = self._get_cute_bold_font(14) or NSFont.boldSystemFontOfSize_(14)
                from AppKit import NSAttributedString, NSFontAttributeName
                title.setAttributedStringValue_(NSAttributedString.alloc().initWithString_attributes_(t, {NSFontAttributeName: cute}))
            except Exception:
                title.setStringValue_("无法打开页面")
            card.addSubview_(title)

            label = NSTextField.alloc().initWithFrame_(NSMakeRect(16, 64, card_w - 32, 44))
            label.setBezeled_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            label.setDrawsBackground_(False)
            label.setLineBreakMode_(NSLineBreakByWordWrapping)
            label.setAllowsDefaultTighteningForTruncation_(True)
            card.addSubview_(label)
            self._error_label = label

            # 按钮
            def _mk_btn(title_str, x):
                btn = NSButton.alloc().initWithFrame_(NSMakeRect(x, 16, 140, 28))
                btn.setBezelStyle_(NSBezelStyleRounded)
                btn.setTitle_(title_str)
                return btn

            retry_title = self._i18n_or_default('button.retry', '重试')
            home_title = self._i18n_or_default('button.home', '返回主页')

            retry = _mk_btn(retry_title, 16)
            home = _mk_btn(home_title, card_w - 16 - 140)

            try:
                retry.setTarget_(self)
                retry.setAction_(objc.selector(self.errorRetry_, signature=b'v@:@'))
            except Exception:
                pass
            try:
                home.setTarget_(self)
                home.setAction_(objc.selector(self.errorGoHome_, signature=b'v@:@'))
            except Exception:
                pass

            card.addSubview_(retry)
            card.addSubview_(home)

            # 叠放在 WebView 之上、顶栏之下
            try:
                self.root_view.addSubview_positioned_relativeTo_(overlay, NSWindowAbove, self.webview)
                if self.top_bar:
                    self.top_bar.removeFromSuperview()
                    self.root_view.addSubview_positioned_relativeTo_(self.top_bar, NSWindowAbove, overlay)
            except Exception:
                self.root_view.addSubview_(overlay)

            self.error_overlay = overlay
        except Exception:
            pass

    def _show_error_overlay(self, message: str):
        try:
            self._ensure_error_overlay()
            if not self.error_overlay:
                return
            # 文案
            text = self._i18n_or_default('error.navigationFailed', '网络连接中断或页面无法加载')
            if message:
                text = f"{text}\n{message}"
            if self._error_label:
                self._error_label.setStringValue_(text)
            self.error_overlay.setHidden_(False)
        except Exception:
            pass

    def _hide_error_overlay(self):
        try:
            if self.error_overlay:
                self.error_overlay.setHidden_(True)
        except Exception:
            pass

    # ---- 平台图标预取与主页更新 ----
    def _prefetch_platform_icons(self):
        try:
            import threading
            def worker():
                try:
                    platforms = {}
                    if self.homepage_manager:
                        try:
                            platforms = self.homepage_manager.get_available_platforms()
                        except Exception:
                            platforms = {}
                    for pid, info in platforms.items():
                        url = info.get('url') if isinstance(info, dict) else None
                        ok = self._download_and_cache_icon(pid, url)
                        if ok:
                            # 如果此时仍在主页，回填该行的图标为本地缓存
                            self._update_homepage_icon(pid)
                except Exception:
                    pass
            threading.Thread(target=worker, daemon=True).start()
        except Exception:
            pass

    def _download_and_cache_icon(self, platform_id: str, url: str) -> bool:
        try:
            if not url:
                return False
            from urllib.parse import urlparse
            host = ''
            try:
                host = urlparse(url).netloc
            except Exception:
                pass
            s2 = f"https://www.google.com/s2/favicons?sz=64&domain={host}" if host else None
            from .components.config_manager import ConfigManager as _CM
            icon_dir = os.path.join(os.path.dirname(_CM.config_path()), 'icons')
            os.makedirs(icon_dir, exist_ok=True)
            # 若已存在缓存，跳过
            for ext in ('png', 'ico'):
                p = os.path.join(icon_dir, f"{platform_id}.{ext}")
                if os.path.exists(p):
                    return True
            # 优先下载 s2 PNG
            data = None
            if s2:
                try:
                    n = NSURL.URLWithString_(s2)
                    data = NSData.dataWithContentsOfURL_(n)
                    if data:
                        fp = os.path.join(icon_dir, f"{platform_id}.png")
                        data.writeToFile_atomically_(fp, True)
                        return True
                except Exception:
                    data = None
            # 退回网站 favicon
            try:
                fav = url.rstrip('/') + '/favicon.ico'
                n = NSURL.URLWithString_(fav)
                data = NSData.dataWithContentsOfURL_(n)
                if data:
                    fp = os.path.join(icon_dir, f"{platform_id}.ico")
                    data.writeToFile_atomically_(fp, True)
                    return True
            except Exception:
                pass
        except Exception:
            pass
        return False

    def _update_homepage_icon(self, platform_id: str):
        if not getattr(self, 'last_loaded_is_homepage', False):
            return
        try:
            from .components.config_manager import ConfigManager as _CM
            icon_dir = os.path.join(os.path.dirname(_CM.config_path()), 'icons')
            icon_path = None
            for ext in ('png', 'ico'):
                p = os.path.join(icon_dir, f"{platform_id}.{ext}")
                if os.path.exists(p):
                    icon_path = 'file://' + p
                    break
            if not icon_path:
                return
            js = f"""
                (function(){{
                    const row = document.querySelector('.hrow[data-pid="{platform_id}"]');
                    if (!row) return;
                    const img = row.querySelector('.title img.icon');
                    if (img) img.src = '{icon_path.replace("'", "\\'")}';
                }})();
            """
            self._js_eval(js)
        except Exception:
            pass

    # 错误覆盖层按钮事件
    def errorRetry_(self, sender):
        try:
            self._hide_error_overlay()
            # 优先使用 WKWebView.reload
            try:
                self.webview.reload()
            except Exception:
                try:
                    self.webview.reload_(None)
                except Exception:
                    self.webview.reload(None)
        except Exception:
            pass

    def errorGoHome_(self, sender):
        try:
            self._hide_error_overlay()
            if self.navigation_controller:
                self.navigation_controller.navigate_to_homepage()
            self._load_homepage()
        except Exception:
            pass

    def _show_skeleton_overlay(self):
        try:
            self._ensure_skeleton_view()
            if self.skeleton_view:
                self.skeleton_view.setHidden_(False)
        except Exception:
            pass

    def _hide_skeleton_overlay(self):
        try:
            if self.skeleton_view:
                self.skeleton_view.setHidden_(True)
        except Exception:
            pass

    def _should_show_skeleton_for_webview(self, webView) -> bool:
        """仅对当前前台可见内容显示骨架；主页与后台加载都不显示。"""
        try:
            # 主页永不显示骨架
            if getattr(self, 'last_loaded_is_homepage', False):
                return False
            # 抑制标记优先
            if getattr(self, '_skeleton_suppress_until_finish', False):
                return False
            if getattr(self, '_skeleton_suppress_next', False):
                return False
            # 多页面模式：仅当该 webView 是当前活动页面且可见
            if getattr(self, 'is_multiwindow_mode', False):
                apid = getattr(self, '_active_page_id', None)
                active = self._pages_map.get(apid) if apid else None
                if active is None:
                    return False
                # 避免隐藏中的页面触发骨架
                try:
                    if hasattr(active, 'isHidden') and active.isHidden():
                        return False
                except Exception:
                    pass
                # 仅当活动页仍在加载中
                try:
                    is_loading = bool(active.isLoading()) if hasattr(active, 'isLoading') else False
                except Exception:
                    is_loading = False
                return webView == active and is_loading
            # 单页面模式：仅当 webView 即主 webview 且当前不是主页
            if webView != getattr(self, 'webview', None):
                return False
            try:
                return bool(webView.isLoading()) if hasattr(webView, 'isLoading') else False
            except Exception:
                return False
        except Exception:
            return False

    # 处理导航变化
    def handle_navigation_change(self, page_type, platform_id=None, window_id=None):
        """处理导航状态变化"""
        print(f"导航变化: {page_type}, 平台: {platform_id}")

        if page_type == "homepage":
            # 单窗口多页面：回到主页时隐藏所有后台页面，显示主页 WebView
            try:
                for _wid, _wv in list(getattr(self, '_pages_map', {}).items()):
                    _wv.setHidden_(True)
                self._active_page_id = None
                if getattr(self, 'webview', None):
                    self.webview.setHidden_(False)
            except Exception:
                pass
            self._load_homepage()
        elif page_type == "chat" and platform_id:
            # 进入平台页
            if self.is_multiwindow_mode:
                # 多页面模式：不显示骨架，直接切换到已有页或创建前台页
                try:
                    # 隐藏主页 WebView
                    if getattr(self, 'webview', None):
                        self.webview.setHidden_(True)
                except Exception:
                    pass
                # 优先指定的 window_id；否则选取已有；否则创建
                target = None
                if window_id and window_id in getattr(self, '_pages_map', {}):
                    target = window_id
                else:
                    try:
                        ordered = sorted(
                            [(wid, meta) for wid, meta in self._page_meta.items() if meta.get('platform_id') == platform_id],
                            key=lambda kv: kv[1].get('created_at') or 0
                        )
                        target = ordered[0][0] if ordered else None
                    except Exception:
                        target = None
                if target:
                    self._pages_switch(target)
                else:
                    wid = self._pages_create(platform_id, background=False)
                    if wid:
                        self._pages_switch(wid)
                # 进入页面后，下拉不包含“主页”
                try:
                    self._populate_ai_selector(include_home_first=False)
                except Exception:
                    pass
                return
            # 单页面模式：展示骨架并加载
            try:
                self._show_skeleton_overlay()
            except Exception:
                pass
            try:
                self._populate_ai_selector(include_home_first=False)
            except Exception:
                pass
            self._load_ai_service(platform_id)
            try:
                self._select_ai_item(platform_id, window_id)
            except Exception:
                pass

    # 更新返回按钮显示状态
    def update_back_button_visibility(self, should_show):
        """更新返回按钮显示状态（左上角图标）"""
        try:
            if hasattr(self, 'back_button') and self.back_button:
                self.back_button.setHidden_(not bool(should_show))
            if hasattr(self, 'back_button_bg') and self.back_button_bg:
                self.back_button_bg.setHidden_(not bool(should_show))
        except Exception as e:
            print(f"DEBUG: update_back_button_visibility 异常: {e}")

    # 更新AI选择器显示状态
    def update_ai_selector_visibility(self, should_show):
        """更新AI选择器显示状态（供外部调用）"""
        return self._update_ai_selector_ui(should_show)

    # 更新窗口标题
    def update_window_title(self, title):
        """更新窗口标题"""
        if hasattr(self, 'window'):
            self.window.setTitle_(title)
