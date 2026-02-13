
import re

def validar_arquivos_formato_camadas(conteudo: str) -> tuple[bool, str]:
    camadas_obrigatorias = ['Camada Superfície Brilhante', 'Camada Congelada', 'Camada Submersa',
                            'Camada Gelo Profundo', 'Camada Núcleo Abissal', 'Espero que tenham gostado.']
    posicao_anterior = -1
    posicoes_camadas = {}
    for camada in camadas_obrigatorias:
        posicao_atual = conteudo.find(camada)
        if posicao_atual == -1: return False, f"Erro: A seção obrigatória '{camada}' não foi encontrada."
        if posicao_atual < posicao_anterior: return False, f"Erro: A seção '{camada}' está fora da ordem esperada."
        posicao_anterior = posicao_atual
        posicoes_camadas[camada] = posicao_atual
    if posicoes_camadas['Camada Superfície Brilhante'] == 0: return False, "Erro: Falta o texto de introdução."
    for i in range(len(camadas_obrigatorias) - 2):
        camada_atual, camada_seguinte = camadas_obrigatorias[i], camadas_obrigatorias[i + 1]
        inicio_secao = posicoes_camadas[camada_atual] + len(camada_atual)
        fim_secao = posicoes_camadas[camada_seguinte]
        secao_texto = conteudo[inicio_secao:fim_secao]
        topicos_encontrados = re.findall(r'Número (\d)\.', secao_texto)
        if not (1 <= len(
            topicos_encontrados) <= 3): return False, f"Erro na '{camada_atual}': É necessário ter entre 1 e 3 tópicos. Encontrados: {len(topicos_encontrados)}."
        numeros_topicos = [int(n) for n in topicos_encontrados]
        if numeros_topicos != list(range(1,
                                         len(numeros_topicos) + 1)): return False, f"Erro na '{camada_atual}': Os tópicos não estão em ordem sequencial."
    posicao_final_esperada = posicoes_camadas['Espero que tenham gostado.'] + len('Espero que tenham gostado.')
    if len(conteudo.strip()) <= posicao_final_esperada: return False, "Erro: Falta o texto de encerramento."
    return True, "Sucesso! \nO arquivo está no formato correto."

def validar_arquivos_formato_topicos(conteudo):
    frase_divisoria = "Espero que tenham gostado."
    if frase_divisoria not in conteudo:
        return False, f"O arquivo deve conter a frase exata: '{frase_divisoria}'"

    partes = conteudo.rsplit(frase_divisoria, 1)
    conteudo_antes_divisoria = partes[0]
    conteudo_encerramento = partes[1]

    palavras_encerramento = conteudo_encerramento.split()
    if len(palavras_encerramento) < 10:
        return False, f"O encerramento (após '{frase_divisoria}') deve ter no mínimo 10 palavras. Encontradas: {len(palavras_encerramento)}"

    padrao_topico = r"Número \d+\.\s+.*?\."

    topicos_encontrados = re.findall(padrao_topico, conteudo_antes_divisoria)

    if len(topicos_encontrados) < 3:
        return False, f"O arquivo deve ter no mínimo 3 tópicos no formato 'Número X. Título.'. Encontrados: {len(topicos_encontrados)}"

    match_primeiro_topico = re.search(padrao_topico, conteudo_antes_divisoria)

    if match_primeiro_topico:
        indice_inicio_topicos = match_primeiro_topico.start()
        texto_intro = conteudo_antes_divisoria[:indice_inicio_topicos]
        palavras_intro = texto_intro.split()

        if len(palavras_intro) < 10:
            return False, f"A introdução (antes do primeiro tópico 'Número X...') deve ter no mínimo 10 palavras. Encontradas: {len(palavras_intro)}"
    else:
        return False, "Não foi possível identificar o início dos tópicos para validar a introdução."

    return True, "Arquivo de Tópicos válido."
