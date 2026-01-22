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
from dotenv import load_dotenv
from prettytable import PrettyTable

def check_certbot():
    """Check if certbot is installed"""
    try:
        subprocess.run(['certbot', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def reload_nginx():
    """Reload nginx configuration"""
    try:
        subprocess.run(['sudo', 'systemctl', 'reload', 'nginx'], check=True)
        print("Nginx reloaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to reload nginx: {e}")

def install_certbot():
    """Install certbot if not present"""
    print("Certbot not found. Installing...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'certbot'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install certbot: {e}")
        sys.exit(1)

def obtain_certificate(domain, email, webroot=None, update_nginx=False):
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
        if update_nginx:
            reload_nginx()
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to obtain certificate: {e}")
        print(f"Error output: {e.stderr}")
        return False

def list_certificates():
    """List all certificates managed by certbot"""
    if not check_certbot():
        print("Certbot is not installed.")
        return

    try:
        result = subprocess.run(['certbot', 'certificates'], capture_output=True, text=True, check=True)
        output = result.stdout

        # Parse the output
        certificates = []
        lines = output.split('\n')
        i = 0
        while i < len(lines):
            if lines[i].startswith('  Certificate Name:'):
                cert_name = lines[i].split(':', 1)[1].strip()
                domains = ''
                expiry = ''
                status = ''
                i += 1
                while i < len(lines) and not lines[i].startswith('  Certificate Name:') and lines[i].strip():
                    if lines[i].startswith('    Domains:'):
                        domains = lines[i].split(':', 1)[1].strip()
                    elif lines[i].startswith('    Expiry Date:'):
                        expiry_line = lines[i].split(':', 1)[1].strip()
                        expiry = expiry_line.split(' (')[0].strip()
                        status = expiry_line.split(' (')[1].rstrip(')') if ' (' in expiry_line else ''
                    i += 1
                certificates.append({
                    'Certificate Name': cert_name,
                    'Domains': domains,
                    'Expiry Date': expiry,
                    'Status': status
                })
            else:
                i += 1

        if not certificates:
            print("No certificates found.")
            return

        # Create table
        table = PrettyTable()
        table.field_names = ['Certificate Name', 'Domains', 'Expiry Date', 'Status']
        for cert in certificates:
            table.add_row([cert['Certificate Name'], cert['Domains'], cert['Expiry Date'], cert['Status']])

        print("Certificates managed by Certbot:")
        print(table)

    except subprocess.CalledProcessError as e:
        print(f"Failed to list certificates: {e}")
        print(f"Error output: {e.stderr}")

def check_certificate_status(domain):
    """Check if certificate exists for domain and return days remaining or None"""
    cert_path = f"/etc/letsencrypt/live/{domain}/cert.pem"

    if not os.path.exists(cert_path):
        print(f"Certificate for domain {domain} does not exist.")
        return None

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

        days = time_remaining.days
        hours = time_remaining.seconds // 3600
        minutes = (time_remaining.seconds % 3600) // 60

        if time_remaining.total_seconds() <= 0:
            print(f"Certificate for domain {domain} has expired.")
            print(f"Expired on: {end_date}")
            return 0
        else:
            print(f"Certificate for domain {domain} exists.")
            print(f"Expires on: {end_date}")
            print(f"Time remaining: {days} days, {hours} hours, {minutes} minutes")
            return days

    except subprocess.CalledProcessError as e:
        print(f"Failed to check certificate: {e}")
        return None
    except ValueError as e:
        print(f"Failed to parse certificate date: {e}")
        return None

def auto_update_certificates():
    """Automatically check and renew certificates for all domains in config"""
    load_dotenv()

    domains_str = os.getenv('DOMAINS')
    email = os.getenv('EMAIL')
    threshold_days = int(os.getenv('THRESHOLD_DAYS', 30))
    webroot = os.getenv('WEBROOT', '').strip() or None
    use_certbot = os.getenv('USE_CERTBOT', 'true').lower() == 'true'
    update_nginx = os.getenv('UPDATE_NGINX', 'true').lower() == 'true'

    if not domains_str:
        print("Error: DOMAINS not set in .env")
        sys.exit(1)
    if not email:
        print("Error: EMAIL not set in .env")
        sys.exit(1)

    domains = [d.strip() for d in domains_str.split(',') if d.strip()]

    if not use_certbot:
        print("Certbot usage is disabled in configuration.")
        return

    if not check_certbot():
        install_certbot()

    for domain in domains:
        print(f"\nChecking certificate for {domain}...")
        days_remaining = check_certificate_status(domain)
        if days_remaining is None:
            print(f"No certificate found for {domain}. Obtaining new certificate...")
            success = obtain_certificate(domain, email, webroot, update_nginx)
            if not success:
                print(f"Failed to obtain certificate for {domain}")
        elif days_remaining <= threshold_days:
            print(f"Certificate for {domain} expires in {days_remaining} days (<= {threshold_days}). Renewing...")
            success = obtain_certificate(domain, email, webroot, update_nginx)
            if not success:
                print(f"Failed to renew certificate for {domain}")
        else:
            print(f"Certificate for {domain} is valid for {days_remaining} days. No renewal needed.")

def main():
    # Load environment variables
    load_dotenv()

    # Check if running in manual mode (with args) or auto mode
    if len(sys.argv) > 1:
        # Manual mode with command line arguments
        parser = argparse.ArgumentParser(description="Auto-obtain Let's Encrypt SSL certificate, check certificate status, or list certificates")
        parser.add_argument('--domain', help="Domain name for the certificate (required for --check or obtaining)")
        parser.add_argument('--email', help="Email address for Let's Encrypt registration (required for obtaining certificate)")
        parser.add_argument('--webroot', help="Webroot path for webroot authentication (optional)")
        parser.add_argument('--check', action='store_true', help="Check certificate status instead of obtaining new certificate")
        parser.add_argument('--list', action='store_true', help="List all certificates managed by certbot")

        args = parser.parse_args()

        if args.list:
            # List all certificates
            list_certificates()
        elif args.check:
            # Check certificate status
            if not args.domain:
                print("Error: --domain is required for --check")
                sys.exit(1)
            check_certificate_status(args.domain)
        else:
            # Obtain certificate
            if not args.domain or not args.email:
                print("Error: --domain and --email are required when obtaining a certificate")
                sys.exit(1)

            if not check_certbot():
                install_certbot()

            success = obtain_certificate(args.domain, args.email, args.webroot)
            if success:
                print("Certificate renewal setup completed.")
            else:
                sys.exit(1)
    else:
        # Auto mode using .env configuration
        auto_update_certificates()

if __name__ == '__main__':
    main()
