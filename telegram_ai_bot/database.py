import aiosqlite

DB_FILE = 'users.db'

async def init_db():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                is_premium INTEGER DEFAULT 0,
                language TEXT
            )
        """)
        await db.commit()

async def add_user(user_id, username):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
        await db.commit()

async def get_all_users():
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT id, username, is_premium FROM users") as cursor:
            return await cursor.fetchall()

async def set_premium(user_id):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE users SET is_premium = 1 WHERE id = ?", (user_id,))
        await db.commit()

async def is_user_premium(user_id):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT is_premium FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row and row[0] == 1

async def set_user_language(user_id, lang):
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("UPDATE users SET language = ? WHERE id = ?", (lang, user_id))
        await db.commit()

async def get_user_language(user_id):
    async with aiosqlite.connect(DB_FILE) as db:
        async with db.execute("SELECT language FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None