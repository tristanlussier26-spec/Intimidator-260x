# Installe / met à jour le show QLC+ et le Stream Deck XL.
#   irm https://github.com/tristanlussier26-spec/Intimidator-260x/raw/main/install.ps1 | iex
$ErrorActionPreference = "Stop"
$d = "$HOME\Documents\Show-Rock"
$u = "https://github.com/tristanlussier26-spec/Intimidator-260x/raw/main/show"
$files = "Show-Rock.qxw", "Chauvet-Intimidator-Spot-260X.qxf", "UKing-ZQ01061-RGBW-Par.qxf", "MOSFiATA-PAR-36-RGB.qxf", "Lancer-QLC.bat",
         "QLC-Plus-Show.streamDeckPlugin", "Show-Rock-XL.streamDeckProfile"

New-Item -ItemType Directory -Force $d | Out-Null
foreach ($f in $files) {
    Write-Host "Téléchargement de $f..."
    Invoke-WebRequest "$u/$f" -OutFile "$d\$f" -UseBasicParsing
    Unblock-File "$d\$f"
}

Write-Host "Installation du plugin Stream Deck (confirme dans Stream Deck)..."
Start-Process "$d\QLC-Plus-Show.streamDeckPlugin"
Start-Sleep 8
Write-Host "Import du profil XL (choisis ton Stream Deck XL)..."
Start-Process "$d\Show-Rock-XL.streamDeckProfile"
Start-Sleep 3
Write-Host "Lancement de QLC+ (accès web + mode show)..."
Start-Process "$d\Lancer-QLC.bat"
Write-Host "C'est prêt : $d"
