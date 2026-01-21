#!/usr/bin/env python3
"""
Auto-update TLS Certificate Script using Certbot
This script automates the process of obtaining Let's Encrypt SSL certificates using Certbot
and provides functionality to check certificate existence and expiration status.
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime

def check_certbot():
    """Check if certbot is installed"""
    try:
        subprocess.run(['certbot', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_certbot():
    """Install certbot if not present"""
    print("Certbot not found. Installing...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'certbot'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install certbot: {e}")
        sys.exit(1)

def obtain_certificate(domain, email, webroot=None):
    """Obtain SSL certificate using certbot"""
    cmd = ['certbot', 'certonly', '--agree-tos', '--email', email]

    if webroot:
        # Webroot authentication
        cmd.extend(['--webroot', '-w', webroot, '-d', domain])
    else:
        # Standalone authentication (requires port 80 to be free)
        cmd.extend(['--standalone', '-d', domain])

    print(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Certificate obtained successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to obtain certificate: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_certificate_status(domain):
    """Check if certificate exists for domain and show expiration info"""
    cert_path = f"/etc/letsencrypt/live/{domain}/cert.pem"

    if not os.path.exists(cert_path):
        print(f"Certificate for domain {domain} does not exist.")
        return False

    try:
        # Get certificate expiration date using openssl
        cmd = ['openssl', 'x509', '-in', cert_path, '-noout', '-enddate']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse the expiration date
        # Output format: notAfter=Dec 31 23:59:59 2024 GMT
        end_date_str = result.stdout.strip().split('=')[1]
        end_date = datetime.strptime(end_date_str, '%b %d %H:%M:%S %Y %Z')

        now = datetime.now()
        time_remaining = end_date - now

        if time_remaining.total_seconds() <= 0:
            print(f"Certificate for domain {domain} has expired.")
            print(f"Expired on: {end_date}")
        else:
            days = time_remaining.days
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            print(f"Certificate for domain {domain} exists.")
            print(f"Expires on: {end_date}")
            print(f"Time remaining: {days} days, {hours} hours, {minutes} minutes")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Failed to check certificate: {e}")
        return False
    except ValueError as e:
        print(f"Failed to parse certificate date: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Auto-obtain Let's Encrypt SSL certificate or check certificate status")
    parser.add_argument('--domain', required=True, help="Domain name for the certificate")
    parser.add_argument('--email', help="Email address for Let's Encrypt registration (required for obtaining certificate)")
    parser.add_argument('--webroot', help="Webroot path for webroot authentication (optional)")
    parser.add_argument('--check', action='store_true', help="Check certificate status instead of obtaining new certificate")

    args = parser.parse_args()

    if args.check:
        # Check certificate status
        check_certificate_status(args.domain)
    else:
        # Obtain certificate
        if not args.email:
            print("Error: --email is required when obtaining a certificate")
            sys.exit(1)

        if not check_certbot():
            install_certbot()

        success = obtain_certificate(args.domain, args.email, args.webroot)
        if success:
            print("Certificate renewal setup completed.")
        else:
            sys.exit(1)

if __name__ == '__main__':
    main()
