import json
from automated_video_generator.config import BASE_DIR

def adicionar_imagens_em_intervalos(entrada_json, saida_json, duracao_imagem=6, tolerancia_minima=4):
    """
    Lê um arquivo JSON de intervalos, e para cada intervalo, gera uma lista
    de "imagens" que preenchem a duração daquele intervalo.
    """
    with open(entrada_json, "r", encoding="utf-8") as f:
        intervalos = json.load(f)

    novos_intervalos = []

    for intervalo in intervalos:
        inicio = intervalo["start"]
        fim = intervalo["end"]

        # Usa o nome do próprio intervalo como base para os nomes das imagens.
        # Ex: "intervalo_introducao", "intervalo_conclusao", etc.
        base_nome_imagem = intervalo["nome"]

        imagens = []
        tempo_atual = inicio
        i = 1

        # Adiciona imagens de duração fixa enquanto houver espaço
        while tempo_atual + duracao_imagem <= fim:
            imagens.append({
                "nome": f"imagem_{i}_{base_nome_imagem}",
                "start": tempo_atual,
                "end": tempo_atual + duracao_imagem
            })
            tempo_atual += duracao_imagem
            i += 1

        tempo_restante = fim - tempo_atual

        if tempo_restante >= tolerancia_minima:
            # Se o tempo restante for grande o suficiente, cria uma nova imagem
            imagens.append({
                "nome": f"imagem_{i}_{base_nome_imagem}",
                "start": tempo_atual,
                "end": fim
            })
        elif tempo_restante > 0 and imagens:
            # Se for pequeno, apenas estende a duração da última imagem adicionada
            imagens[-1]["end"] = fim
        elif tempo_restante > 0 and not imagens:
            # Se o intervalo inteiro for menor que a duração de uma imagem,
            # cria uma única imagem que o preenche completamente.
            imagens.append({
                "nome": f"imagem_1_{base_nome_imagem}",
                "start": inicio,
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
    entrada_path = BASE_DIR / "data" / "topics_video" / "intervalos_entre_topicos.json"
    saida_path = BASE_DIR / "data" / "topics_video" / "imagens_em_intervalos_topicos.json"

    # Parâmetros de tempo para exibição de cada imagem (em segundos)
    duracao_imagem = 15.0
    tolerancia_minima = 7.0

    # Gerar e salvar
    adicionar_imagens_em_intervalos(entrada_path, saida_path, duracao_imagem, tolerancia_minima)


if __name__ == "__main__":
    main()
