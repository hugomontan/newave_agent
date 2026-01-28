## Deploy na EC2 sem Docker (SSH + systemd, usando usuário `ubuntu`)

### 1. Preparar a EC2 (uma vez)

- **Criar instância** (Ubuntu)
  - Liberar no Security Group:
    - Porta 22 (SSH).
    - Portas 80/443 (se usar Nginx).
    - Opcional: 3000/8000 apenas para testes internos.
  - Garantir saída HTTPS para internet (para acessar Azure OpenAI).

- **Instalar dependências básicas** (via SSH na EC2, como usuário `ubuntu`)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm git nginx
```

- **Criar diretório da aplicação (usando o próprio `ubuntu`)**

```bash
sudo mkdir -p /opt/nw_multi
sudo chown -R ubuntu:ubuntu /opt/nw_multi
```

---

### 2. Trazer o código para a EC2 (sem git na EC2)

Se a EC2 não tiver `git` ou `apt` funcionando, você pode enviar o código a partir do seu computador local.

#### 2.1 Empacotar o projeto localmente (Windows)

No seu computador:
- No Explorer, clique com o botão direito na pasta do projeto `nw_multi`.
- Escolha **Enviar para → Pasta compactada (.zip)**.
- Suponha que o arquivo gerado seja `C:\Users\SEU_USUARIO\Desktop\nw_multi.zip`.

#### 2.2 Enviar o `.zip` para a EC2 via `scp`

No PowerShell/CMD do seu computador (onde você já usa `ssh`), rode:

```powershell
scp -i C:\caminho\para\sua-chave.pem C:\Users\SEU_USUARIO\Desktop\nw_multi.zip usuario@HOST:/home/usuario/
```

- `usuario` é o mesmo que você usa no `ssh` (`ubuntu`, `ec2-user`, etc.).
- `HOST` é o hostname/IP que você usa no SSH.

#### 2.3 Descompactar no diretório de deploy

Na EC2 (já conectado via SSH como o mesmo usuário):

```bash
sudo mkdir -p /opt/nw_multi
sudo chown -R "$USER:$USER" /opt/nw_multi

mv ~/nw_multi.zip /opt/nw_multi/
cd /opt/nw_multi
unzip nw_multi.zip
```

Se o `.zip` criar uma pasta `nw_multi` dentro de `/opt/nw_multi`, ajuste:

```bash
cd /opt/nw_multi
ls
# Se aparecer uma pasta nw_multi dentro, faça:
mv nw_multi/* .
mv nw_multi/.* . 2>/dev/null || true
rmdir nw_multi
```

Ao final, você deve ter o código em `/opt/nw_multi` com a estrutura `backend/`, `frontend/`, etc.

---

### 3. Configurar e rodar o backend

#### 3.1 Criar venv e instalar dependências (como `ubuntu`)

```bash
cd /opt/nw_multi/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3.2 Criar arquivo de variáveis de ambiente do backend

Exemplo em `/etc/nw_multi_backend.env`:

```bash
sudo tee /etc/nw_multi_backend.env >/dev/null <<'EOF'
OPENAI_API_KEY=SEU_AZURE_KEY
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

AZURE_OPENAI_API_KEY=SEU_AZURE_KEY
AZURE_OPENAI_ENDPOINT=https://it-commodities.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-01

DEBUG_MODE=false
EOF
```

#### 3.3 Criar serviço systemd do backend

Arquivo `/etc/systemd/system/nw-multi-backend.service`:

```ini
[Unit]
Description=NW Multi Backend (FastAPI)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/nw_multi/backend
EnvironmentFile=/etc/nw_multi_backend.env
ExecStart=/opt/nw_multi/backend/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 3.4 Ativar e iniciar backend

```bash
sudo systemctl daemon-reload
sudo systemctl enable nw-multi-backend
sudo systemctl start nw-multi-backend
sudo systemctl status nw-multi-backend
```

Teste rápido na própria EC2:

```bash
curl http://localhost:8000/
```

---

### 4. Configurar e rodar o frontend

#### 4.1 Instalar dependências e fazer build (como `ubuntu`)

```bash
cd /opt/nw_multi/frontend
npm install

# API do backend vista pelo browser (ajuste o host/proxy):
NEXT_PUBLIC_API_URL=http://SEU_HOST_OU_PROXY:8000 npm run build
```

#### 4.2 Criar serviço systemd do frontend

Arquivo `/etc/systemd/system/nw-multi-frontend.service`:

```ini
[Unit]
Description=NW Multi Frontend (Next.js)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/nw_multi/frontend
Environment=NODE_ENV=production
Environment=NEXT_PUBLIC_API_URL=http://SEU_HOST_OU_PROXY:8000
ExecStart=/usr/bin/npm start -- --port 3000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4.3 Ativar e iniciar frontend

```bash
sudo systemctl daemon-reload
sudo systemctl enable nw-multi-frontend
sudo systemctl start nw-multi-frontend
sudo systemctl status nw-multi-frontend
```

Teste rápido:

```bash
curl http://localhost:3000/
```

---

### 5. (Opcional) Nginx como reverse proxy

#### 5.1 Configuração básica de Nginx

Arquivo `/etc/nginx/sites-available/nw_multi`:

```nginx
server {
    listen 80;
    server_name SEU_DOMINIO_OU_IP;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        proxy_buffering off;  # ajuda no streaming SSE
    }

    location / {
        proxy_pass http://127.0.0.1:3000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ativar site e recarregar:

```bash
sudo ln -s /etc/nginx/sites-available/nw_multi /etc/nginx/sites-enabled/nw_multi
sudo nginx -t
sudo systemctl reload nginx
```

#### 5.2 Ajustar `NEXT_PUBLIC_API_URL`

Se o frontend estiver em `http://SEU_DOMINIO/` e o backend por trás de `/api`, use no build:

```bash
NEXT_PUBLIC_API_URL=http://SEU_DOMINIO npm run build
```

O código do frontend já acrescenta `/api/newave`, `/api/decomp`, `/api/dessem` sobre essa base.

---

### 6. Parar, atualizar e reiniciar (deploy de novas versões)

- **Parar serviços (derrubar app)**:

```bash
sudo systemctl stop nw-multi-frontend
sudo systemctl stop nw-multi-backend
```

- **Atualizar código** (via git), como `ubuntu`:

```bash
cd /opt/nw_multi
git pull
```

- **Reinstalar dependências se necessário**:

Backend:

```bash
cd /opt/nw_multi/backend
source .venv/bin/activate
pip install -r requirements.txt
```

Frontend:

```bash
cd /opt/nw_multi/frontend
npm install
NEXT_PUBLIC_API_URL=http://SEU_DOMINIO npm run build
```

- **Subir novamente**:

```bash
sudo systemctl start nw-multi-backend
sudo systemctl start nw-multi-frontend
```

Ou, para recarregar com segurança após mudanças:

```bash
sudo systemctl restart nw-multi-backend
sudo systemctl restart nw-multi-frontend
```

---

### 7. Smoke tests básicos após deploy

- `curl http://SEU_DOMINIO/` → deve retornar a página do frontend.
- `curl http://SEU_DOMINIO/api/newave/` → deve responder (ou 404 controlado) via backend.
- No navegador interno da intranet:
  - Acessar a UI, subir um deck e fazer uma query que use RAG, verificando se a resposta vem sem erros de Azure/OpenAI.

