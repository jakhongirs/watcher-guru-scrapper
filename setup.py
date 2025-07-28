#!/usr/bin/env python3
"""
Setup script for WatcherGuru Telegram Monitor
"""

import os
import sys
import subprocess

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def create_env_file():
    """Create .env file from template"""
    if os.path.exists(".env"):
        print("⚠️  .env file already exists. Skipping creation.")
        return True
    
    if os.path.exists("config_template.txt"):
        try:
            with open("config_template.txt", "r") as template:
                content = template.read()
            
            with open(".env", "w") as env_file:
                env_file.write(content)
            
            print("✅ .env file created from template!")
            print("📝 Please edit .env file with your actual credentials before running the monitor.")
            return True
        except Exception as e:
            print(f"❌ Error creating .env file: {e}")
            return False
    else:
        print("❌ config_template.txt not found!")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up WatcherGuru Telegram Monitor...")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your Telegram API credentials")
    print("2. Get API credentials from: https://my.telegram.org/apps")
    print("3. Set your destination channel in DESTINATION_CHANNEL")
    print("4. Run: python telegram_monitor.py")
    print("\n📖 For detailed instructions, see README.md")

if __name__ == "__main__":
    main() 