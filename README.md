# PJSK Item Teat Plugin for AstrBot

This plugin integrates the Sekai deck recommendation functionality and other PJSK-related features from moe-sekai/lunabot into AstrBot, allowing users to get optimized deck recommendations for Project Sekai songs and access other PJSK-related information.

## Features

- **Deck Recommendation**: Get optimized deck recommendations for Project Sekai songs
- **System Information**: Query system information from moe-sekai API
- **Help Command**: Display available commands and usage instructions
- **Easy Configuration**: Configure through environment variables

## Installation

1. **Clone this repository** to your AstrBot plugins directory:

```bash
git clone https://github.com/Wakelight56/PJSKitemteat.git
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Install playwright browsers** (required by some dependencies):

```bash
playwright install
```

## Configuration

Configure the plugin using the following environment variables:

| Environment Variable | Description | Default Value |
|---------------------|-------------|---------------|
| `MOE_SEKAI_TOKEN` | Your moe-sekai API token | Empty string |
| `SEKAI_MASTERDATA_DIR` | Path to the Project Sekai masterdata directory | `./masterdata` |
| `SEKAI_MUSICMETAS_PATH` | Path to the musicmetas.json file | `./musicmetas.json` |
| `SEKAI_USER_DATA_PATH` | Path to the user data JSON file | `./user_data.json` |

## Usage

### Commands

1. **Deck Recommendation**
   ```
   /deck <music_id> <difficulty> [target] [algorithm]
   ```
   - **Parameters**:
     - `music_id`: The ID of the song
     - `difficulty`: The difficulty level (easy, normal, hard, expert, master)
     - `target` (optional): The optimization target (score, power, skill, bonus) - default: score
     - `algorithm` (optional): The algorithm to use (ga, dfs) - default: ga
   - **Example**:
     ```
     /deck 74 expert score ga
     ```

2. **System Information**
   ```
   /system
   ```
   - Displays system information from the moe-sekai API, including server time, timezone, maintenance status, and app versions

3. **Help**
   ```
   /help
   ```
   - Displays this help message

## Dependencies

- [astrbot](https://github.com/AstrBotDevs/AstrBot): The bot framework
- [sekai-deck-recommend-cpp](https://github.com/moe-sekai/sekai-deck-recommend-cpp): C++ optimized deck recommendation library
- [requests](https://pypi.org/project/requests/): HTTP library for API requests
- [transformers](https://pypi.org/project/transformers/): Required by AstrBot
- [numpy](https://pypi.org/project/numpy/): Required by sekai-deck-recommend-cpp

## Notes

- You need to provide the Project Sekai masterdata and musicmetas files for the deck recommendation feature to work correctly
- The first time you run the plugin, it may take some time to initialize as it loads the masterdata
- You need to set the `MOE_SEKAI_TOKEN` environment variable to use the system information feature

## Acknowledgments

- [moe-sekai/lunabot](https://github.com/moe-sekai/lunabot): The original multi-functional chatbot based on Nonebot2
- [moe-sekai/sekai-deck-recommend-cpp](https://github.com/moe-sekai/sekai-deck-recommend-cpp): C++ optimized deck recommendation library
- [AstrBotDevs/AstrBot](https://github.com/AstrBotDevs/AstrBot): The bot framework
