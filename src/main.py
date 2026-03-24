from astrbot import Star
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
    def __init__(self):
        super().__init__()
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
    
    def start(self):
        """Start the plugin"""
        self.logger.info("Starting Sekai deck recommendation plugin")
        return True
    
    def stop(self):
        """Stop the plugin"""
        self.logger.info("Stopping Sekai deck recommendation plugin")
        return True
    
    async def handle_message(self, message):
        """Handle incoming messages"""
        if message.content.startswith("/deck"):
            await self.handle_deck_command(message)
        elif message.content.startswith("/eventdeck"):
            await self.handle_event_deck_command(message)
        elif message.content.startswith("/challengedeck"):
            await self.handle_challenge_deck_command(message)
        elif message.content.startswith("/bonusdeck"):
            await self.handle_bonus_deck_command(message)
        elif message.content.startswith("/noeventdeck"):
            await self.handle_no_event_deck_command(message)
        elif message.content.startswith("/system"):
            await self.handle_system_command(message)
        elif message.content.startswith("/help"):
            await self.handle_help_command(message)
    
    async def handle_deck_command(self, message):
        """Handle general deck recommendation command"""
        try:
            # Parse command arguments
            args = message.content.split(" ")
            if len(args) < 3:
                await message.reply("Usage: /deck <music_id> <difficulty> [target] [algorithm]")
                return
            
            music_id = int(args[1])
            difficulty = args[2]
            target = args[3] if len(args) > 3 else "score"
            algorithm = args[4] if len(args) > 4 else "ga"
            
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                await message.reply("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                await message.reply("Invalid algorithm. Must be one of: ga, dfs")
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
            await message.reply(response)
            
        except Exception as e:
            self.logger.error(f"Error handling deck command: {e}")
            await message.reply(f"Error: {str(e)}")
    
    async def handle_event_deck_command(self, message):
        """Handle event deck recommendation command"""
        try:
            # Parse command arguments
            args = message.content.split(" ")
            if len(args) < 3:
                await message.reply("Usage: /eventdeck <event_id> <music_id> <difficulty> [target] [algorithm]")
                return
            
            event_id = int(args[1])
            music_id = int(args[2])
            difficulty = args[3]
            target = args[4] if len(args) > 4 else "score"
            algorithm = args[5] if len(args) > 5 else "ga"
            
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                await message.reply("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                await message.reply("Invalid algorithm. Must be one of: ga, dfs")
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
            await message.reply(response)
            
        except Exception as e:
            self.logger.error(f"Error handling event deck command: {e}")
            await message.reply(f"Error: {str(e)}")
    
    async def handle_challenge_deck_command(self, message):
        """Handle challenge deck recommendation command"""
        try:
            # Parse command arguments
            args = message.content.split(" ")
            if len(args) < 3:
                await message.reply("Usage: /challengedeck <music_id> <difficulty> [character_id] [target] [algorithm]")
                return
            
            music_id = int(args[1])
            difficulty = args[2]
            character_id = int(args[3]) if len(args) > 3 else None
            target = args[4] if len(args) > 4 else "score"
            algorithm = args[5] if len(args) > 5 else "ga"
            
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                await message.reply("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                await message.reply("Invalid algorithm. Must be one of: ga, dfs")
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
            await message.reply(response)
            
        except Exception as e:
            self.logger.error(f"Error handling challenge deck command: {e}")
            await message.reply(f"Error: {str(e)}")
    
    async def handle_bonus_deck_command(self, message):
        """Handle bonus deck recommendation command"""
        try:
            # Parse command arguments
            args = message.content.split(" ")
            if len(args) < 3:
                await message.reply("Usage: /bonusdeck <event_id> <target_bonus> [algorithm]")
                return
            
            event_id = int(args[1])
            target_bonus = int(args[2])
            algorithm = args[3] if len(args) > 3 else "dfs"
            
            # Validate parameters
            if algorithm not in ["ga", "dfs"]:
                await message.reply("Invalid algorithm. Must be one of: ga, dfs")
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
            await message.reply(response)
            
        except Exception as e:
            self.logger.error(f"Error handling bonus deck command: {e}")
            await message.reply(f"Error: {str(e)}")
    
    async def handle_no_event_deck_command(self, message):
        """Handle no event deck recommendation command"""
        try:
            # Parse command arguments
            args = message.content.split(" ")
            if len(args) < 3:
                await message.reply("Usage: /noeventdeck <music_id> <difficulty> [target] [algorithm]")
                return
            
            music_id = int(args[1])
            difficulty = args[2]
            target = args[3] if len(args) > 3 else "score"
            algorithm = args[4] if len(args) > 4 else "ga"
            
            # Validate parameters
            if target not in ["score", "power", "skill", "bonus"]:
                await message.reply("Invalid target. Must be one of: score, power, skill, bonus")
                return
            
            if algorithm not in ["ga", "dfs"]:
                await message.reply("Invalid algorithm. Must be one of: ga, dfs")
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
            await message.reply(response)
            
        except Exception as e:
            self.logger.error(f"Error handling no event deck command: {e}")
            await message.reply(f"Error: {str(e)}")
    
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
    
    async def handle_system_command(self, message):
        """Handle system information command"""
        try:
            if not self.moe_sekai_token:
                await message.reply("Error: MOE_SEKAI_TOKEN is not configured")
                return
            
            system_info = self.get_system_info()
            if not system_info:
                await message.reply("Error: Failed to get system information")
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
            
            await message.reply(response)
            
        except Exception as e:
            self.logger.error(f"Error handling system command: {e}")
            await message.reply(f"Error: {str(e)}")
    
    async def handle_help_command(self, message):
        """Handle help command"""
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
            
            await message.reply(response)
            
        except Exception as e:
            self.logger.error(f"Error handling help command: {e}")
            await message.reply(f"Error: {str(e)}")

# Create plugin instance
plugin = SekaiDeckPlugin()
