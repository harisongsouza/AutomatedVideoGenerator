import json

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
    Monta as frases ditas durante cada imagem e cria um novo JSON.

    Args:
        caminho_json_estrutura (str): Caminho para o JSON com a estrutura de tópicos e imagens.
        caminho_json_transcricao (str): Caminho para o JSON com a transcrição palavra por palavra.
        caminho_json_saida (str): Caminho onde o novo JSON com as frases será salvo.
    """
    estrutura_video = carregar_json(caminho_json_estrutura)
    transcricao = carregar_json(caminho_json_transcricao)

    nova_estrutura_video = []

    for segmento in estrutura_video:
        novo_segmento = segmento.copy()  # Copia o segmento original
        if "imagens" in novo_segmento:
            novas_imagens_info = []
            for imagem_info in novo_segmento["imagens"]:
                img_start_time = imagem_info["start"]
                img_end_time = imagem_info["end"]

                palavras_no_intervalo = []
                for palavra_entry in transcricao:
                    palavra_start_time = palavra_entry["start"]
                    # Consideramos uma palavra como parte da frase da imagem se
                    # o início da palavra estiver dentro do intervalo de tempo da imagem.
                    # [img_start_time, img_end_time)
                    if palavra_start_time >= img_start_time and palavra_start_time < img_end_time:
                        # .strip() remove espaços extras no início/fim da palavra (ex: " Quem")
                        palavras_no_intervalo.append(palavra_entry["word"].strip())
                    
                    # Otimização: Se a transcrição estiver ordenada por tempo e a palavra atual
                    # já começou depois do fim da imagem, podemos parar de procurar para esta imagem.
                    if palavra_start_time >= img_end_time and len(palavras_no_intervalo) > 0:
                        # Esta otimização assume que a lista de transcrição está ordenada.
                        # Se não tiver certeza, remova este `break`.
                        break 


                frase_dita = " ".join(palavras_no_intervalo)

                nova_imagem_info = imagem_info.copy()
                nova_imagem_info["frase_dita"] = frase_dita
                novas_imagens_info.append(nova_imagem_info)
            
            novo_segmento["imagens"] = novas_imagens_info
        nova_estrutura_video.append(novo_segmento)

    salvar_json(nova_estrutura_video, caminho_json_saida)
    print(f"Novo JSON com frases gerado em: {caminho_json_saida}")
    return nova_estrutura_video


def main():
    # Crie arquivos de exemplo para testar (copie e cole seu JSON de exemplo neles)

    # Definir os caminhos para os arquivos de exemplo
    caminho_estrutura_exemplo = "C:/Users/souza/Downloads/VideoCreator/data/imagens_em_intervalos_topicos.json"
    caminho_transcricao_exemplo = "C:/Users/souza/Downloads/VideoCreator/data/transcription_words.json"
    caminho_saida_exemplo = "C:/Users/souza/Downloads/VideoCreator/data/video_com_frases_exemplo.json"

    # Executar a função principal
    dados_gerados = montar_frases_para_imagens(
        caminho_estrutura_exemplo,
        caminho_transcricao_exemplo,
        caminho_saida_exemplo
    )

    # Opcional: Imprimir o resultado para verificação rápida
    # print("\nDados gerados:")
    # print(json.dumps(dados_gerados, ensure_ascii=False, indent=2))
    
if __name__ == "__main__":
    main()