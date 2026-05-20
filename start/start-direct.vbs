' Launcher direct pentru Worship PPT Generator
' Ruleaza pythonw.exe direct fara CMD intermediary

Set WshShell = CreateObject("WScript.Shell")

' Obtine calea catre directorul start (unde e acest fisier)
strStartPath = WshShell.CurrentDirectory
strAppPath = strStartPath & "\.."
strPythonPath = strAppPath & "\venv\Scripts\pythonw.exe"
strMainPath = strAppPath & "\main.py"

' Seteaza working directory
WshShell.CurrentDirectory = strAppPath

' Ruleaza pythonw direct (windowstyle 0 = hidden, wait = False)
WshShell.Run """" & strPythonPath & """ """ & strMainPath & """ --ui", 0, False

Set WshShell = Nothing
