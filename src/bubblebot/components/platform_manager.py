"""
AI平台管理器

实现AI平台的增删管理，支持用户自定义平台选择和配置持久化。
负责管理用户的AI平台选择、配置存储以及平台状态的统一管理。
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from ..models.platform_config import PlatformConfig, AIServiceConfig, PlatformType


@dataclass
class PlatformManagerConfig:
    """平台管理器配置"""
    config_file_path: str = "~/.bubblebot/platforms.json"
    backup_config_path: str = "~/.bubblebot/platforms_backup.json"
    auto_save: bool = True
    auto_backup: bool = True
    max_backup_files: int = 5


class PlatformManager:
    """
    AI平台管理器
    
    负责管理AI平台的配置、用户选择和持久化存储。
    提供平台的增删改查、启用禁用、默认设置等功能。
    """
    
    def __init__(self, config: Optional[PlatformManagerConfig] = None):
        """
        初始化平台管理器
        
        Args:
            config: 管理器配置，如果为None使用默认配置
        """
        self.config = config or PlatformManagerConfig()
        self._platform_config = PlatformConfig()
        self._listeners: List[Callable[[str, Dict], None]] = []
        self._config_loaded = False
        
        # 确保配置目录存在
        self._ensure_config_directory()
        
        # 加载配置
        self.load_config()
    
    def _ensure_config_directory(self):
        """确保配置目录存在"""
        config_path = Path(self.config.config_file_path).expanduser()
        config_dir = config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
    
    def add_change_listener(self, listener: Callable[[str, Dict], None]):
        """
        添加变更监听器
        
        Args:
            listener: 监听器函数，接收事件类型和数据
        """
        self._listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[str, Dict], None]):
        """移除变更监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def _notify_listeners(self, event_type: str, data: Dict):
        """通知所有监听器"""
        for listener in self._listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                print(f"监听器通知失败: {e}")
    
    def load_config(self) -> bool:
        """
        从文件加载平台配置
        
        Returns:
            bool: 加载是否成功
        """
        try:
            config_path = Path(self.config.config_file_path).expanduser()
            
            if not config_path.exists():
                # 如果配置文件不存在，使用默认配置并保存
                self._platform_config = PlatformConfig()
                self.save_config()
                self._config_loaded = True
                return True
            
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._platform_config = PlatformConfig.from_dict(data)
            self._config_loaded = True
            
            self._notify_listeners("config_loaded", {"success": True})
            return True
            
        except Exception as e:
            print(f"加载平台配置失败: {e}")
            # 如果加载失败，尝试加载备份
            if self._load_backup_config():
                return True
            
            # 如果备份也失败，使用默认配置
            self._platform_config = PlatformConfig()
            self._config_loaded = True
            self._notify_listeners("config_loaded", {"success": False, "error": str(e)})
            return False
    
    def _load_backup_config(self) -> bool:
        """加载备份配置"""
        try:
            backup_path = Path(self.config.backup_config_path).expanduser()
            if backup_path.exists():
                with open(backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._platform_config = PlatformConfig.from_dict(data)
                print("从备份配置加载成功")
                return True
        except Exception as e:
            print(f"加载备份配置失败: {e}")
        
        return False
    
    def save_config(self) -> bool:
        """
        保存平台配置到文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            config_path = Path(self.config.config_file_path).expanduser()
            
            # 创建备份
            if self.config.auto_backup and config_path.exists():
                self._create_backup()
            
            # 保存配置
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._platform_config.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._notify_listeners("config_saved", {"success": True})
            return True
            
        except Exception as e:
            print(f"保存平台配置失败: {e}")
            self._notify_listeners("config_saved", {"success": False, "error": str(e)})
            return False
    
    def _create_backup(self):
        """创建配置备份"""
        try:
            config_path = Path(self.config.config_file_path).expanduser()
            backup_path = Path(self.config.backup_config_path).expanduser()
            
            # 创建时间戳备份
            import time
            timestamp = int(time.time())
            timestamped_backup = backup_path.parent / f"platforms_backup_{timestamp}.json"
            
            # 复制当前配置到备份
            if config_path.exists():
                import shutil
                shutil.copy2(config_path, timestamped_backup)
                shutil.copy2(config_path, backup_path)
            
            # 清理旧备份文件
            self._cleanup_old_backups()
            
        except Exception as e:
            print(f"创建备份失败: {e}")
    
    def _cleanup_old_backups(self):
        """清理旧的备份文件"""
        try:
            backup_dir = Path(self.config.backup_config_path).expanduser().parent
            backup_files = list(backup_dir.glob("platforms_backup_*.json"))
            
            # 按修改时间排序，保留最新的几个
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 删除超出数量限制的备份文件
            for backup_file in backup_files[self.config.max_backup_files:]:
                backup_file.unlink()
                
        except Exception as e:
            print(f"清理备份文件失败: {e}")
    
    def add_platform(self, platform_config: AIServiceConfig) -> bool:
        """
        添加新的AI平台
        
        Args:
            platform_config: 平台配置对象
            
        Returns:
            bool: 添加是否成功
        """
        success = self._platform_config.add_platform(platform_config)
        
        if success:
            if self.config.auto_save:
                self.save_config()
            
            self._notify_listeners("platform_added", {
                "platform_id": platform_config.platform_id,
                "platform": platform_config.to_dict()
            })
        
        return success
    
    def remove_platform(self, platform_id: str) -> bool:
        """
        移除AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 移除是否成功
        """
        platform_info = self._platform_config.get_platform(platform_id)
        success = self._platform_config.remove_platform(platform_id)
        
        if success:
            if self.config.auto_save:
                self.save_config()
            
            self._notify_listeners("platform_removed", {
                "platform_id": platform_id,
                "platform": platform_info.to_dict() if platform_info else None
            })
        
        return success
    
    def enable_platform(self, platform_id: str) -> bool:
        """
        启用AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 启用是否成功
        """
        success = self._platform_config.enable_platform(platform_id)
        
        if success:
            if self.config.auto_save:
                self.save_config()
            
            self._notify_listeners("platform_enabled", {"platform_id": platform_id})
        
        return success
    
    def disable_platform(self, platform_id: str) -> bool:
        """
        禁用AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 禁用是否成功
        """
        success = self._platform_config.disable_platform(platform_id)
        
        if success:
            if self.config.auto_save:
                self.save_config()
            
            self._notify_listeners("platform_disabled", {"platform_id": platform_id})
        
        return success
    
    def set_default_platform(self, platform_id: str) -> bool:
        """
        设置默认AI平台
        
        Args:
            platform_id: 平台标识符
            
        Returns:
            bool: 设置是否成功
        """
        success = self._platform_config.set_default_platform(platform_id)
        
        if success:
            if self.config.auto_save:
                self.save_config()
            
            self._notify_listeners("default_platform_changed", {"platform_id": platform_id})
        
        return success
    
    def get_platform(self, platform_id: str) -> Optional[AIServiceConfig]:
        """获取指定平台配置"""
        return self._platform_config.get_platform(platform_id)
    
    def get_enabled_platforms(self) -> List[AIServiceConfig]:
        """获取已启用的平台列表"""
        return self._platform_config.get_enabled_platforms()
    
    def get_all_platforms(self) -> List[AIServiceConfig]:
        """获取所有平台列表"""
        return self._platform_config.get_all_platforms()
    
    def get_default_platform(self) -> Optional[AIServiceConfig]:
        """获取默认平台配置"""
        if self._platform_config.default_platform:
            return self.get_platform(self._platform_config.default_platform)
        return None
    
    def update_platform(self, platform_id: str, updates: Dict) -> bool:
        """
        更新平台配置
        
        Args:
            platform_id: 平台标识符
            updates: 要更新的配置字典
            
        Returns:
            bool: 更新是否成功
        """
        platform = self.get_platform(platform_id)
        if not platform:
            return False
        
        try:
            # 更新配置
            for key, value in updates.items():
                if hasattr(platform, key):
                    setattr(platform, key, value)
            
            if self.config.auto_save:
                self.save_config()
            
            self._notify_listeners("platform_updated", {
                "platform_id": platform_id,
                "updates": updates,
                "platform": platform.to_dict()
            })
            
            return True
            
        except Exception as e:
            print(f"更新平台配置失败: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """
        重置为默认配置
        
        Returns:
            bool: 重置是否成功
        """
        try:
            # 创建备份
            if self.config.auto_backup:
                self._create_backup()
            
            # 重置为默认配置
            self._platform_config = PlatformConfig()
            
            if self.config.auto_save:
                self.save_config()
            
            self._notify_listeners("config_reset", {"success": True})
            return True
            
        except Exception as e:
            print(f"重置配置失败: {e}")
            self._notify_listeners("config_reset", {"success": False, "error": str(e)})
            return False
    
    def export_config(self, export_path: str) -> bool:
        """
        导出配置到指定路径
        
        Args:
            export_path: 导出文件路径
            
        Returns:
            bool: 导出是否成功
        """
        try:
            export_path = Path(export_path).expanduser()
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self._platform_config.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._notify_listeners("config_exported", {"path": str(export_path)})
            return True
            
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str, merge: bool = False) -> bool:
        """
        从指定路径导入配置
        
        Args:
            import_path: 导入文件路径
            merge: 是否与现有配置合并，False表示完全替换
            
        Returns:
            bool: 导入是否成功
        """
        try:
            import_path = Path(import_path).expanduser()
            
            if not import_path.exists():
                return False
            
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if merge:
                # 合并配置
                imported_config = PlatformConfig.from_dict(data)
                for platform_id, platform in imported_config.platforms.items():
                    self._platform_config.add_platform(platform)
            else:
                # 完全替换
                if self.config.auto_backup:
                    self._create_backup()
                
                self._platform_config = PlatformConfig.from_dict(data)
            
            if self.config.auto_save:
                self.save_config()
            
            self._notify_listeners("config_imported", {
                "path": str(import_path),
                "merge": merge
            })
            
            return True
            
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
    
    def get_platform_statistics(self) -> Dict:
        """获取平台统计信息"""
        all_platforms = self.get_all_platforms()
        enabled_platforms = self.get_enabled_platforms()
        
        # 计算可用槽位（若无上限则为None）
        max_enabled = getattr(self._platform_config, 'max_enabled_platforms', None)
        enabled_slots = (max_enabled - len(enabled_platforms)) if isinstance(max_enabled, int) else None
        return {
            "total_platforms": len(all_platforms),
            "enabled_platforms": len(enabled_platforms),
            "available_slots": 7 - len(all_platforms),
            "enabled_slots": enabled_slots,
            "default_platform": self._platform_config.default_platform,
            "platforms_by_type": self._get_platforms_by_type()
        }
    
    def _get_platforms_by_type(self) -> Dict[str, int]:
        """获取按类型分组的平台数量"""
        type_counts = {}
        for platform in self.get_all_platforms():
            platform_type = getattr(platform, 'platform_type', 'unknown')
            type_counts[platform_type] = type_counts.get(platform_type, 0) + 1
        
        return type_counts
    
    def validate_config(self) -> Dict[str, List[str]]:
        """
        验证配置的有效性
        
        Returns:
            Dict: 验证结果，包含错误和警告信息
        """
        errors = []
        warnings = []
        
        try:
            all_platforms = self.get_all_platforms()
            enabled_platforms = self.get_enabled_platforms()
            
            # 检查平台数量限制
            if len(all_platforms) > 7:
                errors.append("平台总数超过了最大限制(7个)")
            
            max_enabled = getattr(self._platform_config, 'max_enabled_platforms', None)
            if isinstance(max_enabled, int) and len(enabled_platforms) > max_enabled:
                errors.append(f"启用的平台数量超过了最大限制({max_enabled}个)")
            
            # 检查默认平台
            if self._platform_config.default_platform:
                if self._platform_config.default_platform not in [p.platform_id for p in enabled_platforms]:
                    errors.append("默认平台未启用或不存在")
            elif enabled_platforms:
                warnings.append("有启用的平台但未设置默认平台")
            
            # 检查平台配置
            for platform in all_platforms:
                if not platform.url:
                    errors.append(f"平台 {platform.platform_id} 缺少URL配置")
                if not platform.name:
                    errors.append(f"平台 {platform.platform_id} 缺少名称配置")
            
            # 检查重复的平台ID
            platform_ids = [p.platform_id for p in all_platforms]
            if len(platform_ids) != len(set(platform_ids)):
                errors.append("存在重复的平台ID")
            
        except Exception as e:
            errors.append(f"配置验证过程中发生错误: {e}")
        
        return {
            "errors": errors,
            "warnings": warnings,
            "valid": len(errors) == 0
        }
    
    @property
    def is_config_loaded(self) -> bool:
        """配置是否已加载"""
        return self._config_loaded
    
    @property
    def platform_config(self) -> PlatformConfig:
        """获取平台配置对象（只读）"""
        return self._platform_config
