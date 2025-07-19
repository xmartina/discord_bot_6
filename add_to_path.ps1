$ScriptsPath = "C:\Users\Admin\AppData\Roaming\Python\Python310\Scripts"
$LocalBinPath = "C:\Users\Admin\.local\bin"

# Check if the paths already exist in the user's PATH
$CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Add Python Scripts directory to PATH if not already there
if ($CurrentPath -notlike "*$ScriptsPath*") {
    # Add the path to the user's PATH environment variable
    $CurrentPath = $CurrentPath + ";" + $ScriptsPath
    [Environment]::SetEnvironmentVariable("Path", $CurrentPath, "User")
    Write-Host "Added $ScriptsPath to your PATH environment variable." -ForegroundColor Green
} else {
    Write-Host "$ScriptsPath is already in your PATH environment variable." -ForegroundColor Yellow
}

# Add Local Bin directory to PATH if not already there
if ($CurrentPath -notlike "*$LocalBinPath*") {
    # Add the path to the user's PATH environment variable
    $CurrentPath = $CurrentPath + ";" + $LocalBinPath
    [Environment]::SetEnvironmentVariable("Path", $CurrentPath, "User")
    Write-Host "Added $LocalBinPath to your PATH environment variable." -ForegroundColor Green
} else {
    Write-Host "$LocalBinPath is already in your PATH environment variable." -ForegroundColor Yellow
}

# Also update the current session's PATH
$env:Path = "$env:Path;$ScriptsPath;$LocalBinPath"
Write-Host "Updated current session's PATH. You can now use aider without restarting." 