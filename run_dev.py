#!/usr/bin/env python3
"""
Development startup script for FBX to MDL Converter
This script runs the application in development mode without Docker
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    # Check Python packages
    try:
        import flask
        import magic
        print("✅ Python dependencies OK")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("Install with: pip install -r backend/requirements.txt")
        return False
    
    # Check Blender
    try:
        result = subprocess.run(['blender', '--version'], 
                              capture_output=True, timeout=10)
        if result.returncode == 0:
            print("✅ Blender OK")
        else:
            print("❌ Blender not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Blender not found")
        print("Install Blender and add to PATH")
        return False
    
    # Check Wine
    try:
        result = subprocess.run(['wine', '--version'], 
                              capture_output=True, timeout=10)
        if result.returncode == 0:
            print("✅ Wine OK")
        else:
            print("❌ Wine not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Wine not found")
        print("Install Wine for studiomdl.exe support")
        return False
    
    # Check studiomdl.exe
    studiomdl_path = "/usr/local/wine/cstrike/studiomdl.exe"
    if os.path.exists(studiomdl_path):
        print("✅ studiomdl.exe found")
    else:
        print(f"⚠️  studiomdl.exe not found at {studiomdl_path}")
        print("The application will run but MDL compilation will fail")
    
    return True

def setup_environment():
    """Setup development environment"""
    print("🔧 Setting up environment...")
    
    # Create necessary directories
    os.makedirs("backend/uploads", exist_ok=True)
    os.makedirs("backend/outputs", exist_ok=True)
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    os.environ['PYTHONPATH'] = os.path.abspath('backend')
    
    # Wine environment
    wine_prefix = os.path.expanduser('~/.wine')
    os.environ['WINEPREFIX'] = wine_prefix
    os.environ['WINEARCH'] = 'win32'
    
    print("✅ Environment setup complete")

def run_application(host='localhost', port=5000, debug=True):
    """Run the Flask application"""
    print(f"🚀 Starting FBX to MDL Converter on {host}:{port}")
    print(f"🌐 Open your browser to: http://{host}:{port}")
    print("🛑 Press Ctrl+C to stop")
    
    # Change to backend directory
    os.chdir('backend')
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(host=host, port=port, debug=debug, threaded=True)
    except ImportError:
        print("❌ Failed to import Flask application")
        print("Make sure you're in the correct directory and dependencies are installed")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped")
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

def run_tests():
    """Run basic functionality tests"""
    print("🧪 Running basic tests...")
    
    os.chdir('backend')
    
    try:
        from fbx_processor import FBXProcessor
        from utils import SecurityValidator, RateLimiter
        
        print("✅ Import test passed")
        
        # Test FBXProcessor
        processor = FBXProcessor()
        is_valid, errors = processor.validate_requirements()
        
        if is_valid:
            print("✅ FBX processor validation passed")
        else:
            print("⚠️  FBX processor validation warnings:")
            for error in errors:
                print(f"   - {error}")
        
        # Test SecurityValidator
        validator = SecurityValidator()
        print("✅ Security validator initialized")
        
        # Test RateLimiter
        rate_limiter = RateLimiter()
        print("✅ Rate limiter initialized")
        
        print("✅ All tests passed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='FBX to MDL Converter Development Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--no-debug', action='store_true', help='Disable debug mode')
    parser.add_argument('--test', action='store_true', help='Run tests instead of starting server')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies only')
    
    args = parser.parse_args()
    
    print("🎯 FBX to MDL Converter - Development Mode")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        sys.exit(1)
    
    if args.check_deps:
        print("\n✅ All dependencies are satisfied")
        return
    
    # Setup environment
    setup_environment()
    
    if args.test:
        if run_tests():
            print("\n✅ All tests passed - ready for development")
        else:
            print("\n❌ Tests failed")
            sys.exit(1)
        return
    
    # Run application
    try:
        run_application(
            host=args.host,
            port=args.port,
            debug=not args.no_debug
        )
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()