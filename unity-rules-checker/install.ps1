###############################################################################
# Unity开发规则检查工具 - 安装脚本 (Windows PowerShell)
###############################################################################

#Requires -Version 5.1

[CmdletBinding()]
param()

# 颜色函数（适用于支持ANSI的控制台）
function Print-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

# 检查是否在Unity项目目录中
function Test-UnityProject {
    if (-not (Test-Path "Assets")) {
        Print-Error "未检测到Unity项目（找不到Assets目录）"
        Print-Info "请在Unity项目根目录中运行此脚本"
        return $false
    }
    Print-Success "检测到Unity项目"
    return $true
}

# 创建备份
function Backup-Existing {
    param([string]$Path)

    if (Test-Path $Path) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "${Path}_backup_$timestamp"
        Print-Warning "发现现有配置，正在备份到: $backupPath"
        Copy-Item -Path $Path -Destination $backupPath -Recurse
        Print-Success "备份完成"
    }
}

# 安装SKILL文件
function Install-Skills {
    Print-Header "安装Claude Code SKILL"

    $skillSource = ".claude\skills\check-rules.md"
    $skillTarget = "..\.claude\skills\check-rules.md"

    # 创建目标目录
    $null = New-Item -ItemType Directory -Force -Path "..\.claude\skills"

    # 复制SKILL文件
    if (Test-Path $skillSource) {
        Copy-Item -Path $skillSource -Destination $skillTarget -Force
        Print-Success "已安装: check-rules.md"
    } else {
        Print-Error "找不到源文件: $skillSource"
        return $false
    }

    return $true
}

# 安装Hook文件
function Install-Hooks {
    Print-Header "安装Git Hooks（可选）"

    if (-not (Test-Path "..\.git")) {
        Print-Warning "未检测到Git仓库，跳过Hook安装"
        return
    }

    $installHook = Read-Host "是否安装Git pre-commit Hook？(y/N)"

    if ($installHook -ne "y" -and $installHook -ne "Y") {
        Print-Info "跳过Hook安装"
        return
    }

    $hookSource = ".claude\hooks\pre-commit.md"
    $hookTarget = "..\.git\hooks\pre-commit"
    $configSource = ".claude\hooks\config.json"
    $configTarget = "..\.claude\hooks\config.json"

    # 创建目标目录
    $null = New-Item -ItemType Directory -Force -Path "..\.claude\hooks"

    # 复制Hook文件
    if (Test-Path $hookSource) {
        Copy-Item -Path $hookSource -Destination $hookTarget -Force
        # Windows不需要设置可执行权限
        Print-Success "已安装: pre-commit Hook"
    }

    # 复制配置文件
    if (Test-Path $configSource) {
        Copy-Item -Path $configSource -Destination $configTarget -Force
        Print-Success "已安装: Hook配置文件"
    }

    Print-Info "Git Hook将在每次提交前自动检查代码规则"
}

# 安装规则文档
function Install-Docs {
    Print-Header "安装规则文档"

    $docsSource = "docs\开发规则清单.md"
    $docsTarget = "..\docs\开发规则清单.md"

    # 创建目标目录
    $null = New-Item -ItemType Directory -Force -Path "..\docs"

    # 复制文档
    if (Test-Path $docsSource) {
        Copy-Item -Path $docsSource -Destination $docsTarget -Force
        Print-Success "已安装: 开发规则清单.md"
    } else {
        Print-Warning "找不到规则文档: $docsSource"
        Print-Info "SKILL将使用内置规则（功能可能受限）"
    }
}

# 验证安装
function Verify-Installation {
    Print-Header "验证安装"

    $errors = 0

    if (Test-Path "..\.claude\skills\check-rules.md") {
        Print-Success "SKILL文件已安装"
    } else {
        Print-Error "SKILL文件未找到"
        $errors++
    }

    if (Test-Path "..\docs\开发规则清单.md") {
        Print-Success "规则文档已安装"
    } else {
        Print-Warning "规则文档未找到（可选）"
    }

    if (Test-Path "..\.git\hooks\pre-commit") {
        Print-Success "Git Hook已安装"
    }

    return $errors -eq 0
}

# 显示使用说明
function Show-Usage {
    Print-Header "安装完成！"

    @"

Unity开发规则检查工具安装成功！

使用方法：
1. 在Claude Code中运行：
   /check-rules Assets\Scripts\YourScript.cs

2. 检查整个目录：
   /check-rules Assets\Scripts

3. 只检查CRITICAL规则：
   /check-rules Assets\Scripts --severity=CRITICAL

4. 查看帮助：
   /check-rules --help

文档位置：
- 规则清单: .\docs\开发规则清单.md
- SKILL文件: .\.claude\skills\check-rules.md

卸载方法：
Remove-Item -Recurse -Force .claude\skills\check-rules.md
Remove-Item -Recurse -Force .claude\hooks
Remove-Item -Recurse -Force docs\开发规则清单.md
Remove-Item -Force .git\hooks\pre-commit

"@

    if (Test-Path "..\.git\hooks\pre-commit") {
        Print-Info "Git Hook已配置，提交代码时将自动检查"
    }
}

# 主安装流程
function Main {
    Clear-Host
    Print-Header "Unity开发规则检查工具 - 安装向导"

    # 检查Unity项目
    if (-not (Test-UnityProject)) {
        exit 1
    }

    # 显示版本信息
    if (Test-Path "VERSION") {
        $version = Get-Content "VERSION" -TotalCount 1
        Print-Info "工具版本: $version"
    }

    Write-Host ""
    $confirm = Read-Host "是否继续安装？(y/N)"

    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Print-Info "安装已取消"
        exit 0
    }

    # 备份现有配置
    Backup-Existing "..\.claude"
    Backup-Existing "..\docs"

    # 执行安装
    $success = $true

    if (-not (Install-Skills)) {
        $success = $false
    }

    Install-Docs
    Install-Hooks

    # 验证
    if ($success -and (Verify-Installation)) {
        Show-Usage
    } else {
        Print-Error "安装过程中出现问题，请检查错误信息"
        exit 1
    }
}

# 运行主程序
Main
