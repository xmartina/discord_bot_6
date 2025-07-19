# SSL Fix for Discord Bot

This document explains how to fix SSL certificate verification issues with the Discord bot on Windows servers, particularly on AWS EC2 instances.

## The Problem

When running the Discord bot on certain Windows environments, especially AWS EC2 instances, you may encounter SSL certificate verification errors like:

```
SSLCertVerificationError: (5, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)')
```

This happens because the Windows environment doesn't have the proper root certificates installed or accessible to Python.

## The Solution

We've implemented several fixes to address this issue:

1. **Certificate Installation**: The `install_certificates.py` script installs proper certificates using the `certifi` package.

2. **SSL Patch**: The `ssl_patch.py` file is imported at the beginning of `main.py` to ensure SSL works correctly.

3. **Environment Variables**: The `start_bot_ssl_fixed.bat` script sets the necessary environment variables to use the correct certificates.

## How to Use

1. **Install Certificates**:
   ```
   .\install_certificates.bat
   ```
   This will install the `certifi` package and create the SSL patch file.

2. **Start the Bot**:
   ```
   .\start_bot_ssl_fixed.bat
   ```
   This will start the bot with the proper SSL configuration.

## Technical Details

The fix works by:

1. Using the certificates from the `certifi` package
2. Setting the appropriate environment variables (`SSL_CERT_FILE` and `REQUESTS_CA_BUNDLE`)
3. As a fallback, disabling SSL verification entirely if needed

## Security Note

Disabling SSL verification is not recommended for production environments as it makes your application vulnerable to man-in-the-middle attacks. The proper solution is to install the correct root certificates on your system.

However, in some environments like AWS EC2 instances, this may be difficult to configure, so this workaround is provided to get the bot running.

## Files Added

- `install_certificates.py`: Script to install certificates
- `install_certificates.bat`: Batch file to run the certificate installation
- `ssl_patch.py`: Python module that fixes SSL verification
- `start_bot_ssl_fixed.bat`: Batch file to start the bot with SSL fix
- `SSL_FIX_README.md`: This documentation file 