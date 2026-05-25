Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory
strParent = strPath & "\.."
WshShell.CurrentDirectory = strParent
WshShell.Run "venv\Scripts\pythonw.exe main.py", 0, False
Set WshShell = Nothing
