import sys
import time
import os
import subprocess
import psutil
import json
import re
import sqlite3
from colorama import init, Fore, Style
import vdf
import shutil

# Determine NSGTT executable path (absolute)
NSGTT_EXECUTABLE = os.path.abspath(os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "nsgtt.exe" if getattr(sys, 'frozen', False) else "nsgtt.py"))

# Initialize colorama
init(autoreset=True)

# Determine base path for DB and config (handle PyInstaller --onefile)
def get_base_path():
    if getattr(sys, 'frozen', False):  # Running as PyInstaller executable
        return os.path.dirname(sys.executable)
    else:  # Running as script
        return os.path.dirname(os.path.abspath(__file__))

# Load configuration from config.json
def load_config():
    config_path = os.path.join(get_base_path(), 'config.json')
    if not os.path.exists(config_path):
        print(f"{Fore.RED}Config file not found at {config_path}! Using default values.{Style.RESET_ALL}")
        return {
            "STEAM_PATH": r"C:\Program Files (x86)\Steam",
            "NOTES_APPID": "2371090"
        }  # Default values if config doesn't exist

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Fore.RED}Error reading config.json: {str(e)}. Using default values.{Style.RESET_ALL}")
        return {
            "STEAM_PATH": r"C:\Program Files (x86)\Steam",
            "NOTES_APPID": "2371090"
        }

# Load the configuration
config = load_config()
STEAM_PATH = config.get("STEAM_PATH", r"C:\Program Files (x86)\Steam")  # Fallback to default if not found
NOTES_APPID = config.get("NOTES_APPID", "2371090")  # Fallback to default if not found

# Database path (same directory as executable or script)
DB_PATH = os.path.join(get_base_path(), "nsgtt.db")

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

# Function to format time in seconds to H:i:s
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Function to retrieve game data (time played and count)
def get_game_data(game_name):
    print(f"{Fore.CYAN}Retrieving data for game: {game_name}{Style.RESET_ALL}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT time_played, play_count FROM game_time WHERE game_name = ?", (game_name,))
            result = cursor.fetchone()
            if result:
                print(f"{Fore.GREEN}Found data: time_played={result[0]}, play_count={result[1]}{Style.RESET_ALL}")
                return result[0], result[1]
            print(f"{Fore.YELLOW}No data found for {game_name}. Returning defaults.{Style.RESET_ALL}")
            return 0.0, 0
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error retrieving data for '{game_name}': {str(e)}{Style.RESET_ALL}")
        return 0.0, 0

