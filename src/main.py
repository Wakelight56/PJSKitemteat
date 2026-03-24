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
import requests
import re
from datetime import datetime

class SekaiDeckPlugin(Star):
    def __init__(self, context):
        super().__init__(context)
        self.name = "sekai_deck"
        self.description = "Sekai deck recommendation plugin"
        self.sekai_deck_recommend = SekaiDeckRecommend()
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
            
            # Get plugin data directory
            self.plugin_data_path = get_astrbot_data_path() / "plugin_data" / self.name
            self.plugin_data_path.mkdir(parents=True, exist_ok=True)
            
            # Create user data directory
            self.user_data_dir = self.plugin_data_path / "user_data"
            self.user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Test moe-sekai API connection
            if self.moe_sekai_token:
                system_info = self.get_system_info()
                if system_info:
                    self.logger.info("Successfully connected to moe-sekai API")
                else:
                    self.logger.warning("Failed to connect to moe-sekai API")
            
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
    
    def _api_request(self, endpoint):
        """Make a request to the moe-sekai API"""
        if not self.moe_sekai_token:
            return None
        
        url = f"https://seka-api.exmeaning.com/api/jp/{endpoint}"
        headers = {
            "x-moe-sekai-token": self.moe_sekai_token
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"API request failed: {e}")
            return None
    
    def get_system_info(self):
        """Get system information from moe-sekai API"""
        return self._api_request("system")
    
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
    
    @filter.command("system")
    async def handle_system_command(self, event: AstrMessageEvent):
        """Get system information from moe-sekai API
        Usage: /system
        """
        try:
            if not self.moe_sekai_token:
                yield event.plain_result("Error: MOE_SEKAI_TOKEN is not configured")
                return
            
            system_info = self.get_system_info()
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
            response += "6. **/system**\n"
            response += "   - Get system information from moe-sekai API\n\n"
            response += "7. **/help**\n"
            response += "   - Show this help message\n\n"
            response += "=== Configuration ===\n"
            response += "- moe_sekai_token: Your moe-sekai API token\n"
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
