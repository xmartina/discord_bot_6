
import ssl
import certifi
import os

# Use certifi certificates
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# If that fails, disable verification as a last resort
ssl._create_default_https_context = ssl._create_unverified_context
