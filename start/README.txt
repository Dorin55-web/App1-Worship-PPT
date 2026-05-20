# Optiuni de pornire

## start-direct.vbs (RECOMANDAT - Cel mai rapid)
Porneste aplicatia **direct** folosind pythonw.exe, fara CMD.
- Dubclik pe `start-direct.vbs`
- Cel mai rapid - sare peste CMD complet
- Nu se vede nicio fereastra
- **Acelasi timp de pornire ca start-ui.bat**

## start-hidden.vbs
Porneste aplicatia **prin CMD ascuns**.
- Dubclik pe `start-hidden.vbs`
- Trece prin batch file (activare venv)
- Pare mai lent pentru ca nu vezi feedback-ul
- Functioneaza identic, doar ca ascuns

## start-ui.bat
Versiunea **vizibila** - vezi CMD-ul 1 secunda.
- Dubclik pe `start-ui.bat`
- Arata CMD-ul cand activeaza venv-ul
- Apoi dispare si apare FLET

## start-ui-debug.bat
Versiune pentru **depanare** - afiseaza CMD permanent.
- Dubclik pe `start-ui-debug.bat`
- Vezi toate mesajele [HOTKEY], [UI] in consola
- Util daca ceva nu functioneaza

## Cum sa creezi un shortcut pe desktop:
1. Click dreapta pe `start-direct.vbs` (cel mai rapid)
2. "Send to" -> "Desktop (create shortcut)"
3. Redenumeste shortcut-ul: "Worship PPT Generator"
4. Dubclik pe shortcut pentru a porni aplicatia

## De ce start-direct.vbs e cel mai bun:
- Porneste direct pythonw.exe (fara intermediari)
- Nu creeaza proces CMD deloc
- Timp de pornire identic cu variantele vizibile
- Zero ferestre in fundal
