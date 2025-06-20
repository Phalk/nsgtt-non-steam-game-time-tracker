# Non-Steam Game Time Tracker (NSGTT)

**NSGTT** is a Python script that tracks playtime for non-Steam games added as shortcuts in Steam. It monitors running processes, logs playtime to a SQLite database, and updates Steam notes with session details (last played, total time, and play count).

## Features
- **Process Monitoring**: Detects when non-Steam games (listed in `shortcuts.vdf`) start and stop, tracking their runtime.
- **Database Storage**: Saves total playtime and play count per game in a SQLite database (`nsgtt.db`).
- **Steam Note Integration**: Updates Steam notes in the specified `NOTES_APPID` directory with formatted session info.
- **Debug Mode**: Toggle verbose logging via `DEBUG` in `config.json` for troubleshooting.
- **Robust Error Handling**: Continues monitoring even if errors occur during process termination or file operations.
- **Efficient File Handling**: Caches `shortcuts.vdf` and reloads only when modified, minimizing file I/O.

## Requirements
- **Python 3.8+**
- **Dependencies** (install via `pip`):
  ```bash
  pip install psutil colorama vdf
  ```
- **Windows OS** (uses `os.system('cls')` for console clearing; adaptable for other OSes).
- **Steam Installed**: Requires a valid Steam installation with non-Steam games added as shortcuts.
- **Write Permissions**: Needs write access to the Steam `userdata` directory and the NSGTT directory for the database and notes.

## Installation
1. **Clone or Download**:
   ```bash
   git clone https://github.com/yourusername/nsgtt.git
   cd nsgtt
   ```
   Or download and extract the ZIP file.

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   Create `requirements.txt` with:
   ```
   psutil
   colorama
   vdf
   ```

3. **Configure**:
   Create `config.json` in the NSGTT directory:
   ```json
   {
       "STEAM_PATH": "C:\\Program Files (x86)\\Steam",
       "NOTES_APPID": "2371090",
       "CHECK_INTERVAL": 5,
       "USERDATA_ID": "00000000",
       "DEBUG": false
   }
   ```
   - `STEAM_PATH`: Path to your Steam installation.
   - `NOTES_APPID`: Steam AppID for note storage (default: `2371090`).
   - `CHECK_INTERVAL`: Seconds between process checks (default: `5`).
   - `USERDATA_ID`: Steam userdata folder ID (e.g., `54808062`). If `null`, uses the first valid folder.
   - `DEBUG`: Set to `true` for verbose logging, `false` for minimal output.

4. **Add Non-Steam Games to Steam**:
   - In Steam, go to Library > Add a Game > Add a Non-Steam Game.
   - Select the game's executable (e.g., `Cuphead.exe`).
   - Ensure the game appears in `shortcuts.vdf` (located at `STEAM_PATH/userdata/USERDATA_ID/config/shortcuts.vdf`).

## Usage
1. **Run the Program**:
   ```bash
   python nsgtt.py
   ```
   - The script initializes the database (`nsgtt.db`), detects the userdata ID, and starts monitoring.
   - Console output:
     - Startup: Shows database initialization and userdata ID.
     - Game Start: "Started tracking [Game] (PID: X, Time: HH:MM:SS, Count: Y)".
     - Game Stop: "Stopped tracking [Game] (PID: X, Session: HH:MM:SS, Total: HH:MM:SS, Count: Y)".
     - Monitoring: Updates "Monitoring... (X processes tracked, iteration Y)" in place.
     - Errors: Displays any issues (e.g., database or file access errors).

2. **View Statistics**:
   ```bash
   python nsgtt.py --show
   ```
   - Displays a table of all tracked games with total playtime and play count.

3. **Stop the Program**:
   - Press `Ctrl+C` to stop monitoring. The console will show "Monitor stopped by user."

## Running as a Windows Service with NSSM
To run NSGTT as a background service on Windows, use NSSM (Non-Sucking Service Manager).

