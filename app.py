import os
import json
import redis
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuração Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Configuração Redis para persistência dos resumos
# Na VPS Hostinger, o redis costuma rodar em localhost:6379
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Credenciais de Admin
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/api/leads')
@login_required
def get_leads():
    try:
        response = supabase.table('customers').select("*").execute()
        leads = response.data
        
        for lead in leads:
            phone = lead.get('phone')
            # Busca resumo persistido no Redis
            stored_data = r.get(f"summary:{phone}")
            if stored_data:
                data = json.loads(stored_data)
                lead['summary'] = data['summary']
                lead['deactivation_time'] = data['timestamp']
            else:
                lead['summary'] = None
                lead['deactivation_time'] = "1970-01-01T00:00:00"

        # Ordenação: Inativos primeiro, depois por tempo de desativação
        leads.sort(key=lambda x: (not x.get('active', True), x.get('deactivation_time', "")), reverse=True)
        return jsonify({"success": True, "leads": leads})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update_summary', methods=['POST'])
def update_summary():
    try:
        data = request.json
        phone = data.get('phone')
        summary = data.get('summary')
        
        if not phone:
            return jsonify({"success": False, "error": "Phone is required"}), 400
            
        summary_data = {
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
        # Persiste no Redis (expira em 24h para não encher a memória eternamente)
        r.setex(f"summary:{phone}", 86400, json.dumps(summary_data))
        
        # Notifica todos os painéis abertos via WebSocket em tempo real
        socketio.emit('new_lead_update', {"phone": phone, "summary": summary})
        
        return jsonify({"success": True, "message": "Summary persisted and broadcasted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/toggle_status/<phone>', methods=['POST'])
@login_required
def toggle_status(phone):
    try:
        response = supabase.table('customers').select("active").eq("phone", phone).single().execute()
        new_status = not response.data['active']
        supabase.table('customers').update({"active": new_status}).eq("phone", phone).execute()
        
        if new_status:
            r.delete(f"summary:{phone}")
            
        # Notifica o frontend para atualizar a lista
        socketio.emit('refresh_list')
        return jsonify({"success": True, "new_status": new_status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
