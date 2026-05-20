#!/usr/bin/env python3
"""
Script pentru build Flet Windows - cu workaround pentru fisierele 'nul'
"""
import os
import shutil
import subprocess
import tempfile

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
FLUTTER_DIR = os.path.join(os.path.expanduser("~"), "flutter", "3.38.7")
FLET_EXE = os.path.join(PROJECT_DIR, "venv", "Scripts", "flet.exe")

def clean_build():
    """Curata si pregatete proiectul pentru build"""
    
    # Creeaza director temporar curat
    temp_dir = tempfile.mkdtemp(prefix="flet_build_")
    print(f"[INFO] Director temporar: {temp_dir}")
    
    # Listeaza ce trebuie copiat
    items_to_copy = [
        'main.py', 'requirements.txt', 'pyproject.toml',
        'config', 'core', 'flet_ui', 'services', 'start', 'interfaces'
    ]
    
    print("[INFO] Copiere fisiere in director temporar...")
    for item in items_to_copy:
        src = os.path.join(PROJECT_DIR, item)
        dst = os.path.join(temp_dir, item)
        
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print(f"  [DIR] {item}")
        elif os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"  [FILE] {item}")
    
    return temp_dir

def run_build(clean_dir):
    """Ruleaza build Flet"""
    
    os.chdir(clean_dir)
    
    # Environment
    env = os.environ.copy()
    env['FLUTTER_ROOT'] = FLUTTER_DIR
    env['PATH'] = os.path.join(FLUTTER_DIR, "bin") + os.pathsep + env.get('PATH', '')
    env['PYTHONIOENCODING'] = 'utf-8'
    
    print("\n" + "="*60)
    print("BUILD FLET WINDOWS")
    print("="*60)
    
    print("\n[INFO] Pornire build...")
    print("  Acest proces dureaza 5-10 minute")
    print("  Nu inchide aceasta fereastra!")
    
    # Rulare build
    result = subprocess.run(
        [FLET_EXE, "build", "windows", "--verbose"],
        env=env,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    # Salvare log
    with open(os.path.join(PROJECT_DIR, 'build_final.log'), 'w', encoding='utf-8') as f:
        f.write(result.stdout)
        if result.stderr:
            f.write("\n\nSTDERR:\n")
            f.write(result.stderr)
    
    print("\n" + "="*60)
    print("REZULTAT")
    print("="*60)
    
    if result.returncode == 0:
        print("\n[SUCCESS] Build complet cu succes!")
        
        # Copiere rezultat
        exe_src = os.path.join(clean_dir, "build", "windows", "x64", "release", "worship_ppt_generator.exe")
        exe_dst = os.path.join(PROJECT_DIR, "build", "Worship PPT Generator.exe")
        
        if os.path.exists(exe_src):
            os.makedirs(os.path.dirname(exe_dst), exist_ok=True)
            shutil.copy2(exe_src, exe_dst)
            print(f"\n[OK] Executabil: {exe_dst}")
        
        # Copiere tot folderul windows
        windows_src = os.path.join(clean_dir, "build", "windows")
        windows_dst = os.path.join(PROJECT_DIR, "build", "windows_final")
        if os.path.exists(windows_src):
            if os.path.exists(windows_dst):
                shutil.rmtree(windows_dst)
            shutil.copytree(windows_src, windows_dst)
            print(f"[OK] Folder Windows: {windows_dst}")
        
        return True
    else:
        print(f"\n[FAIL] Build esuat (cod: {result.returncode})")
        print("\n[INFO] Log salvat in: build_final.log")
        return False

if __name__ == "__main__":
    print("="*60)
    print("BUILD FLET - CLEAN WORKAROUND")
    print("="*60)
    
    try:
        clean_dir = clean_build()
        success = run_build(clean_dir)
        
        # Curare
        shutil.rmtree(clean_dir)
        
        if success:
            print("\n" + "="*60)
            print("BUILD FINALIZAT CU SUCCES!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("BUILD ESUAT")
            print("="*60)
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
    
    input("\nApasa Enter pentru a iesi...")