1. **Install NSSM**:
   - Download NSSM from [https://nssm.cc/download](https://nssm.cc/download).
   - Extract and place `nssm.exe` in a directory (e.g., `C:\Program Files\nssm`).

2. **Prepare the Script**:
   - Place `nsgtt.py` in a stable location (e.g., `C:\Scripts\nsgtt.py`).
   - Optionally, convert to an executable with `pyinstaller`:
     ```bash
     pip install pyinstaller
     pyinstaller --onefile nsgtt.py
     ```
     This creates `nsgtt.exe` in the `dist` folder.

3. **Install the Service**:
   - Open Command Prompt as Administrator.
   - Install the service:
     ```bash
     nssm install NSGTT "C:\Python39\python.exe" "C:\Scripts\nsgtt.py"
     ```
     Replace paths with your Python interpreter and script locations. If using the executable:
     ```bash
     nssm install NSGTT "C:\Scripts\dist\nsgtt.exe"
     ```

4. **Configure the Service**:
   - Edit settings with:
     ```bash
     nssm edit NSGTT
     ```
   - In the NSSM GUI:
     - **Application tab**: Verify the path and arguments.
     - **Details tab**: Set display name to "Non-Steam Game Time Tracker".
     - **Log on tab**: Use "Local System account" or a specific user with Steam directory access.
     - **I/O tab**: Optionally set output to `C:\Logs\nsgtt.log`.
     - Save changes.

5. **Start the Service**:
   - Start the service:
     ```bash
     nssm start NSGTT
     ```
   - Or use Windows Services (`services.msc`), find "Non-Steam Game Time Tracker", and start it.

6. **Manage the Service**:
   - Check status:
     ```bash
     nssm status NSGTT
     ```
   - Stop the service:
     ```bash
     nssm stop NSGTT
     ```
   - Remove the service:
     ```bash
     nssm remove NSGTT confirm
     ```

7. **Verify Operation**:
   - Check the log file (if configured) or `nsgtt.db` for updates.
   - Ensure Steam notes are updated in `STEAM_PATH/userdata/USERDATA_ID/NOTES_APPID/remote`.

## Console Output
With `DEBUG: false`, the console is kept clean:
- **Startup**:
  ```
  ===== [ NSGTT - Non Steam Game Time Tracker ] =====
  Initializing database at: E:\Arquivos\Ferramentas\NSGTT\nsgtt.db
  Database initialized successfully.
  Using USERDATA_ID from config: 54808062
  Starting process monitor...
  ```
- **Game Starts**:
  ```
  Started tracking Cuphead (PID: 16660, Time: 00:02:01, Count: 2)
  ```
- **Game Stops**:
  ```
  Stopped tracking Cuphead (PID: 16660, Session: 00:00:10, Total: 00:02:11, Count: 3)
  ```
- **Monitoring**:
  ```
  Monitoring... (0 processes tracked, iteration 12)
  ```
- **Shortcuts Reload**:
  ```
  Reloading shortcuts.vdf (modified at Sat May 24 00:15:00 2025)
  ```

With `DEBUG: true`, additional verbose messages appear (e.g., "Retrieving data for game: Cuphead").

## Database
- **Location**: `nsgtt.db` in the NSGTT directory.
- **Schema**:
  ```sql
  CREATE TABLE game_time (
      game_name TEXT PRIMARY KEY,
      time_played REAL,
      play_count INTEGER
  );
  ```
- Stores each game's name, total playtime (seconds), and play count.

## Steam Notes
- **Location**: `STEAM_PATH/userdata/USERDATA_ID/NOTES_APPID/remote/notes_shortcut_[GameName]`.
- **Format**: JSON with a single note per game:
  ```json
  {
      "notes": [
          {
              "title": "Last session: 2025-05-24 00:12 || Time played: 00:02:11 (played 3 times)",
              "content": "\n📅 Last played: 2025-05-24 00:12\n⏱️ Recorded time: 00:02:11\n🔢 Times played: 3\n",
              "time_modified": 1748212320
          }
      ]
  }
  ```

## Troubleshooting
- **Crash on Game Termination**:
  - Ensure `DEBUG: true` in `config.json` and check for error messages.
  - Verify write permissions for `nsgtt.db` and the Steam `remote` directory.
- **No Games Detected**:
  - Confirm games are added as non-Steam shortcuts in Steam.
  - Check `shortcuts.vdf` for correct executable paths.
- **Steam Note Not Updating**:
  - Verify `NOTES_APPID` and `USERDATA_ID` in `config.json`.
  - Run as administrator if permission errors occur:
    ```bash
    python nsgtt.py
    ```
- **Console Clutter**:
  - Ensure `DEBUG: false` for minimal output.
  - Confirm you're on Windows (uses `cls` for clearing).


## Contributing
- Fork the repository and submit pull requests for bug fixes or features.
- Report issues via GitHub Issues, including console output with `DEBUG: true`.

## License
MIT License. See `LICENSE` for details.

## Credits
Developed by Phalk. Inspired by the need to track non-Steam game playtime seamlessly within Steam.
