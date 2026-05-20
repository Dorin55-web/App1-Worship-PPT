' Launcher ascuns pentru Worship PPT Generator
' Ruleaza aplicatia fara sa arate fereastra CMD

Set WshShell = CreateObject("WScript.Shell")

' Obtine calea catre directorul start
strPath = WshShell.CurrentDirectory

' Construieste calea catre scriptul batch
strBatchPath = strPath & "\start-ui.bat"

' Ruleaza batch-ul ascuns (windowstyle 0 = hidden)
WshShell.Run "cmd /c """ & strBatchPath & """", 0, False

Set WshShell = Nothing
