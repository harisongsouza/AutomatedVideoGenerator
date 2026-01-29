import json
import unicodedata
import re
from rapidfuzz.fuzz import ratio
from thefuzz import fuzz

""" def extrair_topicos_do_arquivo(caminho_do_arquivo):
    topicos_encontrados = []
    try:
        with open(caminho_do_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.read()
            # Expressão regular para encontrar o padrão "Número X. Tema."
            # \d+ corresponde a um ou mais dígitos
            # .*? corresponde a qualquer caractere (exceto nova linha) o mínimo possível
            # \. corresponde ao ponto final literal
            padrao = r"Número\s\d+\.\s.*?\."
            topicos_encontrados = re.findall(padrao, conteudo)
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_do_arquivo}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")
    return topicos_encontrados """

def extrair_topicos_do_arquivo(caminho_do_arquivo):
    topicos_encontrados = []
    try:
        with open(caminho_do_arquivo, 'r', encoding='utf-8') as arquivo:
            conteudo = arquivo.read()
            
            # Expressão regular modificada para encontrar um dos dois padrões:
            # 1. "Número \d+\. .*?\." -> Para "Número X. Tema."
            # 2. "Espero que tenham gostado\." -> Para a frase exata
            # O operador "|" funciona como um "OU"
            padrao = r"(Número\s\d+\.\s.*?\.)|(Espero que tenham gostado\.)"
            
            topicos_encontrados = re.findall(padrao, conteudo)
            
            # re.findall com grupos de captura (usando parênteses) retorna uma
            # lista de tuplas. Precisamos achatar a lista para ter um resultado simples.
            topicos_encontrados = [item for tupla in topicos_encontrados for item in tupla if item]

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_do_arquivo}' não foi encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro ao ler o arquivo: {e}")
        
    return topicos_encontrados

json_path = "C:/Users/souza/Videos/VideoCreator/data/transcription_words.json"
saida_path = "C:/Users/souza/Videos/VideoCreator/data/topicos.json"
limiar_similaridade = 75  

#criar funcao regex para pegar topicos do roteiro de forma automatica.
""" frases_alvo = [
    "Número 1. Bob Esponja.",
    "Número 2. Dragon Ball Z.",
    "Número 3. Padrinhos Mágicos.",
    "Número 1. Fadas.",
    "Número 2. Os Jetsons.",
    "Número 3. O Homem de Ferro (anos 60).",
    "Número 1. A Turma do Didi.",
    "Número 2. Os Herculóides.",
    "Número 3. Caverna do Dragão.",
    "Número 1. Beavis and Butt-Head.",
    "Número 2. Ren & Stimpy.",
    "Número 3. Freakazoid.",
    "Número 1. Luluca.",
    "Número 2. Episódio perdido de Caverna do Dragão.",
    "Número 3. O desenho maldito de 1984."
] """

""" 
def normalizar(texto):
    "Remove acentos, pontuação, caixa alta e espaços extras."
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    texto = re.sub(r'[^\w\s]', '', texto)  # remove pontuação
    return re.sub(r'\s+', ' ', texto).strip().lower()
 """

""" def encontrar_frases_em_transcricao(transcricao, frases_alvo, limiar=80):
    "Procura frases-alvo (com 2+ palavras) na transcrição."
    resultados = []
    palavras = transcricao

    for frase_alvo in frases_alvo:
        frase_alvo_normalizada = normalizar(frase_alvo)
        num_palavras = len(frase_alvo.split())

        for i in range(len(palavras) - num_palavras + 1):
            bloco = palavras[i:i + num_palavras]
            frase_bloco = ' '.join(p["word"].strip() for p in bloco)
            frase_bloco_normalizada = normalizar(frase_bloco)

            similaridade = ratio(frase_bloco_normalizada, frase_alvo_normalizada)

            if similaridade >= limiar:
                resultados.append({
                    "word": frase_alvo,
                    "start": bloco[0]["start"],
                    "end": bloco[-1]["end"],
                    "find": frase_bloco
                })

    return resultados """
    #forma que funciona antiga, mas encontra e tras mais de uma frase para um topico


def normalizar(texto):
    """Converte para minúsculas e remove pontuações básicas."""
    texto = texto.lower()
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto


def encontrar_melhor_correspondencia(transcricao, frases_alvo, limiar=80):
    resultados_finais = []
    palavras_transcricao = transcricao

    # Itera sobre cada frase que queremos encontrar
    for frase_alvo in frases_alvo:
        # Variáveis para guardar a melhor correspondência encontrada ATÉ AGORA para esta frase_alvo
        melhor_match = None
        maior_similaridade = -1  # Começa com -1 para garantir que a primeira acima do limiar seja pega

        frase_alvo_normalizada = normalizar(frase_alvo)
        num_palavras_alvo = len(frase_alvo.split())
        
        if len(palavras_transcricao) < num_palavras_alvo:
            continue

        # Itera sobre todos os blocos de texto possíveis na transcrição
        for i in range(len(palavras_transcricao) - num_palavras_alvo + 1):
            bloco = palavras_transcricao[i : i + num_palavras_alvo]
            frase_bloco = ' '.join(p["word"].strip() for p in bloco)
            frase_bloco_normalizada = normalizar(frase_bloco)

            # Calcula a similaridade
            similaridade = fuzz.ratio(frase_bloco_normalizada, frase_alvo_normalizada)

            # Se encontrarmos uma correspondência MELHOR que a anterior E acima do limiar...
            if similaridade > maior_similaridade and similaridade >= limiar:
                # ...atualizamos a nossa melhor correspondência.
                maior_similaridade = similaridade
                
                # Determina o 'end_time' corretamente
                end_time_calculado = None
                indice_palavra_seguinte = i + num_palavras_alvo # 'num_palavras_alvo' é o número de palavras na frase_alvo
                
                if indice_palavra_seguinte < len(palavras_transcricao):
                    # Se houver uma próxima palavra, 'end' é o 'start' dela
                    end_time_calculado = palavras_transcricao[indice_palavra_seguinte]["start"]
                else:
                    # Se for o final da transcrição, 'end' é o 'end' da última palavra do bloco
                    end_time_calculado = bloco[-1]["end"]
                
                melhor_match = {
                    "word": frase_alvo,
                    "start": bloco[0]["start"],
                    "end": end_time_calculado, # <<<<<< LINHA MODIFICADA
                    "find": frase_bloco,
                    "similarity": similaridade
                }

    # Ao final da busca para a frase_alvo atual, se um bom match foi encontrado,
    # adiciona-o à lista de resultados finais.
        if melhor_match:
            resultados_finais.append(melhor_match)

    return resultados_finais
 

def main():
    frases_alvo = extrair_topicos_do_arquivo("C:/Users/souza/Videos/VideoCreator/data/roteiro.txt")
    with open(json_path, "r", encoding="utf-8") as f:
        transcricao = json.load(f)

    resultados = encontrar_melhor_correspondencia(transcricao, frases_alvo, limiar_similaridade)
    print("Topicos gerados com sucesso.")
    #print(resultados)
    #tem que descartar os termos que nao tem os "numero 1." antes deles, e manter só o que tem.
    #isso nao esta sendo feito.
    
    # Salva em arquivo
    with open(saida_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
        
        
if __name__ == "__main__": 
    main()