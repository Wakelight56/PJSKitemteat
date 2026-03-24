from astrbot import Star
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.message_components import Plain, Image, At
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
        self.masterdata_dir = os.environ.get("SEKAI_MASTERDATA_DIR", "./masterdata")
        self.musicmetas_path = os.environ.get("SEKAI_MUSICMETAS_PATH", "./musicmetas.json")
        self.user_data_path = os.environ.get("SEKAI_USER_DATA_PATH", "./user_data.json")
        self.moe_sekai_token = os.environ.get("MOE_SEKAI_TOKEN", "")
        self.api_base_url = "https://seka-api.exmeaning.com/api/jp"
        self._initialize()
    
    def _initialize(self):
        """Initialize the deck recommendation service"""
        try:
            if os.path.exists(self.masterdata_dir):
                self.sekai_deck_recommend.update_masterdata(self.masterdata_dir, "jp")
            if os.path.exists(self.musicmetas_path):
                self.sekai_deck_recommend.update_musicmetas(self.musicmetas_path, "jp")
            
            # Test moe-sekai API connection
            if self.moe_sekai_token:
                system_info = self.get_system_info()
                if system_info:
                    self.logger.info("Successfully connected to moe-sekai API")
                else:
                    self.logger.warning("Failed to connect to moe-sekai API")
        except Exception as e:
            self.logger.error(f"Failed to initialize deck recommendation service: {e}")
    
    def _api_request(self, endpoint):
        """Make a request to the moe-sekai API"""
        if not self.moe_sekai_token:
            return None
        
        url = f"{self.api_base_url}/{endpoint}"
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
    async def handle_deck_command(self, event: AstrMessageEvent, music_id: int, difficulty: str, target: str = "score", algorithm: str = "ga"):
        """Get general deck recommendation
        Usage: /deck <music_id> <difficulty> [target] [algorithm]
        Example: /deck 74 expert score ga
        Target options: score, power, skill, bonus
        Algorithm options: ga, dfs
        """
        try:
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                yield event.plain_result("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = target
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = self.user_data_path
            options.live_type = "multi"
            options.music_id = music_id
            options.music_diff = difficulty
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("eventdeck")
    async def handle_event_deck_command(self, event: AstrMessageEvent, event_id: int, music_id: int, difficulty: str, target: str = "score", algorithm: str = "ga"):
        """Get event deck recommendation
        Usage: /eventdeck <event_id> <music_id> <difficulty> [target] [algorithm]
        Example: /eventdeck 160 74 expert score ga
        """
        try:
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                yield event.plain_result("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = target
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = self.user_data_path
            options.live_type = "multi"
            options.music_id = music_id
            options.music_diff = difficulty
            options.event_id = event_id
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling event deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("challengedeck")
    async def handle_challenge_deck_command(self, event: AstrMessageEvent, music_id: int, difficulty: str, character_id: int = None, target: str = "score", algorithm: str = "ga"):
        """Get challenge deck recommendation
        Usage: /challengedeck <music_id> <difficulty> [character_id] [target] [algorithm]
        Example: /challengedeck 74 expert 1 score ga
        """
        try:
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                yield event.plain_result("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = target
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = self.user_data_path
            options.live_type = "challenge"
            options.music_id = music_id
            options.music_diff = difficulty
            if character_id:
                options.challenge_live_character_id = character_id
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling challenge deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("bonusdeck")
    async def handle_bonus_deck_command(self, event: AstrMessageEvent, event_id: int, target_bonus: int, algorithm: str = "dfs"):
        """Get bonus deck recommendation
        Usage: /bonusdeck <event_id> <target_bonus> [algorithm]
        Example: /bonusdeck 160 120 dfs
        """
        try:
            # Validate parameters
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = "bonus"
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = self.user_data_path
            options.live_type = "solo"
            options.event_id = event_id
            options.target_bonus_list = [target_bonus]
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
            yield event.plain_result(response)
            
        except Exception as e:
            self.logger.error(f"Error handling bonus deck command: {e}")
            yield event.plain_result(f"Error: {str(e)}")
    
    @filter.command("noeventdeck")
    async def handle_no_event_deck_command(self, event: AstrMessageEvent, music_id: int, difficulty: str, target: str = "score", algorithm: str = "ga"):
        """Get deck recommendation without event bonus
        Usage: /noeventdeck <music_id> <difficulty> [target] [algorithm]
        Example: /noeventdeck 74 expert score ga
        """
        try:
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                yield event.plain_result("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                yield event.plain_result("Invalid algorithm. Must be one of: ga, dfs")
                return
            
            # Create recommendation options
            options = DeckRecommendOptions()
            options.target = target
            options.algorithm = algorithm
            options.region = "jp"
            options.user_data_file_path = self.user_data_path
            options.live_type = "multi"
            options.music_id = music_id
            options.music_diff = difficulty
            options.event_id = None
            
            # Get recommendation result
            result = self.sekai_deck_recommend.recommend(options)
            
            # Format and send response
            response = self._format_deck_result(result)
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
            response += "- MOE_SEKAI_TOKEN: Your moe-sekai API token\n"
            response += "- SEKAI_MASTERDATA_DIR: Path to masterdata directory\n"
            response += "- SEKAI_MUSICMETAS_PATH: Path to musicmetas.json\n"
            response += "- SEKAI_USER_DATA_PATH: Path to user data JSON\n"
            
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
            for i, deck in enumerate(result.decks[:3]):  # Show top 3 decks
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
