@echo off
title Lumify Builder
color 0A
echo.
echo  ==========================================
echo    Lumify - Final Build
echo  ==========================================
echo.

echo  [1/3] Installing dependencies...
pip install PyQt5 pyinstaller --quiet

echo.
echo  [2/3] Building Lumify.exe...

C:\Users\%USERNAME%\AppData\Local\Python\pythoncore-3.14-64\python.exe -m PyInstaller --name "Lumify" --windowed --onefile --clean --icon "icon.ico" --add-data "icon.ico;." --add-data "icon.png;." lumify.py

if not exist "dist\Lumify.exe" (
    python -m PyInstaller --name "Lumify" --windowed --onefile --clean --icon "icon.ico" --add-data "icon.ico;." --add-data "icon.png;." lumify.py
)

if not exist "dist\Lumify.exe" (
    echo  ERROR: Build failed. Check errors above.
    pause & exit /b 1
)

echo.
echo  [3/3] Creating Lumify_Setup.exe...

(
echo !include "MUI2.nsh"
echo Name "Lumify"
echo OutFile "Lumify_Setup.exe"
echo InstallDir "$PROGRAMFILES\Lumify"
echo RequestExecutionLevel admin
echo !insertmacro MUI_PAGE_WELCOME
echo !insertmacro MUI_PAGE_DIRECTORY
echo !insertmacro MUI_PAGE_INSTFILES
echo !insertmacro MUI_PAGE_FINISH
echo !insertmacro MUI_UNPAGE_CONFIRM
echo !insertmacro MUI_UNPAGE_INSTFILES
echo !insertmacro MUI_LANGUAGE "English"
echo Section "Install"
echo   SetOutPath "$INSTDIR"
echo   File "dist\Lumify.exe"
echo   File "icon.ico"
echo   CreateDirectory "$SMPROGRAMS\Lumify"
echo   CreateShortcut "$SMPROGRAMS\Lumify\Lumify.lnk" "$INSTDIR\Lumify.exe" "" "$INSTDIR\icon.ico"
echo   CreateShortcut "$DESKTOP\Lumify.lnk" "$INSTDIR\Lumify.exe" "" "$INSTDIR\icon.ico"
echo   WriteUninstaller "$INSTDIR\Uninstall.exe"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Lumify" "DisplayName" "Lumify"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Lumify" "UninstallString" "$INSTDIR\Uninstall.exe"
echo   WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Lumify" "DisplayIcon" "$INSTDIR\icon.ico"
echo SectionEnd
echo Section "Uninstall"
echo   Delete "$INSTDIR\Lumify.exe"
echo   Delete "$INSTDIR\icon.ico"
echo   Delete "$INSTDIR\Uninstall.exe"
echo   RMDir "$INSTDIR"
echo   Delete "$SMPROGRAMS\Lumify\Lumify.lnk"
echo   RMDir "$SMPROGRAMS\Lumify"
echo   Delete "$DESKTOP\Lumify.lnk"
echo   DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Lumify"
echo SectionEnd
) > lumify_installer.nsi

where makensis >nul 2>&1
if %errorlevel% equ 0 (
    makensis lumify_installer.nsi
    if exist "Lumify_Setup.exe" (
        echo.
        echo  ==========================================
        echo    SUCCESS! Lumify_Setup.exe is ready!
        echo    Double click to install on any PC!
        echo  ==========================================
    )
) else (
    echo.
    echo  Install NSIS: https://nsis.sourceforge.io/Download
    echo  Then run build.bat again for Setup.exe
    echo.
    echo  dist\Lumify.exe works directly right now!
)
echo.
pause
