# Discord Bot Windows Setup Script (PowerShell)
# Run this script to automatically set up the Discord bot on Windows

param(
    [switch]$SkipPython,
    [switch]$Help
)

if ($Help) {
    Write-Host "Discord Bot Windows Setup Script"
    Write-Host "Usage: .\setup_windows.ps1 [-SkipPython] [-Help]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SkipPython    Skip Python installation check"
    Write-Host "  -Help          Show this help message"
    exit 0
}

Write-Host "=====================================" -ForegroundColor Green
Write-Host "Discord Bot Windows Setup (PowerShell)" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Function to write colored output
function Write-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param($Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue
}

function Write-Warning {
    param($Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Warning "Running without administrator privileges. Some operations may fail."
    Write-Info "Consider running PowerShell as Administrator for best results."
    Write-Host ""
}

# Check Python installation
if (-not $SkipPython) {
    Write-Info "Checking Python installation..."

    if (Test-Command "python") {
        try {
            $pythonVersion = & python --version 2>&1
            Write-Success "Python found: $pythonVersion"

            # Check if Python version is 3.8 or higher
            if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
                $major = [int]$matches[1]
                $minor = [int]$matches[2]

                if ($major -ge 3 -and $minor -ge 8) {
                    Write-Success "Python version is compatible"
                } else {
                    Write-Error "Python version $major.$minor is too old. Please install Python 3.8 or higher."
                    Write-Info "Download from: https://python.org/downloads/"
                    exit 1
                }
            }
        } catch {
            Write-Error "Python found but version check failed"
            exit 1
        }
    } else {
        Write-Error "Python is not installed or not in PATH"
        Write-Info "Please install Python from https://python.org/downloads/"
        Write-Info "Make sure to check 'Add Python to PATH' during installation"
        exit 1
    }
    Write-Host ""
}

# Check if requirements.txt exists
if (-not (Test-Path "requirements.txt")) {
    Write-Error "requirements.txt not found in current directory"
    Write-Info "Make sure you're running this script from the Discord_bot directory"
    exit 1
}

# Create virtual environment
Write-Info "Creating virtual environment..."
try {
    & python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Virtual environment created successfully"
    } else {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
} catch {
    Write-Error "Error creating virtual environment: $_"
    exit 1
}
Write-Host ""

# Activate virtual environment
Write-Info "Activating virtual environment..."
$activateScript = "venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    try {
        & $activateScript
        Write-Success "Virtual environment activated"
    } catch {
        Write-Warning "Failed to activate virtual environment using PowerShell script"
        Write-Info "This is normal on some systems. Continuing with installation..."
    }
} else {
    Write-Warning "PowerShell activation script not found. This is normal on some systems."
}
Write-Host ""

# Install dependencies
Write-Info "Installing Python dependencies..."
try {
    $env:VIRTUAL_ENV = (Get-Location).Path + "\venv"
    $env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:PATH"

    & python -m pip install --upgrade pip
    & python -m pip install -r requirements.txt

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dependencies installed successfully"
    } else {
        Write-Error "Failed to install dependencies"
        Write-Info "Check your internet connection and try again"
        exit 1
    }
} catch {
    Write-Error "Error installing dependencies: $_"
    exit 1
}
Write-Host ""

# Create necessary directories
Write-Info "Creating necessary directories..."
$directories = @("data", "logs", "backups")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        try {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Success "Created directory: $dir"
        } catch {
            Write-Error "Failed to create directory: $dir"
        }
    } else {
        Write-Success "Directory already exists: $dir"
    }
}
Write-Host ""

# Check if config.yaml exists
if (-not (Test-Path "config.yaml")) {
    Write-Info "config.yaml not found. Creating from template..."
    if (Test-Path "config_template_windows.yaml") {
        try {
            Copy-Item "config_template_windows.yaml" "config.yaml"
            Write-Success "Created config.yaml from template"
        } catch {
            Write-Error "Failed to create config.yaml from template"
        }
    } else {
        Write-Warning "No config template found. You'll need to create config.yaml manually"
    }
} else {
    Write-Success "config.yaml already exists"
}
Write-Host ""

# Final setup verification
Write-Info "Verifying setup..."
$setupOK = $true

# Check virtual environment
if (Test-Path "venv\Scripts\python.exe") {
    Write-Success "Virtual environment is properly set up"
} else {
    Write-Error "Virtual environment setup failed"
    $setupOK = $false
}

# Check key directories
foreach ($dir in $directories) {
    if (Test-Path $dir) {
        Write-Success "Directory $dir is ready"
    } else {
        Write-Error "Directory $dir is missing"
        $setupOK = $false
    }
}

# Check config file
if (Test-Path "config.yaml") {
    Write-Success "Configuration file is ready"
} else {
    Write-Error "Configuration file is missing"
    $setupOK = $false
}

Write-Host ""
Write-Host "=====================================" -ForegroundColor Green
Write-Host "Setup Summary" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

if ($setupOK) {
    Write-Success "Setup completed successfully!"
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Edit config.yaml with your Discord tokens:" -ForegroundColor White
    Write-Host "   - Bot token (from Discord Developer Portal)" -ForegroundColor White
    Write-Host "   - User token (from Discord web app)" -ForegroundColor White
    Write-Host "   - Your Discord user ID" -ForegroundColor White
    Write-Host ""
    Write-Host "2. Run the test script:" -ForegroundColor White
    Write-Host "   .\test_bot.ps1" -ForegroundColor Green
    Write-Host ""
    Write-Host "3. Start the bot:" -ForegroundColor White
    Write-Host "   .\start_bot.ps1" -ForegroundColor Green
    Write-Host ""
    Write-Host "For help getting tokens, see WINDOWS_SETUP_GUIDE.md" -ForegroundColor Cyan
} else {
    Write-Error "Setup completed with errors!"
    Write-Host ""
    Write-Host "Please fix the errors above and run the setup script again." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
