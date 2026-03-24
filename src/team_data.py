import json
import os
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

class TeamDataManager:
    """队伍数据管理器"""
    
    def __init__(self, plugin_name):
        """初始化队伍数据管理器
        
        Args:
            plugin_name: 插件名称，用于确定数据存储路径
        """
        # 获取插件数据目录
        self.plugin_data_path = get_astrbot_data_path() / "plugin_data" / plugin_name
        self.plugin_data_path.mkdir(parents=True, exist_ok=True)
        
        # 创建队伍数据目录
        self.team_data_dir = self.plugin_data_path / "teams"
        self.team_data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_team_file_path(self, user_id):
        """获取用户队伍文件路径
        
        Args:
            user_id: 用户ID
            
        Returns:
            队伍文件路径
        """
        return self.team_data_dir / f"user_{user_id}.json"
    
    def load_user_teams(self, user_id):
        """加载用户队伍数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户队伍数据，格式为 {"队伍名": [卡牌ID1, 卡牌ID2, ...]}
        """
        team_file_path = self._get_user_team_file_path(user_id)
        if not team_file_path.exists():
            return {}
        
        try:
            with open(team_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载队伍数据失败: {e}")
            return {}
    
    def save_user_teams(self, user_id, teams):
        """保存用户队伍数据
        
        Args:
            user_id: 用户ID
            teams: 用户队伍数据
            
        Returns:
            是否保存成功
        """
        team_file_path = self._get_user_team_file_path(user_id)
        try:
            with open(team_file_path, 'w', encoding='utf-8') as f:
                json.dump(teams, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存队伍数据失败: {e}")
            return False
    
    def create_team(self, user_id, team_name):
        """创建新队伍
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            
        Returns:
            是否创建成功
        """
        teams = self.load_user_teams(user_id)
        if team_name in teams:
            return False  # 队伍已存在
        
        teams[team_name] = []  # 创建空队伍
        return self.save_user_teams(user_id, teams)
    
    def add_card_to_team(self, user_id, team_name, card_id):
        """向队伍添加卡牌
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            card_id: 卡牌ID
            
        Returns:
            是否添加成功
        """
        teams = self.load_user_teams(user_id)
        if team_name not in teams:
            return False  # 队伍不存在
        
        # 检查队伍是否已满（最多5张卡）
        if len(teams[team_name]) >= 5:
            return False
        
        # 检查卡牌是否已在队伍中
        if card_id in teams[team_name]:
            return False
        
        teams[team_name].append(card_id)
        return self.save_user_teams(user_id, teams)
    
    def remove_card_from_team(self, user_id, team_name, position):
        """从队伍移除卡牌
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            position: 卡牌位置（从1开始）
            
        Returns:
            是否移除成功
        """
        teams = self.load_user_teams(user_id)
        if team_name not in teams:
            return False  # 队伍不存在
        
        # 检查位置是否有效
        if position < 1 or position > len(teams[team_name]):
            return False
        
        # 移除指定位置的卡牌（位置从1开始，所以索引减1）
        teams[team_name].pop(position - 1)
        return self.save_user_teams(user_id, teams)
    
    def delete_team(self, user_id, team_name):
        """删除队伍
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            
        Returns:
            是否删除成功
        """
        teams = self.load_user_teams(user_id)
        if team_name not in teams:
            return False  # 队伍不存在
        
        del teams[team_name]
        return self.save_user_teams(user_id, teams)
