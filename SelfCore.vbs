Set FSO = CreateObject("Scripting.FileSystemObject")
Set Shell = CreateObject("WScript.Shell")

' Set working directory to script location
Dim scriptDir
scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
Shell.CurrentDirectory = scriptDir

' Kill any orphaned Electron instances first
Shell.Run "cmd /c taskkill /F /IM electron.exe >nul 2>&1", 0, True

' Start Python backend (hidden window)
Shell.Run "cmd /c py -3 selfcore.py", 0, False

' Wait for Python to start
WScript.Sleep 2000

' Start Next.js dev server (hidden window)
Shell.Run "cmd /c npx next dev", 0, False

' Wait for Next.js to be ready
WScript.Sleep 4000

' Start Electron (hidden window — it creates its own GUI)
Shell.Run "cmd /c npx electron .", 0, False
