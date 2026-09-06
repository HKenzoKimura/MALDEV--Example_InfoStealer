# 🔴 Purple Team Simulation — LNK Loader + GitHub C2 + Infostealer

> **Context:** This project was developed as a **tabletop exercise simulation** to validate detection capabilities across EDR, SIEM, and network monitoring layers. The goal was to emulate a realistic threat actor TTP chain and measure MTTR, alert fidelity, and detection gaps in a controlled environment.
>
> Developed by: HKK
>
> 
> ⚠️ *No production systems were targeted. All execution occurred in isolated lab infrastructure.*

---

## `$ cat ./objective.txt`

Simulate a **multi-stage intrusion chain** — from initial access to data exfiltration — using techniques commonly observed in real-world commodity malware and targeted campaigns, with the following design constraints:

- **No custom C2 infrastructure** — leverage legitimate web services to blend with normal traffic
- **Minimal disk footprint** — payload lives in memory or `%TEMP%` with cleanup
- **Realistic lure vector** — initial access via document-like artifact, not raw executable
- **Measurable** — each stage produces detectable artifacts to validate blue team coverage

---

## `$ cat ./kill_chain.txt`

```
┌─────────────────────────────────────────────────────────────────────┐
│                        KILL CHAIN OVERVIEW                          │
├──────────────┬──────────────┬───────────────┬───────────────────────┤
│  STAGE 1     │  STAGE 2     │  STAGE 3      │  STAGE 4              │
│  Initial     │  Execution   │  Persistence  │  Collection &         │
│  Access      │  + Dropper   │  + Staging    │  Exfiltration         │
├──────────────┼──────────────┼───────────────┼───────────────────────┤
│ LNK disguised│ Encoded PS1  │ Scheduled     │ Infostealer runs:     │
│ as .docx     │ fetches      │ Tasks created │ sysinfo, creds,       │
│ delivered to │ dropper from │ for dropper   │ network scan,         │
│ victim       │ GitHub API   │ + stealer     │ vault → ZIP → GitHub  │
└──────────────┴──────────────┴───────────────┴───────────────────────┘

  Victim  ──►  LNK  ──►  PowerShell  ──►  GitHub API (C2)
                                │                │
                          Dropper PS1 ◄───────────┘
                                │
                    Scheduled Task (persistence)
                                │
                          Stealer PS1 ◄── GitHub API (C2)
                                │
                    Collection → ZIP → GitHub (exfil)
```

---

## `$ cat ./design_decisions.md`

### 1. LNK como vetor de Initial Access

**Por que LNK e não um macro Office ou EXE direto?**

Arquivos `.lnk` (Windows Shortcut) são tratados como documentos pelo sistema operacional quando combinados com um ícone legítimo (ex: `WINWORD.EXE`). A decisão técnica envolve três fatores:

- **Bypass de restrições de extensão:** muitos ambientes bloqueiam `.exe`, `.bat`, `.vbs` por email/download, mas `.lnk` historicamente tem restrições mais permissivas
- **Argumento `-EncodedCommand`:** o payload vai Base64-encoded diretamente no argumento do `powershell.exe`, eliminando a necessidade de arquivo intermediário no disco no momento da entrega
- **`WindowStyle 7` (minimized):** a janela do PowerShell não aparece para o usuário, reduzindo a chance de detecção visual

**Limitação reconhecida:** Windows 11 e políticas mais recentes adicionaram avisos visuais para execução de LNK. Em ambientes modernos, o vetor exigiria uma camada adicional de engenharia social.

---

### 2. GitHub como C2 — Legitimate Web Service Abuse

**Por que usar a API do GitHub como Command & Control?**

Esta é a decisão de design mais estratégica do projeto. Usar infraestrutura legítima como C2 — técnica conhecida como **Living off Trusted Sites (LoTS)** — apresenta vantagens defensivas significativas para o atacante:

- **Tráfego HTTPS para `api.github.com`** é indistinguível de tráfego legítimo de desenvolvimento em redes corporativas
- **Sem necessidade de domínio próprio** — elimina indicadores como domínios recém-registrados, certificados auto-assinados ou IPs suspeitos
- **Latência de resposta** de uma API REST real contribui para evasão de sandboxes que detectam padrões de beacon regulares

