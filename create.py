import sqlite3


def add_user(username, password):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print(f"Пользователь '{username}' успешно добавлен.")
    except sqlite3.IntegrityError:
        print(f"Ошибка: Пользователь '{username}' уже существует.")
    finally:
        conn.close()

add_user('admin', 'password123')
add_user('user', 'user')
add_user('1', '1')