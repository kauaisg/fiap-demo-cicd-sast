from flask import Flask, request, jsonify
import sqlite3
import subprocess
import os
import re
import socket
from typing import Optional

app = Flask(__name__)

# ✅ SEGURO: Usar variáveis de ambiente para secrets
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'dev-password-change-in-production')

app.config['SECRET_KEY'] = SECRET_KEY

# ✅ CORRIGIDO: SQL Injection - usando parâmetros preparados
@app.route('/user')
def get_user():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'error': 'id parameter is required'}), 400
    
    # Validar que user_id é numérico
    if not user_id.isdigit():
        return jsonify({'error': 'id must be a number'}), 400
    
    try:
        conn = sqlite3.connect('users.db')
        # SEGURO: usar parâmetros preparados
        result = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchall()
        conn.close()
        return jsonify({'users': result})
    except sqlite3.Error as e:
        return jsonify({'error': 'Database error'}), 500

# ✅ CORRIGIDO: Command Injection - validação e whitelist
def is_valid_hostname(hostname: str) -> bool:
    """Valida se o hostname é seguro para ping"""
    if not hostname or len(hostname) > 253:
        return False
    
    # Não permitir sequências perigosas primeiro (antes da regex)
    dangerous_patterns = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r', ' ', '\t']
    for pattern in dangerous_patterns:
        if pattern in hostname:
            return False
    
    # Permitir apenas caracteres alfanuméricos, pontos e hífens
    # Esta regex deve ser a validação final
    if not re.match(r'^[a-zA-Z0-9.-]+$', hostname):
        return False
    
    # Validações adicionais de segurança
    # Não permitir hostnames que começam ou terminam com ponto ou hífen
    if hostname.startswith('.') or hostname.endswith('.') or hostname.startswith('-') or hostname.endswith('-'):
        return False
    
    # Não permitir sequências de pontos ou hífens
    if '..' in hostname or '--' in hostname:
        return False
    
    return True

@app.route('/ping')
def ping():
    host = request.args.get('host')
    if not host:
        return jsonify({'error': 'host parameter is required'}), 400
    
    # Validar hostname antes de executar comando
    if not is_valid_hostname(host):
        return jsonify({'error': 'Invalid hostname format'}), 400
    
    try:
        # SEGURO: usar subprocess sem shell=True e com lista de argumentos
        output = subprocess.check_output(
            ['ping', '-c', '1', host],
            stderr=subprocess.STDOUT,
            timeout=5
        )
        return jsonify({'result': output.decode('utf-8')})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Ping timeout'}), 408
    except subprocess.CalledProcessError as e:
        return jsonify({'error': 'Ping failed', 'details': e.output.decode('utf-8')}), 500
    except Exception as e:
        return jsonify({'error': 'Unexpected error'}), 500

# ✅ CORRETO: SQL com parâmetros
@app.route('/user/safe')
def get_user_safe():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'error': 'id parameter is required'}), 400
    
    # Validar que user_id é numérico
    if not user_id.isdigit():
        return jsonify({'error': 'id must be a number'}), 400
    
    try:
        conn = sqlite3.connect('users.db')
        result = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchall()
        conn.close()
        return jsonify({'users': result})
    except sqlite3.Error as e:
        return jsonify({'error': 'Database error'}), 500

@app.route('/health')
def health():
    """Endpoint de health check"""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    # ✅ SEGURO: debug baseado em variável de ambiente
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
