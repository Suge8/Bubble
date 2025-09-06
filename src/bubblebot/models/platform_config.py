"""
AI平台配置数据模型

定义AI平台的配置信息和服务配置，支持多窗口系统的基础数据结构。
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from enum import Enum


class PlatformType(Enum):
    """AI平台类型枚举"""
    OPENAI = "openai"
    GEMINI = "gemini"
    GROK = "grok"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    ZAI = "zai"
    QWEN = "qwen"


@dataclass
class AIServiceConfig:
    """
    AI服务配置类
    
    定义单个AI服务的基本配置信息，包括URL、显示名称、状态等。
    """
    platform_id: str
    name: str
    url: str
    display_name: str
    enabled: bool = True
    max_windows: int = 5
    description: Optional[str] = None
    icon_path: Optional[str] = None
    
    def __post_init__(self):
        """初始化后的验证"""
        if self.max_windows < 1:
            raise ValueError("max_windows必须大于0")
        if self.max_windows > 5:
            raise ValueError("max_windows不能超过5")
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "platform_id": self.platform_id,
            "name": self.name,
            "url": self.url,
            "display_name": self.display_name,
            "enabled": self.enabled,
            "max_windows": self.max_windows,
            "description": self.description,
            "icon_path": self.icon_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AIServiceConfig':
        """从字典创建实例"""
        return cls(
            platform_id=data["platform_id"],
            name=data["name"], 
            url=data["url"],
            display_name=data["display_name"],
            enabled=data.get("enabled", True),
            max_windows=data.get("max_windows", 5),
            description=data.get("description"),
            icon_path=data.get("icon_path")
        )


@dataclass 
class PlatformConfig:
    """
    AI平台配置管理器
    
    管理所有AI平台的配置信息，提供平台的增删改查操作。
    支持多窗口系统的平台配置管理。
    """
    platforms: Dict[str, AIServiceConfig] = field(default_factory=dict)
    default_platform: Optional[str] = None
    enabled_platforms: List[str] = field(default_factory=list)
    max_total_platforms: int = 7
    
    def __post_init__(self):
        """初始化默认平台配置"""
        if not self.platforms:
            self._load_default_platforms()
    
    def _load_default_platforms(self):
        """加载默认AI平台配置"""
        default_platforms = [
            AIServiceConfig(
                platform_id="openai",
                name="ChatGPT",
                url="https://chat.openai.com",
                display_name="OpenAI ChatGPT",
                description="OpenAI的先进对话AI模型"
            ),
            AIServiceConfig(
                platform_id="gemini", 
                name="Gemini",
                url="https://gemini.google.com",
                display_name="Google Gemini", 
                description="Google的多模态AI助手"
            ),
            AIServiceConfig(
                platform_id="grok",
                name="Grok",
                url="https://grok.com",
                display_name="xAI Grok",
                description="xAI的幽默风趣AI助手"
            ),
            AIServiceConfig(
                platform_id="claude",
                name="Claude", 
                url="https://claude.ai/chat",
                display_name="Anthropic Claude",
                description="Anthropic的安全可靠AI助手"
            ),
            AIServiceConfig(
                platform_id="deepseek",
                name="DeepSeek",
                url="https://chat.deepseek.com", 
                display_name="DeepSeek Chat",
                description="深度求索的中文AI对话模型"
            ),
            AIServiceConfig(
                platform_id="zai",
                name="Zai",
                url="https://zai.chat",
                display_name="Zai Chat", 
                description="智能对话AI平台"
            ),
            AIServiceConfig(
                platform_id="qwen",
                name="Qwen", 
                url="https://qwen.chat",
                display_name="通义千问",
                description="阿里云的大语言模型"
            )
        ]
        
        for platform in default_platforms:
            self.platforms[platform.platform_id] = platform
    
    def add_platform(self, platform_config: AIServiceConfig) -> bool:
        """
        添加AI平台配置
        
        Args:
            platform_config: 平台配置对象
            
        Returns:
            bool: 添加是否成功
        """
        if len(self.platforms) >= self.max_total_platforms:
            return False
            
        if platform_config.platform_id in self.platforms:
            return False
            
        self.platforms[platform_config.platform_id] = platform_config
        return True
    
    def remove_platform(self, platform_id: str) -> bool:
        """
        移除AI平台配置
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 移除是否成功
        """
        if platform_id in self.platforms:
            del self.platforms[platform_id]
            
            # 从启用列表中移除
            if platform_id in self.enabled_platforms:
                self.enabled_platforms.remove(platform_id)
            
            # 如果是默认平台，清除默认设置
            if self.default_platform == platform_id:
                self.default_platform = None
                # 如果还有启用的平台，设置第一个为默认
                if self.enabled_platforms:
                    self.default_platform = self.enabled_platforms[0]
            
            return True
        return False
    
    def enable_platform(self, platform_id: str) -> bool:
        """
        启用AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 启用是否成功
        """
        if platform_id not in self.platforms:
            return False
            
        if platform_id not in self.enabled_platforms:
            if len(self.enabled_platforms) >= 5:  # 最多5个启用平台
                return False
            self.enabled_platforms.append(platform_id)
            self.platforms[platform_id].enabled = True
            
            # 如果没有默认平台，设置为默认
            if not self.default_platform:
                self.default_platform = platform_id
        
        return True
    
    def disable_platform(self, platform_id: str) -> bool:
        """
        禁用AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 禁用是否成功
        """
        if platform_id in self.enabled_platforms:
            self.enabled_platforms.remove(platform_id)
            if platform_id in self.platforms:
                self.platforms[platform_id].enabled = False
            
            # 如果禁用的是默认平台，重新设置默认
            if self.default_platform == platform_id:
                self.default_platform = self.enabled_platforms[0] if self.enabled_platforms else None
            
            return True
        return False
    
    def set_default_platform(self, platform_id: str) -> bool:
        """
        设置默认AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 设置是否成功
        """
        if platform_id in self.platforms and platform_id in self.enabled_platforms:
            self.default_platform = platform_id
            return True
        return False
    
    def get_platform(self, platform_id: str) -> Optional[AIServiceConfig]:
        """获取指定平台配置"""
        return self.platforms.get(platform_id)
    
    def get_enabled_platforms(self) -> List[AIServiceConfig]:
        """获取已启用的平台列表"""
        return [self.platforms[pid] for pid in self.enabled_platforms if pid in self.platforms]
    
    def get_all_platforms(self) -> List[AIServiceConfig]:
        """获取所有平台列表"""
        return list(self.platforms.values())
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "platforms": {pid: platform.to_dict() for pid, platform in self.platforms.items()},
            "default_platform": self.default_platform,
            "enabled_platforms": self.enabled_platforms,
            "max_total_platforms": self.max_total_platforms
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PlatformConfig':
        """从字典创建实例"""
        instance = cls(
            platforms={},
            default_platform=data.get("default_platform"),
            enabled_platforms=data.get("enabled_platforms", []),
            max_total_platforms=data.get("max_total_platforms", 7)
        )
        
        # 加载平台配置
        platforms_data = data.get("platforms", {})
        for pid, platform_data in platforms_data.items():
            instance.platforms[pid] = AIServiceConfig.from_dict(platform_data)
            
        return instance