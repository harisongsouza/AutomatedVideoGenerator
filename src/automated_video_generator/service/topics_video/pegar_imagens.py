import subprocess
import json
import os
import shutil
import time
import unicodedata
import uuid  # Para gerar nomes únicos para o backup
from pathlib import Path

def remover_acentos(texto):
    remover = "´^~\"'"  # Adiciona aspas duplas (") e simples (')
    return ''.join(
        c for c in unicodedata.normalize('NFKD', texto)
        if not unicodedata.combining(c) and c not in remover
    )

def executar_script_powershell(caminho_script, urls_file_folder_to_save=None, arquivo_de_urls_path=None, pasta_onde_imagens_serao_salvas=None, frase_de_busca=None):

    if urls_file_folder_to_save is None:
        urls_file_folder_to_save = "None"

    if arquivo_de_urls_path is None:
        arquivo_de_urls_path = "None"

    if pasta_onde_imagens_serao_salvas is None:
        pasta_onde_imagens_serao_salvas = "None"

    if frase_de_busca is None:
        frase_de_busca = "None"

    comando = ["powershell", "-ExecutionPolicy", "Bypass", "-File", caminho_script, urls_file_folder_to_save, arquivo_de_urls_path, pasta_onde_imagens_serao_salvas, frase_de_busca]

    try:
        resultado = subprocess.run(
            comando,
            check=True,
            capture_output=True,
            text=True
        )
        print(f" ✅ Script '{caminho_script}' executado com sucesso!")

        path_line = None
        for line in resultado.stdout.splitlines():
            line = line.strip()
            if line.startswith('{') and '"Path"' in line:
                path_line = line
                break

        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        if caminho_script == BASE_DIR / "utils" / "topics_video" / "download_images_from_links_file.ps1":

            if path_line:
                try:
                    output_dict = json.loads(path_line)
                    if 'Path' in output_dict:
                        caminho_imagem = output_dict['Path']
                        print(f"Caminho Completo Imagem: {caminho_imagem}")
                        data_to_save = {'path_da_imagem': caminho_imagem.replace("\\", "/")}
                        return data_to_save
                    else:
                        print(" ❌ Chave 'Path' não encontrada na linha de saída.")
                        return None
                except json.JSONDecodeError:
                    print(f" ❌ Não foi possível decodificar a linha como JSON: {path_line}")
                    return None
            else:
                print(" ❌ Nenhuma linha JSON com 'Path' encontrada na saída.")
                return None

    except subprocess.CalledProcessError as e:
        print(f" ❌ Erro ao executar {caminho_script}")
        print(e.stderr)
        raise

def deletar_arquivo_downloads(nome_arquivo):
    try:
        # Obtém o caminho para a pasta de Downloads do usuário
        caminho_downloads = os.path.join(os.path.expanduser("~"), "Downloads")

        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        caminho_downloads = BASE_DIR / "data" / "topics_video"

        # Constrói o caminho completo para o arquivo
        caminho_arquivo = os.path.join(caminho_downloads, nome_arquivo)

        # Verifica se o arquivo existe antes de tentar deletar
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
            print(f"Arquivo '{nome_arquivo}' deletado com sucesso da pasta Downloads.")
        else:
            print(f"Arquivo '{nome_arquivo}' não encontrado na pasta Downloads.")

    except Exception as e:
        print(f"Ocorreu um erro ao deletar o arquivo: {e}")


def limpar_apenas_imagens_recursivo(pasta):
    # Extensões que queremos apagar
    extensoes_para_deletar = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.json'}

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
                print(f"Arquivo deletado: {item.name}")

    print(f"✅ Limpeza concluída em {pasta}. Estrutura de pastas e arquivos .py preservada.")


