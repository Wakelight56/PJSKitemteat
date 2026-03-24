# AstrBot Sekai Deck Recommendation Plugin

This plugin integrates the Sekai deck recommendation functionality into AstrBot, allowing users to get optimized deck recommendations for Project Sekai songs.

## Features

- Recommend optimized decks for Project Sekai songs
- Support different optimization targets: score, power, skill, bonus
- Support different algorithms: genetic algorithm (ga) and brute-force search (dfs)
- Easy configuration through environment variables

## Installation

1. Clone this repository to your AstrBot plugins directory:

```bash
git clone https://github.com/Wakelight56/PJSKitemteat.git
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Install playwright browsers (required by some dependencies):

```bash
playwright install
```

## Configuration

Configure the plugin using the following environment variables:

- `SEKAI_MASTERDATA_DIR`: Path to the Project Sekai masterdata directory
- `SEKAI_MUSICMETAS_PATH`: Path to the musicmetas.json file
- `SEKAI_USER_DATA_PATH`: Path to the user data JSON file

## Usage

In your chat with AstrBot, use the `/deck` command to get deck recommendations:

```
/deck <music_id> <difficulty> [target] [algorithm]
```

### Parameters

- `music_id`: The ID of the song
- `difficulty`: The difficulty level (easy, normal, hard, expert, master)
- `target` (optional): The optimization target (score, power, skill, bonus) - default: score
- `algorithm` (optional): The algorithm to use (ga, dfs) - default: ga

### Example

```
/deck 74 expert score ga
```

This will recommend an optimized deck for song ID 74 on expert difficulty, optimizing for score using the genetic algorithm.

## Dependencies

- [sekai-deck-recommend-cpp](https://github.com/moe-sekai/sekai-deck-recommend-cpp): C++ optimized deck recommendation library
- [AstrBot](https://github.com/AstrBotDevs/AstrBot): The bot framework

## Notes

- You need to provide the Project Sekai masterdata and musicmetas files for the plugin to work correctly.
- The first time you run the plugin, it may take some time to initialize as it loads the masterdata.
