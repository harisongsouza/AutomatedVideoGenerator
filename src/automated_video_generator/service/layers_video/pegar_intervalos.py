import json

def gerar_intervalos_entre_camadas(palavras, camadas):
    intervalos = []

    palavras_ordenadas = sorted(palavras, key=lambda x: x["start"])
    inicio_total = palavras_ordenadas[0]["start"]
    fim_total = palavras_ordenadas[-1]["end"]

    # Primeiro intervalo: do início da transcrição até o início da 1ª camada
    if camadas: # Garante que existe pelo menos uma camada
        inicio_primeira_camada = camadas[0]["start"]
        # Cria o intervalo de introdução se houver tempo (ou silêncio) antes do início da primeira camada
        if inicio_total < inicio_primeira_camada:
            intervalos.append({
                "nome": "intervalo_introducao",
                "start": inicio_total,
                "end": inicio_primeira_camada # MODIFICADO: 'end' é o 'start' da primeira camada
            })

    # Intervalos para cada camada
    # O intervalo associado a uma camada X começa no start(X) e termina:
    # - no start(X+1) se X não for a última camada
    # - no fim_total da transcrição se X for a última camada
    if camadas: # Processar apenas se houver camadas
        for i in range(len(camadas)):
            camada_atual = camadas[i]
            # O nome do intervalo continua baseado na "camada_atual"
            nome_intervalo = "intervalo_" + camada_atual["word"].lower().replace(' ', '_')
            # O 'start' do intervalo é o 'start' da camada atual
            start_intervalo = camada_atual["start"] 
            
            end_intervalo = None
            if i < len(camadas) - 1: # Se esta NÃO é a última camada da lista
                camada_proxima = camadas[i+1]
                end_intervalo = camada_proxima["start"] # MODIFICADO: 'end' é o 'start' da próxima camada
            else: # Esta É a última camada da lista
                end_intervalo = fim_total # MANTÉM LÓGICA: 'end' é o fim total da transcrição
            
            intervalos.append({
                "nome": nome_intervalo,
                "start": start_intervalo,
                "end": end_intervalo
            })

    return intervalos


