"""
AI窗口实例数据模型

定义AI窗口的状态管理和实例信息，支持多窗口同平台管理。
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple
from enum import Enum
from datetime import datetime
import uuid


class WindowState(Enum):
    """窗口状态枚举"""
    INACTIVE = "inactive"      # 未激活
    ACTIVE = "active"          # 激活中
    MINIMIZED = "minimized"    # 最小化
    HIDDEN = "hidden"          # 隐藏
    LOADING = "loading"        # 加载中
    ERROR = "error"            # 错误状态


class WindowType(Enum):
    """窗口类型枚举"""
    MAIN = "main"              # 主窗口
    SECONDARY = "secondary"    # 副窗口
    POPUP = "popup"           # 弹出窗口


@dataclass
class WindowGeometry:
    """窗口几何信息"""
    x: int = 100
    y: int = 100
    width: int = 800
    height: int = 600
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "x": self.x,
            "y": self.y, 
            "width": self.width,
            "height": self.height
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WindowGeometry':
        """从字典创建实例"""
        return cls(
            x=data.get("x", 100),
            y=data.get("y", 100),
            width=data.get("width", 800),
            height=data.get("height", 600)
        )


@dataclass
class AIWindow:
    """
    AI窗口实例类
    
    管理单个AI窗口的状态、配置和生命周期。
    支持多窗口同平台管理和窗口状态追踪。
    """
    window_id: str
    platform_id: str
    window_type: WindowType = WindowType.MAIN
    state: WindowState = WindowState.INACTIVE
    geometry: WindowGeometry = field(default_factory=WindowGeometry)
    created_at: datetime = field(default_factory=datetime.now)
    last_active_at: Optional[datetime] = None
    url: Optional[str] = None
    title: Optional[str] = None
    user_agent: Optional[str] = None
    session_data: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.window_id:
            self.window_id = str(uuid.uuid4())
    
    def activate(self):
        """激活窗口"""
        self.state = WindowState.ACTIVE
        self.last_active_at = datetime.now()
    
    def deactivate(self):
        """取消激活窗口"""
        self.state = WindowState.INACTIVE
    
    def minimize(self):
        """最小化窗口"""
        self.state = WindowState.MINIMIZED
    
    def hide(self):
        """隐藏窗口"""
        self.state = WindowState.HIDDEN
    
    def show_loading(self):
        """显示加载状态"""
        self.state = WindowState.LOADING
    
    def set_error(self):
        """设置错误状态"""
        self.state = WindowState.ERROR
    
    def update_geometry(self, x: int, y: int, width: int, height: int):
        """更新窗口几何信息"""
        self.geometry.x = x
        self.geometry.y = y
        self.geometry.width = width
        self.geometry.height = height
    
    def update_url(self, url: str):
        """更新窗口URL"""
        self.url = url
    
    def update_title(self, title: str):
        """更新窗口标题"""
        self.title = title
    
    def set_session_data(self, key: str, value: any):
        """设置会话数据"""
        self.session_data[key] = value
    
    def get_session_data(self, key: str, default=None):
        """获取会话数据"""
        return self.session_data.get(key, default)
    
    def is_active(self) -> bool:
        """检查窗口是否激活"""
        return self.state == WindowState.ACTIVE
    
    def is_visible(self) -> bool:
        """检查窗口是否可见"""
        return self.state in [WindowState.ACTIVE, WindowState.INACTIVE, WindowState.LOADING]
    
    def get_display_name(self) -> str:
        """获取窗口显示名称"""
        return self.title or f"{self.platform_id}-{self.window_id[:8]}"
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "window_id": self.window_id,
            "platform_id": self.platform_id,
            "window_type": self.window_type.value,
            "state": self.state.value,
            "geometry": self.geometry.to_dict(),
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat() if self.last_active_at else None,
            "url": self.url,
            "title": self.title,
            "user_agent": self.user_agent,
            "session_data": self.session_data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AIWindow':
        """从字典创建实例"""
        return cls(
            window_id=data["window_id"],
            platform_id=data["platform_id"],
            window_type=WindowType(data.get("window_type", "main")),
            state=WindowState(data.get("state", "inactive")),
            geometry=WindowGeometry.from_dict(data.get("geometry", {})),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            last_active_at=datetime.fromisoformat(data["last_active_at"]) if data.get("last_active_at") else None,
            url=data.get("url"),
            title=data.get("title"),
            user_agent=data.get("user_agent"),
            session_data=data.get("session_data", {})
        )


@dataclass
class WindowManager:
    """
    窗口管理器类
    
    管理所有AI窗口实例，提供窗口的创建、删除、查找和状态管理功能。
    支持多窗口同平台管理，确保不超过限制。
    """
    windows: Dict[str, AIWindow] = field(default_factory=dict)
    active_window_id: Optional[str] = None
    # None 表示不限制数量；保持向后兼容，默认不限制
    max_windows_per_platform: Optional[int] = None
    max_total_windows: Optional[int] = None
    
    def create_window(self, platform_id: str, window_type: WindowType = WindowType.MAIN, 
                     geometry: Optional[WindowGeometry] = None) -> Optional[AIWindow]:
        """
        创建新窗口
        
        Args:
            platform_id: 平台标识符
            window_type: 窗口类型
            geometry: 窗口几何信息
            
        Returns:
            Optional[AIWindow]: 创建的窗口实例，如果失败返回None
        """
        # 检查总窗口与平台窗口数量限制（None 表示不限制）
        if isinstance(self.max_total_windows, int) and len(self.windows) >= self.max_total_windows:
            return None
        platform_windows = self.get_platform_windows(platform_id)
        if isinstance(self.max_windows_per_platform, int) and len(platform_windows) >= self.max_windows_per_platform:
            return None
        
        # 创建新窗口
        window = AIWindow(
            window_id=str(uuid.uuid4()),
            platform_id=platform_id,
            window_type=window_type,
            geometry=geometry or WindowGeometry()
        )
        
        self.windows[window.window_id] = window
        return window
    
    def remove_window(self, window_id: str) -> bool:
        """
        移除窗口
        
        Args:
            window_id: 窗口标识符
            
        Returns:
            bool: 移除是否成功
        """
        if window_id in self.windows:
            del self.windows[window_id]
            
            # 如果移除的是活动窗口，清除活动窗口设置
            if self.active_window_id == window_id:
                self.active_window_id = None
            
            return True
        return False
    
    def get_window(self, window_id: str) -> Optional[AIWindow]:
        """获取指定窗口"""
        return self.windows.get(window_id)
    
    def get_platform_windows(self, platform_id: str) -> List[AIWindow]:
        """获取指定平台的所有窗口"""
        return [window for window in self.windows.values() if window.platform_id == platform_id]
    
    def get_active_window(self) -> Optional[AIWindow]:
        """获取当前活动窗口"""
        if self.active_window_id:
            return self.windows.get(self.active_window_id)
        return None
    
    def set_active_window(self, window_id: str) -> bool:
        """
        设置活动窗口
        
        Args:
            window_id: 窗口标识符
            
        Returns:
            bool: 设置是否成功
        """
        if window_id in self.windows:
            # 取消之前活动窗口的激活状态
            if self.active_window_id and self.active_window_id in self.windows:
                self.windows[self.active_window_id].deactivate()
            
            # 激活新窗口
            self.windows[window_id].activate()
            self.active_window_id = window_id
            return True
        return False
    
    def get_visible_windows(self) -> List[AIWindow]:
        """获取所有可见窗口"""
        return [window for window in self.windows.values() if window.is_visible()]
    
    def get_all_windows(self) -> List[AIWindow]:
        """获取所有窗口"""
        return list(self.windows.values())
    
    def close_platform_windows(self, platform_id: str) -> int:
        """
        关闭指定平台的所有窗口
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            int: 关闭的窗口数量
        """
        platform_windows = self.get_platform_windows(platform_id)
        count = 0
        
        for window in platform_windows:
            if self.remove_window(window.window_id):
                count += 1
        
        return count
    
    def get_platform_window_count(self, platform_id: str) -> int:
        """获取指定平台的窗口数量"""
        return len(self.get_platform_windows(platform_id))
    
    def can_create_window(self, platform_id: str) -> bool:
        """检查是否可以为指定平台创建新窗口（默认不限制）。"""
        if isinstance(self.max_total_windows, int) and len(self.windows) >= self.max_total_windows:
            return False
        if isinstance(self.max_windows_per_platform, int) and self.get_platform_window_count(platform_id) >= self.max_windows_per_platform:
            return False
        return True
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "windows": {wid: window.to_dict() for wid, window in self.windows.items()},
            "active_window_id": self.active_window_id,
            "max_windows_per_platform": self.max_windows_per_platform,
            "max_total_windows": self.max_total_windows
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WindowManager':
        """从字典创建实例"""
        # 默认不限制窗口数量：当配置缺失时，将上限设为 None
        instance = cls(
            windows={},
            active_window_id=data.get("active_window_id"),
            max_windows_per_platform=data.get("max_windows_per_platform", None),
            max_total_windows=data.get("max_total_windows", None)
        )
        
        # 加载窗口数据
        windows_data = data.get("windows", {})
        for wid, window_data in windows_data.items():
            instance.windows[wid] = AIWindow.from_dict(window_data)
        
        return instance
