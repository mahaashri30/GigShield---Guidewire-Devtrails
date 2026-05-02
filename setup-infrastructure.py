"""
SUSANOO INFRASTRUCTURE SETUP SCRIPT
Sets up PostgreSQL, Redis, and Tesseract-OCR for Windows
"""

import os
import subprocess
import sys
from pathlib import Path


def print_header(title):
    """Print formatted section header"""
    print("\n" + "╔" + "═" * 66 + "╗")
    print("║" + title.center(66) + "║")
    print("╚" + "═" * 66 + "╝")


def check_docker():
    """Check if Docker is installed"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Docker found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    return False


def setup_postgresql(docker_available):
    """Set up PostgreSQL"""
    print_header("STEP 1: Setting up PostgreSQL Database")
    
    if docker_available:
        print("\n📦 Starting PostgreSQL Docker container...")
        try:
            # Check if container already exists
            subprocess.run(
                ["docker", "rm", "susanoo-postgres"],
                capture_output=True
            )
        except:
            pass
        
        cmd = [
            "docker", "run", "-d",
            "--name", "susanoo-postgres",
            "-p", "5432:5432",
            "-e", "POSTGRES_USER=susanoo",
            "-e", "POSTGRES_PASSWORD=susanoo_password",
            "-e", "POSTGRES_DB=susanoo",
            "-v", "susanoo-postgres-data:/var/lib/postgresql/data",
            "postgres:15"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ PostgreSQL container started!")
                print("\n   Connection Details:")
                print("   ├─ Host: localhost")
                print("   ├─ Port: 5432")
                print("   ├─ User: susanoo")
                print("   ├─ Password: susanoo_password")
                print("   └─ Database: susanoo")
                return True
            else:
                print(f"❌ Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    else:
        print("\n⚠️  Docker not found. Manual installation needed:")
        print("   1. Download: https://www.postgresql.org/download/windows/")
        print("   2. Use default port 5432 and password: susanoo_password")
        return False


def setup_redis(docker_available):
    """Set up Redis"""
    print_header("STEP 2: Setting up Redis Cache Server")
    
    if docker_available:
        print("\n📦 Starting Redis Docker container...")
        try:
            # Check if container already exists
            subprocess.run(
                ["docker", "rm", "susanoo-redis"],
                capture_output=True
            )
        except:
            pass
        
        cmd = [
            "docker", "run", "-d",
            "--name", "susanoo-redis",
            "-p", "6379:6379",
            "redis:7-alpine"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Redis container started!")
                print("\n   Connection Details:")
                print("   ├─ Host: localhost")
                print("   └─ Port: 6379")
                
                # Test connection
                try:
                    test_result = subprocess.run(
                        ["docker", "exec", "susanoo-redis", "redis-cli", "ping"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if "PONG" in test_result.stdout:
                        print("\n✅ Redis is responding correctly!")
                except:
                    pass
                return True
            else:
                print(f"❌ Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    else:
        print("\n⚠️  Docker not found. Cannot set up Redis.")
        print("   Please install Docker Desktop first.")
        return False


def setup_tesseract():
    """Check/guide Tesseract setup"""
    print_header("STEP 3: Checking Tesseract-OCR Installation")
    
    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract found: {version}")
            return True
    except FileNotFoundError:
        pass
    
    print("\n⚠️  Tesseract-OCR not found in PATH")
    print("\n📥 Manual Installation Instructions:")
    print("   1. Download: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   2. Run: tesseract-ocr-w64-setup-v5.*.exe")
    print("   3. Default installation path: C:\\Program Files\\Tesseract-OCR")
    print("   4. Restart PowerShell after installation")
    
    return False


def setup_env_file():
    """Create .env file for backend"""
    print_header("STEP 4: Creating Environment Variables File")
    
    backend_dir = Path("c:/Users/vdmah/OneDrive/Desktop/Susanoo/backend")
    env_file = backend_dir / ".env"
    
    env_content = """# Database Configuration
DATABASE_URL=postgresql+asyncpg://susanoo:susanoo_password@localhost:5432/susanoo
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=susanoo
DATABASE_PASSWORD=susanoo_password
DATABASE_NAME=susanoo

# Redis Configuration
REDIS_URL=redis://localhost:6379
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT Configuration
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# OTP Configuration (2Factor.in)
OTP_API_KEY=your_2factor_api_key_here

