"""Onboarding CLI for Politicagem.

This script introduces the project, installs dependencies, can create
an optional desktop shortcut using the Politicagem icon, and helps
with IPFS setup for static snapshots.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
ELECTRON_DIR = ROOT_DIR / "electron-app"
ICON_ICO_PATH = ELECTRON_DIR / "assets" / "politicagem-p.ico"
LAUNCHER_BAT_PATH = ROOT_DIR / "politicagem-desktop.bat"
GENERATE_SNAPSHOT_SCRIPT = ROOT_DIR / "generate_snapshot.sh"

ASCII_ART = r"""
PPPP   OOO   L      III  TTTTT  III   CCCC    A     GGG   EEEE  M   M
P   P O   O  L       I     T     I   C       A A   G      E     MM MM
PPPP  O   O  L       I     T     I   C      AAAAA  G GGG  EEE   M M M
P     O   O  L       I     T     I   C      A   A  G   G  E     M   M
P      OOO   LLLLL  III    T    III   CCCC  A   A   GGG   EEEE  M   M
"""


def log(message: str) -> None:
    print(message, flush=True)


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "[S/n]" if default else "[s/N]"
    valid_yes = {"s", "sim", "y", "yes"}
    valid_no = {"n", "nao", "no"}

    while True:
        answer = input(f"{prompt} {suffix}: ").strip().lower()
        if not answer:
            return default
        if answer in valid_yes:
            return True
        if answer in valid_no:
            return False
        log("Resposta invalida. Digite s ou n.")


def run_command(command: list[str], cwd: Path | None = None) -> None:
    pretty = " ".join(command)
    log(f"\n> Executando: {pretty}")
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def explain_project() -> None:
    log(ASCII_ART)
    log("Politicagem: agregador de noticias RSS com visual de jornal classico.")
    log("- Nao armazena noticias em banco de dados.")
    log("- Busca os feeds RSS em tempo real, por requisicao.")
    log("- O foco e centralizar fontes em uma leitura unica e rapida.")
    log("- Suporta snapshots estaticos para IPFS (descentralizacao).")
    log("- Acesso via servidor web, terminal ou app desktop (Electron).")


def install_python_dependencies() -> None:
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=ROOT_DIR)


def detect_os() -> str:
    """Detecta o sistema operacional atual."""
    system = platform.system().lower()
    if system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def check_ipfs_installed() -> bool:
    """Verifica se o IPFS ja esta instalado."""
    return shutil.which("ipfs") is not None


def install_ipfs_linux() -> None:
    """Instala IPFS no Linux usando o script oficial."""
    log("📦 Instalando IPFS no Linux...")
    
    # Tentar usar o script de instalacao oficial do IPFS
    install_script = "https://dist.ipfs.io/go-ipfs/v0.28.0/go-ipfs_v0.28.0_linux-amd64.tar.gz"
    
    # Criar diretorio temporario
    temp_dir = ROOT_DIR / "temp_ipfs_install"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Baixar
        run_command(["curl", "-L", "-o", str(temp_dir / "ipfs.tar.gz"), install_script])
        
        # Extrair
        run_command(["tar", "-xzf", str(temp_dir / "ipfs.tar.gz"), "-C", str(temp_dir)])
        
        # Instalar (move para ~/.local/bin ou /usr/local/bin)
        ipfs_binary = temp_dir / "go-ipfs" / "ipfs"
        local_bin = Path.home() / ".local" / "bin"
        local_bin.mkdir(parents=True, exist_ok=True)
        
        shutil.copy(str(ipfs_binary), str(local_bin / "ipfs"))
        os.chmod(str(local_bin / "ipfs"), 0o755)  # Tornar executavel
        
        log(f"✅ IPFS instalado em: {local_bin / 'ipfs'}")
        log("⚠️  Adicione ~/.local/bin ao seu PATH se ainda nao estiver:")
        log("   export PATH=$HOME/.local/bin:$PATH")
        
    finally:
        # Limpar arquivos temporarios
        shutil.rmtree(temp_dir, ignore_errors=True)


def install_ipfs_macos() -> None:
    """Instala IPFS no macOS usando Homebrew."""
    log("📦 Instalando IPFS no macOS via Homebrew...")
    run_command(["brew", "install", "ipfs"])


def install_ipfs_windows() -> None:
    """Instala IPFS no Windows usando Chocolatey ou Winget."""
    log("📦 Instalando IPFS no Windows...")
    
    # Tentar Chocolatey primeiro
    if shutil.which("choco"):
        run_command(["choco", "install", "ipfs", "-y"])
    # Senao tentar winget
    elif shutil.which("winget"):
        run_command(["winget", "install", "--id", "IPFS.IPFS", "-e"])
    else:
        raise RuntimeError(
            "Nenhum gerenciador de pacotes encontrado (Chocolatey ou Winget). "
            "Instale manualmente em: https://docs.ipfs.io/install/"
        )


def install_ipfs() -> None:
    """Instala IPFS baseado no sistema operacional detectado."""
    if check_ipfs_installed():
        log("✅ IPFS ja esta instalado.")
        return
    
    os_type = detect_os()
    log(f"🔍 Sistema operacional detectado: {os_type}")
    
    if os_type == "linux":
        install_ipfs_linux()
    elif os_type == "macos":
        install_ipfs_macos()
    elif os_type == "windows":
        install_ipfs_windows()
    else:
        raise RuntimeError(f"Sistema operacional nao suportado: {os_type}")


def initialize_ipfs() -> None:
    """Inicializa o IPFS se ainda nao estiver configurado."""
    ipfs_dir = Path.home() / ".ipfs"
    
    if ipfs_dir.exists():
        log("✅ IPFS ja esta inicializado.")
        return
    
    log("🔧 Inicializando IPFS...")
    run_command(["ipfs", "init"])
    log("✅ IPFS inicializado com sucesso.")


def make_snapshot_script_executable() -> None:
    """Torna o script de snapshot executavel no Linux/macOS."""
    if os.name != "nt" and GENERATE_SNAPSHOT_SCRIPT.exists():
        run_command(["chmod", "+x", str(GENERATE_SNAPSHOT_SCRIPT)])
        log("✅ Script generate_snapshot.sh tornado executavel.")


def install_electron_dependencies() -> None:
    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        raise RuntimeError("npm nao encontrado. Instale Node.js para continuar.")
    run_command([npm_cmd, "install"], cwd=ELECTRON_DIR)


def write_launcher_bat() -> None:
    content = """@echo off
