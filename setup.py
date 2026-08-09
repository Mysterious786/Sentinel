"""
Sentinel setup script - Complete development environment setup
"""
import os
import sys
import subprocess
import asyncio
from pathlib import Path


def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🛡️  {title}")
    print(f"{'='*60}")


def print_step(step, description):
    """Print a formatted step"""
    print(f"\n{step}. {description}")
    print("-" * 40)


def run_command(command, description="", check=True):
    """Run a shell command with error handling"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def check_prerequisites():
    """Check if required tools are installed"""
    print_step(1, "Checking Prerequisites")
    
    requirements = [
        ("python3", "Python 3.11+"),
        ("pip", "Python Package Manager"),
        ("node", "Node.js 18+"),
        ("npm", "Node Package Manager")
    ]
    
    missing = []
    for cmd, name in requirements:
        if not run_command(f"which {cmd}", check=False):
            missing.append(name)
        else:
            print(f"✅ {name} found")
    
    if missing:
        print(f"\n❌ Missing requirements: {', '.join(missing)}")
        print("\nPlease install the missing requirements and run setup again.")
        return False
    
    print("\n✅ All prerequisites satisfied")
    return True


def setup_python_environment():
    """Set up Python virtual environment and dependencies"""
    print_step(2, "Setting up Python Environment")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print("Creating virtual environment...")
        if not run_command("python3 -m venv venv"):
            return False
    else:
        print("Virtual environment already exists")
    
    # Install Python dependencies
    print("Installing Python dependencies...")
    pip_cmd = "venv/bin/pip" if os.name != 'nt' else "venv\\Scripts\\pip"
    
    if not run_command(f"{pip_cmd} install --upgrade pip"):
        return False
    
    print("Installing core requirements...")
    if not run_command(f"{pip_cmd} install -r requirements.txt"):
        return False
    
    # Install optional dependencies for better embeddings
    print("Installing optional AI packages...")
    optional_packages = [
        "sentence-transformers",
        "openai",
        "torch --index-url https://download.pytorch.org/whl/cpu"
    ]
    
    for package in optional_packages:
        print(f"Installing {package}...")
        # Don't fail setup if optional packages fail
        run_command(f"{pip_cmd} install {package}", check=False)
    
    print("✅ Python environment setup complete")
    return True


def setup_frontend():
    """Set up the React frontend"""
    print_step(3, "Setting up Frontend")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install npm dependencies
    print("Installing Node.js dependencies...")
    if not run_command("npm install", check=False):  # npm install can have warnings
        print("⚠️  npm install completed with warnings (this is often normal)")
    
    print("✅ Frontend setup complete")
    return True


def setup_environment_file():
    """Create environment configuration file"""
    print_step(4, "Setting up Environment Configuration")
    
    env_file = Path(".env")
    if env_file.exists():
        print("Environment file already exists")
        return True
    
    print("Creating .env file from template...")
    
    # Copy from example
    try:
        with open(".env.example", "r") as f:
            content = f.read()
        
        with open(".env", "w") as f:
            f.write(content)
        
        print("✅ Environment file created")
        print("\n⚠️  IMPORTANT: Please edit .env file with your actual configuration:")
        print("   - CockroachDB connection string")
        print("   - AWS credentials and region")
        print("   - Other service configurations")
        
        return True
    
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def display_next_steps():
    """Display next steps for the user"""
    print_step(5, "Setup Complete! Next Steps")
    
    print("""
🎉 Sentinel is ready for development!

Next steps:

1. Check your credential setup:
   python check_credentials.py

2. Configure your environment (optional):
   - Edit .env file with your CockroachDB connection string
   - Set up AWS credentials (aws configure)
   - Add OpenAI API key for better embeddings

3. Set up the database (if using CockroachDB):
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   python scripts/setup_database.py

4. Start the development servers:

   Backend API:
   python local_server.py

   Frontend (in another terminal):
   cd frontend && npm start

5. Test your setup:
   python test_sentinel.py

6. Demo the system:
   python scripts/demo_data_generator.py credential_stuffing

7. Deploy to AWS (when ready):
   ./scripts/deploy.sh

📚 Documentation:
   - README.md - Complete project documentation
   - CREDENTIALS_SETUP.md - Detailed credential guide  
   - ARCHITECTURE.md - Technical deep dive
   - DEMO.md - Presentation guide

🌐 URLs (once running):
   - API Server: http://localhost:8000
   - Dashboard: http://localhost:3000
   - Health Check: http://localhost:8000/health

🚀 Embedding Provider Options:
   1. AWS Bedrock (best, requires AWS account)
   2. OpenAI (good, requires API key)  
   3. Local models (works offline, already installed)
   4. Mock data (instant demo, no setup)

🔐 Database Options:
   1. CockroachDB Cloud (best, free tier available)
   2. Local PostgreSQL (good for development)
   3. Mock data (instant demo, no setup)

🎭 For a quick demo without any setup:
   Just run 'python local_server.py' - it will use local embeddings and mock data!
""")


def main():
    """Main setup function"""
    print_header("SENTINEL SETUP")
    print("Persistent Threat Hunter - Development Environment Setup")
    
    try:
        # Check prerequisites
        if not check_prerequisites():
            sys.exit(1)
        
        # Setup Python environment
        if not setup_python_environment():
            print("❌ Python environment setup failed")
            sys.exit(1)
        
        # Setup frontend
        os.chdir("frontend")
        frontend_success = setup_frontend()
        os.chdir("..")
        
        if not frontend_success:
            print("❌ Frontend setup failed")
            sys.exit(1)
        
        # Setup environment file
        if not setup_environment_file():
            print("❌ Environment setup failed")
            sys.exit(1)
        
        # Display next steps
        display_next_steps()
        
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()