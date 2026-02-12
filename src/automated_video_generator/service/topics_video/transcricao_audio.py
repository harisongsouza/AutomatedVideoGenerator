from faster_whisper import WhisperModel
import json
from pathlib import Path

def main():
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    arquivo_transcricao = BASE_DIR / "data" / "topics_video" / "transcription.json"
    arquivo_transcricao_words = BASE_DIR / "data" / "topics_video" / "transcription_words.json"

    with open(arquivo_transcricao, 'r', encoding="utf-8") as f:
        intervalos = json.load(f)

    # Caminho do arquivo de áudio
    #audio_path = "C:/Users/souza/Downloads/VideoCreator/assets/audio/narracao.wav"

    # Inicializa o modelo (você pode trocar por 'large-v3' ou outro)
    #model = WhisperModel("base", compute_type="float32")  # use "int8" para mais desempenho
    #model = WhisperModel("medium", compute_type="float32")  # use "int8" para mais desempenho

    # Transcrição com palavras e timestamps
#    segments, _ = model.transcribe(audio_path, word_timestamps=True)
    segments = intervalos

    # Lista para armazenar resultados
    words_data = []

    # Extrai as palavras e seus tempos
    for segment in segments["segments"]:
        for word in segment["words"]:
            words_data.append({
                "word": word["word"],
                "start": word["start"],
                "end": word["end"]
            })

    # Salva em um arquivo JSON
    with open(arquivo_transcricao_words, "w", encoding="utf-8") as f:
        json.dump(words_data, f, ensure_ascii=False, indent=2)

    print("✅ Transcrição salva em 'transcription_words.json'")

if __name__ == "__main__":
    main()
