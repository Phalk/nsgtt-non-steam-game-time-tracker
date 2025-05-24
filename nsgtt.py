import sys
import time
import os
import psutil
import json
import re
import sqlite3
from colorama import init, Fore, Style
import vdf

# Initialize colorama
init(autoreset=True)

# Determine base path for DB and config
def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# Load configuration from config.json
def load_config():
    config_path = os.path.join(get_base_path(), 'config.json')
    if not os.path.exists(config_path):
        print(f"{Fore.RED}Config file not found at {config_path}! Using default values.{Style.RESET_ALL}")
        return {
            "STEAM_PATH": r"C:\Program Files (x86)\Steam",
            "NOTES_APPID": "2371090",
            "CHECK_INTERVAL": 5,
            "USERDATA_ID": None,
            "DEBUG": False
        }

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Fore.RED}Error reading config.json: {str(e)}. Using default values.{Style.RESET_ALL}")
        return {
            "STEAM_PATH": r"C:\Program Files (x86)\Steam",
            "NOTES_APPID": "2371090",
            "CHECK_INTERVAL": 5,
            "USERDATA_ID": None,
            "DEBUG": False
        }

# Load the configuration
config = load_config()
STEAM_PATH = config.get("STEAM_PATH", r"C:\Program Files (x86)\Steam")
NOTES_APPID = config.get("NOTES_APPID", "2371090")
CHECK_INTERVAL = config.get("CHECK_INTERVAL", 5)
USERDATA_ID = config.get("USERDATA_ID", None)
DEBUG = config.get("DEBUG", False)
DB_PATH = os.path.join(get_base_path(), "nsgtt.db")

# Conditional debug print
def debug_print(message):
    if DEBUG:
        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

# Get userdata folder ID
def get_userdata_id():
    userdata_path = os.path.join(STEAM_PATH, "userdata")
    if not os.path.isdir(userdata_path):
        print(f"{Fore.RED}userdata directory not found at {userdata_path}{Style.RESET_ALL}")
        return None

    if USERDATA_ID and os.path.isdir(os.path.join(userdata_path, USERDATA_ID)):
        print(f"{Fore.GREEN}Using USERDATA_ID from config: {USERDATA_ID}{Style.RESET_ALL}")
        return USERDATA_ID

    user_dirs = [d for d in os.listdir(userdata_path) if os.path.isdir(os.path.join(userdata_path, d)) and d.isdigit()]
    if user_dirs:
        selected_id = user_dirs[0]
        print(f"{Fore.YELLOW}No USERDATA_ID specified in config. Using first userdata folder: {selected_id}{Style.RESET_ALL}")
        return selected_id

    print(f"{Fore.RED}No valid userdata folders found in {userdata_path}{Style.RESET_ALL}")
    return None

# Initialize SQLite database
def init_db():
    print(f"{Fore.CYAN}Initializing database at: {DB_PATH}{Style.RESET_ALL}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_time (
                    game_name TEXT PRIMARY KEY,
                    time_played REAL,
                    play_count INTEGER
                )
            """)
            conn.commit()
        print(f"{Fore.GREEN}Database initialized successfully.{Style.RESET_ALL}")
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error initializing database: {str(e)}{Style.RESET_ALL}")

# Format time in seconds to H:M:S
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Retrieve game data
def get_game_data(game_name):
    debug_print(f"Retrieving data for game: {game_name}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT time_played, play_count FROM game_time WHERE game_name = ?", (game_name,))
            result = cursor.fetchone()
            if result:
                debug_print(f"Found data: time_played={result[0]}, play_count={result[1]}")
                return result[0], result[1]
            debug_print(f"No data found for {game_name}. Returning defaults.")
            return 0.0, 0
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error retrieving data for '{game_name}': {str(e)}{Style.RESET_ALL}")
        return 0.0, 0

# Save game time and play count
def save_game_data(game_name, elapsed_time, count):
    debug_print(f"Saving data for game: {game_name}, time: {elapsed_time}, count: {count}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO game_time (game_name, time_played, play_count)
                VALUES (?, ?, ?)
            """, (game_name, elapsed_time, count))
            conn.commit()
        debug_print(f"Data saved successfully for {game_name}.")
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error saving data for '{game_name}': {str(e)}{Style.RESET_ALL}")

