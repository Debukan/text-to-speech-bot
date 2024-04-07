import sqlite3
import logging
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.log",
    filemode="a",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class DataBase:
    def __init__(self):
        self.conn = self.prepare_db()


    # подготовка базы данных
    def prepare_db(self):
        try:
            conn = sqlite3.connect(config.DB_NAME, check_same_thread=False)
            logging.info("Database is ready")
            return conn
        except Exception as e:
            logging.error(e)
            exit(1)
            
    def execute_query(self, sql_query, data=None):
        logging.info(f"DATABASE: Execute query: {sql_query}")

        cursor = self.conn.cursor()
        if data:
            cursor.execute(sql_query, data)
        else:
            cursor.execute(sql_query)

        self.conn.commit()
        logging.info(f"DATABASE: Запрос был выполнен")

    def execute_selection_query(self, sql_query, data=None):
        logging.info(f"DATABASE: Execute query: {sql_query}")

        cursor = self.conn.cursor()

        if data:
            cursor.execute(sql_query, data)
        else:
            cursor.execute(sql_query)
        rows = cursor.fetchall()
        logging.info(f"DATABASE: Запрос был выполнен")
        return rows
    

    # создание таблицы users
    def create_table(self):
        cursor = self.conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER,
            username TEXT,
            message TEXT,
            tts_symbols INTEGER DEFAULT 0
        )
        """
        cursor.execute(create_table_query)
        self.conn.commit()
        logging.info("Таблица users создана")

   
    # создание таблицы history
    def create_table_history(self):
        cursor = self.conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            tts_symbols INTEGER DEFAULT 0
        )
        """
        cursor.execute(create_table_query)
        self.conn.commit()
        logging.info("DATABASE: Таблица history создана")

    
    # создание таблицы token_usage
    def create_table_token_usage(self):
        cursor = self.conn.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS token_usage (
            id INTEGER PRIMARY KEY,
            number INTEGER DEFAULT 1,
            tokens INTEGER DEFAULT 0
        );
        """
        cursor.execute(create_table_query)
        self.conn.commit()
        logging.info(f"DATABASE: Таблица token_usage создана")

    
    # обновление значения в таблице users
    def update_data(self, user_id, column, value):
        cursor = self.conn.cursor()
        update_table_query = f"""
        UPDATE users SET {column} = ? WHERE user_id = ?;
        """
        cursor.execute(update_table_query, (value, user_id))
        self.conn.commit()
        logging.info(f"DATABASE: Значение таблицы {column}")

    
    # вставка значения в таблицу users
    def insert_data(self, user_id, subject, value):
        cursor = self.conn.cursor()
        insert_data_query = f"""
        INSERT INTO users ({subject})
        SELECT ?
        WHERE NOT EXISTS (SELECT * FROM users WHERE user_id = ?);
        """
        cursor.execute(insert_data_query, (value, user_id))
        self.conn.commit()
        logging.info(f"DATABASE: Данные {subject} были вставлены")


    # добавление пользователя в базу данных
    def add_user(self, user_id, username = "", message = "", tts_symbols = 0):    
        add_user_query = f"""
        INSERT INTO users(user_id, username, message, tts_symbols)
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE user_id = ?);
        """
        self.execute_query(add_user_query, [user_id, username, message, tts_symbols, user_id])
        logging.info(f"DATABASE: Пользователь {username} с id: {user_id} был добавлен")

    
    # проверка есть ли такой столбец в таблице users
    def is_value_in_table(self, column_name, value):
        sql_query = f'SELECT EXISTS (SELECT 1 FROM {config.TABLE_NAME} WHERE {column_name} = ?)'
        rows = self.execute_selection_query(sql_query, [value])
        return len(rows) > 0


    # получение словаря с данными пользователя из базы данных
    def get_data_for_user(self, user_id):
        if self.is_value_in_table('user_id', user_id):
            sql_query = f'SELECT *' \
                        f'FROM {config.TABLE_NAME} WHERE user_id = ? LIMIT 1'
            row = self.execute_selection_query(sql_query, [user_id])[0]
            result = {
                "username": row[2],
                "message": row[3],
                "tts_symbols": row[4]
            }
            logging.info(f"DATABASE: Данные были найдены и возвращены")
            return result
        else:
            logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")
            self.add_user(user_id)
            return {
                "username": "",
                "message": "",
                "tts_symbols": 0,
            }
        
    
    # проверка есть ли такой пользователь в базе данных
    def user_exists(self, user_id):
        if not self.is_value_in_table('user_id', user_id):
            logging.info(f"DATABASE: Пользователь с id = {user_id} не найден")
            self.add_user(user_id)
            return True
        return False


    # добавление в историю запрос пользователя
    def add_history(self, user_id, username, message, symbols):
        add_history_query = f"""
        INSERT INTO history(user_id, username, message, tts_symbols)
        SELECT ?, ?, ?, ?
        """
        self.execute_query(add_history_query, [user_id, username, message, symbols])
        logging.info(f"DATABASE: История пользователя {username} с id: {user_id} добавлена")

    
    # получение истории запросов пользователя из базы данных
    def get_history(self, user_id):
        sql_query = f'SELECT *' \
                    f'FROM history WHERE user_id = ?'
        rows = self.execute_selection_query(sql_query, [user_id])
        return rows
    

    # обновление значения в таблице token_usage
    def update_usage_token(self, tokens):
        cursor = self.conn.cursor()
        update_table_query = f"""
        UPDATE token_usage SET tokens = ? WHERE number = 1;
        """
        cursor.execute(update_table_query, (tokens,))
        self.conn.commit()
        logging.info(f"DATABASE: Таблица token_usage обновлена")


    # получение токенов из token_usage
    def get_token_usage(self):
        cursor = self.conn.cursor()
        get_tokens_query = """
        SELECT tokens
        FROM token_usage
        """
        row = self.execute_selection_query(get_tokens_query)
        tokens = row[0][0]
        logging.info(f"DATABASE: Токены из таблицы token_usage получены")
        return tokens
    

    # добавление токенов в таблицу token_usage
    def insert_token_usage_data(self, tokens):
        cursor = self.conn.cursor()
        insert_data_query = f"""
        INSERT INTO token_usage (tokens)
        SELECT ?
        WHERE NOT EXISTS (SELECT * FROM token_usage WHERE number = 1);
        """
        cursor.execute(insert_data_query, (tokens,))
        self.conn.commit()
        logging.info(f"DATABASE: Токены в таблицу token_usage были добавлены")

