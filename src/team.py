from .team_data import TeamDataManager

class TeamManager:
    """队伍管理器"""
    
    def __init__(self, plugin_name):
        """初始化队伍管理器
        
        Args:
            plugin_name: 插件名称
        """
        self.team_data_manager = TeamDataManager(plugin_name)
        # 模拟卡牌综合力数据，实际应用中应该从卡牌数据中获取
        self.card_power_data = {
            101: 1000, 102: 1200, 103: 1500,
            201: 1800, 202: 2000, 203: 2200,
            301: 2500, 302: 2800, 303: 3000,
            401: 3200, 402: 3500, 403: 3800,
            501: 4000, 502: 4200, 503: 4500,
        }
    
    def create_team(self, user_id, team_name):
        """创建队伍
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            
        Returns:
            操作结果消息
        """
        success = self.team_data_manager.create_team(user_id, team_name)
        if success:
            return f"队伍 {team_name} 创建成功！"
        else:
            return f"队伍 {team_name} 已存在，创建失败。"
    
    def add_card(self, user_id, team_name, card_id):
        """向队伍添加卡牌
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            card_id: 卡牌ID
            
        Returns:
            操作结果消息
        """
        # 检查卡牌ID是否有效（这里简单检查是否为数字）
        if not isinstance(card_id, int):
            try:
                card_id = int(card_id)
            except ValueError:
                return "卡牌ID必须是数字。"
        
        success = self.team_data_manager.add_card_to_team(user_id, team_name, card_id)
        if success:
            return f"卡牌 {card_id} 已成功添加到队伍 {team_name}。"
        else:
            # 检查队伍是否存在
            teams = self.team_data_manager.load_user_teams(user_id)
            if team_name not in teams:
                return f"队伍 {team_name} 不存在。"
            # 检查队伍是否已满
            if len(teams[team_name]) >= 5:
                return f"队伍 {team_name} 已满（最多5张卡）。"
            # 检查卡牌是否已在队伍中
            if card_id in teams[team_name]:
                return f"卡牌 {card_id} 已在队伍 {team_name} 中。"
            return "添加卡牌失败，请稍后重试。"
    
    def remove_card(self, user_id, team_name, position):
        """从队伍移除卡牌
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            position: 卡牌位置（从1开始）
            
        Returns:
            操作结果消息
        """
        # 检查位置是否有效
        if not isinstance(position, int):
            try:
                position = int(position)
            except ValueError:
                return "位置必须是数字。"
        
        success = self.team_data_manager.remove_card_from_team(user_id, team_name, position)
        if success:
            return f"已从队伍 {team_name} 中移除位置 {position} 的卡牌。"
        else:
            # 检查队伍是否存在
            teams = self.team_data_manager.load_user_teams(user_id)
            if team_name not in teams:
                return f"队伍 {team_name} 不存在。"
            # 检查位置是否有效
            if position < 1 or position > len(teams[team_name]):
                return f"无效的位置，队伍 {team_name} 只有 {len(teams[team_name])} 张卡。"
            return "移除卡牌失败，请稍后重试。"
    
    def list_teams(self, user_id):
        """查看用户所有队伍
        
        Args:
            user_id: 用户ID
            
        Returns:
            队伍列表消息
        """
        teams = self.team_data_manager.load_user_teams(user_id)
        if not teams:
            return "你还没有创建任何队伍。"
        
        message = "你的队伍列表：\n\n"
        for i, (team_name, cards) in enumerate(teams.items(), 1):
            message += f"{i}. {team_name}（{len(cards)}/5）\n"
        
        return message
    
    def show_team(self, user_id, team_name):
        """显示队伍详情
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            
        Returns:
            队伍详情消息
        """
        teams = self.team_data_manager.load_user_teams(user_id)
        if team_name not in teams:
            return f"队伍 {team_name} 不存在。"
        
        cards = teams[team_name]
        message = f"队伍 {team_name} 详情：\n\n"
        
        if not cards:
            message += "队伍为空。"
        else:
            for i, card_id in enumerate(cards, 1):
                power = self.card_power_data.get(card_id, 0)
                message += f"{i}. 卡牌ID: {card_id}，综合力: {power}\n"
        
        return message
    
    def calculate_team_power(self, user_id, team_name):
        """计算队伍综合力
        
        Args:
            user_id: 用户ID
            team_name: 队伍名称
            
        Returns:
            队伍综合力消息
        """
        teams = self.team_data_manager.load_user_teams(user_id)
        if team_name not in teams:
            return f"队伍 {team_name} 不存在。"
        
        cards = teams[team_name]
        if not cards:
            return f"队伍 {team_name} 为空，无法计算综合力。"
        
        total_power = 0
        for card_id in cards:
            total_power += self.card_power_data.get(card_id, 0)
        
        message = f"队伍 {team_name} 的综合力：\n\n"
        message += f"总综合力: {total_power}\n"
        message += f"平均综合力: {total_power // len(cards)}\n\n"
        
        # 显示每张卡的综合力
        for i, card_id in enumerate(cards, 1):
            power = self.card_power_data.get(card_id, 0)
            message += f"{i}. 卡牌ID: {card_id}，综合力: {power}\n"
        
        return message
