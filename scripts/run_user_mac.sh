# Check Git
if ! command -v git &> /dev/null
then
    echo "Installing Git..."
    brew install git
fi

# Check Python
if ! command -v python3 &> /dev/null
then
    echo "Installing Python..."
    brew install python
fi

# Create venv
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Activate
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install Playwright
playwright install chromium

# Pull latest code
git pull origin main

# Run crawler
python3 ParallelCrawler.py --user "$USER"

# Push results
git add .
git commit -m "$USER run"
git push origin main