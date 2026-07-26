#!/usr/bin/env python3
"""
Setup Verification Script
Checks if the development environment is properly configured
"""

import os
import sys
import subprocess
from pathlib import Path

def check_command(cmd, version_flag="--version"):
    """Check if a command exists and return its version"""
    try:
        result = subprocess.run(
            [cmd, version_flag],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() or result.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

def check_file_exists(path, description):
    """Check if a file exists"""
    if Path(path).exists():
        return f"✅ {description}: {path}"
    else:
        return f"❌ {description}: {path} (NOT FOUND)"

def check_directory_exists(path, description):
    """Check if a directory exists"""
    if Path(path).is_dir():
        return f"✅ {description}: {path}"
    else:
        return f"❌ {description}: {path} (NOT FOUND)"

def main():
    print("=" * 60)
    print("CodeForge AI - Setup Verification")
    print("=" * 60)
    print()
    
    # Check system requirements
    print("📋 System Requirements:")
    print("-" * 60)
    
    requirements = {
        "Node.js": ("node", "--version"),
        "npm": ("npm", "--version"),
        "Python": ("python3", "--version"),
        "Python (v2)": ("python", "--version"),
        "Docker": ("docker", "--version"),
        "Docker Compose": ("docker-compose", "--version"),
        "Git": ("git", "--version"),
    }
    
    system_ok = True
    for name, (cmd, flag) in requirements.items():
        version = check_command(cmd, flag)
        if version:
            print(f"✅ {name}: {version}")
        else:
            print(f"❌ {name}: NOT FOUND")
            system_ok = False
    
    print()
    
    # Check project structure
    print("📁 Project Structure:")
    print("-" * 60)
    
    structure_checks = [
        ("frontend", "Frontend directory"),
        ("backend", "Backend directory"),
        ("docker", "Docker directory"),
        ("docs", "Documentation directory"),
        (".github", "GitHub workflows directory"),
        (".vscode", "VSCode configuration directory"),
    ]
    
    structure_ok = True
    for path, description in structure_checks:
        result = check_directory_exists(path, description)
        print(result)
        if "❌" in result:
            structure_ok = False
    
    print()
    
    # Check configuration files
    print("⚙️ Configuration Files:")
    print("-" * 60)
    
    config_checks = [
        ("frontend/package.json", "Frontend package.json"),
        ("frontend/tsconfig.json", "Frontend TypeScript config"),
        ("frontend/next.config.ts", "Next.js config"),
        ("frontend/tailwind.config.ts", "Tailwind config"),
        ("backend/requirements.txt", "Backend requirements"),
        ("backend/pyproject.toml", "Backend pyproject"),
        ("docker-compose.yml", "Docker Compose config"),
        (".env.example", "Environment template"),
        (".gitignore", "Git ignore rules"),
        ("README.md", "README"),
        ("Makefile", "Makefile"),
    ]
    
    config_ok = True
    for path, description in config_checks:
        result = check_file_exists(path, description)
        print(result)
        if "❌" in result:
            config_ok = False
    
    print()
    
    # Check Python environment
    print("🐍 Python Environment:")
    print("-" * 60)
    
    python_version = check_command("python3", "--version")
    if python_version:
        print(f"✅ Python version: {python_version}")
        # Check if >= 3.12
        if "3.12" in python_version or "3.13" in python_version:
            print("✅ Python 3.12+ detected")
        else:
            print("⚠️  Python 3.12+ recommended")
    else:
        print("❌ Python not found")
    
    venv_exists = Path("backend/venv").is_dir()
    if venv_exists:
        print("✅ Virtual environment exists")
    else:
        print("❌ Virtual environment not found (run: cd backend && python -m venv venv)")
    
    print()
    
    # Check Node environment
    print("📦 Node.js Environment:")
    print("-" * 60)
    
    node_version = check_command("node", "--version")
    if node_version:
        print(f"✅ Node.js version: {node_version}")
        # Check if >= 18.17
        version_parts = node_version.replace("v", "").split(".")
        major = int(version_parts[0])
        if major >= 18:
            print("✅ Node.js 18+ detected")
        else:
            print("⚠️  Node.js 18+ recommended")
    else:
        print("❌ Node.js not found")
    
    frontend_deps = Path("frontend/node_modules").is_dir()
    if frontend_deps:
        print("✅ Node modules installed")
    else:
        print("❌ Node modules not found (run: cd frontend && npm install)")
    
    print()
    
    # Check Docker
    print("🐳 Docker Environment:")
    print("-" * 60)
    
    docker_version = check_command("docker", "--version")
    if docker_version:
        print(f"✅ Docker version: {docker_version}")
    else:
        print("❌ Docker not found")
    
    docker_compose_version = check_command("docker-compose", "--version")
    if docker_compose_version:
        print(f"✅ Docker Compose version: {docker_compose_version}")
    else:
        print("❌ Docker Compose not found")
    
    print()
    
    # Summary
    print("=" * 60)
    print("📊 Summary:")
    print("=" * 60)
    
    if system_ok and structure_ok and config_ok:
        print("✅ All checks passed!")
        print()
        print("Next steps:")
        print("  1. Review GETTING_STARTED.md for detailed setup")
        print("  2. Copy .env.example to .env: cp .env.example .env")
        print("  3. Install dependencies: make install")
        print("  4. Start services: make dev")
        print()
        return 0
    else:
        print("⚠️  Some checks failed. Please review the output above.")
        print()
        print("Common fixes:")
        print("  - Install missing system requirements")
        print("  - Create Python virtual environment: python3 -m venv backend/venv")
        print("  - Install frontend dependencies: cd frontend && npm install")
        print("  - Install backend dependencies: cd backend && source venv/bin/activate && pip install -r requirements.txt")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
