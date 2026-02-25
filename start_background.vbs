Set WshShell = CreateObject("WScript.Shell")
' Run the batch file silently (0 means hidden window)
WshShell.Run "cmd /c ""C:\Users\HP\OneDrive\Desktop\TruthGuard_AI\run_forever.bat""", 0
Set WshShell = Nothing
