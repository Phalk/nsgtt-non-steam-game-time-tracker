# NSGTT - Non Steam Game Time Tracker

import sys
import time
import os
import subprocess
import psutil  # To check running processes
import json
from colorama import init, Fore, Style

# Initializes colorama
init(autoreset=True)

# Path to the time database
db_file = "time_played.txt"

# Function to format time in seconds to H:i:s format
def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Function to retrieve game data (time played and count)
def get_game_data(game_name):
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith(game_name):
                    try:
                        time_played, count = line.split('=')[1].split(',')
                        return float(time_played), int(count)
                    except ValueError:
                        print(f"{Fore.RED}Error processing data for the game '{game_name}'.")
                        return 0.0, 0
    return 0.0, 0

# Function to save game time and play count
def save_game_data(game_name, elapsed_time, count):
    lines = []
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            lines = f.readlines()

    # Update or add game time and count in the file
    found = False
    for i, line in enumerate(lines):
        if line.startswith(game_name):
            lines[i] = f"{game_name}={elapsed_time},{count}\n"
            found = True
            break
    if not found:
        lines.append(f"{game_name}={elapsed_time},{count}\n")

    with open(db_file, 'w') as f:
        f.writelines(lines)

# Function to update the Steam Note with enhanced styling
def update_steam_note(steam_note_path, game_name, time_played, count):
    if steam_note_path:
        try:
            print(f"{Fore.YELLOW}Updating Steam Note at: {steam_note_path}{Style.RESET_ALL}")
             
            with open(steam_note_path, 'r', encoding='utf-8') as f:
                steam_data = json.load(f)

            # Update only the first note
            if "notes" in steam_data and len(steam_data["notes"]) > 0:
                last_played = time.strftime("%Y-%m-%d %H:%M", time.localtime())
                formatted_time_played = format_time(time_played)

                # Styled formatting
                steam_data["notes"][0]["title"] = f"Last session: {last_played} || Time played: {formatted_time_played} (played {count} times)"
                steam_data["notes"][0]["content"] = f"""
 📅 Last played: {last_played}                 
 ⏱️ Recorded time: {formatted_time_played}       
 🔁 Times played: {count}                       
 """
                steam_data["notes"][0]["time_modified"] = int(time.time())

                with open(steam_note_path, 'w', encoding='utf-8') as f:
                    json.dump(steam_data, f, indent=4)

                print(f"{Fore.GREEN}Steam Note updated successfully!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}No notes found in the Steam Note file!{Style.RESET_ALL}")
        
        except Exception as e:
            print(f"{Fore.RED}Error updating the Steam Note: {str(e)}{Style.RESET_ALL}")

# Function to run the game and monitor the time
def run_and_monitor(executable_path, game_name, steam_note_path=None):
    # Retrieve the already played time and start count
    elapsed_time, count = get_game_data(game_name)

    print(f"{Fore.CYAN}Selected game: {game_name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Time played: {format_time(elapsed_time)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Times started: {count}{Style.RESET_ALL}")

    # Start the timer
    start_time = time.time()
    print(f"{Fore.GREEN}Timer started for '{game_name}'...{Style.RESET_ALL}")

    # Attempt to start the game from the executable's directory
    game_dir = os.path.dirname(executable_path)
    process = subprocess.Popen(executable_path, cwd=game_dir)

    try:
        # Monitor the process while the game is running
        while process.poll() is None:
            current_time = time.time() - start_time + elapsed_time
            print(f"\r{Fore.CYAN}Time played: {format_time(current_time)}", end="")
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # When the process ends
    elapsed_time += time.time() - start_time
    count += 1

    print(f"\n{Fore.GREEN}Total time for '{game_name}': {format_time(elapsed_time)}{Style.RESET_ALL}")

    # Save the time and count data
    save_game_data(game_name, elapsed_time, count)
    print(f"{Fore.YELLOW}Time for '{game_name}' saved successfully.{Style.RESET_ALL}")

    # Update the Steam Note, if provided
    update_steam_note(steam_note_path, game_name, elapsed_time, count)

# Main function
def main():
    print(f"{Fore.GREEN}===== [ NSGTT - Non Steam Game Time Tracker ] ====={Style.RESET_ALL}")

    if len(sys.argv) < 3 or sys.argv[1] != "--run":
        print(f"{Fore.RED}Please provide the executable path with the '--run' parameter.{Style.RESET_ALL}\n")
        return

    executable_path = sys.argv[2]
    game_name = os.path.splitext(os.path.basename(executable_path))[0]  # Game name without extension
    steam_note_path = None

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == "--gamename" and (i + 1) < len(sys.argv):
            game_name = sys.argv[i + 1]
            i += 2
        elif sys.argv[i].lower() in ("--note", "--steamnote") and (i + 1) < len(sys.argv):
            steam_note_path = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # Run the game and monitor the time
    run_and_monitor(executable_path, game_name, steam_note_path)

if __name__ == "__main__":
    main()
