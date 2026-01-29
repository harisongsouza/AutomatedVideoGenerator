import json
import bisect

def carregar_json(caminho_arquivo):
    """Carrega dados de um arquivo JSON."""
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)

def salvar_json(dados, caminho_arquivo):
    """Salva dados em um arquivo JSON."""
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

def montar_frases_para_imagens(caminho_json_estrutura, caminho_json_transcricao, caminho_json_saida):
    """
    Atribui as palavras faladas a cada intervalo de imagem de forma otimizada.
    """
    estrutura_video = carregar_json(caminho_json_estrutura)
    transcricao = carregar_json(caminho_json_transcricao)
    
    # Garante que a transcrição esteja ordenada por tempo para a busca otimizada
    transcricao.sort(key=lambda p: p['start'])
    # Cria uma lista apenas com os tempos de início para a busca binária
    tempos_de_inicio = [p['start'] for p in transcricao]

    for segmento in estrutura_video:
        if "imagens" in segmento:
            for imagem in segmento["imagens"]:
                img_start = imagem["start"]
                img_end = imagem["end"]
                
                # Otimização: Encontra o índice da primeira palavra relevante usando busca binária.
                # Isso evita ter que percorrer a lista de transcrição desde o início a cada vez.
                start_index = bisect.bisect_left(tempos_de_inicio, img_start)
                
                palavras_no_intervalo = []
                # Percorre a transcrição apenas a partir do índice encontrado
                for i in range(start_index, len(transcricao)):
                    palavra_entry = transcricao[i]
                    
                    # Se a palavra atual já está fora do tempo da imagem, podemos parar
                    if palavra_entry['start'] >= img_end:
                        break
                    
                    palavras_no_intervalo.append(palavra_entry["word"].strip().replace("–", ""))
                
                imagem["frase_dita"] = " ".join(palavras_no_intervalo)

    salvar_json(estrutura_video, caminho_json_saida)
    print(f"✅ Frases atribuídas com sucesso em: {caminho_json_saida}")


def main():
    caminho_estrutura = "C:/Users/souza/Videos/VideoCreator/data/imagens_em_intervalos_topicos.json"
    caminho_transcricao = "C:/Users/souza/Videos/VideoCreator/data/transcription_words.json"
    caminho_saida = "C:/Users/souza/Videos/VideoCreator/data/video_com_frases.json"

    montar_frases_para_imagens(caminho_estrutura, caminho_transcricao, caminho_saida)
    
if __name__ == "__main__":
    main()