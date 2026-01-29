import os
import json
# O módulo tempfile não será mais usado para criar o arquivo, mas o deixamos caso precise no futuro.
import tempfile 
from pydub import AudioSegment
from faster_whisper import WhisperModel
import time

# --- Configurações ---
AUDIO_FILE_PATH = "C:/Users/souza/Videos/VideoCreator/assets/audio/narracao.wav" 
MODEL_SIZE = "medium"
#MODEL_SIZE = "large-v3"
COMPUTE_TYPE = "float32"
CHUNK_LENGTH_MS = 30 * 1000

# --- NOVA LINHA: Define o nome para a nossa pasta de chunks temporários ---
TEMP_CHUNK_DIR = "temp_chunks"

def transcribe_audio_in_chunks(audio_path):
    if not os.path.exists(audio_path):
        print(f"Erro: O arquivo de áudio não foi encontrado em '{audio_path}'")
        return

    # --- NOVA LINHA: Cria a nossa pasta temporária se ela não existir ---
    os.makedirs(TEMP_CHUNK_DIR, exist_ok=True)
    print(f"Pasta temporária '{TEMP_CHUNK_DIR}' garantida.")

    print("--- Iniciando a transcrição ---")
    print(f"Carregando o modelo Whisper '{MODEL_SIZE}'...")
    
    try:
        model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)
    except Exception as e:
        print(f"Erro ao carregar o modelo Whisper: {e}")
        return

    print("Modelo carregado. Carregando e dividindo o áudio...")

    try:
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        print(f"Erro ao carregar o arquivo de áudio com pydub: {e}")
        return

    total_duration_ms = len(audio)
    chunks = range(0, total_duration_ms, CHUNK_LENGTH_MS)
    
    final_segments = []
    full_text = ""
    language_info = None
    segment_id_counter = 0

    print(f"Áudio dividido em {len(chunks)} partes. Iniciando a transcrição de cada parte...")
    start_time = time.time()

    for i, start_ms in enumerate(chunks):
        end_ms = start_ms + CHUNK_LENGTH_MS
        end_ms = min(end_ms, total_duration_ms)
        
        audio_chunk = audio[start_ms:end_ms]
        offset_seconds = start_ms / 1000.0

        # --- MUDANÇA PRINCIPAL: Em vez de usar tempfile, criamos o arquivo na nossa pasta ---
        temp_chunk_filename = os.path.join(TEMP_CHUNK_DIR, f"chunk_{i}.mp3")
        
        try:
            # Exporta o chunk para o nosso caminho definido
            audio_chunk.export(temp_chunk_filename, format="mp3")
            
            # Transcreve o chunk
            segments, info = model.transcribe(temp_chunk_filename, word_timestamps=True)

            if language_info is None:
                language_info = info
            
            for segment in segments:
                full_text += segment.text + " "
                corrected_start = segment.start + offset_seconds
                corrected_end = segment.end + offset_seconds
                corrected_words = []
                if segment.words:
                    for word in segment.words:
                        corrected_words.append({
                            "word": word.word,
                            "start": word.start + offset_seconds,
                            "end": word.end + offset_seconds,
                            "probability": word.probability,
                        })
                final_segments.append({
                    "id": segment_id_counter,
                    "seek": segment.seek,
                    "start": corrected_start,
                    "end": corrected_end,
                    "text": segment.text,
                    "tokens": segment.tokens,
                    "temperature": segment.temperature,
                    "avg_logprob": segment.avg_logprob,
                    "compression_ratio": segment.compression_ratio,
                    "no_speech_prob": segment.no_speech_prob,
                    "words": corrected_words
                })
                segment_id_counter += 1
        
        finally:
            # --- BOA PRÁTICA: Garante que o arquivo temporário seja deletado mesmo se ocorrer um erro ---
            if os.path.exists(temp_chunk_filename):
                os.remove(temp_chunk_filename)

        print(f"  -> Parte {i+1}/{len(chunks)} concluída.")

    final_transcription = {
        "text": full_text.strip(),
        "segments": final_segments,
        "language": language_info.language if language_info else "unknown",
        "language_probability": language_info.language_probability if language_info else 0.0
    }

    output_filename = "C:/Users/souza/Videos/VideoCreator/data/transcription.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(final_transcription, f, indent=2, ensure_ascii=False)

    end_time = time.time()
    total_time = end_time - start_time
    print("\n--- Transcrição Concluída! ---")
    print(f"O resultado foi salvo em '{output_filename}'")
    print(f"Tempo total de processamento: {total_time:.2f} segundos.")


# --- Executar o script ---
def main():
    transcribe_audio_in_chunks(AUDIO_FILE_PATH)
    
if __name__ == "__main__":
    main()