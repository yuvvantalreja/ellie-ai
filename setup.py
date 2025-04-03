#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil
from getpass import getpass

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("\nInstalling dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("Error: Failed to install dependencies")
        sys.exit(1)

def setup_env_file():
    """Set up the .env file with API key"""
    if os.path.exists(".env"):
        print("\n.env file already exists. Do you want to overwrite it? (y/n): ", end="")
        if input().lower() != 'y':
            print("Skipping .env file setup")
            return

    print("\nSetting up .env file...")
    api_key = getpass("Enter your Groq API key: ")
    
    if not api_key:
        print("No API key provided. You can add it later to the .env file.")
        api_key = "your_api_key_here"
    
    model = input("Enter Groq model name (default: llama3-70b-8192): ")
    if not model:
        model = "llama3-70b-8192"
    
    materials_dir = input("Enter course materials directory (default: course_materials): ")
    if not materials_dir:
        materials_dir = "course_materials"
    
    with open(".env", "w") as f:
        f.write(f"GROQ_API_KEY={api_key}\n")
        f.write(f"GROQ_MODEL={model}\n")
        f.write(f"MATERIALS_DIR={materials_dir}\n")
    
    print(".env file created successfully!")

def setup_directories():
    """Set up necessary directories"""
    print("\nSetting up directories...")
    os.makedirs("course_materials", exist_ok=True)
    os.makedirs("vectorstores", exist_ok=True)
    
    # Create a demo course if it doesn't exist
    demo_dir = os.path.join("course_materials", "DEMO101")
    if not os.path.exists(demo_dir):
        os.makedirs(demo_dir, exist_ok=True)
        
        # Create a sample text file for the demo course
        with open(os.path.join(demo_dir, "introduction.txt"), "w") as f:
            f.write("""# Introduction to DEMO101
            
This is a sample course file to demonstrate the AI Teaching Assistant.

Key Topics:
1. Introduction to Artificial Intelligence
2. Machine Learning Fundamentals
3. Neural Networks
4. Natural Language Processing
5. Retrieval-Augmented Generation

The final project involves building a simple AI system that can answer questions based on a knowledge base.
            """)
        
        print("Created demo course DEMO101 with sample material")
    
    print("Directories set up successfully!")

def main():
    """Main setup function"""
    print("=" * 50)
    print("AI Teaching Assistant Setup")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Set up .env file
    setup_env_file()
    
    # Set up directories
    setup_directories()
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("=" * 50)
    print("\nTo start the web interface, run: python web_app.py")
    print("To start the command-line interface, run: python cli.py --course COURSE_ID")
    print("\nFor more information, see the README.md file.")

if __name__ == "__main__":
    main() 