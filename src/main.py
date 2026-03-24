from astrbot import Star
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Plain, Image, At
from astrbot.core.utils.astrbot_path import get_astrbot_data_path
from sekai_deck_recommend_cpp import (
    SekaiDeckRecommend, 
    DeckRecommendOptions,
    DeckRecommendCardConfig
)
import json
import os
import aiohttp
import re
import asyncio
from datetime import datetime

class SekaiDeckPlugin(Star):
    def __init__(self, context):
        super().__init__(context)
        self.name = "sekai_deck"
        self.description = "Sekai deck recommendation plugin"
        self.sekai_deck_recommend = SekaiDeckRecommend()
        self.SERVERS = ["cn", "tw", "jp"]
        self.SERVER_NAME = {"cn": "国服", "tw": "台服", "jp": "日服"}
        self._initialize()
    
    def _initialize(self):
        """Initialize the deck recommendation service"""
        try:
            # Get configuration from AstrBot config system
            self.moe_sekai_token = self.get_config("moe_sekai_token", "")
            self.masterdata_dir = self.get_config("masterdata_dir", "./masterdata")
            self.musicmetas_path = self.get_config("musicmetas_path", "./musicmetas.json")
            self.default_algorithm = self.get_config("default_algorithm", "ga")
            self.default_target = self.get_config("default_target", "score")
            self.show_top_decks = self.get_config("show_top_decks", 3)
            self.api_base = self.get_config("api_base", "https://seka-api.exmeaning.com")
            
            # Get plugin data directory
            self.plugin_data_path = get_astrbot_data_path() / "plugin_data" / self.name
            self.plugin_data_path.mkdir(parents=True, exist_ok=True)
            
            # Create user data directory
            self.user_data_dir = self.plugin_data_path / "user_data"
            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create bind data file path
            self.bind_data_path = self.plugin_data_path / "bind_data.json"
            
            # Update masterdata and musicmetas if files exist
            if os.path.exists(self.masterdata_dir):
                self.sekai_deck_recommend.update_masterdata(self.masterdata_dir, "jp")
            if os.path.exists(self.musicmetas_path):
                self.sekai_deck_recommend.update_musicmetas(self.musicmetas_path, "jp")
        except Exception as e:
            self.logger.error(f"Failed to initialize deck recommendation service: {e}")
    
    def _get_user_data_path(self, user_id):
        """Get user data file path based on user ID"""
        return self.user_data_dir / f"user_{user_id}.json"
    
    def _get_user_suite_path(self, user_id):
        """Get user suite file path based on user ID"""
        return self.user_data_dir / f"suite_{user_id}.json"
    
    def _load_user_suite(self, user_id):
        """Load user suite data"""
        suite_path = self._get_user_suite_path(user_id)
        if suite_path.exists():
            try:
                with open(suite_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load user suite: {e}")
        return {}
    
    def _save_user_suite(self, user_id, suite_data):
        """Save user suite data"""
        suite_path = self._get_user_suite_path(user_id)
        try:
            with open(suite_path, 'w', encoding='utf-8') as f:
                json.dump(suite_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save user suite: {e}")
            return False
    
    # ───────────────────────── 绑定数据读写 ──────────────────────────
    
    def _load_binds(self):
        """{ "user_id": {"cn": "id或null", "tw": "id或null", "jp": "id或null", "default": "cn"} }"""
        if not self.bind_data_path.exists():
            return {}
        try:
            return json.loads(self.bind_data_path.read_text("utf-8"))
        except Exception as e:
            self.logger.error(f"Failed to load bind data: {e}")
            return {}
    
    def _save_binds(self, data):
        try:
            self.bind_data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
        except Exception as e:
            self.logger.error(f"Failed to save bind data: {e}")
    
    def _get_user_binds(self, user_id):
        binds = self._load_binds()
        user_id_str = str(user_id)
        if user_id_str not in binds or not isinstance(binds[user_id_str], dict):
            binds[user_id_str] = {"cn": None, "tw": None, "jp": None, "default": None}
            self._save_binds(binds)
        return binds[user_id_str]
    
    def _has_any_bind(self, user_binds):
        return any(user_binds.get(s) for s in ["cn", "tw", "jp"])
    
    def _mask_id(self, sekai_id):
        if not sekai_id or len(sekai_id) <= 6:
            return sekai_id
        return "*" * (len(sekai_id) - 6) + sekai_id[-6:]
    
    # ───────────────────────── API 请求 ──────────────────────────
    
    async def _api_request(self, endpoint):
        """Make an async request to the moe-sekai API"""
        if not self.moe_sekai_token:
            return None
        
        url = f"{self.api_base}/api/jp/{endpoint}"
        headers = {
            "x-moe-sekai-token": self.moe_sekai_token
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            self.logger.error(f"API request failed: {e}")
            return None
    
    async def get_system_info(self):
        """Get system information from moe-sekai API"""
        return await self._api_request("system")
    
    async def fetch_profile(self, sekai_id, server):
        """请求指定服务器个人页，返回 {"server": "cn", "name": "xxx"} 或 None"""
        url = f"{self.api_base}/profile/{server}/{sekai_id}?token={self.moe_sekai_token}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=15) as response:
                    response.raise_for_status()
                    content = await response.text()
                    if "加载失败" in content:
                        return None
                    name_match = re.search(r'<[^>]*class="[^\"]*name[^\"]*"[^>]*>([^<]+)<', content)
                    name = name_match.group(1).strip() if name_match else "未知"
                    return {"server": server, "name": name}
        except Exception as e:
            self.logger.warning(f"[bind] {server} 请求失败：{e}")
            return None
    
    # ───────────────────────── 绑定功能 ──────────────────────────
    
    def format_bind_status(self, user_binds):
        default = user_binds.get("default")
        lines = []
        for s in self.SERVERS:
            sid = user_binds.get(s)
            prefix = "@ " if s == default else "     "
            lines.append(f"{prefix}【{self.SERVER_NAME[s]}】")
            lines.append(self._mask_id(sid) if sid else "未绑定")
        default_name = self.SERVER_NAME.get(default, "未设置") if default else "未设置"
        lines.append(f"你的默认服务器为【{default_name}】")
        lines.append("通过' /pjsk服务器 cn|tw|jp '可切换你的默认服务器")
        return "\n".join(lines)
    
    def bind_success_msg(self, server, name):
        return (
            f"{self.SERVER_NAME[server]}绑定成功: {name}\n"
            f"你的默认服务器已修改为【{self.SERVER_NAME[server]}】\n"
            f"通过' /pjsk服务器 cn|tw|jp '可切换你的默认服务器"
        )
    
    @filter.command("绑定")
    async def handle_bind_command(self, event: AstrMessageEvent, sekai_id: str = None, server: str = None):
        """绑定 Project Sekai 账号
        Usage: /绑定 <sekai_id> [server]
        Example: /绑定 123456 jp
        Server options: cn, tw, jp
        """
        try:
            user_id = event.get_sender_id()
            binds = self._load_binds()
            user_binds = self._get_user_binds(user_id)
            
            # 无id
            if not sekai_id:
                if server:
                    # /绑定 无id
                    sid = user_binds.get(server)
                    if not sid:
                        return f"请输入要绑定的 id，例如：/绑定 114514 {server}"
                    return f"当前绑定的{self.SERVER_NAME[server]}为：\n{self._mask_id(sid)}"
                else:
                    # /绑定 无id
                    if not self._has_any_bind(user_binds):
                        return "请输入要绑定的 id，例如：/绑定 114514"
                    return self.format_bind_status(user_binds)
            
            # 有id，指定服务器
            if server:
                if server not in self.SERVERS:
                    return f"请输入有效的服务器：{', '.join(self.SERVERS)}"
                
                result = await self.fetch_profile(sekai_id, server)
                if not result:
                    return "绑定失败，请检查id是否正确"
                
                user_binds[server] = sekai_id
                user_binds["default"] = server
                binds[str(user_id)] = user_binds
                self._save_binds(binds)
                return self.bind_success_msg(server, result["name"])
            
            # 有id，自动检测三服
            results = await asyncio.gather(
                *[self.fetch_profile(sekai_id, s) for s in self.SERVERS],
                return_exceptions=True
            )
            
            success = [r for r in results if isinstance(r, dict)]
            if not success:
                return "所有可请求服务器绑定失败，请检查id是否正确！"
            
            msgs = []
            for r in success:
                s = r["server"]
                user_binds[s] = sekai_id
                user_binds["default"] = s
                msgs.append(f"{self.SERVER_NAME[s]}绑定成功: {r['name']}")
            
            msgs.append(f"你的默认服务器已修改为【{self.SERVER_NAME[user_binds['default']]}】")
            msgs.append("通过' /pjsk服务器 cn|tw|jp '可切换你的默认服务器")
            binds[str(user_id)] = user_binds
            self._save_binds(binds)
            return "\n".join(msgs)
            
        except Exception as e:
            self.logger.error(f"Error handling bind command: {e}")
            return f"Error: {str(e)}"
    
    @filter.command("pjsk服务器")
    async def handle_switch_server_command(self, event: AstrMessageEvent, server: str = None):
        """切换默认服务器
        Usage: /pjsk服务器 [server]
        Example: /pjsk服务器 jp
        Server options: cn, tw, jp
        """
        try:
            user_id = event.get_sender_id()
            binds = self._load_binds()
            user_binds = self._get_user_binds(user_id)
            
            if not server:
                if not self._has_any_bind(user_binds):
                    return "你还没绑定任何账号！"
                return self.format_bind_status(user_binds)
            
            if server not in self.SERVERS:
                return f"请输入有效的服务器：{', '.join(self.SERVERS)}"
            if not user_binds.get(server):
                return f"你还没有绑定{self.SERVER_NAME[server]}的账号"
            
            user_binds["default"] = server
            binds[str(user_id)] = user_binds
            self._save_binds(binds)
            return f"已将默认服务器切换为【{self.SERVER_NAME[server]}】"
            
        except Exception as e:
            self.logger.error(f"Error handling switch server command: {e}")
            return f"Error: {str(e)}"
    
    # ───────────────────────── 组卡功能 ──────────────────────────
    
    @filter.command("deck")
    async def handle_deck_command(self, event: AstrMessageEvent, music_id: int, difficulty: str, target: str = None, algorithm: str = None):
        """Get general deck recommendation
        Usage: /deck <music_id> <difficulty> [target] [algorithm]
        Example: /deck 74 expert score ga
        Target options: score, power, skill, bonus
        Algorithm options: ga, dfs
        """
        try:
            # Get user ID
            user_id = event.get_sender_id()
            
            # Use default values if not provided
            if target is None:
                target = self.default_target
            if algorithm is None:
                algorithm = self.default_algorithm
            
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                yield event.plain_result("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Get user data path
            user_data_path = self._get_user_data_path(user_id)
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = target
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = str(user_data_path)
            options.live_type = "multi"
            options.music_id = music_id
            options.music_diff = difficulty
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            
            # Try to render as image for better display
            try:
                image_url = await self.text_to_image(response)
                yield event.image_result(image_url)
            except Exception as e:
                self.logger.warning(f"Failed to render image: {e}")
                yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("eventdeck")
    async def handle_event_deck_command(self, event: AstrMessageEvent, event_id: int, music_id: int, difficulty: str, target: str = None, algorithm: str = None):
        """Get event deck recommendation
        Usage: /eventdeck <event_id> <music_id> <difficulty> [target] [algorithm]
        Example: /eventdeck 160 74 expert score ga
        """
        try:
            # Get user ID
            user_id = event.get_sender_id()
            
            # Use default values if not provided
            if target is None:
                target = self.default_target
            if algorithm is None:
                algorithm = self.default_algorithm
            
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                yield event.plain_result("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Get user data path
            user_data_path = self._get_user_data_path(user_id)
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = target
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = str(user_data_path)
            options.live_type = "multi"
            options.music_id = music_id
            options.music_diff = difficulty
            options.event_id = event_id
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            
            # Try to render as image for better display
            try:
                image_url = await self.text_to_image(response)
                yield event.image_result(image_url)
            except Exception as e:
                self.logger.warning(f"Failed to render image: {e}")
                yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling event deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("challengedeck")
    async def handle_challenge_deck_command(self, event: AstrMessageEvent, music_id: int, difficulty: str, character_id: int = None, target: str = None, algorithm: str = None):
        """Get challenge deck recommendation
        Usage: /challengedeck <music_id> <difficulty> [character_id] [target] [algorithm]
        Example: /challengedeck 74 expert 1 score ga
        """
        try:
            # Get user ID
            user_id = event.get_sender_id()
            
            # Use default values if not provided
            if target is None:
                target = self.default_target
            if algorithm is None:
                algorithm = self.default_algorithm
            
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                yield event.plain_result("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Get user data path
            user_data_path = self._get_user_data_path(user_id)
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = target
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = str(user_data_path)
            options.live_type = "challenge"
            options.music_id = music_id
            options.music_diff = difficulty
            if character_id:
                options.challenge_live_character_id = character_id
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            
            # Try to render as image for better display
            try:
                image_url = await self.text_to_image(response)
                yield event.image_result(image_url)
            except Exception as e:
                self.logger.warning(f"Failed to render image: {e}")
                yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling challenge deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("bonusdeck")
    async def handle_bonus_deck_command(self, event: AstrMessageEvent, event_id: int, target_bonus: int, algorithm: str = None):
        """Get bonus deck recommendation
        Usage: /bonusdeck <event_id> <target_bonus> [algorithm]
        Example: /bonusdeck 160 120 dfs
        """
        try:
            # Get user ID
            user_id = event.get_sender_id()
            
            # Use default value if not provided
            if algorithm is None:
                algorithm = self.default_algorithm
            
            # Validate parameters
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Get user data path
            user_data_path = self._get_user_data_path(user_id)
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = "bonus"
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = str(user_data_path)
            options.live_type = "solo"
            options.event_id = event_id
            options.target_bonus_list = [target_bonus]
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            
            # Try to render as image for better display
            try:
                image_url = await self.text_to_image(response)
                yield event.image_result(image_url)
            except Exception as e:
                self.logger.warning(f"Failed to render image: {e}")
                yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling bonus deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("noeventdeck")
    async def handle_no_event_deck_command(self, event: AstrMessageEvent, music_id: int, difficulty: str, target: str = None, algorithm: str = None):
        """Get deck recommendation without event bonus
        Usage: /noeventdeck <music_id> <difficulty> [target] [algorithm]
        Example: /noeventdeck 74 expert score ga
        """
        try:
            # Get user ID
            user_id = event.get_sender_id()
            
            # Use default values if not provided
            if target is None:
                target = self.default_target
            if algorithm is None:
                algorithm = self.default_algorithm
            
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                yield event.plain_result("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Get user data path
            user_data_path = self._get_user_data_path(user_id)
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = target
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = str(user_data_path)
            options.live_type = "multi"
            options.music_id = music_id
            options.music_diff = difficulty
            options.event_id = None
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            
            # Try to render as image for better display
            try:
                image_url = await self.text_to_image(response)
                yield event.image_result(image_url)
            except Exception as e:
                self.logger.warning(f"Failed to render image: {e}")
                yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling no event deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("suite")
    async def handle_suite_command(self, event: AstrMessageEvent, action: str = None, *args):
        """Manage user suite data
        Usage:
        /suite list - List current suite
        /suite add <card_id> <level> <skill_level> - Add card to suite
        /suite remove <card_id> - Remove card from suite
        /suite clear - Clear all suite data
        /suite import <data> - Import suite data (JSON format)
        /suite export - Export current suite data
        """
        try:
            # Get user ID
            user_id = event.get_sender_id()
            
            # Load current suite data
            suite_data = self._load_user_suite(user_id)
            
            if action is None:
                yield event.plain_result("Usage: /suite <action> [args]\nActions: list, add, remove, clear, import, export")
                return
            
            if action == "list":
                if not suite_data:
                    yield event.plain_result("Your suite is empty.")
                    return
                
                response = "Your Suite:\n\n"
                for card_id, card_info in suite_data.items():
                    response += f"Card ID: {card_id}\n"
                    response += f"  Level: {card_info.get('level', 1)}\n"
                    response += f"  Skill Level: {card_info.get('skill_level', 1)}\n\n"
                
                # Try to render as image for better display
                try:
                    image_url = await self.text_to_image(response)
                    yield event.image_result(image_url)
                except Exception as e:
                    self.logger.warning(f"Failed to render image: {e}")
                    yield event.plain_result(response)
                
            elif action == "add":
                if len(args) < 3:
                    yield event.plain_result("Usage: /suite add <card_id> <level> <skill_level>")
                    return
                
                card_id = args[0]
                level = int(args[1])
                skill_level = int(args[2])
                
                suite_data[card_id] = {
                    "level": level,
                    "skill_level": skill_level
                }
                
                if self._save_user_suite(user_id, suite_data):
                    yield event.plain_result(f"Added card {card_id} to suite.")
                else:
                    yield event.plain_result("Failed to save suite data.")
                
            elif action == "remove":
                if len(args) < 1:
                    yield event.plain_result("Usage: /suite remove <card_id>")
                    return
                
                card_id = args[0]
                if card_id in suite_data:
                    del suite_data[card_id]
                    if self._save_user_suite(user_id, suite_data):
                        yield event.plain_result(f"Removed card {card_id} from suite.")
                    else:
                        yield event.plain_result("Failed to save suite data.")
                else:
                    yield event.plain_result(f"Card {card_id} not found in suite.")
                
            elif action == "clear":
                if self._save_user_suite(user_id, {}):
                    yield event.plain_result("Suite cleared.")
                else:
                    yield event.plain_result("Failed to clear suite data.")
                
            elif action == "import":
                if len(args) < 1:
                    yield event.plain_result("Usage: /suite import <data> (JSON format)")
                    return
                
                try:
                    import_data = json.loads(' '.join(args))
                    if isinstance(import_data, dict):
                        if self._save_user_suite(user_id, import_data):
                            yield event.plain_result("Suite data imported successfully.")
                        else:
                            yield event.plain_result("Failed to save imported suite data.")
                    else:
                        yield event.plain_result("Invalid suite data format. Expected JSON object.")
                except json.JSONDecodeError:
                    yield event.plain_result("Invalid JSON format.")
                
            elif action == "export":
                if not suite_data:
                    yield event.plain_result("Your suite is empty.")
                    return
                
                export_data = json.dumps(suite_data, ensure_ascii=False, indent=2)
                response = f"Your Suite Data:\n\n{export_data}"
                
                # Try to render as image for better display
                try:
                    image_url = await self.text_to_image(response)
                    yield event.image_result(image_url)
                except Exception as e:
                    self.logger.warning(f"Failed to render image: {e}")
                    yield event.plain_result(response)
                
            else:
                yield event.plain_result("Invalid action. Available actions: list, add, remove, clear, import, export")
            
        except Exception as e:
            self.logger.error(f"Error handling suite command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("system")
    async def handle_system_command(self, event: AstrMessageEvent):
        """Get system information from moe-sekai API
        Usage: /system
        """
        try:
            if not self.moe_sekai_token:
                yield event.plain_result("Error: MOE_SEKAI_TOKEN is not configured")
                return
            
            system_info = await self.get_system_info()
            if not system_info:
                yield event.plain_result("Error: Failed to get system information")
                return
            
            # Format system information
            response = "System Information:\n"
            response += f"Server Time: {system_info.get('serverDate', 'N/A')}\n"
            response += f"Timezone: {system_info.get('timezone', 'N/A')}\n"
            response += f"Profile: {system_info.get('profile', 'N/A')}\n"
            response += f"Maintenance Status: {system_info.get('maintenanceStatus', 'N/A')}\n"
            
            # Add app versions
            app_versions = system_info.get('appVersions', [])
            if app_versions:
                response += "\nApp Versions:\n"
                for version in app_versions[:3]:  # Show first 3 versions
                    app_version = version.get('appVersion', 'N/A')
                    status = version.get('appVersionStatus', 'N/A')
                    response += f"- Version {app_version}: {status}\n"
                if len(app_versions) > 3:
                    response += f"... and {len(app_versions) - 3} more versions\n"
            
            # Try to render as image for better display
            try:
                image_url = await self.text_to_image(response)
                yield event.image_result(image_url)
            except Exception as e:
                self.logger.warning(f"Failed to render image: {e}")
                yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling system command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("help", alias={"帮助"})
    async def handle_help_command(self, event: AstrMessageEvent):
        """Show help message
        Usage: /help
        """
        try:
            response = "=== PJSK Item Teat Plugin Help ===\n\n"
            response += "**Available Commands:**\n\n"
            response += "1. **/deck <music_id> <difficulty> [target] [algorithm]**\n"
            response += "   - Get general deck recommendation\n"
            response += "   - Example: /deck 74 expert score ga\n"
            response += "   - Target options: score, power, skill, bonus\n"
            response += "   - Algorithm options: ga, dfs\n\n"
            response += "2. **/eventdeck <event_id> <music_id> <difficulty> [target] [algorithm]**\n"
            response += "   - Get event deck recommendation\n"
            response += "   - Example: /eventdeck 160 74 expert score ga\n\n"
            response += "3. **/challengedeck <music_id> <difficulty> [character_id] [target] [algorithm]**\n"
            response += "   - Get challenge deck recommendation\n"
            response += "   - Example: /challengedeck 74 expert 1 score ga\n\n"
            response += "4. **/bonusdeck <event_id> <target_bonus> [algorithm]**\n"
            response += "   - Get bonus deck recommendation\n"
            response += "   - Example: /bonusdeck 160 120 dfs\n\n"
            response += "5. **/noeventdeck <music_id> <difficulty> [target] [algorithm]**\n"
            response += "   - Get deck recommendation without event bonus\n"
            response += "   - Example: /noeventdeck 74 expert score ga\n\n"
            response += "6. **/suite <action> [args]**\n"
            response += "   - Manage user suite data\n"
            response += "   - Actions: list, add, remove, clear, import, export\n"
            response += "   - Example: /suite add 123 50 10\n\n"
            response += "7. **/绑定 <sekai_id> [server]**\n"
            response += "   - Bind Project Sekai account\n"
            response += "   - Example: /绑定 123456 jp\n"
            response += "   - Server options: cn, tw, jp\n\n"
            response += "8. **/pjsk服务器 [server]**\n"
            response += "   - Switch default server\n"
            response += "   - Example: /pjsk服务器 jp\n"
            response += "   - Server options: cn, tw, jp\n\n"
            response += "9. **/system**\n"
            response += "   - Get system information from moe-sekai API\n\n"
            response += "10. **/help**\n"
            response += "   - Show this help message\n\n"
            response += "=== Configuration ===\n"
            response += "- moe_sekai_token: Your moe-sekai API token\n"
            response += "- api_base: API base URL (default: https://seka-api.exmeaning.com)\n"
            response += "- masterdata_dir: Path to masterdata directory\n"
            response += "- musicmetas_path: Path to musicmetas.json\n"
            response += "- default_algorithm: Default algorithm (ga/dfs)\n"
            response += "- default_target: Default target (score/power/skill/bonus)\n"
            response += "- show_top_decks: Number of top decks to show\n"
            
            # Try to render as image for better display
            try:
                image_url = await self.text_to_image(response)
                yield event.image_result(image_url)
            except Exception as e:
                self.logger.warning(f"Failed to render image: {e}")
                yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling help command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    def _format_deck_result(self, result):
        """Format the deck recommendation result"""
        if not result:
            return "No deck recommendation found"
        
        # Format the result into a readable message
        response = "Deck Recommendation Result:\n\n"
        
        if hasattr(result, 'decks') and result.decks:
            for i, deck in enumerate(result.decks[:self.show_top_decks]):  # Show configured number of decks
                response += f"Deck {i+1}:\n"
                response += f"Score: {deck.score}\n"
                response += f"Total Power: {deck.total_power}\n"
                response += "Cards:\n"
                for card in deck.cards:
                    response += f"- Card ID: {card.card_id}, Level: {card.level}, Skill Level: {card.skill_level}\n"
                response += "\n"
        else:
            response += json.dumps(result, ensure_ascii=False, indent=2)
        
        return response
