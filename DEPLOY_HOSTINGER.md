# Guia de Deploy na VPS Hostinger

Este guia ajudará você a configurar seu Painel de Controle usando **Nginx** e **Gunicorn** em uma VPS Ubuntu.

## 1. Preparação da VPS
Acesse sua VPS via SSH e atualize o sistema:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git -y
```
    
## 2. Configuração do Projeto
Crie a pasta do projeto e suba seus arquivos (ou use git):
```bash
mkdir ~/chatbot_panel
cd ~/chatbot_panel
# [Suba os arquivos para cá]

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configuração do Systemd (Gunicorn)
Copie o arquivo de serviço fornecido para o sistema:
```bash
sudo cp ~/chatbot_panel/chatbot_panel.service /etc/systemd/system/
sudo systemctl start chatbot_panel
sudo systemctl enable chatbot_panel
```

## 4. Configuração do Nginx (Proxy Reverso)
Crie um arquivo de configuração para o site:
```bash
sudo nano /etc/nginx/sites-available/chatbot_panel
```
Cole o seguinte conteúdo (ajuste o domínio se tiver um):
```nginx
server {
    listen 80;
    server_name seu_ip_ou_dominio;

    location / {
        include proxy_params;
        proxy_pass http://unix:/root/chatbot_panel/chatbot_panel.sock;
    }
}
```
Ative a configuração e reinicie o Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/chatbot_panel /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 5. Firewall
Certifique-se de que as portas 80 (HTTP) e 5000 (se quiser acesso direto) estão abertas:
```bash
sudo ufw allow 'Nginx Full'
```