cd /d "%~dp0electron-app"
if not exist node_modules (
  echo Dependencias do Electron nao encontradas.
  echo Rode onboarding novamente e instale o Electron.
)
npm start
"""
    LAUNCHER_BAT_PATH.write_text(content, encoding="utf-8")


def powershell_escape(value: str) -> str:
    return value.replace("'", "''")


def create_desktop_shortcut() -> None:
    if os.name != "nt":
        log("Criacao de atalho automatico disponivel apenas no Windows.")
        return

    if not ICON_ICO_PATH.exists():
        raise FileNotFoundError(f"Icone nao encontrado: {ICON_ICO_PATH}")

    write_launcher_bat()

    desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    if not desktop_dir.exists():
        raise FileNotFoundError(f"Area de Trabalho nao encontrada: {desktop_dir}")

    shortcut_path = desktop_dir / "Politicagem.lnk"
    target_path = LAUNCHER_BAT_PATH

    script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{powershell_escape(str(shortcut_path))}')
$Shortcut.TargetPath = '{powershell_escape(str(target_path))}'
$Shortcut.WorkingDirectory = '{powershell_escape(str(ROOT_DIR))}'
$Shortcut.IconLocation = '{powershell_escape(str(ICON_ICO_PATH))},0'
$Shortcut.Description = 'Politicagem - agregador RSS sem armazenamento local'
$Shortcut.Save()
"""

    run_command(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ]
    )


def run_onboarding(auto: bool, skip_ipfs: bool = False) -> None:
    explain_project()

    do_python = True
    do_electron = True
    do_ipfs = True
    do_shortcut = os.name == "nt"

    if not auto:
        do_python = ask_yes_no("Instalar dependencias Python agora?", default=True)
        do_electron = ask_yes_no("Instalar dependencias Electron agora?", default=True)
        if not skip_ipfs:
            do_ipfs = ask_yes_no("Instalar e configurar IPFS para snapshots estaticos?", default=True)
        if os.name == "nt":
            do_shortcut = ask_yes_no("Criar atalho na Area de Trabalho?", default=True)

    if do_python:
        install_python_dependencies()
        log("[OK] Dependencias Python instaladas.")

    if do_ipfs:
        try:
            install_ipfs()
            initialize_ipfs()
            make_snapshot_script_executable()
            log("[OK] IPFS instalado e configurado.")
        except Exception as exc:
            log(f"[AVISO] Nao foi possivel instalar IPFS automaticamente: {exc}")
            log("        Instale manualmente em: https://docs.ipfs.io/install/")

    if do_electron:
        install_electron_dependencies()
        log("[OK] Dependencias Electron instaladas.")

    if do_shortcut:
        create_desktop_shortcut()
        log("[OK] Atalho da Area de Trabalho criado com o icone do Politicagem.")

    log("\n" + "=" * 60)
    log("Onboarding concluido!")
    log("=" * 60)
    log("\n🚀 Como usar o Politicagem:")
    log("   Servidor web: python app.py")
    log("   Modo terminal: python main.py")
    log("   App desktop:   cd electron-app && npm start")
    log("\n📦 Snapshots estaticos para IPFS:")
    log("   Gerar snapshot: ./generate_snapshot.sh")
    log("   Ou manualmente: python snapshot_generator.py")
    log("\n💡 Para IPFS, certifique-se de iniciar o daemon:")
    log("   ipfs daemon")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Onboarding CLI do Politicagem - configuracao inicial completa"
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Executa tudo sem perguntas (instala Python, IPFS, Electron e atalho no Windows).",
    )
    parser.add_argument(
        "--skip-ipfs",
        action="store_true",
        help="Pula instalacao do IPFS (apenas Python e Electron).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        run_onboarding(auto=args.auto, skip_ipfs=args.skip_ipfs)
    except subprocess.CalledProcessError as exc:
        log(f"\n[ERRO] Falha ao executar comando (codigo {exc.returncode}).")
        raise SystemExit(exc.returncode) from exc
    except Exception as exc:
        log(f"\n[ERRO] {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
