#!/usr/bin/env python3
"""
Project Structure Validator
Ensures all required files and directories exist
"""

import os
import sys

def check_structure():
    """Validate project structure"""
    
    required_structure = {
        'backend': {
            'type': 'dir',
            'files': [
                'app.py',
                'database.py',
                'requirements.txt',
                'Dockerfile',
                '.env.example',
                'STARTUP_GUIDE.md'
            ],
            'dirs': [
                'indicators',
                'utils',
                'data',
                'logs',
                'venv'
            ]
        },
        'frontend': {
            'type': 'dir',
            'files': [
                'package.json',
                'start-frontend.bat',
                'Dockerfile',
                '.env.example',
                '.env.local',
                'STARTUP_GUIDE.md',
                'tailwind.config.js',
                'postcss.config.js'
            ],
            'dirs': [
                'src',
                'public',
                'node_modules'
            ]
        },
        'Prerequisite': {
            'type': 'dir',
            'dirs': [
                'node-v20.19.5-win-x64'
            ],
            'files': [
                'README.md'
            ]
        },
        'docs': [
            'README.md',
            'START_HERE.md',
            'INDEX.md',
            'QUICKSTART.md',
            'INSTALLATION.md',
            'RUN_LOCALHOST.md',
            'TROUBLESHOOTING.md',
            'API_TESTING.md',
            'QUICK_REFERENCE.md',
            'PROJECT_STRUCTURE.md',
            'PROJECT_SUMMARY.md',
            'PERFORMANCE.md',
            'PERFORMANCE_SUMMARY.md',
            'DISTRIBUTION.md',
            'CHANGELOG.md'
        ],
        'config': [
            '.gitignore',
            'docker-compose.yml',
            'setup.ps1',
            'setup.sh',
            'cleanup.ps1',
            'TheTool.code-workspace'
        ]
    }
    
    print("Validating Project Structure")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Check backend structure
    print("\n?? Backend:")
    if os.path.isdir('backend'):
        print("  ? backend/ exists")
        
        for file in required_structure['backend']['files']:
            path = os.path.join('backend', file)
            if os.path.exists(path):
                print(f"  ? {file}")
            else:
                print(f"  ? {file} - MISSING")
                if file == 'venv':
                    warnings.append(f"backend/{file} - Run setup.ps1")
                else:
                    errors.append(f"backend/{file}")
        
        for dir_name in required_structure['backend']['dirs']:
            path = os.path.join('backend', dir_name)
            if os.path.isdir(path):
                print(f"  ? {dir_name}/")
            else:
                print(f"  ? {dir_name}/ - MISSING")
                if dir_name in ['venv', 'data', 'logs']:
                    warnings.append(f"backend/{dir_name}/ - Created on first run")
                else:
                    errors.append(f"backend/{dir_name}/")
    else:
        print("  ? backend/ - MISSING")
        errors.append("backend/")
    
    # Check frontend structure
    print("\n??  Frontend:")
    if os.path.isdir('frontend'):
        print("  ? frontend/ exists")
        
        for file in required_structure['frontend']['files']:
            path = os.path.join('frontend', file)
            if os.path.exists(path):
                print(f"  ? {file}")
            else:
                print(f"  ? {file} - MISSING")
                if file == 'node_modules':
                    warnings.append(f"frontend/{file} - Run setup.ps1")
                elif file == '.env.local':
                    warnings.append(f"frontend/{file} - Created by setup")
                else:
                    errors.append(f"frontend/{file}")
        
        for dir_name in required_structure['frontend']['dirs']:
            path = os.path.join('frontend', dir_name)
            if os.path.isdir(path):
                print(f"  ? {dir_name}/")
            else:
                print(f"  ? {dir_name}/ - MISSING")
                if dir_name == 'node_modules':
                    warnings.append(f"frontend/{dir_name}/ - Run npm install")
                else:
                    errors.append(f"frontend/{dir_name}/")
    else:
        print("  ? frontend/ - MISSING")
        errors.append("frontend/")
    
    # Check Prerequisite
    print("\n?? Prerequisites:")
    if os.path.isdir('Prerequisite'):
        print("  ? Prerequisite/ exists")
        
        node_path = 'Prerequisite/node-v20.19.5-win-x64'
        if os.path.isdir(node_path):
            print("  ? node-v20.19.5-win-x64/")
            if os.path.exists(os.path.join(node_path, 'node.exe')):
                print("  ? node.exe")
            else:
                print("  ? node.exe - MISSING")
                errors.append("node.exe in bundled Node.js")
        else:
            print("  ? node-v20.19.5-win-x64/ - MISSING")
            errors.append("Bundled Node.js")
    else:
        print("  ? Prerequisite/ - MISSING")
        errors.append("Prerequisite/")
    
    # Check documentation
    print("\n?? Documentation:")
    for doc in required_structure['docs']:
        if os.path.exists(doc):
            print(f"  ? {doc}")
        else:
            print(f"  ? {doc} - MISSING")
            errors.append(doc)
    
    # Check config files
    print("\n??  Configuration:")
    for config in required_structure['config']:
        if os.path.exists(config):
            print(f"  ? {config}")
        else:
            print(f"  ? {config} - MISSING")
            errors.append(config)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    if not errors and not warnings:
        print("? All files and directories present!")
        print("?? Project structure is valid!")
        return 0
    
    if warnings:
        print(f"\n??  {len(warnings)} Warning(s):")
        for warning in warnings:
            print(f"  - {warning}")
    
    if errors:
        print(f"\n? {len(errors)} Error(s):")
        for error in errors:
            print(f"  - {error}")
        print("\n?? Some files are missing. Please check the project package.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(check_structure())
