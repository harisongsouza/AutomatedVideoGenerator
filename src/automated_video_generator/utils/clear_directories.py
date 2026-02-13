from pathlib import Path


def clear_directories(pasta):
    print(f"Limpando pastas do projeto ...")

    # Extensões que queremos apagar
    extensoes_para_deletar = {
        '.json', '.txt',
        '.wav', '.mp3', '.mp4', '.webp',
        '.jpg', '.jpeg', '.png', '.gif'
    }

    caminho_base = Path(pasta)

    # rglob("*") percorre a pasta e TODAS as subpastas
    for item in caminho_base.rglob("*"):
        # Só deleta se:
        # 1. For um arquivo
        # 2. A extensão estiver na lista
        # 3. O nome NÃO for __init__.py (proteção extra)
        if item.is_file() and item.suffix.lower() in extensoes_para_deletar:
            if item.name != "__init__.py":
                item.unlink()
                #print(f"Arquivo deletado: {item.name}")

    print(f"✅ Limpeza concluída em {pasta}. Estrutura de pastas e arquivos .py preservada.")
