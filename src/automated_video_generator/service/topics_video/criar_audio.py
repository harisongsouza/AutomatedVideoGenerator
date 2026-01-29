import asyncio
import edge_tts

async def ler_roteiro_e_converter():
    arquivo_roteiro = "/home/harison/Documentos/VideoCreator/data/roteiro.txt"  # Arquivo com o texto
    voz = "pt-BR-AntonioNeural"  # Escolha da voz
    rate = "-15%"  # Fala mais lenta para efeito dramático
    pitch = "-5Hz"  # Voz mais grave para terror
    arquivo_audio = "C:/Users/souza/Videos/VideoCreator/assets/audio/narracao.wav"  # Nome do arquivo de saída

    # Lendo o roteiro do arquivo
    with open(arquivo_roteiro, "r", encoding="utf-8") as f:
        texto = f.read()

    # Gerando o áudio
    tts = edge_tts.Communicate(texto, voice=voz, rate=rate, pitch=pitch)
    await tts.save(arquivo_audio)

    print(f"✅ Áudio gerado: {arquivo_audio}")

def main():
    asyncio.run(ler_roteiro_e_converter())

if __name__ == "__main__":
    main()


#tem que ser mais lento