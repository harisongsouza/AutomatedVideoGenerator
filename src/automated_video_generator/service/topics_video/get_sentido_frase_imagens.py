import json
import re
import unicodedata
import uuid
import spacy
from deep_translator import GoogleTranslator

# --- CONFIGURAÇÃO INICIAL (executa apenas uma vez) ---
print("Carregando modelo de linguagem (spaCy)...")
nlp = spacy.load("en_core_web_md")
print("Modelo carregado.")

# --- FUNÇÕES AUXILIARES ---

def remover_acentos(texto):
    """Remove acentos de uma string."""
    return ''.join(c for c in unicodedata.normalize('NFKD', texto) if not unicodedata.combining(c))

def remover_palavras_repetidas(texto):
    """Remove palavras duplicadas de uma string, mantendo a ordem."""
    palavras = texto.split()
    vistas = set()
    resultado = []
    for palavra in palavras:
        if palavra.lower() not in vistas:
            resultado.append(palavra)
            vistas.add(palavra.lower())
    return ' '.join(resultado)

def traduzir_para_ingles(frase):
    """Traduz uma frase de português para inglês."""
    if not frase.strip():
        return ""
    return GoogleTranslator(source='pt', target='en').translate(frase)

def extrair_entidades_ingles(frase_em_pt):
    """Extrai entidades nomeadas de uma frase."""
    frase_em_en = traduzir_para_ingles(frase_em_pt)
    if not frase_em_en:
        return []
    doc = nlp(frase_em_en)
    tipos_desejados = {"PERSON", "ORG", "PRODUCT", "WORK_OF_ART", "GPE", "LOC"}
    entidades = [ent.text for ent in doc.ents if ent.label_ in tipos_desejados]
    return list(set(entidades))

def extrair_nome_base_da_imagem(nome_imagem):
    """Extrai e formata o nome base de uma imagem. Ex: 'imagem_1_intro' -> 'Intro'."""
    # Regex corrigido para capturar o texto até o final da string.
    match = re.search(r"imagem_\d+_(.*)$", nome_imagem)
    if match:
        nome_bruto = match.group(1).replace("_", " ")
        # Remove prefixos comuns para limpar o nome
        nome_bruto = re.sub(r"intervalo (entre|introducao|conclusao|pos)", "", nome_bruto, flags=re.IGNORECASE).strip()
        return nome_bruto.title()
    return ""

# --- FUNÇÃO PRINCIPAL DE PROCESSAMENTO ---

def gerar_termos_de_busca(dados_video, tema_geral):
    """
    Processa os dados do vídeo para adicionar uma 'frase_de_busca' a cada imagem.
    """
    tema_sem_acentos = remover_acentos(tema_geral)
    
    for bloco in dados_video:
        for imagem in bloco.get("imagens", []):
            frase_dita = imagem.get("frase_dita", "")
            
            # 1. Extrai entidades da frase falada
            termos_extraidos = extrair_entidades_ingles(frase_dita)
            
            # 2. Extrai o nome base da própria imagem
            nome_extraido = extrair_nome_base_da_imagem(imagem.get("nome", ""))
            nome_base = re.sub(r'Número\s+\d+', '', nome_extraido)

            
            # 3. Monta a frase de busca
            partes_busca = [tema_sem_acentos, nome_base] + termos_extraidos
            busca_combinada = " ".join(filter(None, partes_busca)) # Une as partes, ignorando as vazias
            
            # 4. Adiciona um ID único para evitar cache excessivo e limpa palavras repetidas
            busca_final = f"{busca_combinada} {uuid.uuid4()}"
            imagem["frase_de_busca"] = remover_palavras_repetidas(busca_final)
            
    return dados_video

# --- EXECUÇÃO ---
 
def main(tema):
    """
    Orquestra o processo: carrega os dados, gera os termos de busca e salva o resultado.
    """
    tema_do_video = tema # Defina o tema principal aqui
    
    arquivo_entrada = "C:/Users/souza/Videos/VideoCreator/data/video_com_frases.json"
    arquivo_saida = "C:/Users/souza/Videos/VideoCreator/data/video_final_com_buscas.json"

    print(f"Lendo arquivo de entrada: {arquivo_entrada}")
    with open(arquivo_entrada, "r", encoding="utf-8") as f:
        dados_iniciais = json.load(f)

    print("Processando e gerando termos de busca...")
    dados_finais = gerar_termos_de_busca(dados_iniciais, tema_do_video)

    print(f"Salvando resultado em: {arquivo_saida}")
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(dados_finais, f, indent=2, ensure_ascii=False)
        
    print("✅ Arquivo criado video_final_com_buscas.json!")
    print("Removendo intervalo_introducao, intervalo_conclusao do arquivo...")
    
    
    #Remover intervalos de introdução e conclusao
    # Carrega o JSON em uma lista de dicionários
        # Caminhos dos arquivos
    entrada_path = "C:/Users/souza/Videos/VideoCreator/data/video_final_com_buscas.json"

    # Carregar os intervalos entre tópicos
    with open(entrada_path, "r", encoding="utf-8") as f:
        termos_chaves_busca = json.load(f)
        
    # Lista para armazenar os objetos que queremos manter
    new_data = []

    # Nomes dos objetos a serem removidos
    nomes_para_remover = ["intervalo_introducao", "intervalo_conclusao"]

    # Itera sobre a lista original e adiciona à nova lista apenas os objetos que não estão na lista de remoção
    for item in termos_chaves_busca:
        if item["nome"] not in nomes_para_remover:
            new_data.append(item)
            
    # Salva em arquivo
    with open(entrada_path, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
        
    print("✅ Processo concluído com sucesso!")

        
if __name__ == "__main__":
    main("aa")