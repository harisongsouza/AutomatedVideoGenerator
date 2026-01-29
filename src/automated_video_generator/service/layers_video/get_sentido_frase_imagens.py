import spacy
from deep_translator import GoogleTranslator
import json
import re
import unicodedata
import uuid

# Carrega modelo spaCy em inglês
nlp = spacy.load("en_core_web_md")

def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFKD', texto)
        if not unicodedata.combining(c)
    )
    
def remover_palavras_repetidas(texto):
    palavras = texto.split()
    vistas = set()
    resultado = []
    for palavra in palavras:
        if palavra.lower() not in vistas:
            resultado.append(palavra)
            vistas.add(palavra.lower())
    return ' '.join(resultado)

# Função de tradução
def traduzir_para_ingles(frase):
    return GoogleTranslator(source='pt', target='en').translate(frase)

# Extrair entidades relevantes
def extrair_entidades_ingles(frase_em_pt):
    frase_em_en = traduzir_para_ingles(frase_em_pt)
    doc = nlp(frase_em_en)
    tipos_desejados = {"PERSON", "ORG", "PRODUCT", "WORK_OF_ART"}
    entidades = [ent.text for ent in doc.ents if ent.label_ in tipos_desejados]
    return list(set(entidades))  # Remove duplicatas

# Extrair nome formatado da imagem
def extrair_nome_formatado(nome_arquivo):
    match = re.search(r"imagem_\d+_(.*?)\.", nome_arquivo)
    if match:
        nome_bruto = match.group(1)
        nome_formatado = nome_bruto.replace("_", " ").title()
        return nome_formatado
    return ""

def get_palavras_chaves_intervalo(frase):
    tema_do_video = remover_acentos(frase)
    # Caminhos dos arquivos
    arquivo_entrada = "C:/Users/souza/Downloads/VideoCreator/data/video_com_frases_exemplo.json"
    arquivo_saida = "C:/Users/souza/Downloads/VideoCreator/data/termos_chaves_para_buscar_imagem.json"
 
    # Ler JSON original
    with open(arquivo_entrada, "r", encoding="utf-8") as f:
        dados_lista = json.load(f)

    # Processar cada bloco de dados
    for bloco in dados_lista:
        for imagem in bloco.get("imagens", []):
            frase = imagem.get("frase_dita", "")
            termos_extraidos = extrair_entidades_ingles(frase)
            nome_formatado = extrair_nome_formatado(imagem.get("nome", ""))
            if termos_extraidos:
                busca = nome_formatado + "  " + "  ".join(termos_extraidos)
            else:
                busca = nome_formatado
            id_unico = str(uuid.uuid4())
            tema = tema_do_video + " " + busca + " " + id_unico
            imagem["frase_de_busca"] = remover_palavras_repetidas(tema)
            #imagem["frase_de_busca"] = busca

    # Salvar novo JSON
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(dados_lista, f, indent=2, ensure_ascii=False)

    print("Arquivo salvo como:", arquivo_saida)

def main(tema):
    get_palavras_chaves_intervalo(tema)
    
if __name__ == "__main__":
    main()
    
#SE PARAR DE FUNCIONAR O JEITO SERÁ NA FORÇA BRUTA ABRINDO GPT E PEDINDO PARA ELE DIZER A "FRASE_DE_BUSCA"
#RECEBER TEMA DO VIDEO