# Display game statistics
def display_stats():
    print(f"{Fore.CYAN}Displaying statistics from: {DB_PATH}{Style.RESET_ALL}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT game_name, time_played, play_count FROM game_time")
            rows = cursor.fetchall()

        if not rows:
            print(f"{Fore.YELLOW}No game statistics found in the database.{Style.RESET_ALL}")
            return

        max_name_len = max(len("Game Name"), max(len(row[0]) for row in rows))
        max_time_len = max(len("Time Played"), len("HH:MM:SS"))
        max_count_len = max(len("Play Count"), max(len(str(row[2])) for row in rows))

        print(f"+{'-' * (max_name_len + 2)}+{'-' * (max_time_len + 2)}+{'-' * (max_count_len + 2)}+")
        print(f"| {Fore.CYAN}{'Game Name':<{max_name_len}}{Style.RESET_ALL} | {Fore.CYAN}{'Time Played':<{max_time_len}}{Style.RESET_ALL} | {Fore.CYAN}{'Play Count':<{max_count_len}}{Style.RESET_ALL} |")
        print(f"+{'-' * (max_name_len + 2)}+{'-' * (max_time_len + 2)}+{'-' * (max_count_len + 2)}+")

        for row in rows:
            game_name, time_played, play_count = row
            formatted_time = format_time(time_played)
            print(f"| {game_name:<{max_name_len}} | {formatted_time:<{max_time_len}} | {play_count:<{max_count_len}} |")

        print(f"+{'-' * (max_name_len + 2)}+{'-' * (max_time_len + 2)}+{'-' * (max_count_len + 2)}+")
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error reading database: {str(e)}{Style.RESET_ALL}")

# Get game name from shortcuts.vdf
def get_game_name_from_shortcuts(executable_path, userdata_id):
    if not userdata_id:
        print(f"{Fore.RED}No userdata ID provided. Using executable name.{Style.RESET_ALL}")
        return os.path.splitext(os.path.basename(executable_path))[0]

    shortcuts_path = os.path.join(STEAM_PATH, "userdata", userdata_id, "config", "shortcuts.vdf")
    debug_print(f"Attempting to read shortcuts.vdf at: {shortcuts_path}")
    try:
        with open(shortcuts_path, 'rb') as f:
            data = vdf.binary_load(f)
        shortcuts = data.get('shortcuts', {})
        input_path = os.path.normpath(executable_path).lower()
        for idx, shortcut in shortcuts.items():
            shortcut_exe = shortcut.get('Exe', '').strip('"')
            appname = shortcut.get('AppName', os.path.splitext(os.path.basename(shortcut_exe))[0])
            shortcut_exe_normalized = os.path.normpath(shortcut_exe).lower()
            if shortcut_exe_normalized == input_path:
                debug_print(f"Found game in shortcuts.vdf: {appname}")
                return appname
        debug_print(f"Game not found in shortcuts.vdf. Using executable name.")
        return os.path.splitext(os.path.basename(executable_path))[0]
    except FileNotFoundError:
        print(f"{Fore.RED}shortcuts.vdf not found at {shortcuts_path}. Using executable name.{Style.RESET_ALL}")
        return os.path.splitext(os.path.basename(executable_path))[0]
    except Exception as e:
        print(f"{Fore.RED}Error reading shortcuts.vdf: {str(e)}. Using executable name.{Style.RESET_ALL}")
        return os.path.splitext(os.path.basename(executable_path))[0]

# Clean game name for note filename
def clean_game_name_for_note(game_name):
    cleaned = re.sub(r'[^a-zA-Z0-9]', '_', game_name.strip())
    return f"notes_shortcut_{cleaned}"

# Update or create Steam Note
def update_steam_note(steam_note_path, game_name, time_played, count):
    debug_print(f"Attempting to update Steam note at: {steam_note_path}")
    note_dir = os.path.dirname(steam_note_path)
    if not os.path.isdir(note_dir):
        debug_print(f"Steam Notes directory does not exist: {note_dir}. Creating it.")
        try:
            os.makedirs(note_dir, exist_ok=True)
        except Exception as e:
            print(f"{Fore.RED}Failed to create directory {note_dir}: {str(e)}{Style.RESET_ALL}")
            return

    steam_data = {"notes": []}
    if os.path.isfile(steam_note_path):
        debug_print(f"Reading existing Steam note file")
        try:
            with open(steam_note_path, 'r', encoding='utf-8') as f:
                steam_data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"{Fore.RED}Invalid JSON in Steam note file: {str(e)}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error reading Steam note file: {str(e)}{Style.RESET_ALL}")

    last_played = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    formatted_time_played = format_time(time_played)

    note = {
        "title": f"Last session: {last_played} || Time played: {formatted_time_played} (played {count} times)",
        "content": f"""
📅 Last played: {last_played}                 
⏱️ Recorded time: {formatted_time_played}       
🔢 Times played: {count}                       
""",
        "time_modified": int(time.time())
    }

    if not steam_data["notes"]:
        steam_data["notes"].append(note)
    else:
        steam_data["notes"][0] = note

    debug_print(f"Writing Steam note")
    try:
        with open(steam_note_path, 'w', encoding='utf-8') as f:
            json.dump(steam_data, f, indent=4)
        debug_print(f"Steam Note updated/created successfully at {steam_note_path}")
    except Exception as e:
        print(f"{Fore.RED}Error saving Steam Note: {str(e)}{Style.RESET_ALL}")

