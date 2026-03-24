from astrbot import Star
from sekai_deck_recommend_cpp import (
    SekaiDeckRecommend, 
    DeckRecommendOptions,
    DeckRecommendCardConfig
)
import json
import os

class SekaiDeckPlugin(Star):
    def __init__(self):
        super().__init__()
        self.name = "sekai_deck"
        self.description = "Sekai deck recommendation plugin"
        self.sekai_deck_recommend = SekaiDeckRecommend()
        self.masterdata_dir = os.environ.get("SEKAI_MASTERDATA_DIR", "./masterdata")
        self.musicmetas_path = os.environ.get("SEKAI_MUSICMETAS_PATH", "./musicmetas.json")
        self.user_data_path = os.environ.get("SEKAI_USER_DATA_PATH", "./user_data.json")
        self._initialize()
    
    def _initialize(self):
        """Initialize the deck recommendation service"""
        try:
            if os.path.exists(self.masterdata_dir):
                self.sekai_deck_recommend.update_masterdata(self.masterdata_dir, "jp")
            if os.path.exists(self.musicmetas_path):
                self.sekai_deck_recommend.update_musicmetas(self.musicmetas_path, "jp")
        except Exception as e:
            self.logger.error(f"Failed to initialize deck recommendation service: {e}")
    
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
    
    async def handle_deck_command(self, message):
        """Handle deck recommendation command"""
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
    
    def _format_deck_result(self, result):
        """Format the deck recommendation result"""
        if not result:
            return "No deck recommendation found"
        
        # Format the result into a readable message
        # This is a placeholder, actual formatting depends on the result structure
        return f"Deck recommendation result: {json.dumps(result, ensure_ascii=False, indent=2)}"

# Create plugin instance
plugin = SekaiDeckPlugin()
