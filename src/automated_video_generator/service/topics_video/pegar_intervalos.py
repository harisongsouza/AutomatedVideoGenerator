import json
from pathlib import Path

def gerar_intervalos_entre_topicos(transcricao, topicos):
    """
    Gera intervalos de tempo entre os tópicos fornecidos, cobrindo toda a transcrição.
    Inclui um intervalo de introdução (do início até o primeiro tópico) e um
    intervalo de conclusão (do fim do último tópico até o final da transcrição).
    """
    if not transcricao or not topicos:
        return []

    intervalos = []

    # Ordena a transcrição e os tópicos para garantir a sequência correta
    palavras_ordenadas = sorted(transcricao, key=lambda x: x["start"])
    topicos_ordenados = sorted(topicos, key=lambda t: t["start"])

    inicio_total = palavras_ordenadas[0]["start"]
    fim_total = palavras_ordenadas[-1]["end"]

    # 1. Intervalo de introdução: do início da transcrição ao início do primeiro tópico
    primeiro_topico_start = topicos_ordenados[0]["start"]
    if inicio_total < primeiro_topico_start:
        intervalos.append({
            "nome": "intervalo_introducao",
            "start": inicio_total,
            "end": primeiro_topico_start
        })

    # 2. Intervalos entre os tópicos
    for i in range(len(topicos_ordenados) - 1):
        topico_atual = topicos_ordenados[i]
        proximo_topico = topicos_ordenados[i+1]

        start_intervalo = topico_atual["end"]
        end_intervalo = proximo_topico["start"]

        if start_intervalo < end_intervalo:
            intervalos.append({
                "nome": topico_atual['word'].lower().replace(' ', '_').replace('.', ''),
                "start": start_intervalo,
                "end": end_intervalo
            })

    # 3. Intervalo de conclusão: do fim do último tópico ao fim da transcrição
    ultimo_topico_end = topicos_ordenados[-1]["end"]
    if ultimo_topico_end < fim_total:
        intervalos.append({
            "nome": "intervalo_conclusao",
            "start": ultimo_topico_end,
            "end": fim_total
        })

    return intervalos


def main():
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    path_transcricao = BASE_DIR / "data" / "topics_video" / "transcription_words.json"
    path_topicos = BASE_DIR / "data" / "topics_video" / "topicos.json"
    path_saida = BASE_DIR / "data" / "topics_video" / "intervalos_entre_topicos.json"

    with open(path_transcricao, "r", encoding="utf-8") as f:
        transcricao = json.load(f)

    with open(path_topicos, "r", encoding="utf-8") as f:
        topicos = json.load(f)

    intervalos_topicos = gerar_intervalos_entre_topicos(transcricao, topicos)

    # Salva o resultado final
    with open(path_saida, "w", encoding="utf-8") as f:
        json.dump(intervalos_topicos, f, ensure_ascii=False, indent=2)

    print(f"Arquivo de intervalos entre tópicos salvo em: {path_saida}")

if __name__ == "__main__":
    main()
