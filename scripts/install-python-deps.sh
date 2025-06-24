echo "⚠️ Run this script with sudo or as root user ⚠️"
echo "Python 3.12 must be installed before running"
echo ""

# Install deps
apt update -y
apt install -y ffmpeg

# Install requirements
pip install -r requirements.txt

# Install fake_news_detector library
pip install -e libreria/fake_news_detector
pip install playwright

# Install playwright
yes | playwright install-deps
yes | playwright install