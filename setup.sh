#!/bin/bash

echo "Desktop Utility GUI Setup"
echo "========================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv venv

if [ ! -d "venv" ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo
echo "Activating virtual environment..."
source venv/bin/activate

echo
echo "Upgrading pip..."
python -m pip install --upgrade pip

echo
echo "Installing required packages..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "Error: Failed to install some packages"
    echo "Please check the error messages above"
    exit 1
fi

echo
echo "========================="
echo "Setup completed successfully!"
echo "========================="
echo

# Ask about startup (Linux/Mac)
echo "Would you like to run Desktop Utility GUI automatically when your system starts?"
read -p "Enter Y for Yes, N for No (default: N): " startup_choice

if [[ "$startup_choice" =~ ^[Yy]$ ]]; then
    echo
    echo "Setting up automatic startup..."
    
    # Activate virtual environment and try to enable startup
    source venv/bin/activate
    
    # Check the operating system
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - create desktop entry for autostart
        mkdir -p ~/.config/autostart
        cat > ~/.config/autostart/desktop-utility-gui.desktop << EOF
[Desktop Entry]
Type=Application
Name=Desktop Utility GUI
Exec=$(pwd)/run.sh --minimized
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Comment=Desktop Utility GUI Application
EOF
        echo "Desktop Utility GUI will now start automatically on Linux login."
        echo "You can disable this by removing ~/.config/autostart/desktop-utility-gui.desktop"
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - create LaunchAgent
        mkdir -p ~/Library/LaunchAgents
        cat > ~/Library/LaunchAgents/com.desktop-utility-gui.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.desktop-utility-gui</string>
    <key>ProgramArguments</key>
    <array>
        <string>$(pwd)/run.sh</string>
        <string>--minimized</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardErrorPath</key>
    <string>/tmp/desktop-utility-gui.err</string>
    <key>StandardOutPath</key>
    <string>/tmp/desktop-utility-gui.out</string>
</dict>
</plist>
EOF
        launchctl load ~/Library/LaunchAgents/com.desktop-utility-gui.plist 2>/dev/null
        echo "Desktop Utility GUI will now start automatically on macOS login."
        echo "You can disable this with: launchctl unload ~/Library/LaunchAgents/com.desktop-utility-gui.plist"
    else
        echo "Note: Automatic startup configuration not available for this OS."
        echo "You can manually add $(pwd)/run.sh to your system's startup applications."
    fi
else
    echo
    echo "Automatic startup not enabled. You can configure it later if needed."
fi

echo
echo "========================="
echo "To run the application:"
echo "  1. Run: source venv/bin/activate"
echo "  2. Run: python main.py"
echo
echo "Or simply run: ./run.sh"
echo "========================="