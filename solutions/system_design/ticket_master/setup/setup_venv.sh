#!/bin/bash
# Setup script for Ticketmaster Elasticsearch environment

set -e

echo "🐍 Setting up Python Virtual Environment for Ticketmaster Experiments"
echo "=================================================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup Complete!"
echo "=================================================================="
echo ""
echo "🚀 Next Steps:"
echo "1. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Start Elasticsearch:"
echo "   docker compose up -d"
echo ""
echo "3. Run setup:"
echo "   python setup_experiment.py"
echo ""
echo "4. Load data:"
echo "   python ingest_sample_data.py"
echo ""
echo "5. Run experiments:"
echo "   python experiments.py --experiment search"
echo ""
echo "💡 To deactivate the virtual environment later, run: deactivate"