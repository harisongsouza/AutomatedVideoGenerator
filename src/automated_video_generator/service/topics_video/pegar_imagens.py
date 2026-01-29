import subprocess
import json
import os
import shutil
import time
import unicodedata
import uuid  # Para gerar nomes únicos para o backup

def remover_acentos(texto):
    remover = "´^~\"'"  # Adiciona aspas duplas (") e simples (')
    return ''.join(
        c for c in unicodedata.normalize('NFKD', texto)
        if not unicodedata.combining(c) and c not in remover
    )
    
def executar_script_powershell(caminho_script, argumento=None):
    comando = ["powershell", "-ExecutionPolicy", "Bypass", "-File", caminho_script]
    
    if argumento:
        comando.append(argumento)

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

        if caminho_script == "C:/Users/souza/Videos/VideoCreator/utils/download_images_from_links_file.ps1":
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
        

def deletar_e_recriar_pasta_preservando_subpasta_seguro(caminho_pasta_principal: str, nome_da_pasta_a_preservar: str):

    # Validar se nome_da_pasta_a_preservar é apenas um nome e não um caminho
    if os.path.sep in nome_da_pasta_a_preservar or \
       (os.path.altsep and os.path.altsep in nome_da_pasta_a_preservar):
        print(f"ERRO CRÍTICO: 'nome_da_pasta_a_preservar' ('{nome_da_pasta_a_preservar}') "
              f"deve ser apenas o nome da pasta, não um caminho. Operação abortada.")
        return

    caminho_pasta_principal_abs = os.path.abspath(caminho_pasta_principal)
    caminho_subpasta_original = os.path.join(caminho_pasta_principal_abs, nome_da_pasta_a_preservar)

    # Define um local de backup temporário ao lado da pasta principal
    diretorio_pai = os.path.dirname(caminho_pasta_principal_abs)
    # Gerar um nome único e identificável para o backup
    nome_backup_temporario = f"{nome_da_pasta_a_preservar}__{uuid.uuid4().hex[:8]}__BACKUP_TEMP"
    caminho_backup_temporario = os.path.join(diretorio_pai, nome_backup_temporario)

    subpasta_foi_movida_para_backup = False

    try:
        print(f"--- Iniciando operação para '{caminho_pasta_principal_abs}' preservando '{nome_da_pasta_a_preservar}' ---")

        # 0. Verificar se o local de backup já existe (conflito inesperado)
        if os.path.exists(caminho_backup_temporario):
            print(f"ERRO CRÍTICO: Um local de backup com o nome '{caminho_backup_temporario}' já existe. "
                  f"Por favor, remova-o ou renomeie-o antes de prosseguir. Operação abortada.")
            return

        # 1. Mover a subpasta a ser preservada para o local de backup (se existir)
        if os.path.exists(caminho_subpasta_original) and os.path.isdir(caminho_subpasta_original):
            print(f"Passo 1: Movendo subpasta '{caminho_subpasta_original}' para backup em '{caminho_backup_temporario}'...")
            shutil.move(caminho_subpasta_original, caminho_backup_temporario)
            subpasta_foi_movida_para_backup = True
            print(f"Passo 1: Subpasta '{nome_da_pasta_a_preservar}' movida para backup com sucesso.")
        elif os.path.exists(caminho_pasta_principal_abs): # Pasta principal existe, mas subpasta não
            print(f"Passo 1: Subpasta a preservar '{caminho_subpasta_original}' não encontrada dentro de '{caminho_pasta_principal_abs}'. Nada a preservar em backup.")
        else: # Nem a pasta principal existe
            print(f"Passo 1: Pasta principal '{caminho_pasta_principal_abs}' não existe. A subpasta '{nome_da_pasta_a_preservar}' também não.")

        # 2. Deletar a pasta principal original (se existir)
        if os.path.exists(caminho_pasta_principal_abs):
            print(f"Passo 2: Deletando pasta principal original '{caminho_pasta_principal_abs}'...")
            shutil.rmtree(caminho_pasta_principal_abs)
            print(f"Passo 2: Pasta principal original '{caminho_pasta_principal_abs}' deletada.")
        else:
            print(f"Passo 2: Pasta principal '{caminho_pasta_principal_abs}' não existia para ser deletada.")

        # 3. Recriar a pasta principal
        print(f"Passo 3: Recriando pasta principal '{caminho_pasta_principal_abs}'...")
        os.makedirs(caminho_pasta_principal_abs) # Não usar exist_ok=True, pois acabamos de deletá-la (ou não existia)
        print(f"Passo 3: Nova pasta principal '{caminho_pasta_principal_abs}' criada.")

        # 4. Mover a subpasta de volta do backup (se foi movida)
        if subpasta_foi_movida_para_backup:
            destino_final_subpasta = os.path.join(caminho_pasta_principal_abs, nome_da_pasta_a_preservar)
            print(f"Passo 4: Restaurando '{nome_da_pasta_a_preservar}' de '{caminho_backup_temporario}' para '{destino_final_subpasta}'...")
            shutil.move(caminho_backup_temporario, destino_final_subpasta)
            # Se shutil.move for bem-sucedido, caminho_backup_temporario (a pasta) não existe mais com esse nome.
            subpasta_foi_movida_para_backup = False # Importante: marcar que não está mais em backup
            print(f"Passo 4: Subpasta '{nome_da_pasta_a_preservar}' restaurada com sucesso.")

        print("--- Operação concluída com sucesso. ---")

    except Exception as e:
        print(f"!!!!!!!! ERRO DURANTE A OPERAÇÃO !!!!!!!!")
        print(f"Detalhes do erro: {type(e).__name__} - {e}")
        if subpasta_foi_movida_para_backup:
            # A subpasta está no local de backup e não foi restaurada.
            print(f"###########################################################################")
            print(f"ATENÇÃO CRÍTICA: A subpasta '{nome_da_pasta_a_preservar}' ESTÁ SEGURA EM:")
            print(f"'{caminho_backup_temporario}'")
            print(f"Ela NÃO foi restaurada para '{os.path.join(caminho_pasta_principal_abs, nome_da_pasta_a_preservar)}' devido ao erro.")
            print(f"Por favor, MOVA-A MANUALMENTE para o local desejado e verifique a integridade.")
            print(f"NÃO delete o backup '{caminho_backup_temporario}' até verificar os dados.")
            print(f"###########################################################################")
        else:
            # A subpasta não foi movida para backup, ou o erro ocorreu antes dessa etapa, ou já foi restaurada (menos provável).
            print(f"A subpasta '{nome_da_pasta_a_preservar}' não estava (ou não deveria estar) no local de backup ('{caminho_backup_temporario}') no momento do erro.")
            print(f"Isso pode significar que:")
            print(f"  a) Ela não existia originalmente em '{caminho_subpasta_original}'.")
            print(f"  b) O erro ocorreu antes da tentativa de movê-la para backup.")
            print(f"  c) Ou, menos provável, ela foi restaurada e um erro ocorreu depois.")
            print(f"Verifique o estado de '{caminho_pasta_principal_abs}' e o local original da subpasta.")
            if os.path.exists(caminho_backup_temporario): # Se o backup ainda existe por algum motivo MUITO inesperado
                 print(f"AVISO INESPERADO: Um local de backup '{caminho_backup_temporario}' FOI ENCONTRADO. Verifique seu conteúdo IMEDIATAMENTE.")
    finally:
        print(f"--- Finalizando script para '{caminho_pasta_principal_abs}'. ---")
        # NENHUMA limpeza automática do caminho_backup_temporario aqui para máxima segurança.
        # Se a operação foi bem-sucedida, ele foi movido (não existe mais com aquele nome).
        # Se falhou e a subpasta estava lá, ela PERMANECE lá para recuperação manual.
        if subpasta_foi_movida_para_backup and os.path.exists(caminho_backup_temporario):
            print(f"LEMBRETE: Conforme indicado acima devido a um erro, a subpasta '{nome_da_pasta_a_preservar}' deve estar em '{caminho_backup_temporario}'.")
            print(f"É SUA RESPONSABILIDADE gerenciá-la a partir desse local.")
        elif not subpasta_foi_movida_para_backup and os.path.exists(caminho_backup_temporario):
            # Este caso é muito estranho: a flag diz que não está em backup, mas o caminho de backup existe.
            # Indica uma possível falha na lógica ou um estado inesperado.
            print(f"ALERTA DE INCONSISTÊNCIA: O local de backup '{caminho_backup_temporario}' existe, mas a flag interna "
                  f"indica que a subpasta não deveria estar lá. Isso é altamente inesperado. "
                  f"Por favor, VERIFIQUE o conteúdo de '{caminho_backup_temporario}' CUIDADOSAMENTE.")
                  
                 
                 

