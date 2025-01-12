from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

def get_db_connection():
    connection = mysql.connector.connect(
        host='localhost',
        user='root',  # Use seu usuário MySQL
        password='admin',  # Sua senha MySQL
        database='ebooks_db'  # Nome do banco de dados
    )
    return connection

@app.route('/ebooks', methods=['GET'])
def get_ebooks():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute('SELECT id, titulo, arquivo_path, data_upload FROM ebooks ORDER BY data_upload DESC')
    ebooks = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify(ebooks)

if __name__ == '__main__':
    app.run(debug=True)
