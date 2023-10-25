import pymysql

class Database:
    def __init__(self):
        self.connection = pymysql.connect(
            host="localhost",
            user="root",
            password="i,am,assad.",
            database="api",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        self.create_table()

    def create_table(self):
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS text_corrections (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    input_text TEXT,
                    corrected_text TEXT
                )
            """)
        self.connection.commit()

    def add_correction(self, input_text, corrected_text):
        with self.connection.cursor() as cursor:
            cursor.execute("INSERT INTO text_corrections (input_text, corrected_text) VALUES (%s, %s)",
                           (input_text, corrected_text))
        self.connection.commit()

    def get_correction(self, id):
        with self.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM text_corrections WHERE id = %s", (id,))
            return cursor.fetchone()

    def close(self):
        self.connection.close()
