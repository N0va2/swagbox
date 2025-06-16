# Discord Jukebox Bot 🎵

A feature-rich Discord music bot built with Python that allows servers to create a shared music library. It supports both server-wide playlists managed by admins and personal playlists for every user, creating a collaborative and personalized listening experience.

This project was developed as a personal exercise to learn about asynchronous programming, real-time API integration with Discord, and relational database management in Python.

### ✨ Features

*   **Dual Playlist System:**
    *   **👤 Personal Playlists:** Every user can create, manage, and play their own private playlists.
    *   **🌐 Server Playlists:** Admins can create and manage curated playlists for the entire server.
*   **Audio Playback:** Streams audio directly from YouTube and other sources supported by `yt-dlp`.
*   **Persistent Library:** All playlists and songs are stored in a local SQLite database, so your library is saved even if the bot restarts.
*   **Queue Management:** Add single songs or entire playlists to the queue. Includes `!skip` and `!stop` controls.
*   **Intuitive Command Structure:** Easy-to-use command groups (`!p` for personal, `!s` for server) with helpful feedback.
*   **Role-Based Permissions:** Server playlist management is restricted to users with "Manage Server" permissions.

---

### 🛠️ Tech Stack

*   **Language:** [Python 3.9+](https://www.python.org/)
*   **Discord API Wrapper:** [discord.py](https://github.com/Rapptz/discord.py)
*   **Database:** [SQLite 3](https://www.sqlite.org/index.html) (via Python's built-in `sqlite3` module)
*   **Audio Source & Extraction:** [yt-dlp](https://github.com/yt-dlp/yt-dlp)
*   **Audio Processing:** [FFmpeg](https://ffmpeg.org/)
*   **Audio Encryption:** [PyNaCl](https://pynacl.readthedocs.io/en/latest/) & [libopus](https://opus-codec.org/)

---

### 🚀 Getting Started

Follow these instructions to get a local copy up and running for development and testing purposes.

#### Prerequisites

You must have the following software installed on your system:

1.  **Python 3.9 or newer.**
2.  **FFmpeg:**
    *   Windows: Download from the [official site](https://ffmpeg.org/download.html) and add the `bin` folder to your system's PATH.
    *   macOS (via Homebrew): `brew install ffmpeg`
    *   Linux (Debian/Ubuntu): `sudo apt-get install ffmpeg`
3.  **Opus Audio Codec:**
    *   macOS (via Homebrew): `brew install opus`
    *   Linux (Debian/Ubuntu): `sudo apt-get install libopus0`

#### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate

    # For Windows
    python -m venv .venv
    .venv\Scripts\activate
    ```

3.  **Install the required Python packages:**
    ```sh
    pip install -r requirements.txt
    ```
    *(Note: You will need to create a `requirements.txt` file. See the section below.)*

4.  **Set up your Bot Token:**
    *   Create a file named `.env` in the root of the project.
    *   Add your Discord bot token to this file:
      ```
      DISCORD_TOKEN=YOUR_SUPER_SECRET_BOT_TOKEN_HERE
      ```
    *   Ensure your bot has the `SERVER MEMBERS` and `MESSAGE CONTENT` Privileged Intents enabled in the Discord Developer Portal.

#### Running the Bot

Once the setup is complete, you can start the bot with:

```sh
python bot.py
```

---

### 📝 How to Use

*(This is a condensed version of the user guide. You can expand it if you like.)*

*   **`!play <playlist_name | youtube_url>`**: Plays a playlist or a single song.
*   **`!skip`**: Skips the current song.
*   **`!stop`**: Stops playback and disconnects the bot.

**Personal Playlists:**
*   **`!p create <name>`**: Create your own playlist.
*   **`!p add <name> <url>`**: Add a song to your playlist.
*   **`!p list`**: See all of your playlists.
*   **`!p show <name>`**: See songs in one of your playlists.

**Server Playlists:**
*   **`!s list`**: See all server playlists.
*   **`!s show <name>`**: See songs in a server playlist.
*   **(Admin Only) `!s create <name>`**: Create a new server playlist.
*   **(Admin Only) `!s add <name> <url>`**: Add a song to a server playlist.

---

###
<!-- This is a good place for your name or GitHub handle! -->
### 👤 Author

**[Your Name]**
*   GitHub: [@your-username](https://github.com/your-username)
*   LinkedIn: [Your LinkedIn Profile](https://linkedin.com/in/your-profile)
<!-- End customization -->
