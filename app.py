import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")

# Configuração Supabase
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Armazenamento em memória (Não persiste no banco)
# Estrutura: { "phone": { "summary": "...", "timestamp": datetime } }
memory_summaries = {}

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
        # Busca leads do Supabase
        response = supabase.table('customers').select("*").execute()
        leads = response.data
        
        # Mescla com os resumos e timestamps da memória
        for lead in leads:
            phone = lead.get('phone')
            if phone in memory_summaries:
                lead['summary'] = memory_summaries[phone]['summary']
                lead['deactivation_time'] = memory_summaries[phone]['timestamp']
            else:
                lead['summary'] = None
                lead['deactivation_time'] = "1970-01-01T00:00:00" # Fallback para ordenação

        # Lógica de Ordenação:
        # 1. Inativos (active=False) primeiro.
        # 2. Entre os inativos, os que chegaram por último (deactivation_time mais recente) no topo.
        leads.sort(key=lambda x: (x.get('active', True), x.get('deactivation_time', "")), reverse=True)
        
        # Invertemos a lógica para garantir que active=False (0) venha antes de active=True (1)
        # E que deactivation_time maior (mais recente) venha primeiro.
        leads.sort(key=lambda x: (not x.get('active', True), x.get('deactivation_time', "")), reverse=True)

        return jsonify({"success": True, "leads": leads})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update_summary', methods=['POST'])
def update_summary():
    """
    Endpoint para o n8n enviar o resumo da conversa DIRETAMENTE para o painel.
    """
    try:
        data = request.json
        phone = data.get('phone')
        summary = data.get('summary')
        
        if not phone:
            return jsonify({"success": False, "error": "Phone is required"}), 400
            
        # Salva apenas na memória do servidor
        memory_summaries[phone] = {
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
        # Opcional: Você pode também atualizar o status 'active' no Supabase aqui se o n8n já não o fez
        # supabase.table('customers').update({"active": False}).eq("phone", phone).execute()
        
        return jsonify({"success": True, "message": "Summary received in memory"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/toggle_status/<phone>', methods=['POST'])
@login_required
def toggle_status(phone):
    try:
        response = supabase.table('customers').select("active").eq("phone", phone).single().execute()
        new_status = not response.data['active']
        supabase.table('customers').update({"active": new_status}).eq("phone", phone).execute()
        
        # Se o bot for reativado, limpamos o resumo da memória
        if new_status and phone in memory_summaries:
            del memory_summaries[phone]
            
        return jsonify({"success": True, "new_status": new_status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
