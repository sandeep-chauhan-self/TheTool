# Switch Frontend Environment Script
# Usage: 
#   .\switch-env.ps1 development
#   .\switch-env.ps1 production
#   .\switch-env.ps1 local

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('development', 'production', 'local')]
    [string]$Environment
)

$frontendDir = "frontend"
$envFile = "$frontendDir\.env"
$envDevFile = "$frontendDir\.env.development"
$envProdFile = "$frontendDir\.env.production"

Write-Host "========================================"
Write-Host "Switching frontend to: $Environment"
Write-Host "========================================"

# Read the appropriate .env file
$envContent = switch ($Environment) {
    'development' {
        "# Development Backend (thetool-development.up.railway.app)`n"
        "REACT_APP_ENV=development`n"
        "REACT_APP_API_KEY=_ZQmwHptTFGeAyWWaWXGs1KlJwrZNZFVbxpurC3evBI`n"
        "REACT_APP_DEBUG=true`n"
    }
    'production' {
        "# Production Backend (thetool-production.up.railway.app)`n"
        "REACT_APP_ENV=production`n"
        "REACT_APP_API_KEY=_ZQmwHptTFGeAyWWaWXGs1KlJwrZNZFVbxpurC3evBI`n"
    }
    'local' {
        "# Local Backend (localhost:5000)`n"
        "REACT_APP_ENV=local`n"
        "REACT_APP_API_KEY=_ZQmwHptTFGeAyWWaWXGs1KlJwrZNZFVbxpurC3evBI`n"
        "REACT_APP_DEBUG=true`n"
    }
}

# Update the .env file
Set-Content -Path $envFile -Value $envContent

Write-Host ""
Write-Host "Current .env file:"
Write-Host "========================================"
Get-Content $envFile
Write-Host "========================================"

Write-Host ""
Write-Host "Configuration:"
Write-Host "  Environment: $Environment"

$backendUrls = @{
    development = 'https://thetool-development.up.railway.app'
    production  = 'https://thetool-production.up.railway.app'
    local       = 'http://localhost:5000'
}

Write-Host "  Backend URL: $($backendUrls[$Environment])"

Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. npm install"
Write-Host "  2. npm start"
Write-Host "  3. Frontend will connect to: $($backendUrls[$Environment])"

Write-Host ""
Write-Host "Done! Frontend ready for: $Environment"
