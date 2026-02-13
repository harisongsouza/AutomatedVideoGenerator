from faster_whisper import WhisperModel
import json

def main():
    with open("C:/Users/souza/Downloads/VideoCreator/data/transcription.json", 'r', encoding="utf-8") as f:
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
    with open("C:/Users/souza/Downloads/VideoCreator/data/transcription_words.json", "w", encoding="utf-8") as f:
        json.dump(words_data, f, ensure_ascii=False, indent=2)

    print("✅ Transcrição salva em 'transcription_words.json'")

if __name__ == "__main__":
    main()