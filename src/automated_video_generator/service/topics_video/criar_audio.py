import asyncio
import edge_tts
from pathlib import Path

async def ler_roteiro_e_converter():
    # Define a raiz como a pasta onde o script está
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    # Monta o caminho completo dentro da pasta do projeto
    arquivo_roteiro = BASE_DIR / "data" / "topics_video" / "roteiro.txt"

    voz = "pt-BR-AntonioNeural"  # Escolha da voz
    rate = "-15%"  # Fala mais lenta para efeito dramático
    pitch = "-5Hz"  # Voz mais grave para terror

    arquivo_audio = BASE_DIR / "assets" / "topics_video" / "audio" / "narracao.wav"

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