**Fluxo C2:**
```
Malware  ──►  GET  api.github.com/repos/{owner}/{repo}/contents/{path}
              (Bearer token no header Authorization)
         ◄──  Payload encoded em Base64 no campo .content da resposta JSON
```

O payload em repouso no repositório é armazenado como Base64 nativo — a própria API do GitHub retorna conteúdo de arquivo nesse formato, então não há step extra de decode visível no tráfego.

**Limitação reconhecida:** O token Bearer hardcoded no payload é um indicador crítico. Em implementações mais sofisticadas, a chave seria derivada dinamicamente (ex: baseada em atributos da máquina vítima) ou obtida de um endpoint público diferente.

---

### 3. Obfuscação — GZIP + Base64

**Por que comprimir antes de encodar?**

A cadeia `GZIP → Base64` serve dois propósitos simultâneos:

- **Redução de tamanho:** payloads PowerShell são verbosos; GZIP reduz o tamanho em ~60-70%, importante para o limite de caracteres do argumento `-EncodedCommand`
- **Evasão de assinaturas estáticas:** strings características do payload (nomes de funções, padrões de cmdlets) desaparecem do binário entregue. Um scanner baseado em strings não encontra `Invoke-WebRequest` ou `Out-File` no artefato inicial

**Por que não AES?**

O design atual é intencionalmente "SEM AES" (conforme nomenclatura dos scripts) — a decisão foi manter o projeto dentro do escopo do tabletop sem introduzir criptografia que dificultasse a análise posterior pela equipe azul. Em cenários reais, AES adicionaria uma camada de proteção contra análise em memória, mas também aumentaria significativamente a complexidade de detecção para o exercício.

---

### 4. Persistência via Scheduled Tasks com Name Masquerading

**Por que Scheduled Tasks e por que esses nomes?**

`schtasks` é uma ferramenta nativa do Windows (LOLBIN — Living off the Land Binary), o que significa:

- **Sem binário externo no disco** — a persistência é estabelecida via ferramenta já existente no sistema
- **Execução como processo filho legítimo** — `schtasks.exe` tem comportamento esperado em ambientes corporativos

Os nomes escolhidos (`MicrosoftEdgeUpdateTask`, `MicrosoftUpdatedTaskWeb`) seguem a convenção de **Task Name Spoofing**: imitar nomenclatura de tarefas legítimas da Microsoft para reduzir a chance de detecção em revisões manuais do Task Scheduler.

**Artefato gerado (detectável):**
```
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\TaskCache\Tasks\
```
Qualquer EDR com cobertura de registry e process creation consegue capturar esse comportamento.

---

### 5. Infostealer — Escopo de Coleta

**Quais categorias de dados e por quê cada uma?**

| Categoria | Técnica | Razão estratégica |
|-----------|---------|-------------------|
| System info | `Get-ComputerInfo` | Reconhecimento pós-compromisso — identifica o alvo |
| Network info | `ipconfig`, `whoami /fqdn` | Mapeia o domínio e posição na rede |
| Domain info | `nltest /dsgetdc`, `gpresult` | Identifica se é Domain Controller acessível, GPOs aplicadas |
| User groups | `whoami /groups`, `net localgroup` | Avalia privilégios e vetores de escalação |
| Credential files | `Get-ChildItem` + `Select-String` | Credential hunting em texto plano — padrão comum em credential access |
| Windows Vault | `vaultcmd`, `cmdkey` | Credenciais salvas pelo próprio Windows |
| Recent files | `%APPDATA%\Microsoft\Windows\Recent` | Identifica documentos sensíveis acessados recentemente |
| Network scan | TCP connect em paralelo via Runspaces | Mapeia hosts ativos e portas abertas na subnet — movimentação lateral |

**Exfiltração:** todos os arquivos são comprimidos em ZIP com nome GUID aleatório e enviados via PUT para o repositório GitHub C2 — reutilizando a mesma infraestrutura sem novo tráfego para destinos desconhecidos.

