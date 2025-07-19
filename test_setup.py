#!/usr/bin/env python3
"""
Simple setup verification for YouTube Video Finder
Tests essential dependencies and system requirements
"""

import sys
import importlib
from colorama import init, Fore, Style

# Initialize colorama
init()

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"{Fore.GREEN}✓ {package_name or module_name}{Style.RESET_ALL}")
        return True
    except ImportError:
        print(f"{Fore.RED}❌ {package_name or module_name} - MISSING{Style.RESET_ALL}")
        return False

def main():
    """Run essential setup tests"""
    print(f"{Fore.MAGENTA}🧪 YouTube Video Finder - Setup Verification{Style.RESET_ALL}")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info >= (3, 8):
        print(f"{Fore.GREEN}✓ Python {sys.version_info.major}.{sys.version_info.minor}{Style.RESET_ALL}")
        python_ok = True
    else:
        print(f"{Fore.RED}❌ Python {sys.version_info.major}.{sys.version_info.minor} - Requires 3.8+{Style.RESET_ALL}")
        python_ok = False
    
    # Test essential dependencies
    dependencies = [
        ('selenium', 'Selenium'),
        ('webdriver_manager', 'WebDriver Manager'),
        ('google.generativeai', 'Gemini AI'),
        ('speech_recognition', 'Speech Recognition'),
        ('pyaudio', 'PyAudio'),
        ('googletrans', 'Google Translate'),
        ('colorama', 'Colorama'),
        ('tqdm', 'TQDM')
    ]
    
    print(f"\n{Fore.CYAN}Testing dependencies...{Style.RESET_ALL}")
    failed = []
    for module, name in dependencies:
        if not test_import(module, name):
            failed.append(name)
    
    # Summary
    print(f"\n{'=' * 50}")
    if python_ok and not failed:
        print(f"{Fore.GREEN}🎉 Setup verified! Run: python youtube_video_finder.py{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️ Issues found:{Style.RESET_ALL}")
        if not python_ok:
            print("   - Upgrade Python to 3.8+")
        if failed:
            print("   - Install missing packages: pip install -r requirements.txt")

if __name__ == "__main__":
    main() 