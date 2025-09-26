@echo off
setlocal

:: Validate arguments
if "%~2"=="" (
    echo Usage: %~nx0 [LinkPath] [TargetPath]
    echo Example: %~nx0 "C:\Users\YourName\IsaacLab\_isaac_sim" "C:\Users\YourName\isaacsim"
    exit /b 1
)

set "LINK_PATH=%~1"
set "TARGET_PATH=%~2"

:: Check if symlink already exists
if exist "%LINK_PATH%\" (
    echo Symlink or directory already exists at %LINK_PATH%.
) else (
    :: Create the junction
    powershell -Command "New-Item -ItemType Junction -Path '%LINK_PATH%' -Target '%TARGET_PATH%'"

    if %ERRORLEVEL% neq 0 (
        echo Failed to create symlink at %LINK_PATH%.
        exit /b 1
    ) else (
        echo Symlink created at %LINK_PATH% pointing to %TARGET_PATH%.
    )
)

exit /b 0
