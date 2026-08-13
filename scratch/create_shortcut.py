import os
import subprocess

ps_script = """
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('C:\\Users\\My PC\\Desktop\\Woodworking AI.lnk')
$sc.TargetPath = 'C:\\Users\\My PC\\Desktop\\Start_Woodworking_AI.bat'
$sc.WorkingDirectory = 'd:\\woodworking_ai'
$sc.Description = 'Launch Woodworking AI Server'
$sc.Save()
"""

with open("scratch/create_shortcut.ps1", "w") as f:
    f.write(ps_script)

subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", "scratch/create_shortcut.ps1"])
print("Shortcut created successfully on Desktop!")
