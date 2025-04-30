# NSGTT - Non Steam Game Time Tracker

**NSGTT** is a lightweight tool that tracks playtime for non-Steam games and optionally updates Steam Notes for better integration.

This script monitors the execution of any game executable, records your playtime and number of launches, and updates a formatted Steam Note if configured.

---

## 📜 Features

- 🕒 Tracks total time played for any executable.
- 🔁 Counts how many times you've launched the game.
- 📄 Updates a **Steam Note** (for non-Steam games!) with:
  - Last played date and time
  - Total playtime
  - Number of times launched
- 💾 Saves playtime data locally in a simple `time_played.txt` file.

---

## 🚀 How to Use

### 1. Basic Usage (Tracking a Game)

```bash
nsgtt.exe --run "path\to\your\game.exe"
```

Example:

```bash
nsgtt.exe --run "C:\games\metaphor\refantazio.exe"
```

The game will launch, and the timer will automatically track how long it stays open.

---

## 2. Adding NSGTT to Steam (Shortcut Integration)

You can make NSGTT work directly inside your Steam Library, tracking time automatically!

### Steps:

1. In Steam, click **Add a Non-Steam Game**.
2. Choose any `.exe` file (you'll edit it soon).
3. Right-click the new shortcut → **Properties**.
4. In the **Target** field, replace it with:

```plaintext
"full_path_to_timer.exe" --run "full_path_to_game.exe"
```

Example:

```plaintext
"C:\nsgtt\nsgtt.exe" --run "C:\games\metaphor\refantazio.exe"
```

5. Rename the shortcut to the real game name.
6. (Optional) Set a custom icon for better presentation and grab art assets at SGDB (https://www.steamgriddb.com/).

Now when you launch the game from Steam, NSGTT will monitor it and update your playtime information automatically!

### 3. Auto Updating a Steam Note (Optional)

![image](https://github.com/user-attachments/assets/a4339846-12e1-493d-9396-4d04129db51f)

If you want NSGTT to also update your **Steam Notes** after playing:

```bash
nsgtt.exe --run "path\to\your\game.exe" --note "path\to\steam_note_file"
```

Example (using a common Steam non-Steam note path):

```bash
"C:\nsgtt\nsgtt.exe" --run "C:\games\metaphor\refantazio.exe" --note "C:\Program Files (x86)\Steam\userdata\[YOUR STEAM ID]\2371090\remote\notes_shortcut_Metaphor___ReFantazio"
```

Usually, steam stores the game notes for Non Steam Games at: 
```bash 
C:\Program Files (x86)\Steam\userdata\[YOUR STEAM ID]\2371090\remote\
```


> ⚠️ **VERY IMPORTANT:**  
> 
> - **You must restart Steam** after creating or modifying a Steam Note externally. Steam caches notes, and changes won't show immediately! (Entering Big Picture mode also reloads the notes).
> - **The tool always edits ONLY the first note** of the note file.
> - **If you have written something manually in that first note, it WILL be replaced**.

---

## 📂 Files

- `nsgtt.exe` → Main Executable (made in Python)
- `time_played.txt` → Local database file automatically created, saving:
  - Total playtime (in seconds)
  - Number of launches

Example `time_played.txt`:

```
Skyrim=12345.67,12
```

---

## ❓ FAQ

- **Will this interfere with my games or Steam?**
  - No. It only observes running processes and edits one local note file.

- **If I force-close the game, will time still be recorded?**
  - Yes, it saves data based on the process lifetime.

- **Does it support tracking multiple games?**
  - Absolutely! Each executable is tracked separately.

- **Can I edit multiple notes at once?**
  - No — **currently only the first note**.
 
- **Can I execute games that require 'Run as Administrator' through NSGTT?**
  - Sadly, nope.
    
 - **There are no notes in the 2371090\remote\ folder. Why?**
   - Just create a placeholder note on your steam shortcut page and save it. It should appear there.
---

## 🧠 License

This project is open-source and free for personal use.  
Contributions and suggestions are welcome! 🎮

---
