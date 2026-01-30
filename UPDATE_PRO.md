# Guia de Atualização Profissional (Redis + WebSockets)

Siga estes passos na sua VPS Hostinger para ativar a persistência e o tempo real.

## 1. Instalar o Redis na VPS
O Redis garantirá que os resumos não sumam no F5.
```bash
sudo apt update
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

## 2. Atualizar Dependências do Python
```bash
cd /root/chatbot_panel/painel_whatsapp_odontocompany
source venv/bin/activate
pip install flask-socketio redis eventlet
```

## 3. Ajustar o Gunicorn para WebSockets
O Gunicorn precisa de um "worker" especial para lidar com WebSockets. Edite seu arquivo de serviço:
`nano /etc/systemd/system/chatbot_panel.service`

Mude a linha `ExecStart` para:
```ini
ExecStart=/root/chatbot_panel/painel_whatsapp_odontocompany/venv/bin/gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:5000 app:app
```
*Nota: Para WebSockets, usamos `--worker-class eventlet`.*

## 4. Reiniciar o Painel
```bash
sudo systemctl daemon-reload
sudo systemctl restart chatbot_panel
```

## 5. Nginx (Opcional, mas recomendado)
Se você usa Nginx, adicione estas linhas dentro do bloco `location /` para permitir WebSockets:
```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "Upgrade";
```