def verificar_arquivo_e_string(nome_arquivo, string_procurada):
    pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
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
    # Caminhos dos scripts
    script1 = r"C:/Users/souza/Videos/VideoCreator/utils/duckduckgo.ps1"
    script2 = r"C:/Users/souza/Videos/VideoCreator/utils/download_images_from_links_file.ps1"
        
    # Caminhos dos arquivos
    entrada_path = "C:/Users/souza/Videos/VideoCreator/data/video_final_com_buscas.json"

    # Carregar os intervalos entre tópicos
    with open(entrada_path, "r", encoding="utf-8") as f:
        termos_chaves = json.load(f)
    
    pasta_para_manipular = r"C:/Users/souza/Videos/VideoCreator/assets/imagens"
    pasta_preservar = r"imagens_camadas"
    deletar_e_recriar_pasta_preservando_subpasta_seguro(pasta_para_manipular, pasta_preservar)
    
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
                
                executar_script_powershell(script1, frase_de_busca)
                                
                nome_do_arquivo = "urls.txt"  # Substitua pelo nome real do seu arquivo
                string_para_buscar = "https://"
                resultado = verificar_arquivo_e_string(nome_do_arquivo, string_para_buscar)
                
                if resultado:
                    path_file = executar_script_powershell(script2, frase_de_busca)
                    if path_file is None or path_file.get("path_da_imagem") == "None":
                        resultado = False
                    else:
                        images["path"] = path_file["path_da_imagem"]
                print("#################################################\n")
                
    saida_path = "C:/Users/souza/Videos/VideoCreator/data/add_img_path_img_interv.json"
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