---

## `$ cat ./mitre_mapping.yml`

```yaml
tactics:
  initial_access:
    - T1566.001   # Phishing: Spearphishing Attachment (LNK como lure)
    - T1204.002   # User Execution: Malicious File

  execution:
    - T1059.001   # Command and Scripting Interpreter: PowerShell
    - T1027.013   # Obfuscated Files: Encrypted/Encoded File (GZIP+B64)
    - T1140       # Deobfuscate/Decode Files or Information

  persistence:
    - T1053.005   # Scheduled Task/Job: Scheduled Task
    - T1036.004   # Masquerading: Masquerade Task or Service

  defense_evasion:
    - T1027       # Obfuscated Files or Information
    - T1564.001   # Hide Artifacts: Hidden Files (attrib +h +r)
    - T1036       # Masquerading (ícone WINWORD, nome de task)
    - T1218       # System Binary Proxy Execution (LOLBins)

  credential_access:
    - T1552.001   # Unsecured Credentials: Credentials In Files
    - T1555.004   # Credentials from Password Stores: Windows Credential Manager

  discovery:
    - T1082       # System Information Discovery
    - T1016       # System Network Configuration Discovery
    - T1069       # Permission Groups Discovery
    - T1087       # Account Discovery
    - T1046       # Network Service Discovery (port scan via Runspaces)
    - T1083       # File and Directory Discovery

  lateral_movement:
    - T1046       # Network Service Scanning (base para movimentação)

  collection:
    - T1074.001   # Data Staged: Local Data Staging (ZIP em %TEMP%)
    - T1005       # Data from Local System

  command_and_control:
    - T1102.002   # Web Service: Bidirectional Communication (GitHub API)
    - T1071.001   # Application Layer Protocol: Web Protocols (HTTPS)
    - T1132.001   # Data Encoding: Standard Encoding (Base64)

  exfiltration:
    - T1041       # Exfiltration Over C2 Channel
    - T1020       # Automated Exfiltration
```

---

## `$ cat ./detection_opportunities.md`

> Blue team view — onde essa cadeia deixa artefatos detectáveis.

| Stage | Artefato | Detecção sugerida |
|-------|----------|-------------------|
| LNK execution | `powershell.exe` filho de `explorer.exe` com `-EncodedCommand` | Process creation: parent=explorer, args=-Enc |
| C2 fetch | `Invoke-WebRequest` para `api.github.com` com header `Authorization: Bearer` | DNS + proxy log: `api.github.com` com UA do PowerShell |
| Persistence | `schtasks.exe /create` com nome "Microsoft*" | Sysmon Event ID 1, Scheduled Task creation |
| Hidden file | `attrib +h +r` em `%TEMP%` | File system monitoring em %TEMP% com atributos ocultos |
| Network scan | 256×254 conexões TCP em paralelo via Runspaces | NetFlow: volume anormal de SYN para subnets internas |
| Exfiltration | PUT para `api.github.com/repos/*/contents/` | Proxy: método PUT para GitHub API fora de horário comercial |

---

## `$ cat ./lessons_learned.txt`

```
[+] GitHub como C2 é eficaz contra controles baseados apenas em reputação de IP/domínio
[+] GZIP+Base64 é suficiente para evasão de scanners baseados em strings estáticas
[+] Task name masquerading passa em revisões manuais rápidas do Task Scheduler
[-] Bearer token hardcoded é um IOC crítico — detectado em SIEM com DLP habilitado
[-] Volume de conexões do network scan é anomalia estatística óbvia em NetFlow
[-] attrib +h não escapa de EDRs com filesystem minifilter (CrowdStrike, Defender ATP)
[-] -EncodedCommand é altamente monitorado — ratio de detecção elevado em ambientes maduros
[→] Próximo nível: derivação dinâmica de chave C2, process injection para evasão de EDR
```

---

<p align="center">
  <i>Built for detection validation · All techniques mapped to MITRE ATT&CK · No production systems harmed</i>
</p>
