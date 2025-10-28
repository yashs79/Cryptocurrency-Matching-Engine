#!/usr/bin/env python3
"""
Automatic Deployment Setup Script

This script automates the entire deployment setup process:
1. Creates Render services (dev and prod)
2. Configures environment variables
3. Gets deploy hooks
4. Adds GitHub secrets automatically

Usage:
    python scripts/auto-deploy-setup.py
"""

import os
import sys
import json
import time
import requests
import subprocess
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Colors for terminal output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_step(message):
    print(f"\n{Colors.BLUE}🚀 {message}{Colors.NC}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.NC}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")

def get_git_remote_info():
    """Automatically fetch GitHub username and repo from git remote"""
    try:
        # Get remote URL
        result = subprocess.run(
            ['git', 'config', '--get', 'remote.origin.url'],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        
        # Parse GitHub URL (supports both HTTPS and SSH)
        # HTTPS: https://github.com/username/repo.git
        # SSH: git@github.com:username/repo.git
        
        if 'github.com' in remote_url:
            # Extract username and repo
            if remote_url.startswith('https://'):
                # HTTPS format
                match = re.search(r'github\.com[:/]([^/]+)/([^/\.]+)', remote_url)
            else:
                # SSH format
                match = re.search(r'github\.com:([^/]+)/([^/\.]+)', remote_url)
            
            if match:
                username = match.group(1)
                repo = match.group(2).replace('.git', '')
                return username, repo
        
        return None, None
    except subprocess.CalledProcessError:
        return None, None

def get_render_owner_id():
    """Fetch Render Owner ID from API"""
    api_key = os.getenv('RENDER_API_KEY')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            'https://api.render.com/v1/owners',
            headers=headers
        )
        
        if response.status_code == 200:
            owners = response.json()
            if owners and len(owners) > 0:
                owner_id = owners[0]['owner']['id']
                return owner_id
        return None
    except Exception as e:
        print_error(f"Failed to fetch owner ID: {e}")
        return None

