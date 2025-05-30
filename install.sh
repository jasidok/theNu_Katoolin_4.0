#!/bin/bash
#
# Installation script for Katoolin
# This script checks for dependencies, installs the application,
# and provides configuration options.

set -e

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/katoolin"
APP_NAME="katoolin"
PYTHON_MIN_VERSION="3.10"
REQUIRED_PACKAGES=("python3" "python3-pip" "python3-tk" "apt-transport-https" "gnupg" "curl")

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_message "$RED" "Error: This script must be run as root (sudo)."
        exit 1
    fi
}

# Function to check Python version
check_python_version() {
    print_message "$BLUE" "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_message "$RED" "Error: Python 3 is not installed. Please install Python 3 and try again."
        exit 1
    fi
    
    local python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_message "$GREEN" "Found Python version: $python_version"
    
    if [ "$(printf '%s\n' "$PYTHON_MIN_VERSION" "$python_version" | sort -V | head -n1)" != "$PYTHON_MIN_VERSION" ]; then
        print_message "$RED" "Error: Python version must be at least $PYTHON_MIN_VERSION"
        exit 1
    fi
}

# Function to check and install required packages
check_dependencies() {
    print_message "$BLUE" "Checking dependencies..."
    
    local missing_packages=()
    for package in "${REQUIRED_PACKAGES[@]}"; do
        if ! dpkg -l | grep -q "ii  $package "; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_message "$YELLOW" "The following required packages are missing and will be installed:"
        for package in "${missing_packages[@]}"; do
            echo "  - $package"
        done
        
        read -p "Do you want to install these packages? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_message "$BLUE" "Installing missing packages..."
            apt-get update
            apt-get install -y "${missing_packages[@]}"
        else
            print_message "$RED" "Installation cancelled. Required packages must be installed."
            exit 1
        fi
    else
        print_message "$GREEN" "All required packages are already installed."
    fi
    
    # Check for required Python packages
    print_message "$BLUE" "Checking Python packages..."
    pip3 install -q --upgrade pip
    
    # Install required Python packages
    pip3 install -q tkinter
}

# Function to check if the system is Debian/Ubuntu based
check_system() {
    print_message "$BLUE" "Checking system compatibility..."
    
    if [ ! -f /etc/debian_version ]; then
        print_message "$YELLOW" "Warning: This system does not appear to be Debian/Ubuntu based."
        print_message "$YELLOW" "Katoolin is designed for Debian/Ubuntu systems and may not work correctly on other distributions."
        
        read -p "Do you want to continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_message "$RED" "Installation cancelled."
            exit 1
        fi
    else
        print_message "$GREEN" "System is Debian/Ubuntu based. Continuing installation."
    fi
}

# Function to install the application
install_application() {
    print_message "$BLUE" "Installing Katoolin..."
    
    # Create directories if they don't exist
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    
    # Copy files
    cp -r ./* "$CONFIG_DIR/"
    
    # Create executable script
    cat > "$INSTALL_DIR/$APP_NAME" << EOF
#!/bin/bash
cd "$CONFIG_DIR" && sudo python3 NuKatoo4.py "\$@"
EOF
    
    # Make the script executable
    chmod +x "$INSTALL_DIR/$APP_NAME"
    
    print_message "$GREEN" "Katoolin has been installed successfully!"
    print_message "$GREEN" "You can now run it by typing 'sudo katoolin' in your terminal."
}

# Function to create a desktop entry
create_desktop_entry() {
    print_message "$BLUE" "Creating desktop entry..."
    
    cat > "/usr/share/applications/katoolin.desktop" << EOF
[Desktop Entry]
Name=Katoolin
Comment=Kali Linux Tools Installer
Exec=sudo $INSTALL_DIR/$APP_NAME
Icon=$CONFIG_DIR/icon.png
Terminal=true
Type=Application
Categories=System;Security;
EOF
    
    print_message "$GREEN" "Desktop entry created. Katoolin should now appear in your applications menu."
}

# Function to configure the application
configure_application() {
    print_message "$BLUE" "Configuring Katoolin..."
    
    # Ask if user wants to add Kali repositories automatically
    read -p "Do you want to add Kali Linux repositories during installation? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message "$YELLOW" "Adding Kali Linux repositories..."
        cd "$CONFIG_DIR" && sudo python3 -c "
from core.repository import RepositoryManager
repo_manager = RepositoryManager()
repo_manager.add_repository()
repo_manager.add_key()
repo_manager.update_repositories()
"
        print_message "$GREEN" "Kali Linux repositories added successfully."
    else
        print_message "$YELLOW" "Skipping repository configuration. You can add repositories later using Katoolin."
    fi
    
    # Ask if user wants to start the GUI version by default
    read -p "Do you want to use the GUI version by default? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Update the executable script to start the GUI
        cat > "$INSTALL_DIR/$APP_NAME" << EOF
#!/bin/bash
cd "$CONFIG_DIR" && sudo python3 -c "
import sys
sys.path.insert(0, '$CONFIG_DIR')
from core.gui import main
main()
" "\$@"
EOF
        chmod +x "$INSTALL_DIR/$APP_NAME"
        print_message "$GREEN" "Katoolin will start in GUI mode by default."
    else
        print_message "$YELLOW" "Katoolin will start in CLI mode by default."
    fi
}

# Function to uninstall the application
uninstall_application() {
    print_message "$BLUE" "Uninstalling Katoolin..."
    
    # Ask if user wants to remove Kali repositories
    read -p "Do you want to remove Kali Linux repositories? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message "$YELLOW" "Removing Kali Linux repositories..."
        cd "$CONFIG_DIR" && sudo python3 -c "
from core.repository import RepositoryManager
repo_manager = RepositoryManager()
repo_manager.delete_repository()
"
        print_message "$GREEN" "Kali Linux repositories removed successfully."
    fi
    
    # Remove files
    rm -f "$INSTALL_DIR/$APP_NAME"
    rm -f "/usr/share/applications/katoolin.desktop"
    rm -rf "$CONFIG_DIR"
    
    print_message "$GREEN" "Katoolin has been uninstalled successfully."
}

# Main function
main() {
    print_message "$BLUE" "Katoolin Installation Script"
    print_message "$BLUE" "============================"
    
    # Check if uninstall flag is provided
    if [ "$1" == "--uninstall" ]; then
        check_root
        uninstall_application
        exit 0
    fi
    
    # Check if help flag is provided
    if [ "$1" == "--help" ]; then
        print_message "$GREEN" "Usage: $0 [OPTIONS]"
        print_message "$GREEN" "Options:"
        print_message "$GREEN" "  --uninstall    Uninstall Katoolin"
        print_message "$GREEN" "  --help         Show this help message"
        exit 0
    fi
    
    # Perform installation checks
    check_root
    check_system
    check_python_version
    check_dependencies
    
    # Install and configure the application
    install_application
    create_desktop_entry
    configure_application
    
    print_message "$GREEN" "Installation completed successfully!"
    print_message "$GREEN" "Run 'sudo katoolin' to start the application."
}

# Run the main function with all arguments
main "$@"