import json
import math
import re

def adicionar_imagens_em_intervalos(entrada_json, saida_json, duracao_imagem=6, tolerancia_minima=4):
    with open(entrada_json, "r", encoding="utf-8") as f:
        intervalos = json.load(f)

    novos_intervalos = []

    for intervalo in intervalos:
        inicio = intervalo["start"]
        fim = intervalo["end"]
        duracao = fim - inicio

        imagens = []
        tempo_atual = inicio
        i = 1

        while tempo_atual + duracao_imagem <= fim:
            # Regex para o nome das imagens
            texto = re.sub(r"^Número\s*\d+\.\s*", "", intervalo['topico_atual'], flags=re.IGNORECASE)
            texto = texto.replace(" ", "_")
            texto = texto.lower().strip("_")
            
            imagens.append({
                "nome": f"imagem_{i}_{texto}",
                "start": tempo_atual,
                "end": tempo_atual + duracao_imagem
            })
            tempo_atual += duracao_imagem
            i += 1

        tempo_restante = fim - tempo_atual

        if tempo_restante >= tolerancia_minima:
            # Regex para o nome das imagens
            texto = re.sub(r"^Número\s*\d+\.\s*", "", intervalo['topico_atual'], flags=re.IGNORECASE)
            texto = texto.replace(" ", "_")
            texto = texto.lower().strip("_")

            imagens.append({
                "nome": f"imagem_{i}_{texto}",
                "start": tempo_atual,
                "end": fim
            })
        elif tempo_restante > 0 and imagens:
            imagens[-1]["end"] = fim  # estende a última imagem
        elif tempo_restante > 0 and not imagens:
            # Regex para o nome das imagens
            texto = re.sub(r"^Número\s*\d+\.\s*", "", intervalo['topico_atual'], flags=re.IGNORECASE)
            texto = texto.replace(" ", "_")
            texto = texto.lower().strip("_")
            
            # Caso o intervalo total seja menor que 4 segundos
            imagens.append({
                "nome": f"imagem_{i}_{texto}",
                "start": tempo_atual,
                "end": fim
            })

        novo_intervalo = intervalo.copy()
        novo_intervalo["imagens"] = imagens
        novos_intervalos.append(novo_intervalo)

    with open(saida_json, "w", encoding="utf-8") as f:
        json.dump(novos_intervalos, f, ensure_ascii=False, indent=2)

    print(f"✅ Imagens adicionadas com sucesso em: {saida_json}")


def main():
    # Caminhos dos arquivos
    entrada_path = "C:/Users/souza/Downloads/VideoCreator/data/intervalos_entre_topicos.json"
    saida_path = "C:/Users/souza/Downloads/VideoCreator/data/imagens_em_intervalos_topicos.json"

    # Parâmetro de tempo para exibição de cada imagem
    duracao_imagem = 15.0
    tolerancia_minima = 7.0

    # Gerar e salvar
    adicionar_imagens_em_intervalos(entrada_path, saida_path, duracao_imagem, tolerancia_minima)
    
    
if __name__ == "__main__":
    main()