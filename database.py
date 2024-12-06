from contextlib import asynccontextmanager

import aiosqlite


async def init_db():
    async with aiosqlite.connect('chat.db') as conn:
        await conn.execute('PRAGMA journal_mode=WAL')

        # users
        await conn.execute('''CREATE TABLE IF NOT EXISTS users (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                username TEXT UNIQUE,
                                password TEXT)''')

        # chats
        await conn.execute('''CREATE TABLE IF NOT EXISTS chats (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER,
                                chat_name TEXT,
                                asked_about_files INTEGER DEFAULT 0,
                                FOREIGN KEY (user_id) REFERENCES users(id))''')

        # message
        await conn.execute('''CREATE TABLE IF NOT EXISTS messages (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                chat_id INTEGER,
                                user_id INTEGER,
                                message TEXT,
                                sender TEXT,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (chat_id) REFERENCES chats(id),
                                FOREIGN KEY (user_id) REFERENCES users(id))''')

        await conn.commit()


@asynccontextmanager
async def get_db_connection():
    conn = await aiosqlite.connect('chat.db')
    try:
        yield conn
    finally:
        await conn.close()

async def get_user(username):
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT id FROM users WHERE username = ?", (username,))
        return await cursor.fetchone()

async def save_message(chat_id, user_id, message, sender):
    async with get_db_connection() as conn:
        await conn.execute("INSERT INTO messages (chat_id, user_id, message, sender) VALUES (?, ?, ?, ?)",
                           (chat_id, user_id, message, sender))
        await conn.commit()

async def create_chat(user_id, chat_name):
    async with get_db_connection() as conn:
        await conn.execute("INSERT INTO chats (user_id, chat_name) VALUES (?, ?)", (user_id, chat_name))
        await conn.commit()

async def get_chat_history(chat_id, user_id):
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT message, sender, timestamp FROM messages WHERE chat_id = ? AND user_id = ? ORDER BY timestamp ASC",
                                    (chat_id, user_id))
        return await cursor.fetchall()

async def get_user_chats(user_id):
    async with get_db_connection() as conn:
        cursor = await conn.execute("SELECT id, chat_name FROM chats WHERE user_id = ?", (user_id,))
        return await cursor.fetchall()