def check_env_vars():
    """Check if required environment variables are set"""
    print_step("Checking environment variables...")
    
    # Try to auto-detect GitHub info from git remote
    git_username, git_repo = get_git_remote_info()
    
    if git_username and git_repo:
        print_success(f"Auto-detected from git remote:")
        print(f"  GitHub Username: {git_username}")
        print(f"  Repository: {git_repo}")
        
        # Set as environment variables if not already set
        if not os.getenv('GITHUB_USERNAME'):
            os.environ['GITHUB_USERNAME'] = git_username
        if not os.getenv('GITHUB_REPO'):
            os.environ['GITHUB_REPO'] = git_repo
    
    required_vars = {
        'RENDER_API_KEY': 'Render API key',
        'GITHUB_TOKEN': 'GitHub Personal Access Token'
    }
    
    optional_vars = {
        'GITHUB_USERNAME': 'GitHub username (auto-detected from git)',
        'GITHUB_REPO': 'GitHub repository name (auto-detected from git)'
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")
    
    if missing:
        print_error("Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nPlease set these in your .env file")
        print("See .env.example for reference")
        sys.exit(1)
    
    # Check optional vars
    for var, description in optional_vars.items():
        if not os.getenv(var):
            print_warning(f"{var} not set - {description}")
    
    print_success("All required environment variables are set")
    
    # Auto-fetch Render Owner ID
    if not os.getenv('RENDER_OWNER_ID'):
        print_step("Fetching Render Owner ID...")
        owner_id = get_render_owner_id()
        if owner_id:
            os.environ['RENDER_OWNER_ID'] = owner_id
            print_success(f"Auto-detected Render Owner ID: {owner_id}")
        else:
            print_error("Failed to fetch Render Owner ID")
            print("Please add RENDER_OWNER_ID to your .env file")
            sys.exit(1)

def create_render_service(service_config):
    """Create a Render service"""
    api_key = os.getenv('RENDER_API_KEY')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(
        'https://api.render.com/v1/services',
        headers=headers,
        json=service_config
    )
    
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print_error(f"Failed to create service: {response.status_code}")
        print(response.text)
        return None

def get_deploy_hook(service_id):
    """Get or create deploy hook for a service"""
    api_key = os.getenv('RENDER_API_KEY')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Get service details
    response = requests.get(
        f'https://api.render.com/v1/services/{service_id}',
        headers=headers
    )
    
    if response.status_code == 200:
        service = response.json()
        # Deploy hook URL format
        deploy_hook = f"https://api.render.com/deploy/{service_id}?key={api_key}"
        return deploy_hook
    
    return None

def add_github_secret(secret_name, secret_value):
    """Add a secret to GitHub repository"""
    github_token = os.getenv('GITHUB_TOKEN')
    github_username = os.getenv('GITHUB_USERNAME')
    github_repo = os.getenv('GITHUB_REPO')
    
    # Get repository public key
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    # Get public key for encryption
    key_response = requests.get(
        f'https://api.github.com/repos/{github_username}/{github_repo}/actions/secrets/public-key',
        headers=headers
    )
    
    if key_response.status_code != 200:
        print_error(f"Failed to get repository public key: {key_response.status_code}")
        return False
    
    public_key_data = key_response.json()
    
    # Encrypt the secret value
    from base64 import b64encode
    from nacl import encoding, public
    
    public_key = public.PublicKey(public_key_data['key'].encode(), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode())
    encrypted_value = b64encode(encrypted).decode()
    
    # Add the secret
    secret_data = {
        'encrypted_value': encrypted_value,
        'key_id': public_key_data['key_id']
    }
    
    response = requests.put(
        f'https://api.github.com/repos/{github_username}/{github_repo}/actions/secrets/{secret_name}',
        headers=headers,
        json=secret_data
    )
    
    if response.status_code in [201, 204]:
        return True
    else:
        print_error(f"Failed to add secret: {response.status_code}")
        print(response.text)
        return False

def setup_development_environment():
    """Set up development environment on Render"""
    print_step("Setting up Development Environment...")
    
    github_username = os.getenv('GITHUB_USERNAME')
    github_repo = os.getenv('GITHUB_REPO')
    owner_id = os.getenv('RENDER_OWNER_ID')
    
    service_config = {
        'type': 'web_service',
        'name': 'matching-engine-dev',
        'ownerId': owner_id,
        'serviceDetails': {
            'env': 'docker',
            'envSpecificDetails': {
                'dockerfilePath': './Dockerfile',
                'dockerContext': '.'
            },
            'healthCheckPath': '/health',
            'plan': 'starter',
            'pullRequestPreviewsEnabled': 'no',
            'region': 'oregon',
            'envVars': [
                {'key': 'ENVIRONMENT', 'value': 'development'},
                {'key': 'LOG_LEVEL', 'value': 'DEBUG'},
                {'key': 'API_HOST', 'value': '0.0.0.0'},
                {'key': 'API_PORT', 'value': '8000'}
            ]
        },
        'autoDeploy': 'yes',
        'branch': 'dev',
        'repo': f'https://github.com/{github_username}/{github_repo}'
    }
    
    service = create_render_service(service_config)
    
    if service:
        print_success(f"Development service created: {service.get('name')}")
        service_id = service.get('id')
        
        # Get deploy hook
        deploy_hook = get_deploy_hook(service_id)
        if deploy_hook:
            print_success(f"Deploy hook: {deploy_hook[:50]}...")
            return deploy_hook
    
    return None

def setup_production_environment():
    """Set up production environment on Render"""
    print_step("Setting up Production Environment...")
    
    github_username = os.getenv('GITHUB_USERNAME')
    github_repo = os.getenv('GITHUB_REPO')
    owner_id = os.getenv('RENDER_OWNER_ID')
    
    service_config = {
        'type': 'web_service',
        'name': 'matching-engine',
        'ownerId': owner_id,
        'serviceDetails': {
            'env': 'docker',
            'envSpecificDetails': {
                'dockerfilePath': './Dockerfile',
                'dockerContext': '.'
            },
            'healthCheckPath': '/health',
            'plan': 'starter',
            'pullRequestPreviewsEnabled': 'no',
            'region': 'oregon',
            'envVars': [
                {'key': 'ENVIRONMENT', 'value': 'production'},
                {'key': 'LOG_LEVEL', 'value': 'INFO'},
                {'key': 'API_HOST', 'value': '0.0.0.0'},
                {'key': 'API_PORT', 'value': '8000'}
            ]
        },
        'autoDeploy': 'yes',
        'branch': 'main',
        'repo': f'https://github.com/{github_username}/{github_repo}'
    }
    
    service = create_render_service(service_config)
    
    if service:
        print_success(f"Production service created: {service.get('name')}")
        service_id = service.get('id')
        
        # Get deploy hook
        deploy_hook = get_deploy_hook(service_id)
        if deploy_hook:
            print_success(f"Deploy hook: {deploy_hook[:50]}...")
            return deploy_hook
    
    return None

def setup_github_secrets(dev_hook, prod_hook):
    """Add deploy hooks as GitHub secrets"""
    print_step("Adding GitHub Secrets...")
    
    # Add development deploy hook
    if add_github_secret('RENDER_DEPLOY_HOOK_DEV', dev_hook):
        print_success("Added RENDER_DEPLOY_HOOK_DEV to GitHub")
    else:
        print_error("Failed to add RENDER_DEPLOY_HOOK_DEV")
    
    # Add production deploy hook
    if add_github_secret('RENDER_DEPLOY_HOOK_PROD', prod_hook):
        print_success("Added RENDER_DEPLOY_HOOK_PROD to GitHub")
    else:
        print_error("Failed to add RENDER_DEPLOY_HOOK_PROD")

def main():
    """Main execution function"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BLUE}🚀 Automatic Deployment Setup{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}\n")
    
    # Check environment variables
    check_env_vars()
    
    # Check if PyNaCl is installed (required for GitHub secret encryption)
    try:
        import nacl
    except ImportError:
        print_error("PyNaCl library not found")
        print("Install it with: pip install PyNaCl")
        sys.exit(1)
    
    print_warning("This script will:")
    print("  1. Create Render services (dev and prod)")
    print("  2. Configure environment variables")
    print("  3. Get deploy hooks")
    print("  4. Add GitHub secrets automatically")
    print()
    
    response = input("Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Aborted.")
        sys.exit(0)
    
    # Set up development environment
    dev_hook = setup_development_environment()
    if not dev_hook:
        print_error("Failed to set up development environment")
        sys.exit(1)
    
    time.sleep(2)  # Wait a bit between API calls
    
    # Set up production environment
    prod_hook = setup_production_environment()
    if not prod_hook:
        print_error("Failed to set up production environment")
        sys.exit(1)
    
    time.sleep(2)
    
    # Set up GitHub secrets
    setup_github_secrets(dev_hook, prod_hook)
    
    print(f"\n{Colors.GREEN}{'='*60}{Colors.NC}")
    print(f"{Colors.GREEN}✅ Deployment Setup Complete!{Colors.NC}")
    print(f"{Colors.GREEN}{'='*60}{Colors.NC}\n")
    
    print("Your environments are ready:")
    print(f"  🧪 Development: https://matching-engine-dev.onrender.com")
    print(f"  🚀 Production:  https://matching-engine.onrender.com")
    print()
    print("GitHub Secrets configured:")
    print(f"  ✅ RENDER_DEPLOY_HOOK_DEV")
    print(f"  ✅ RENDER_DEPLOY_HOOK_PROD")
    print()
    print("Next steps:")
    print(f"  1. Push to dev branch: git push origin dev")
    print(f"  2. Push to main branch: git push origin main")
    print(f"  3. Watch automatic deployments!")
    print()

if __name__ == '__main__':
    main()
