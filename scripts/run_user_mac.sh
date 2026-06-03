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
python3 ParallelCrawler.py --user "$1"

# Auto-commit and merge JobDataBank.ods changes
REPO_ROOT="$(pwd)"
JOB_DATA_BANK="$REPO_ROOT/data/JobDataBank.ods"

if [ -f "$JOB_DATA_BANK" ]; then
    echo ""
    echo "Checking for JobDataBank.ods changes..."
    
    if git status --porcelain | grep -q "data/JobDataBank.ods"; then
        echo "Changes detected in JobDataBank.ods. Committing..."
        git add "data/JobDataBank.ods"
        TIMESTAMP=$(date '+%Y-%m-%d %H%M%S')
        git commit -m "Auto-update JobDataBank.ods from $1 run $TIMESTAMP"
        echo "Changes committed successfully."
    else
        echo "No changes in JobDataBank.ods."
    fi
fi