def verificar_arquivo_e_string(nome_arquivo, string_procurada):
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    pasta_downloads = BASE_DIR / "data" / "topics_video"
    caminho_arquivo = os.path.join(pasta_downloads, nome_arquivo)

    if os.path.exists(caminho_arquivo):
        try:
            with open(caminho_arquivo, 'r') as arquivo:
                conteudo = arquivo.read()
                if string_procurada in conteudo:
                    print(f" ✅ Arquivo '{nome_arquivo}' existe e contém conteudo 'https://'.")
                    return True
                else:
                    print(f" ❌ Arquivo '{nome_arquivo}' não existe ou não contém conteudo 'https://'.")
                    return False
        except Exception as e:
            print(f"Erro ao ler o arquivo '{nome_arquivo}': {e}")
            return False
    else:
        print(f"Arquivo '{nome_arquivo}' não foi criado, e não existe na pasta Downloads.")
        time.sleep(5)  # Espera por 5 segundos antes de verificar novamente
        return False


def main():
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    # Caminhos dos scripts
    script1 = BASE_DIR / "utils" / "topics_video" / "duckduckgo.ps1"
    script2 = BASE_DIR / "utils" / "topics_video" / "download_images_from_links_file.ps1"

    # Caminhos dos arquivos
    entrada_path = BASE_DIR / "data" / "topics_video" / "video_final_com_buscas.json"
    urls_file_folder_to_save = BASE_DIR / "data" / "topics_video"
    arquivo_de_urls_path = BASE_DIR / "data" / "topics_video" / "urls.txt"
    pasta_onde_imagens_serao_salvas = BASE_DIR / "assets" / "topics_video" / "imagens"


    # Carregar os intervalos entre tópicos
    with open(entrada_path, "r", encoding="utf-8") as f:
        termos_chaves = json.load(f)

    pasta_para_limpar = BASE_DIR / "assets" / "topics_video" / "imagens"
    limpar_apenas_imagens_recursivo(pasta_para_limpar)

    for topico_intervalo in termos_chaves:
        for images in topico_intervalo["imagens"]:
            frase_de_busca_original = images["frase_de_busca"]
            frase_dita = images["frase_dita"]
            frase_de_busca = remover_acentos(frase_de_busca_original)
            resultado = False

            while resultado is False:
                print("\n#################################################")
                deletar_arquivo_downloads("urls.txt")
                # Executar os scripts
                print(f"FRASE: {frase_dita}")
                frase_de_busca_modificada = frase_de_busca.replace(" ", "_")
                print(f"NOME: {frase_de_busca_modificada.lower()}")

                executar_script_powershell(
                    caminho_script=script1,
                    urls_file_folder_to_save=urls_file_folder_to_save,
                    arquivo_de_urls_path=None,
                    pasta_onde_imagens_serao_salvas=None,
                    frase_de_busca=frase_de_busca
                )

                nome_do_arquivo = "urls.txt"  # Substitua pelo nome real do seu arquivo
                string_para_buscar = "https://"
                resultado = verificar_arquivo_e_string(nome_do_arquivo, string_para_buscar)

                if resultado:
                    path_file = executar_script_powershell(
                        caminho_script=script2,
                        urls_file_folder_to_save=None,
                        arquivo_de_urls_path=arquivo_de_urls_path,
                        pasta_onde_imagens_serao_salvas=pasta_onde_imagens_serao_salvas,
                        frase_de_busca=frase_de_busca
                    )

                    if path_file is None or path_file.get("path_da_imagem") == "None":
                        resultado = False
                    else:
                        images["path"] = path_file["path_da_imagem"]
                print("#################################################\n")

    saida_path = BASE_DIR / "data" / "topics_video" / "add_img_path_img_interv.json"

    # Salva em arquivo
    with open(saida_path, "w", encoding="utf-8") as f:
        json.dump(termos_chaves, f, ensure_ascii=False, indent=2)


    """ saida_path_2 = "C:/Users/souza/Videos/VideoCreator/data/add_img_path_img_interv_SHORTS.json"
    ci = []
    for dd in termos_chaves:
        if dd["camada"] == "intervalo_camada_gelo_profundo":
            ci.append(dd)
    # Salva em arquivo
    with open(saida_path_2, "w", encoding="utf-8") as f:
        json.dump(ci, f, ensure_ascii=False, indent=2) """

    print("CODIGO FINALIZADO!")


if __name__ == "__main__":
    main()
