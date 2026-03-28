"""
SelfCore Phase 5B Self-Test -- Packaging & Distribution (12 items)
"""
import sys
import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

PASS = 0
FAIL = 0
results = []

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        results.append(f"  [PASS] {name}")
    else:
        FAIL += 1
        results.append(f"  [FAIL] {name} -- {detail}")


# ═══════════════════════════════════════════════════════════════
# Test 1: Git repo initialized with clean status
# ═══════════════════════════════════════════════════════════════
try:
    git_dir = os.path.join(PROJECT_ROOT, ".git")
    assert os.path.isdir(git_dir), ".git directory not found"
    import subprocess
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    untracked = [l for l in result.stdout.strip().split("\n") if l.strip()]
    test("1. Git repo clean (untracked: {})".format(len(untracked)),
         len(untracked) == 0,
         f"Dirty files: {untracked[:5]}")
except Exception as e:
    test("1. Git repo status", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 2: package.json metadata correct
# ═══════════════════════════════════════════════════════════════
try:
    pkg_path = os.path.join(PROJECT_ROOT, "package.json")
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    checks = {
        "name": pkg.get("name") == "selfcore",
        "version": pkg.get("version") == "1.0.0",
        "description": "Own your AI identity" in pkg.get("description", ""),
        "author": pkg.get("author") == "SelfCore Team",
        "license": pkg.get("license") == "GPL-3.0",
        "homepage": "github.com" in pkg.get("homepage", ""),
    }
    failed = [k for k, v in checks.items() if not v]
    test("2. package.json metadata correct",
         len(failed) == 0,
         f"Failed: {failed}")
except Exception as e:
    test("2. package.json metadata", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 3: package.json scripts complete
# ═══════════════════════════════════════════════════════════════
try:
    scripts = pkg.get("scripts", {})
    required = ["dev", "build", "sensor", "electron", "app:dev", "dist:win"]
    missing = [s for s in required if s not in scripts]
    test("3. package.json has all 6 required scripts",
         len(missing) == 0,
         f"Missing: {missing}")
except Exception as e:
    test("3. package.json scripts", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 4: electron-builder config parses correctly
# ═══════════════════════════════════════════════════════════════
try:
    build = pkg.get("build", {})
    assert build.get("appId") == "com.selfcore.app"
    assert build.get("productName") == "SelfCore"
    assert build.get("directories", {}).get("output") == "dist"
    # files list
    files = build.get("files", [])
    required_files = ["main.js", "preload.js", "selfcore.py", "analysis_engine.py",
                      "data/**/*", "package.json"]
    missing_files = [f for f in required_files if f not in files]
    assert len(missing_files) == 0, f"Missing in files: {missing_files}"
    # extraResources
    extra = build.get("extraResources", [])
    extra_froms = [e.get("from", "") for e in extra]
    assert "analysis_engine.py" in extra_froms
    assert "data/" in extra_froms
    # win target
    win = build.get("win", {})
    targets = win.get("target", [])
    target_names = [t.get("target", t) if isinstance(t, dict) else t for t in targets]
    assert "nsis" in target_names and "portable" in target_names
    # icon
    assert win.get("icon", "").endswith(".ico")
    # nsis
    nsis = build.get("nsis", {})
    assert nsis.get("oneClick") is False
    assert nsis.get("shortcutName") == "SelfCore"
    test("4. electron-builder config valid (NSIS + Portable)", True)
except Exception as e:
    test("4. electron-builder config", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 5: requirements.txt exists with all packages
# ═══════════════════════════════════════════════════════════════
try:
    req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
    assert os.path.exists(req_path), "requirements.txt not found"
    with open(req_path, "r") as f:
        reqs = [l.strip() for l in f if l.strip()]
    required_pkgs = ["psutil", "cryptography", "spacy", "scikit-learn", "pynvml", "Pillow"]
    missing = [p for p in required_pkgs if p not in reqs]
    test("5. requirements.txt has {} packages".format(len(reqs)),
         len(missing) == 0,
         f"Missing: {missing}")
except Exception as e:
    test("5. requirements.txt", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 6: setup_python.bat exists and is correct
# ═══════════════════════════════════════════════════════════════
try:
    bat_path = os.path.join(PROJECT_ROOT, "setup_python.bat")
    assert os.path.exists(bat_path), "setup_python.bat not found"
    with open(bat_path, "r") as f:
        bat = f.read()
    assert "requirements.txt" in bat
    assert "en_core_web_sm" in bat
    assert "ko_core_news_sm" in bat
    test("6. setup_python.bat correct", True)
except Exception as e:
    test("6. setup_python.bat", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 7: CHANGELOG.md exists and complete
# ═══════════════════════════════════════════════════════════════
try:
    cl_path = os.path.join(PROJECT_ROOT, "CHANGELOG.md")
    assert os.path.exists(cl_path), "CHANGELOG.md not found"
    with open(cl_path, "r", encoding="utf-8") as f:
        cl = f.read()
    assert "v1.0.0" in cl
    assert "Features" in cl
    assert "Privacy" in cl
    assert "AES-256" in cl
    assert "Ollama" in cl
    assert "spaCy" in cl
    test("7. CHANGELOG.md exists and complete", True)
except Exception as e:
    test("7. CHANGELOG.md", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 8: LICENSE file exists with GPL-3.0
# ═══════════════════════════════════════════════════════════════
try:
    lic_path = os.path.join(PROJECT_ROOT, "LICENSE")
    assert os.path.exists(lic_path), "LICENSE not found"
    with open(lic_path, "r", encoding="utf-8") as f:
        lic = f.read()
    assert "GNU GENERAL PUBLIC LICENSE" in lic
    assert "Version 3" in lic
    assert "SelfCore" in lic
    test("8. LICENSE file with GPL-3.0", True)
except Exception as e:
    test("8. LICENSE", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 9: App icon exists in PNG and ICO format
# ═══════════════════════════════════════════════════════════════
try:
    png_path = os.path.join(PROJECT_ROOT, "assets", "icon.png")
    ico_path = os.path.join(PROJECT_ROOT, "assets", "icon.ico")
    assert os.path.exists(png_path), "icon.png not found"
    assert os.path.exists(ico_path), "icon.ico not found"
    png_size = os.path.getsize(png_path)
    ico_size = os.path.getsize(ico_path)
    assert png_size > 1000, f"icon.png too small: {png_size} bytes"
    assert ico_size > 500, f"icon.ico too small: {ico_size} bytes"
    # Verify PNG dimensions
    from PIL import Image
    img = Image.open(png_path)
    w, h = img.size
    assert w >= 256 and h >= 256, f"Icon too small: {w}x{h}"
    test("9. App icon: PNG {}x{} ({}B) + ICO ({}B)".format(w, h, png_size, ico_size), True)
except Exception as e:
    test("9. App icon", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 10: README.md has all required sections
# ═══════════════════════════════════════════════════════════════
try:
    readme_path = os.path.join(PROJECT_ROOT, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme = f.read()
    sections = ["SelfCore", "Features", "Installation", "Prerequisites",
                "Chrome Extension", "How to Use", "Analysis Tab",
                "Tech Stack", "Privacy", "License", "GPL-3.0"]
    missing = [s for s in sections if s not in readme]
    test("10. README.md has all sections",
         len(missing) == 0,
         f"Missing: {missing}")
except Exception as e:
    test("10. README.md", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 11: SelfCore.vbs still launches correctly
# ═══════════════════════════════════════════════════════════════
try:
    vbs_path = r"C:\Users\user\Desktop\SelfCore.vbs"
    assert os.path.exists(vbs_path), "SelfCore.vbs not found"
    with open(vbs_path, "r") as f:
        content = f.read()
    assert "SelfCore" in content and "selfcore.py" in content
    test("11. SelfCore.vbs launcher exists and correct", True)
except Exception as e:
    test("11. SelfCore.vbs", False, str(e))


# ═══════════════════════════════════════════════════════════════
# Test 12: Extension folder complete with INSTALL.html
# ═══════════════════════════════════════════════════════════════
try:
    ext_dir = os.path.join(PROJECT_ROOT, "extension")
    required_ext = ["manifest.json", "background.js", "content.js",
                    "content.css", "popup.html", "popup.js",
                    "INSTALL.html", "icon48.png", "icon128.png"]
    missing = [f for f in required_ext if not os.path.exists(os.path.join(ext_dir, f))]
    test("12. Extension folder complete ({} files)".format(len(required_ext) - len(missing)),
         len(missing) == 0,
         f"Missing: {missing}")
except Exception as e:
    test("12. Extension folder", False, str(e))


# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  SelfCore Phase 5B Self-Test Results")
print("=" * 60)
for r in results:
    print(r)
print("=" * 60)
print(f"  TOTAL: {PASS + FAIL} | PASS: {PASS} | FAIL: {FAIL}")
print("=" * 60)
if FAIL > 0:
    sys.exit(1)