# Monitor processes
def monitor_processes(userdata_id):
    print(f"{Fore.GREEN}Starting process monitor...{Style.RESET_ALL}")
    shortcuts_path = os.path.join(STEAM_PATH, "userdata", userdata_id, "config", "shortcuts.vdf")
    tracked_processes = {}  # Dictionary to store {pid: {exe_path, game_name, start_time, steam_note_path}}
    last_shortcuts_mtime = 0
    shortcuts = {}

    loop_count = 0
    while True:
        loop_count += 1
        try:
            # Reload shortcuts.vdf only if modified
            if os.path.isfile(shortcuts_path):
                current_mtime = os.path.getmtime(shortcuts_path)
                if current_mtime > last_shortcuts_mtime:
                    print(f"{Fore.CYAN}Reloading shortcuts.vdf (modified at {time.ctime(current_mtime)}){Style.RESET_ALL}")
                    with open(shortcuts_path, 'rb') as f:
                        data = vdf.binary_load(f)
                    shortcuts = data.get('shortcuts', {})
                    last_shortcuts_mtime = current_mtime
                    debug_print(f"Loaded {len(shortcuts)} shortcuts from {shortcuts_path}")
            else:
                shortcuts = {}
                print(f"{Fore.YELLOW}shortcuts.vdf not found at {shortcuts_path}{Style.RESET_ALL}")

            # Get current processes
            current_pids = set()
            for proc in psutil.process_iter(['pid', 'exe']):
                try:
                    exe_path = proc.info['exe']
                    if not exe_path or not exe_path.lower().endswith('.exe'):
                        continue
                    current_pids.add(proc.info['pid'])

                    # Check if process matches a shortcut
                    for idx, shortcut in shortcuts.items():
                        shortcut_exe = shortcut.get('Exe', '').strip('"')
                        appname = shortcut.get('AppName', os.path.splitext(os.path.basename(shortcut_exe))[0])
                        shortcut_exe_normalized = os.path.normpath(shortcut_exe).lower()
                        if os.path.normpath(exe_path).lower() == shortcut_exe_normalized and proc.info['pid'] not in tracked_processes:
                            steam_note_path = os.path.join(STEAM_PATH, "userdata", userdata_id, NOTES_APPID, "remote", clean_game_name_for_note(appname))
                            tracked_processes[proc.info['pid']] = {
                                'exe_path': exe_path,
                                'game_name': appname,
                                'start_time': time.time(),
                                'steam_note_path': steam_note_path
                            }
                            elapsed_time, count = get_game_data(appname)
                            os.system('cls')
                            print(f"{Fore.GREEN}Started tracking {appname} (PID: {proc.info['pid']}, Time: {format_time(elapsed_time)}, Count: {count}){Style.RESET_ALL}")
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Check for terminated processes
            terminated_pids = set(tracked_processes.keys()) - current_pids
            for pid in terminated_pids:
                debug_print(f"Processing termination for PID {pid}")
                try:
                    proc_info = tracked_processes.get(pid)
                    if not proc_info:
                        print(f"{Fore.RED}No process info found for PID {pid}{Style.RESET_ALL}")
                        continue
                    debug_print(f"Removing PID {pid} from tracked processes")
                    tracked_processes.pop(pid, None)
                    elapsed_time, count = get_game_data(proc_info['game_name'])
                    session_time = time.time() - proc_info['start_time']
                    elapsed_time += session_time
                    count += 1
                    os.system('cls')
                    print(f"{Fore.YELLOW}Stopped tracking {proc_info['game_name']} (PID: {pid}, Session: {format_time(session_time)}, Total: {format_time(elapsed_time)}, Count: {count}){Style.RESET_ALL}")
                    try:
                        save_game_data(proc_info['game_name'], elapsed_time, count)
                    except Exception as e:
                        print(f"{Fore.RED}Failed to save game data for {proc_info['game_name']}: {str(e)}{Style.RESET_ALL}")
                    try:
                        update_steam_note(proc_info['steam_note_path'], proc_info['game_name'], elapsed_time, count)
                    except Exception as e:
                        print(f"{Fore.RED}Failed to update Steam note for {proc_info['game_name']}: {str(e)}{Style.RESET_ALL}")
                except Exception as e:
                    print(f"{Fore.RED}Error processing termination for PID {pid}: {str(e)}{Style.RESET_ALL}")
                    continue

            # Update status
            os.system('cls')
            print(f"{Fore.CYAN}Monitoring... ({len(tracked_processes)} processes tracked, iteration {loop_count}){Style.RESET_ALL}", end='\r')
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            os.system('cls')
            print(f"{Fore.YELLOW}Monitor stopped by user.{Style.RESET_ALL}")
            break
        except Exception as e:
            os.system('cls')
            print(f"{Fore.RED}Error in monitor loop: {str(e)}{Style.RESET_ALL}")
            time.sleep(CHECK_INTERVAL)

def main():
    print(f"{Fore.GREEN}===== [ NSGTT - Non Steam Game Time Tracker Daemon ] ====={Style.RESET_ALL}")
    init_db()

    if len(sys.argv) >= 2 and sys.argv[1] == "--show":
        display_stats()
        return

    userdata_id = get_userdata_id()
    if not userdata_id:
        print(f"{Fore.RED}Could not determine userdata ID. Cannot start monitoring.{Style.RESET_ALL}")
        return

    monitor_processes(userdata_id)

if __name__ == "__main__":
    main()