# NSGTT - Non Steam Game Time Tracker

**NSGTT** is a lightweight tool that tracks playtime for non-Steam games and optionally updates Steam Notes for seamless integration with your Steam Library.

This script monitors the execution of any game executable, records your playtime and number of launches in a SQLite database, and updates a formatted Steam Note if configured.

---

## 📜 Features

- 🕒 Tracks total time played for any executable.
- 🔁 Counts how many times you've launched the game.
- 📊 Displays playtime statistics for all tracked games.
- 📄 Updates a **Steam Note** (for non-Steam games!) with:
  - Last played date and time
  - Total playtime
  - Number of times launched
- 💾 Saves playtime data locally in a SQLite database (`nsgtt.db`).
- ⚙️ Configurable Steam path and Notes AppID via `config.json`.

---

## 🚀 How to Use

### 1. Basic Usage (Tracking a Game)

```bash
nsgtt.exe --run "path\to\your\game.exe"
```

Example:

```bash
nsgtt.exe --run "C:\Games\Metaphor\Metaphor.exe"
```

The game will launch, and the timer will track how long it stays open. Playtime and launch count are saved in `nsgtt.db`.

### 2. View Statistics

To see playtime statistics for all tracked games:

```bash
nsgtt.exe
```

Output example:

```
Game Statistics:
+----------------------+--------------+-------------+
| Game Name            | Time Played  | Play Count  |
+----------------------+--------------+-------------+
| Metaphor - ReFantazio | 00:01:34     | 1           |
| Cuphead              | 00:05:12     | 3           |
+----------------------+--------------+-------------+
```

---

## 3. Adding NSGTT to Steam (Shortcut Integration)

Integrate NSGTT with Steam to track non-Steam games directly from your Library!

### Steps:

1. In Steam, click **Add a Non-Steam Game**.
2. Choose any `.exe` file (you'll edit it soon).
3. Right-click the new shortcut → **Properties**.
4. In the **Target** field, replace it with:

```plaintext
"full_path_to_nsgtt.exe" --run "full_path_to_game.exe"
```

Example:

```plaintext
"E:\Arquivos\Ferramentas\NSGTT\nsgtt.exe" --run "C:\Games\Metaphor\Metaphor.exe"
```

5. Rename the shortcut to the real game name (ex.: `Metaphor - ReFantazio`).
6. (Optional) Set a custom icon and grab art assets at [SteamGridDB](https://www.steamgriddb.com/).

Now, launching the game from Steam will run NSGTT, track playtime, and update Steam Notes (if configured).

### 4. Auto Updating a Steam Note

![image](https://github.com/user-attachments/assets/a4339846-12e1-493d-9396-4d04129db51f)

NSGTT automatically updates Steam Notes if the game is added as a non-Steam game. The note file is created in:

```
C:\Program Files (x86)\Steam\userdata\[YOUR_STEAM_ID]\2371090\remote\notes_shortcut_[GAME_NAME]
```

Example for `Metaphor - ReFantazio`:

```
C:\Program Files (x86)\Steam\userdata\54808062\2371090\remote\notes_shortcut_Metaphor___ReFantazio
```

The note file is created automatically when you run the game via NSGTT. The note includes:

- Last played date/time
- Total playtime
- Number of launches

> ⚠️ **VERY IMPORTANT:**
>
> - **You must restart Steam** or enter **Big Picture mode** after NSGTT updates a note, as Steam caches notes.
> - NSGTT **only edits the first note** in the note file.
> - Manual changes to the first note will be **overwritten** by NSGTT.
> - If no note file exists, create a placeholder note in Steam for the game to initialize the file.

### 5. Configuration (Optional)

Create a `config.json` file in the same directory as `nsgtt.exe` to customize settings:

```json
{
    "STEAM_PATH": "C:\\Program Files (x86)\\Steam",
    "NOTES_APPID": "2371090"
}
```

If not provided, default values are used.

---

## 📂 Files

- `nsgtt.exe` → Main executable (built with Python and PyInstaller).
- `nsgtt.db` → SQLite database automatically created, storing:
  - Game name
  - Total playtime (in seconds)
  - Number of launches
- `config.json` → Optional configuration file for Steam path and Notes AppID.

Example `nsgtt.db` content (viewed with SQLite browser):

```
game_name              | time_played | play_count
-----------------------|-------------|------------
Metaphor - ReFantazio  | 94.0        | 1
Cuphead               | 312.0       | 3
```

---

## ❓ FAQ

- **Will this interfere with my games or Steam?**
  - No. It only monitors processes and edits note files.

- **If I force-close the game, will time still be recorded?**
  - Yes, playtime is saved based on the process lifetime.

- **Does it support tracking multiple games?**
  - Yes, each game is tracked separately in `nsgtt.db`.

- **Can I edit multiple notes at once?**
  - No, only the first note in the note file is edited.

- **Can I execute games that require 'Run as Administrator' through NSGTT?**
  - No, NSGTT does not support running games as administrator.

- **There are no notes in the 2371090\remote\ folder. Why?**
  - Create a placeholder note in Steam for the game and save it. The file will appear in the `remote` folder.

- **Why don't I see updated notes in Steam?**
  - Restart Steam or enter Big Picture mode to refresh the note cache.

---

## 🧠 License

This project is open-source and free for personal use.  
Contributions and suggestions are welcome! 🎮

---
