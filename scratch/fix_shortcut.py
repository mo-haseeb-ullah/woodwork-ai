import os
import subprocess

# Delete the duplicate raw .bat file on Desktop
bat_desktop = r"C:\Users\My PC\Desktop\Start_Woodworking_AI.bat"
if os.path.exists(bat_desktop):
    os.remove(bat_desktop)
    print(f"Removed {bat_desktop}")

# Point the single 'Woodworking AI' shortcut on Desktop directly to d:\woodworking_ai\Start_Woodworking_AI.bat
ps_script = """
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('C:\\Users\\My PC\\Desktop\\Woodworking AI.lnk')
$sc.TargetPath = 'd:\\woodworking_ai\\Start_Woodworking_AI.bat'
$sc.WorkingDirectory = 'd:\\woodworking_ai'
$sc.Description = 'Launch Woodworking AI Server'
$sc.Save()
"""

with open("scratch/fix_shortcut.ps1", "w") as f:
    f.write(ps_script)

subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "scratch/fix_shortcut.ps1"])
print("Single shortcut updated cleanly on Desktop!")
