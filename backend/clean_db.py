import sqlite3

def clean_db():
    conn = sqlite3.connect('multiagent.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM agent WHERE name IN ('olama', 'ollama', 'dd', 'aa')")
    conn.commit()
    print('Cleaned up misconfigured agents.')
    conn.close()

if __name__ == '__main__':
    clean_db()
