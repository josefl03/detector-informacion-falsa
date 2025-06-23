echo "⚠️ Run this script with sudo or as root user ⚠️"
echo "Python 3.12 must be installed before running"
echo ""

# Install deps
apt install ffmpeg

# Install requirements
pip install -r requirements.txt

# Install fake_news_detector library
pip install -r libreria/fake_news_detector

# Install playwright
playwright install-deps
playwright install

# Install MongoDB 8.0 for Ubuntu 24.04
apt-get install gnupg curl
curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | \
   gpg -o /usr/share/keyrings/mongodb-server-8.0.gpg \
   --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-8.0.list

apt-get update
apt-get install -y mongodb-org
systemctl enable --now mongodb

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
systemctl enable --now ollama

ollama pull all-minilm