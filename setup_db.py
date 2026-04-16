import sqlite3
import os

DB_FILE = 'music_connect.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            user_type TEXT DEFAULT 'musician',
            email TEXT UNIQUE,
            bio TEXT,
            instruments TEXT,
            location TEXT,
            avatar_url TEXT,
            genres TEXT,
            google_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    ''')
    
    # Delete existing users to refresh data
    cursor.execute('DELETE FROM users')
    
    # Seed test users
    test_users = [
        (1, 'Thomas Seitz', 'musician', 'thomasseitz22@gmail.com', 'Hi its me.', 'Bass Guitar Keyboard', 'Munic', 'https://lh3.googleusercontent.com/a/ACg8ocIrhZaOzPMm0yOhVnS9C-zRQBjzntpxVEdml-1fmjUw567Xenob=s96-c', 'Hip Hop, Reggae, Jazz', None),
        (2, 'Alex Rivera', 'musician', 'alex@test.com', 'Guitar virtuoso with 10 years of experience. Love jamming and recording!', 'Electric Guitar, Acoustic Guitar, Bass', 'Los Angeles, CA', 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=200&h=200&fit=crop', 'Rock, Blues, Jazz', None),
        (3, 'Maya Johnson', 'musician', 'maya@test.com', 'Classical trained pianist looking to explore modern genres.', 'Piano, Keyboard, Vocals', 'New York, NY', 'https://images.unsplash.com/photo-1514320291840-2e0a9bf2a9ae?w=200&h=200&fit=crop', 'Classical, Jazz, Pop', None),
        (4, 'DJ Proton', 'producer', 'proton@test.com', 'Electronic music producer. Let\'s create some bangers!', 'DAW, Synth, Turntables', 'Miami, FL', 'https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=200&h=200&fit=crop', 'Electronic, House, Techno', None),
        (5, 'Sarah Mitchell', 'musician', 'sarah@test.com', 'Jazz vocalist and songwriter looking for collaborations', 'Vocals, Piano', 'New York, NY', 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop', 'Jazz, R&B, Pop', None),
        (6, 'Marcus Johnson', 'producer', 'marcus@test.com', 'Electronic music producer with 5+ years experience', 'DAW, Synth, Mix', 'Austin, TX', 'https://images.unsplash.com/photo-1570295999919-56ceb5ecca61?w=200&h=200&fit=crop', 'Electronic, Hip Hop, Pop', None),
        (7, 'Emma Rodriguez', 'band', 'emma@test.com', 'Indie rock band looking for new members', 'Guitar, Drums, Bass', 'Seattle, WA', 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&h=200&fit=crop', 'Indie, Rock, Alternative', None),
        (8, 'Aisha Patel', 'musician', 'aisha@test.com', 'R&B vocalist and songwriter', 'Vocals, Songwriting', 'Chicago, IL', 'https://images.unsplash.com/photo-1460723237483-7a6dc9d0b212?w=200&h=200&fit=crop', 'R&B, Hip Hop, Soul', None),
        (9, 'David Kim', 'producer', 'david@test.com', 'Hip hop producer looking for vocalists', 'DAW, Production, Mix', 'Atlanta, GA', 'https://images.unsplash.com/photo-1506794778202-cad845e021b8?w=200&h=200&fit=crop', 'Hip Hop, R&B, Trap', None),
        (10, 'Luna Vega', 'musician', 'luna@test.com', 'Classical crossover violinist', 'Violin, Piano', 'Boston, MA', 'https://images.unsplash.com/photo-1531746020798-e6953c6bc8e5?w=200&h=200&fit=crop', 'Classical, Neo-Classical, Electronic', None),
    ]
    
    for user in test_users:
        cursor.execute('''
            INSERT OR REPLACE INTO users (id, name, user_type, email, bio, instruments, location, avatar_url, genres, google_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', user)
    
    conn.commit()
    conn.close()
    print("Database initialized with test users!")

if __name__ == '__main__':
    init_db()