# Gemini AI Configuration (Optional - for enhanced OCR)
GEMINI_API_KEY=your_gemini_api_key_here

# Tesseract Configuration
TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe

# Application Configuration
APP_NAME=Susanoo
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000

# AWS/Firebase Configuration (Optional)
# FIREBASE_PROJECT_ID=your_project_id
# FIREBASE_PRIVATE_KEY=your_private_key
# FIREBASE_CLIENT_EMAIL=your_client_email
"""
    
    try:
        env_file.write_text(env_content)
        print(f"\n✅ Created {env_file}")
        print("\n   ⚠️  IMPORTANT: Update these API keys before production:")
        print("      - OTP_API_KEY (get from 2Factor.in)")
        print("      - GEMINI_API_KEY (get from Google Cloud Console)")
        print("      - JWT_SECRET (use a strong random key)")
        return True
    except Exception as e:
        print(f"❌ Error creating .env: {e}")
        return False


def verify_setup(docker_available):
    """Verify all components are set up"""
    print_header("STEP 5: Verifying Infrastructure Setup")
    
    checks = []
    
    # Check Docker containers
    if docker_available:
        print("\n📋 Docker Containers Status:")
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=susanoo", "--format", "table {{.Names}}\\t{{.Status}}"],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            checks.append(True)
        except:
            checks.append(False)
    
    # Check Tesseract
    print("\n📋 Tesseract-OCR Status:")
    try:
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {result.stdout.split(chr(10))[0]}")
            checks.append(True)
        else:
            print("❌ Tesseract not found")
            checks.append(False)
    except:
        print("❌ Tesseract not found in PATH")
        checks.append(False)
    
    # Check .env file
    print("\n📋 Environment Configuration:")
    env_path = Path("c:/Users/vdmah/OneDrive/Desktop/Susanoo/backend/.env")
    if env_path.exists():
        print(f"✅ .env file created: {env_path}")
        checks.append(True)
    else:
        print("❌ .env file not found")
        checks.append(False)
    
    return all(checks)


def print_next_steps():
    """Print next steps"""
    print_header("INFRASTRUCTURE SETUP COMPLETE!")
    
    print("\n🚀 NEXT STEPS:\n")
    print("1️⃣  Update .env file with your API keys:")
    print("   Location: backend\\.env")
    print("   Keys to update:")
    print("      - OTP_API_KEY (from 2Factor.in)")
    print("      - GEMINI_API_KEY (from Google Cloud)")
    print("      - JWT_SECRET (generate a strong key)")
    
    print("\n2️⃣  Start the backend server:")
    print("   cd backend")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    print("\n3️⃣  Run verification tests:")
    print("   python test_verification_system.py")
    print("   python test_verification_advanced.py")
    
    print("\n4️⃣  Access API documentation:")
    print("   http://localhost:8000/docs")
    
    print("\n5️⃣  Test the endpoints:")
    print("   POST /api/v1/verify/phone")
    print("   POST /api/v1/verify/partner-id")
    print("   POST /api/v1/verify/selfie")
    print("   POST /api/v1/verify/govt-id")
    print("   GET /api/v1/verify/status")
    
    print("\n📚 Documentation:")
    print("   - Test Summary: backend/TEST_SUMMARY.md")
    print("   - Full Report: backend/VERIFICATION_SYSTEM_REPORT.txt")
    print("   - API Endpoints: backend/app/api/verification.py")
    print("   - GitHub Branch: feature/verification-system-setup")


def main():
    """Main setup function"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║   SUSANOO INFRASTRUCTURE SETUP SCRIPT (Windows)                ║")
    print("║   Setting up PostgreSQL, Redis, and Tesseract-OCR             ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    # Check Docker availability
    docker_available = check_docker()
    
    if not docker_available:
        print("\n⚠️  Docker not found. Some components cannot be set up automatically.")
        print("   Download Docker Desktop: https://www.docker.com/products/docker-desktop")
    
    # Run setup steps
    pg_ok = setup_postgresql(docker_available)
    redis_ok = setup_redis(docker_available)
    tesseract_ok = setup_tesseract()
    env_ok = setup_env_file()
    
    # Verify setup
    all_ok = verify_setup(docker_available)
    
    # Print next steps
    print_next_steps()
    
    print("\n" + "═" * 66)
    print("✅ Setup complete! You can now start the backend server.")
    print("═" * 66 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