# Function to save game time and play count
def save_game_data(game_name, elapsed_time, count):
    print(f"{Fore.CYAN}Saving data for game: {game_name}, time: {elapsed_time}, count: {count}{Style.RESET_ALL}")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO game_time (game_name, time_played, play_count)
                VALUES (?, ?, ?)
            """, (game_name, elapsed_time, count))
            conn.commit()
        print(f"{Fore.GREEN}Data saved successfully for {game_name}.{Style.RESET_ALL}")
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error saving data for '{game_name}': {str(e)}{Style.RESET_ALL}")

# Function to display game statistics
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

        # Calculate column widths
        max_name_len = max(len("Game Name"), max(len(row[0]) for row in rows))
        max_time_len = max(len("Time Played"), len("HH:MM:SS"))
        max_count_len = max(len("Play Count"), max(len(str(row[2])) for row in rows))

        # Print table header
        print(f"{Fore.CYAN}Game Statistics:{Style.RESET_ALL}")
        print(f"+{'-' * (max_name_len + 2)}+{'-' * (max_time_len + 2)}+{'-' * (max_count_len + 2)}+")
        print(f"| {Fore.CYAN}{'Game Name':<{max_name_len}}{Style.RESET_ALL} | {Fore.CYAN}{'Time Played':<{max_time_len}}{Style.RESET_ALL} | {Fore.CYAN}{'Play Count':<{max_count_len}}{Style.RESET_ALL} |")
        print(f"+{'-' * (max_name_len + 2)}+{'-' * (max_time_len + 2)}+{'-' * (max_count_len + 2)}+")

        # Print table rows
        for row in rows:
            game_name, time_played, play_count = row
            formatted_time = format_time(time_played)
            print(f"| {game_name:<{max_name_len}} | {formatted_time:<{max_time_len}} | {play_count:<{max_count_len}} |")

        # Print table footer
        print(f"+{'-' * (max_name_len + 2)}+{'-' * (max_time_len + 2)}+{'-' * (max_count_len + 2)}+")
    except sqlite3.Error as e:
        print(f"{Fore.RED}Error reading database: {str(e)}{Style.RESET_ALL}")

# Function to get SteamID (userdata folder ID)
def get_steam_id():
    loginusers_path = os.path.join(STEAM_PATH, "config", "loginusers.vdf")
    userdata_path = os.path.join(STEAM_PATH, "userdata")

    # Try reading loginusers.vdf
    steam_id64 = None
    try:
        with open(loginusers_path, 'r', encoding='utf-8') as f:
            data = vdf.load(f)
        users = data.get('users', {})
        if not users:
            print(f"{Fore.YELLOW}No users found in loginusers.vdf{Style.RESET_ALL}")
        else:
            # Prioritize user with mostrecent = 1
            for sid64, user_data in users.items():
                if user_data.get('mostrecent', 0) == 1:
                    steam_id64 = sid64
                    print(f"{Fore.CYAN}Found mostrecent user: SteamID64={sid64}{Style.RESET_ALL}")
                    break
            else:
                # Fallback: Use the user with the latest Timestamp
                latest_user = None
                latest_timestamp = 0
                for sid64, user_data in users.items():
                    timestamp = user_data.get('Timestamp', 0)
                    if isinstance(timestamp, str):
                        try:
                            timestamp = int(timestamp)
                        except ValueError:
                            continue
                    if timestamp > latest_timestamp:
                        latest_timestamp = timestamp
                        latest_user = sid64
                if latest_user:
                    steam_id64 = latest_user
                    print(f"{Fore.CYAN}Found latest user by timestamp: SteamID64={sid64}{Style.RESET_ALL}")

        # Map SteamID64 to userdata folder
        if steam_id64:
            user_folder = find_userdata_folder(steam_id64)
            if user_folder:
                print(f"{Fore.GREEN}Mapped SteamID64={steam_id64} to userdata folder={user_folder}{Style.RESET_ALL}")
                return user_folder

    except FileNotFoundError:
        print(f"{Fore.YELLOW}loginusers.vdf not found at {loginusers_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}Error reading loginusers.vdf: {str(e)}{Style.RESET_ALL}")

    # Fallback: Check userdata directories
    if os.path.isdir(userdata_path):
        user_dirs = [d for d in os.listdir(userdata_path) if os.path.isdir(os.path.join(userdata_path, d)) and d.isdigit()]
        if user_dirs:
            # Sort by modification time of shortcuts.vdf (if exists)
            latest_mtime = 0
            latest_user = None
            for user_dir in user_dirs:
                shortcuts_path = os.path.join(userdata_path, user_dir, "config", "shortcuts.vdf")
                if os.path.isfile(shortcuts_path):
                    mtime = os.path.getmtime(shortcuts_path)
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                        latest_user = user_dir
            if latest_user:
                print(f"{Fore.GREEN}Selected userdata folder by shortcuts.vdf mtime: {latest_user}{Style.RESET_ALL}")
                return latest_user
            # If no shortcuts.vdf, return the first valid user directory
            print(f"{Fore.YELLOW}No shortcuts.vdf found, using first userdata folder: {user_dirs[0]}{Style.RESET_ALL}")
            return user_dirs[0]

    print(f"{Fore.RED}Could not determine SteamID from loginusers.vdf or userdata{Style.RESET_ALL}")
    return None

# Helper function to find userdata folder corresponding to SteamID64
def find_userdata_folder(steam_id64):
    userdata_path = os.path.join(STEAM_PATH, "userdata")
    if not os.path.isdir(userdata_path):
        print(f"{Fore.YELLOW}userdata directory not found at {userdata_path}{Style.RESET_ALL}")
        return None

    # Check each userdata folder for localconfig.vdf
    for user_dir in os.listdir(userdata_path):
        if not user_dir.isdigit():
            continue
        localconfig_path = os.path.join(userdata_path, user_dir, "config", "localconfig.vdf")
        if os.path.isfile(localconfig_path):
            try:
                with open(localconfig_path, 'r', encoding='utf-8') as f:
                    data = vdf.load(f)
                config_steam_id = data.get('UserLocalConfigStore', {}).get('SteamID', '')
                if config_steam_id == steam_id64:
                    # Verify if shortcuts.vdf exists to ensure valid folder
                    shortcuts_path = os.path.join(userdata_path, user_dir, "config", "shortcuts.vdf")
                    if os.path.isfile(shortcuts_path):
                        return user_dir
                    print(f"{Fore.YELLOW}Found matching SteamID64 in {user_dir}, but no shortcuts.vdf{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}Error reading localconfig.vdf in {user_dir}: {str(e)}{Style.RESET_ALL}")
                continue
    print(f"{Fore.YELLOW}No matching userdata folder found for SteamID64={steam_id64}{Style.RESET_ALL}")
    return None

# Function to extract game executable from NSGTT command
def extract_game_exe(shortcut_exe):
    # Match --run "game_path" or --run game_path
    match = re.search(r'--run\s+("([^"]+)"|(\S+))', shortcut_exe)
    if match:
        # Return the game path (group 2 if quoted, group 3 if unquoted)
        game_path = match.group(2) or match.group(3)
        return os.path.normpath(game_path).lower()
    return None




def get_game_name_from_shortcuts(executable_path, steam_id):
    if not steam_id:
        print(f"{Fore.RED}No SteamID provided. Using executable name.{Style.RESET_ALL}")
        return os.path.splitext(os.path.basename(executable_path))[0]

    shortcuts_path = os.path.join(STEAM_PATH, "userdata", steam_id, "config", "shortcuts.vdf")
    print(f"{Fore.CYAN}Attempting to read shortcuts.vdf at: {shortcuts_path}{Style.RESET_ALL}")
    try:
        with open(shortcuts_path, 'rb') as f:  # Read as binary
            data = vdf.binary_load(f)
        shortcuts = data.get('shortcuts', {})
        print(f"{Fore.CYAN}Number of shortcuts found: {len(shortcuts)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Raw shortcuts data: {shortcuts}{Style.RESET_ALL}")  # Adicione esta linha para inspecionar

        input_path = os.path.normpath(executable_path).lower()  # Normalize input path
        print(f"{Fore.CYAN}Searching for game executable: {input_path}{Style.RESET_ALL}")
        for idx, shortcut in shortcuts.items():
            print(f"{Fore.CYAN}Shortcut {idx}: {shortcut}{Style.RESET_ALL}")  # Mostre a entrada completa
            shortcut_exe = shortcut.get('Exe', '').strip('"')
            appname = shortcut.get('AppName', 'N/A')
            print(f"{Fore.CYAN}Checking shortcut {idx}: exe={shortcut_exe}, appname={appname}{Style.RESET_ALL}")
            # Check if shortcut_exe is an NSGTT command
            game_exe = extract_game_exe(shortcut_exe)
            if game_exe:
                print(f"{Fore.CYAN}Extracted game exe: {game_exe}{Style.RESET_ALL}")
                if game_exe == input_path:
                    print(f"{Fore.GREEN}Found game in shortcuts.vdf (NSGTT command): {appname}{Style.RESET_ALL}")
                    return appname
            # Check if the input_path is part of the exe in the vdf
            shortcut_exe_normalized = os.path.normpath(shortcut_exe).lower()
            if input_path in shortcut_exe_normalized:
                print(f"{Fore.GREEN}Found game in shortcuts.vdf (partial match): {appname}{Style.RESET_ALL}")
                return appname
        # Fallback: Use executable name if not found in shortcuts
        print(f"{Fore.YELLOW}Game not found in shortcuts.vdf. Using executable name.{Style.RESET_ALL}")
        return os.path.splitext(os.path.basename(executable_path))[0]
    except FileNotFoundError:
        print(f"{Fore.RED}shortcuts.vdf not found at {shortcuts_path}. Using executable name.{Style.RESET_ALL}")
        return os.path.splitext(os.path.basename(executable_path))[0]
    except Exception as e:
        print(f"{Fore.RED}Error reading shortcuts.vdf: {str(e)}. Using executable name.{Style.RESET_ALL}")
        return os.path.splitext(os.path.basename(executable_path))[0]


# Function to clean game name for note filename
def clean_game_name_for_note(game_name):
    # Replace each non-alphanumeric character with a single underscore
    cleaned = re.sub(r'[^a-zA-Z0-9]', '_', game_name.strip())
    return f"notes_shortcut_{cleaned}"

# Install on shortcuts.vdf
def install_nsgtt_in_shortcuts(steam_id):
    shortcuts_path = os.path.join(STEAM_PATH, "userdata", steam_id, "config", "shortcuts.vdf")
    print(f"{Fore.CYAN}Attempting to modify shortcuts.vdf at: {shortcuts_path}{Style.RESET_ALL}")
    
    try:
        # Create backup
        import shutil
        backup_path = shortcuts_path + ".backup"
        if os.path.isfile(shortcuts_path):
            shutil.copy2(shortcuts_path, backup_path)
            print(f"{Fore.CYAN}Created backup at: {backup_path}{Style.RESET_ALL}")

        with open(shortcuts_path, 'rb') as f:
            data = vdf.binary_load(f)
        shortcuts = data.get('shortcuts', {})
        print(f"{Fore.CYAN}Found {len(shortcuts)} shortcuts in shortcuts.vdf{Style.RESET_ALL}")

        modified = False
        for idx, shortcut in shortcuts.items():
            exe = shortcut.get('Exe', '').strip('"')
            appname = shortcut.get('AppName', os.path.splitext(os.path.basename(exe))[0])
            print(f"{Fore.CYAN}Checking shortcut {idx}: {appname} (Exe: {exe}){Style.RESET_ALL}")

            if 'nsgtt.exe' in exe.lower() or 'nsgtt.py' in exe.lower():
                print(f"{Fore.YELLOW}Shortcut {idx} ({appname}) already uses NSGTT. Skipping.{Style.RESET_ALL}")
                continue

            if not exe or not os.path.isfile(exe.strip('"')):
                print(f"{Fore.YELLOW}Shortcut {idx} ({appname}) has invalid or missing Exe. Skipping.{Style.RESET_ALL}")
                continue

            new_exe = f'"{NSGTT_EXECUTABLE}" --run "{exe}"'
            new_start_dir = os.path.dirname(exe.strip('"')) or shortcut.get('StartDir', '').strip('"') or os.path.dirname(NSGTT_EXECUTABLE)

            print(f"{Fore.CYAN}Updating shortcut {idx} ({appname}):{Style.RESET_ALL}")
            print(f"  Old Exe: {exe}")
            print(f"  New Exe: {new_exe}")
            print(f"  New StartDir: {new_start_dir}")

            shortcut['Exe'] = new_exe
            shortcut['StartDir'] = f'"{new_start_dir}"'
            modified = True

        if modified:
            with open(shortcuts_path, 'wb') as f:
                vdf.binary_dump(data, f)
            print(f"{Fore.GREEN}Successfully updated shortcuts.vdf with NSGTT commands.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No shortcuts needed updating.{Style.RESET_ALL}")

    except FileNotFoundError:
        print(f"{Fore.RED}shortcuts.vdf not found at {shortcuts_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error modifying shortcuts.vdf: {str(e)}{Style.RESET_ALL}")

# Function to extract game executable from NSGTT command
def extract_game_exe(shortcut_exe):
    # Match --run "game_path" or --run game_path
    # This regex is made more robust to handle cases where the NSGTT executable itself might not be perfectly quoted
    # or where the game path might be unquoted.
    match = re.search(r'(?:nsgtt\.exe|nsgtt\.py)"?\s+--run\s+("([^"]+)"|(\S+))', shortcut_exe, re.IGNORECASE)
    if match:
        # Return the game path (group 2 if quoted, group 3 if unquoted)
        game_path = match.group(2) or match.group(3)
        return os.path.normpath(game_path).lower()
    return None

# Uninstall from shortcuts.vdf
def uninstall_nsgtt_from_shortcuts(steam_id):
    shortcuts_path = os.path.join(STEAM_PATH, "userdata", steam_id, "config", "shortcuts.vdf")
    print(f"{Fore.CYAN}Attempting to modify shortcuts.vdf at: {shortcuts_path}{Style.RESET_ALL}")

    try:
        # Create backup
        import shutil
        backup_path = shortcuts_path + ".backup"
        if os.path.isfile(shortcuts_path):
            shutil.copy2(shortcuts_path, backup_path)
            print(f"{Fore.CYAN}Created backup at: {backup_path}{Style.RESET_ALL}")

        with open(shortcuts_path, 'rb') as f:
            data = vdf.binary_load(f)
        shortcuts = data.get('shortcuts', {})
        print(f"{Fore.CYAN}Found {len(shortcuts)} shortcuts in shortcuts.vdf{Style.RESET_ALL}")

        modified = False
        for idx, shortcut in shortcuts.items():
            exe = shortcut.get('Exe', '').strip('"')
            appname = shortcut.get('AppName', os.path.splitext(os.path.basename(exe))[0])
            print(f"{Fore.CYAN}Checking shortcut {idx}: {appname} (Exe: {exe}){Style.RESET_ALL}")

            # Check if NSGTT is part of the command
            if 'nsgtt.exe' not in exe.lower() and 'nsgtt.py' not in exe.lower():
                print(f"{Fore.YELLOW}Shortcut {idx} ({appname}) does not use NSGTT. Skipping.{Style.RESET_ALL}")
                continue

            # Use the more robust extract_game_exe function
            original_exe = extract_game_exe(shortcut.get('Exe', '')) # Pass the raw 'Exe' value including quotes

            if not original_exe or not os.path.isfile(original_exe):
                print(f"{Fore.YELLOW}Original executable not found for {appname}: {original_exe}. Skipping.{Style.RESET_ALL}")
                continue

            # Ensure the original_exe is correctly quoted if it contains spaces
            quoted_original_exe = f'"{original_exe}"' if ' ' in original_exe and not (original_exe.startswith('"') and original_exe.endswith('"')) else original_exe

            new_start_dir = os.path.dirname(original_exe) or shortcut.get('StartDir', '').strip('"') or os.path.dirname(NSGTT_EXECUTABLE)
            # Ensure new_start_dir is correctly quoted
            quoted_new_start_dir = f'"{new_start_dir}"' if ' ' in new_start_dir and not (new_start_dir.startswith('"') and new_start_dir.endswith('"')) else new_start_dir


            print(f"{Fore.CYAN}Reverting shortcut {idx} ({appname}):{Style.RESET_ALL}")
            print(f"  Old Exe: {exe}")
            print(f"  New Exe: {quoted_original_exe}")
            print(f"  New StartDir: {quoted_new_start_dir}")

            shortcut['Exe'] = quoted_original_exe
            shortcut['StartDir'] = quoted_new_start_dir
            modified = True

        if modified:
            with open(shortcuts_path, 'wb') as f:
                vdf.binary_dump(data, f)
            print(f"{Fore.GREEN}Successfully reverted NSGTT from shortcuts.vdf.{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No shortcuts needed reverting.{Style.RESET_ALL}")

    except FileNotFoundError:
        print(f"{Fore.RED}shortcuts.vdf not found at {shortcuts_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error modifying shortcuts.vdf: {str(e)}{Style.RESET_ALL}")

# Function to update or create Steam Note
def update_steam_note(steam_note_path, game_name, time_played, count):
    if not os.path.isdir(os.path.dirname(steam_note_path)):
        print(f"{Fore.RED}Steam Notes directory does not exist: {os.path.dirname(steam_note_path)}{Style.RESET_ALL}")
        return

    steam_data = {"notes": []}
    if os.path.isfile(steam_note_path):
        try:
            with open(steam_note_path, 'r', encoding='utf-8') as f:
                steam_data = json.load(f)
        except json.JSONDecodeError:
            print(f"{Fore.RED}Invalid JSON in Steam Note file: {steam_note_path}{Style.RESET_ALL}")

    last_played = time.strftime("%Y-%m-%d %H:%M", time.localtime())
    formatted_time_played = format_time(time_played)

    # Create or update the note
    note = {
        "title": f"Last session: {last_played} || Time played: {formatted_time_played} (played {count} times)",
        "content": f"""
 📅 Last played: {last_played}                 
 ⏱️ Recorded time: {formatted_time_played}       
 🔁 Times played: {count}                       
 """,
        "time_modified": int(time.time())
    }

    if not steam_data["notes"]:
        steam_data["notes"].append(note)
    else:
        steam_data["notes"][0] = note

    try:
        with open(steam_note_path, 'w', encoding='utf-8') as f:
            json.dump(steam_data, f, indent=4)
        print(f"{Fore.GREEN}Steam Note updated/created successfully at {steam_note_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Error saving Steam Note: {str(e)}{Style.RESET_ALL}")

# Function to run the game and monitor the time
def run_and_monitor(executable_path, game_name, steam_note_path):
    elapsed_time, count = get_game_data(game_name)

    print(f"{Fore.CYAN}Selected game: {game_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Time played: {format_time(elapsed_time)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Times started: {count}{Style.RESET_ALL}")

    start_time = time.time()
    print(f"{Fore.GREEN}Timer started for '{game_name}'...{Style.RESET_ALL}")

    game_dir = os.path.dirname(executable_path)
    try:
        process = subprocess.Popen(executable_path, cwd=game_dir)
        ps_process = psutil.Process(process.pid)
    except Exception as e:
        print(f"{Fore.RED}Failed to start game: {str(e)}{Style.RESET_ALL}")
        return

    try:
        while ps_process.is_running() and ps_process.status() != psutil.STATUS_ZOMBIE:
            current_time = time.time() - start_time + elapsed_time
            print(f"\r{Fore.CYAN}Time played: {format_time(current_time)}", end="")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except psutil.NoSuchProcess:
        pass

    elapsed_time += time.time() - start_time
    count += 1

    print(f"\n{Fore.GREEN}Total time for '{game_name}': {format_time(elapsed_time)}{Style.RESET_ALL}")
    save_game_data(game_name, elapsed_time, count)
    print(f"{Fore.YELLOW}Time for '{game_name}' saved successfully.{Style.RESET_ALL}")
    update_steam_note(steam_note_path, game_name, elapsed_time, count)


def main():
    print(f"{Fore.GREEN}===== [ NSGTT - Non Steam Game Time Tracker ] ====={Style.RESET_ALL}")

    # Initialize database
    init_db()

    # Initialize steam_id
    steam_id = None

    # Check for --install parameter
    if len(sys.argv) >= 2 and sys.argv[1] == "--install":
        steam_id = get_steam_id()
        if steam_id:
            install_nsgtt_in_shortcuts(steam_id)
        else:
            print(f"{Fore.RED}Could not determine SteamID. Cannot proceed with installation.{Style.RESET_ALL}")
        return

    # Check for --uninstall parameter
    if len(sys.argv) >= 2 and sys.argv[1] == "--uninstall":
        steam_id = get_steam_id()
        if steam_id:
            uninstall_nsgtt_from_shortcuts(steam_id)
        else:
            print(f"{Fore.RED}Could not determine SteamID. Cannot proceed with uninstallation.{Style.RESET_ALL}")
        return

    # Check if no parameters or only script name
    if len(sys.argv) == 1:
        display_stats()
        return

    # Check for --run parameter
    if len(sys.argv) < 3 or sys.argv[1] != "--run":
        print(f"{Fore.RED}Please provide the executable path with the '--run' parameter.{Style.RESET_ALL}\n")
        return

    executable_path = sys.argv[2]
    if not os.path.isfile(executable_path) or not executable_path.lower().endswith('.exe'):
        print(f"{Fore.RED}Invalid executable path: {executable_path}{Style.RESET_ALL}")
        return

    # Get SteamID
    steam_id = get_steam_id()

    # Get game name from shortcuts.vdf
    game_name = get_game_name_from_shortcuts(executable_path, steam_id)

    # Construct notes path (without .json extension)
    if not steam_id:
        print(f"{Fore.RED}Could not determine SteamID. Notes will not be saved.{Style.RESET_ALL}")
        steam_note_path = None
    else:
        steam_note_path = os.path.join(STEAM_PATH, "userdata", steam_id, NOTES_APPID, "remote", clean_game_name_for_note(game_name))

    # Run the game and monitor
    run_and_monitor(executable_path, game_name, steam_note_path)

if __name__ == "__main__":
    main()