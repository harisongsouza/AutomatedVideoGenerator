import json
import unicodedata
import re
from rapidfuzz.fuzz import ratio

def main():
    # === CONFIGURAÇÃO ===
    # Caminho para o JSON
    json_path = "C:/Users/souza/Downloads/VideoCreator/data/transcription_words.json"

    # Lista de frases que você quer encontrar
    frases_alvo = [
        "Camada Superfície Brilhante",
        "Camada Congelada",
        "Camada Submersa",
        "Camada Gelo Profundo",
        "Camada Núcleo Abissal",
        "Espero que tenham gostado."
    ]
    limiar_similaridade = 90  # de 0 a 100


    # === FUNÇÕES ===

    # Normaliza strings (tira acento, caixa alta, etc.)
    def normalizar(texto):
        texto = ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
        return texto.lower().strip()


    def encontrar_frases_em_transcricao(transcricao, frases_alvo, limiar=80):
        """Procura frases-alvo (com 2+ palavras) na transcrição."""
        resultados = []
        palavras = transcricao

        for frase_alvo in frases_alvo:
            if frase_alvo == "Camada Superfície Brilhante":
                video_path = "C:/Users/souza/Downloads/VideoCreator/assets/videos/camadas/camada_superficie_brilhante.mp4"
                img_sobreposta = "C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_camadas/imagens_sobreposta_camadas/1.jpg"
            elif frase_alvo == "Camada Congelada":
                video_path = "C:/Users/souza/Downloads/VideoCreator/assets/videos/camadas/camada_congelada.mp4"
                img_sobreposta = "C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_camadas/imagens_sobreposta_camadas/2.jpg"
            elif frase_alvo == "Camada Submersa":
            #elif frase_alvo == "Zona Submersa":
                video_path = "C:/Users/souza/Downloads/VideoCreator/assets/videos/camadas/camada_submersa.mp4"
                img_sobreposta = "C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_camadas/imagens_sobreposta_camadas/3.jpeg"
            elif frase_alvo == "Camada Gelo Profundo":
            #elif frase_alvo == "Gelo Profundo":
                video_path = "C:/Users/souza/Downloads/VideoCreator/assets/videos/camadas/camada_gelo_profundo.mp4"
                img_sobreposta = "C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_camadas/imagens_sobreposta_camadas/4.jpeg"
            elif frase_alvo == "Camada Núcleo Abissal":
                video_path = "C:/Users/souza/Downloads/VideoCreator/assets/videos/camadas/camada_nucleo_abissal.mp4"
                img_sobreposta = "C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_camadas/imagens_sobreposta_camadas/5.jpeg"
            elif frase_alvo == "Espero que tenham gostado.":
                video_path = "C:/Users/souza/Downloads/VideoCreator/assets/videos/camadas/espero_que_tenha_gostado.mp4"
                img_sobreposta = "C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_camadas/imagens_sobreposta_camadas/1.jpg"
            frase_alvo_normalizada = normalizar(frase_alvo)
            num_palavras = len(frase_alvo.split())

            for i in range(len(palavras) - num_palavras + 1):
                bloco = palavras[i:i + num_palavras]
                frase_bloco = ' '.join(p["word"].strip() for p in bloco)
                frase_bloco_normalizada = normalizar(frase_bloco)

                similaridade = ratio(frase_bloco_normalizada, frase_alvo_normalizada)

                if similaridade >= limiar:
                    end_time = None
                    # Caso especial para "Espero que tenham gostado."
                    if frase_alvo == "Espero que tenham gostado.":
                        end_time = palavras[-1]["end"]
                    else:
                        # Verifica se há uma palavra seguinte na transcrição
                        indice_palavra_seguinte = i + num_palavras
                        if indice_palavra_seguinte < len(palavras):
                            end_time = palavras[indice_palavra_seguinte]["start"]
                        else:
                            # Se a frase encontrada é a última parte da transcrição,
                            # usa o "end" da última palavra do bloco
                            end_time = bloco[-1]["end"]
                    
                    # Garante que end_time tenha um valor (fallback para o final da última palavra do bloco se algo der errado)
                    if end_time is None:
                        end_time = bloco[-1]["end"]
                    
                    resultados.append({
                        "word": frase_alvo,
                        "start": bloco[0]["start"],
                        "end": end_time,
                        "find": frase_bloco,
                        "video_path_base": video_path,
                        "img_sobreposta": img_sobreposta
                    })

        return resultados


    # === EXECUÇÃO ===

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            transcricao = json.load(f)
    except Exception as e:
        print(f"Erro ao carregar JSON: {e}")
        transcricao = []

    try:
        resultados = encontrar_frases_em_transcricao(transcricao, frases_alvo, limiar_similaridade)
        #resultados_sem_ultimo_repetido_item = resultados[:-1]
        saida_path = "C:/Users/souza/Downloads/VideoCreator/data/camadas.json"
        # Salva em arquivo
        with open(saida_path, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
            #json.dump(resultados_sem_ultimo_repetido_item, f, ensure_ascii=False, indent=2)


        if(len(resultados) == 6):
            print(f"✅ {len(resultados)} resultado(s) encontrado(s). Salvo em: {saida_path}")
        #if(len(resultados_sem_ultimo_repetido_item) == 6):
         #   print(f"✅ {len(resultados_sem_ultimo_repetido_item)} resultado(s) encontrado(s). Salvo em: {saida_path}")
        else:
            print(f"❌ Não tem 6 resultado(s) encontrado(s). Salvo em: {saida_path}")
    except Exception as e:
        print(f"Erro ao processar frases: {e}")

if __name__ == "__main__":
    main()