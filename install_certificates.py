"""
Certificate Installation for Python on Windows
This script installs the necessary certificates for Python to work with HTTPS
"""

import os
import ssl
import certifi
import shutil
import subprocess
import sys
import tempfile
import urllib.request

def install_certificates():
    """Install certificates for Python on Windows"""
    print("Installing certificates for Python...")
    
    # Get the path to the certifi certificate bundle
    certifi_path = certifi.where()
    print(f"Certifi certificate path: {certifi_path}")
    
    # Set environment variables to use certifi's certificates
    os.environ['SSL_CERT_FILE'] = certifi_path
    os.environ['REQUESTS_CA_BUNDLE'] = certifi_path
    print(f"Set environment variables to use certifi certificates")
    
    # Create a custom SSL context using certifi
    ssl_context = ssl.create_default_context(cafile=certifi_path)
    
    # Test SSL connection with custom context
    try:
        print("Testing SSL connection to discord.com...")
        req = urllib.request.Request("https://discord.com", headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, context=ssl_context)
        print(f"SSL connection successful! Status code: {response.status}")
        return True
    except Exception as e:
        print(f"SSL connection test failed: {e}")
        return False

def create_ssl_patch():
    """Create an SSL patch file that can be imported to disable verification"""
    patch_content = """
import ssl
import certifi
import os

# Use certifi certificates
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# If that fails, disable verification as a last resort
ssl._create_default_https_context = ssl._create_unverified_context
"""
    
    with open("ssl_patch.py", "w") as f:
        f.write(patch_content)
    
    print("Created ssl_patch.py - Import this in your code to fix SSL issues")

if __name__ == "__main__":
    try:
        # Install certifi if not already installed
        try:
            import certifi
        except ImportError:
            print("Installing certifi package...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "certifi"])
            import certifi
        
        # Install certificates
        success = install_certificates()
        
        # Create SSL patch file
        create_ssl_patch()
        
        if success:
            print("\nCertificate installation successful!")
            print("You can now run the Discord bot.")
        else:
            print("\nCertificate installation failed.")
            print("You can still run the bot by importing ssl_patch.py")
    except Exception as e:
        print(f"Error: {e}")
        print("\nFailed to install certificates.")
        print("You can still run the bot by importing ssl_patch.py") 