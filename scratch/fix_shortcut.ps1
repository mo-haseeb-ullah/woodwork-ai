
$ws = New-Object -ComObject WScript.Shell
$sc = $ws.CreateShortcut('C:\Users\My PC\Desktop\Woodworking AI.lnk')
$sc.TargetPath = 'd:\woodworking_ai\Start_Woodworking_AI.bat'
$sc.WorkingDirectory = 'd:\woodworking_ai'
$sc.Description = 'Launch Woodworking AI Server'
$sc.Save()
