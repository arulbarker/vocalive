@echo off
:: StreamMate AI - Quick Commit Script
:: Simple one-click commit and push without errors

echo.
echo 🚀 StreamMate AI - Quick Commit
echo ===============================
echo.

:: Check if we're in a git repository
if not exist ".git" (
    echo ❌ Error: Not in a Git repository!
    pause
    exit /b 1
)

:: Add all changes
echo 📦 Adding all changes...
git add .

:: Check if there are changes to commit
git diff --cached --quiet
if %ERRORLEVEL% EQU 0 (
    echo ✅ No changes to commit
    echo Repository is already up to date!
    pause
    exit /b 0
)

:: Create commit with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD% %HH%:%Min%:%Sec%"

echo 📝 Creating commit...
git commit -m "StreamMate AI Update - %timestamp%"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Commit failed!
    pause
    exit /b 1
)

echo ✅ Commit created successfully!

:: Push to remote
echo 🚀 Pushing to GitHub...
git push origin master

if %ERRORLEVEL% EQU 0 (
    echo ✅ Push completed successfully!
    echo 🎉 All changes uploaded to GitHub!
) else (
    echo ⚠️ Push failed, trying force push...
    git push origin master --force-with-lease
    
    if %ERRORLEVEL% EQU 0 (
        echo ✅ Force push successful!
    ) else (
        echo ❌ Push failed completely!
        echo Please check your internet connection or repository access.
        pause
        exit /b 1
    )
)

echo.
echo 🎉 Git operations completed successfully!
echo Your StreamMate AI changes are now on GitHub.
echo.
pause 