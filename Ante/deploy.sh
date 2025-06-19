#!/bin/bash

# EC2 Deployment Script for Flask Store Management System
echo " Starting deployment of Flask Store Management System..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx supervisor postgresql postgresql-contrib

# Create application directory
sudo mkdir -p /var/www/store-management
cd /var/www/store-management

# Create virtual environment
sudo python3 -m venv venv
sudo chown -R $USER:$USER /var/www/store-management

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Setup PostgreSQL
sudo -u postgres psql << 'EOF'
CREATE DATABASE storedb;
CREATE USER storeuser WITH PASSWORD 'SecurePassword123';
GRANT ALL PRIVILEGES ON DATABASE storedb TO storeuser;
\q
EOF

# Create environment file
cat > .env << 'EOF'
FLASK_APP=run.py
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-change-this
DATABASE_URL=postgresql://storeuser:SecurePassword123@localhost/storedb
EOF

# Initialize database
export FLASK_APP=run.py
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Create initial admin user and sample data
python3 run.py --init-data

# Create Gunicorn configuration
cat > gunicorn.conf.py << 'EOF'
bind = "127.0.0.1:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
timeout = 30
keepalive = 2
preload_app = True
EOF

# Create Supervisor configuration
sudo tee /etc/supervisor/conf.d/store-management.conf << 'EOF'
[program:store-management]
command=/var/www/store-management/venv/bin/gunicorn --config gunicorn.conf.py run:app
directory=/var/www/store-management
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/store-management.log
environment=PATH="/var/www/store-management/venv/bin"
EOF

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/store-management << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/store-management/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/store-management /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Set permissions
sudo chown -R www-data:www-data /var/www/store-management
sudo chmod -R 755 /var/www/store-management

# Start services
sudo systemctl reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start store-management
sudo systemctl restart nginx

# Enable services
sudo systemctl enable supervisor
sudo systemctl enable nginx
sudo systemctl enable postgresql

# Configure firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable

echo "✅ Deployment completed!"
echo "🌐 Access your store at: http://$(curl -s ifconfig.me)"
echo "🔐 Login with: admin / StoreAdmin2025!"