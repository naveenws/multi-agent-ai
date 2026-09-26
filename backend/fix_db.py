import sqlite3

def update_db():
    conn = sqlite3.connect('multiagent.db')
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE agent SET model='gemini-3.8-flash' WHERE model='gemini-2.5-flash'")
        conn.commit()
        print('Updated models in DB.')
    except Exception as e:
        print('Error:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    update_db()
