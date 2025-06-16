import sqlite3

def setup_database():
    """Creates the tables for a multi-playlist system."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    # Master table for all unique songs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            added_by_name TEXT
        )
    ''')
    # Table for playlists (both user and server)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            owner_id INTEGER,  -- NULL for server-wide playlists
            name TEXT NOT NULL,
            UNIQUE(guild_id, owner_id, name)
        )
    ''')
    # Linking table to connect songs to playlists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS playlist_songs (
            playlist_id INTEGER,
            song_id INTEGER,
            FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY(song_id) REFERENCES songs(id),
            PRIMARY KEY(playlist_id, song_id)
        )
    ''')
    conn.commit()
    conn.close()

# --- Song Management ---
def add_or_get_song(title, url, user_name):
    """Adds a song to the master list if it doesn't exist, returns its ID."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO songs (title, url, added_by_name) VALUES (?, ?, ?)", (title, url, user_name))
        song_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError: # Song URL already exists
        cursor.execute("SELECT id FROM songs WHERE url = ?", (url,))
        song_id = cursor.fetchone()[0]
    finally:
        conn.close()
    return song_id

# --- Playlist Management ---
def create_playlist(guild_id, name, owner_id=None):
    """Creates a playlist. owner_id=None makes it a server playlist."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO playlists (guild_id, owner_id, name) VALUES (?, ?, ?)",
            (guild_id, owner_id, name)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError: # Playlist with that name already exists for that user/server
        return False
    finally:
        conn.close()

def get_playlist(guild_id, name, owner_id=None):
    """Gets a specific playlist's ID and name."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name FROM playlists WHERE guild_id = ? AND name = ? AND owner_id IS ?",
        (guild_id, name, owner_id)
    )
    playlist = cursor.fetchone()
    conn.close()
    return playlist

def get_user_playlists(guild_id, owner_id):
    """Gets all playlists for a specific user."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM playlists WHERE guild_id = ? AND owner_id = ? ORDER BY name",
        (guild_id, owner_id)
    )
    playlists = cursor.fetchall()
    conn.close()
    return playlists

def get_server_playlists(guild_id):
    """Gets all server-wide playlists."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM playlists WHERE guild_id = ? AND owner_id IS NULL ORDER BY name",
        (guild_id,)
    )
    playlists = cursor.fetchall()
    conn.close()
    return playlists

def delete_playlist(guild_id, name, owner_id=None):
    """Deletes a playlist. ON DELETE CASCADE will handle playlist_songs."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM playlists WHERE guild_id = ? AND name = ? AND owner_id IS ?",
        (guild_id, name, owner_id)
    )
    changes = conn.total_changes
    conn.commit()
    conn.close()
    return changes > 0

# --- Playlist Content Management ---
def add_song_to_playlist(playlist_id, song_id):
    """Adds a song to a playlist."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)", (playlist_id, song_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Song is already in that playlist
    finally:
        conn.close()

def get_songs_from_playlist(playlist_id):
    """Retrieves all songs (id, title, url) from a given playlist."""
    conn = sqlite3.connect('music_library.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.id, s.title, s.url 
        FROM songs s
        JOIN playlist_songs ps ON s.id = ps.song_id
        WHERE ps.playlist_id = ?
        ORDER BY s.title
    ''', (playlist_id,))
    songs = cursor.fetchall()
    conn.close()
    return songs