def gerar_intervalos_entre_topicos(transcricao, camadas, topicos):
    intervalos_resultado = []

    # Opcional: Descomente a linha abaixo se a transcrição não estiver garantidamente ordenada.
    # transcricao.sort(key=lambda x: x["start"])

    for camada in camadas:
        camada_start = camada["start"]
        camada_end = camada["end"]
        camada_nome = camada["nome"]

        # Filtra tópicos que estão dentro do intervalo da camada
        # Um tópico deve começar antes do fim da camada para ser considerado nela.
        topicos_na_camada = [
            t for t in topicos if camada_start <= t["start"] < camada_end
        ]
        # Ordena os tópicos por tempo de início
        topicos_na_camada.sort(key=lambda t: t["start"])

        if not topicos_na_camada:
            continue

        for i in range(len(topicos_na_camada)):
            topico_atual = topicos_na_camada[i]
            topico_fim = topico_atual["end"]

            # === INÍCIO DO INTERVALO ===
            # Encontra a primeira palavra na transcrição que começa APÓS o fim do tópico_atual
            # e ANTES do fim da camada.
            palavras_apos_topico = [
                p for p in transcricao if p["start"] >= topico_fim and p["start"] < camada_end
            ]
            
            start_do_intervalo_atual = topico_fim  # Fallback: se não houver palavras após o tópico.
            if palavras_apos_topico:
                # Se a transcrição principal já está ordenada, palavras_apos_topico também estará.
                start_do_intervalo_atual = palavras_apos_topico[0]["start"]
            
            # === FIM DO INTERVALO ===
            # Define o limite superior para este intervalo:
            # ou o início do próximo tópico, ou o fim da camada.
            limite_superior_intervalo = camada_end 
            if i + 1 < len(topicos_na_camada):
                limite_superior_intervalo = topicos_na_camada[i + 1]["start"]

            end_final_para_este_intervalo = limite_superior_intervalo # Valor padrão inicial

            # Se o início do intervalo já está no limite superior ou além,
            # o intervalo tem tamanho zero ou é inválido (se start > limite).
            # O 'end' será igual ao 'start' ou ao limite, o que for mais restritivo para um intervalo válido.
            if start_do_intervalo_atual >= limite_superior_intervalo:
                end_final_para_este_intervalo = start_do_intervalo_atual
            else:
                # Procurar a última palavra na transcrição cujo 'start' está no espaço
                # [start_do_intervalo_atual, limite_superior_intervalo).
                ultima_palavra_dentro_do_espaco_idx = -1
                for k in range(len(transcricao)):
                    palavra_k_start = transcricao[k]["start"]
                    
                    # Se a palavra atual já começa no limite superior ou depois,
                    # todas as palavras subsequentes também estarão além.
                    if palavra_k_start >= limite_superior_intervalo:
                        break 
                    
                    # Considerar apenas palavras que começam em ou após o início do nosso intervalo.
                    if palavra_k_start >= start_do_intervalo_atual:
                        ultima_palavra_dentro_do_espaco_idx = k
                
                if ultima_palavra_dentro_do_espaco_idx != -1:
                    # Encontramos pelo menos uma palavra no espaço do intervalo.
                    # Agora, verificamos se existe uma palavra *imediatamente após* ela na transcrição.
                    if ultima_palavra_dentro_do_espaco_idx + 1 < len(transcricao):
                        proxima_palavra_global_start = transcricao[ultima_palavra_dentro_do_espaco_idx + 1]["start"]
                        
                        # Se o 'start' da próxima palavra global ainda estiver estritamente antes
                        # do nosso limite_superior_intervalo, usamos ele como 'end'.
                        if proxima_palavra_global_start < limite_superior_intervalo:
                            end_final_para_este_intervalo = proxima_palavra_global_start
                        # else: a próxima palavra já está no/após o limite_superior_intervalo,
                        # então o 'end' do intervalo permanece limite_superior_intervalo.
                    # else: (ultima_palavra_dentro_do_espaco_idx é a última palavra da transcrição)
                    # o 'end' do intervalo permanece limite_superior_intervalo.
                # else: (nenhuma palavra encontrada no espaço [start_do_intervalo_atual, limite_superior_intervalo) )
                # o 'end' do intervalo permanece limite_superior_intervalo.
                # Isso significa que o intervalo [start_do_intervalo_atual, limite_superior_intervalo] está "vazio" de palavras.

            # Adicionar o intervalo somente se start <= end.
            # Isso permite intervalos de tamanho zero (start == end) mas evita inválidos (start > end).
            if start_do_intervalo_atual <= end_final_para_este_intervalo:
                intervalo = {
                    "camada": camada_nome,
                    "topico_atual": topico_atual["word"], # Nome do tópico que ANTECEDE este intervalo
                    "start": start_do_intervalo_atual,
                    "end": end_final_para_este_intervalo
                }
                intervalos_resultado.append(intervalo)

    return intervalos_resultado


def atribuir_camada_a_topicos(topicos, camadas):
    for topico in topicos:
        for camada in camadas:
            if camada["start"] <= topico["start"] < camada["end"]:
                topico["camada"] = camada["nome"]
                break
    return topicos


def main():
    json_path = "C:/Users/souza/Downloads/VideoCreator/data/transcription_words.json"

    with open(json_path, "r", encoding="utf-8") as f:
        transcricao = json.load(f)
    
    json_path2 = "C:/Users/souza/Downloads/VideoCreator/data/camadas.json"

    with open(json_path2, "r", encoding="utf-8") as f:
        camadas = json.load(f)
    
    json_path3 = "C:/Users/souza/Downloads/VideoCreator/data/topicos.json"

    with open(json_path3, "r", encoding="utf-8") as f:
        topicos = json.load(f)
      
    intervalo_camadas = gerar_intervalos_entre_camadas(transcricao, camadas)

    topicos_com_camada = atribuir_camada_a_topicos(topicos, intervalo_camadas)
    
    intervalos_topicos = gerar_intervalos_entre_topicos(transcricao, intervalo_camadas, topicos_com_camada)

    # Salvar se quiser
    with open("C:/Users/souza/Downloads/VideoCreator/data/intervalos_entre_camadas.json", "w", encoding="utf-8") as f:
        json.dump(intervalo_camadas, f, ensure_ascii=False, indent=2)
        
    # Salvar se quiser
    with open("C:/Users/souza/Downloads/VideoCreator/data/intervalos_entre_topicos.json", "w", encoding="utf-8") as f:
        json.dump(intervalos_topicos, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()