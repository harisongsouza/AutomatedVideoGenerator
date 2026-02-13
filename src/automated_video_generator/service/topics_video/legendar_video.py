import moviepy.editor as mp
import whisper
import os
import json # Para salvar metadados

from moviepy.config import change_settings

# Ajuste se necessário
change_settings({"IMAGEMAGICK_BINARY": r"C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"})


def forcar_inicio_em_zero(lista_filtrada):
    if not lista_filtrada:
        return []

    # Pega o tempo de início do primeiro item da lista. Este é o nosso "offset".
    offset = lista_filtrada[0]['start']
    
    lista_ajustada = []
    for item in lista_filtrada:
        item_ajustado = item.copy()
        
        # Subtrai o offset do primeiro item para rebasear todos os outros
        item_ajustado['start'] = round(item['start'] - offset, 4)
        item_ajustado['end'] = round(item['end'] - offset, 4)
        
        lista_ajustada.append(item_ajustado)
        
    return lista_ajustada


def create_subtitles(video_path: str, output_path: str):
    print("🚀 Iniciando o processo...")

    # 1. Carregar o vídeo e extrair o áudio
    print("1/5 - Carregando vídeo e extraindo áudio...")
    video_clip = mp.VideoFileClip(video_path)
    #audio_path = "temp_audio.mp3"
    #video_clip.audio.write_audiofile(audio_path)


    # 4. Criar clipes de texto para cada palavra
    print("4/5 - Gerando legendas...")
    subtitle_clips = []
    
    
    entrada_path = "C:/Users/souza/Videos/VideoCreatorHowTo/data/transcription_words.json"

    # Carregar os intervalos entre tópicos
    with open(entrada_path, "r", encoding="utf-8") as f:
        transcription_words = json.load(f)
    
        
    entrada_path_2 = "C:/Users/souza/Videos/VideoCreatorHowTo/data/final_list_render.json"

    # Carregar os intervalos entre tópicos
    with open(entrada_path_2, "r", encoding="utf-8") as f:
        transcription_words_2 = json.load(f)
        
    aassd = transcription_words_2[0]["inicio"]
    aassd_2 = transcription_words_2[-1]["fim"]

    
    list_words = []
    
    for item in transcription_words:
        if item["start"] >= aassd and item["end"] <= aassd_2:
            list_words.append(item)
    
    new_list_words = forcar_inicio_em_zero(list_words)

    
    for word in new_list_words:
        text = word['word'].upper()
        start_time = word['start']
        end_time = word['end']
        duration = end_time - start_time

        # Estilo da legenda (fonte, tamanho, cor, contorno)
        text_clip = mp.TextClip(
            txt=text,
            fontsize=100,
            font='Arial-Black', # Uma fonte ousada e comum. Tente 'Arial-Black' também.
            #font='C:/Users/souza/Videos/VideoCreatorHowTo/BebasNeue-Regular.ttf', # Uma fonte ousada e comum. Tente 'Arial-Black' também.
            color='yellow',
            stroke_color='black',
            stroke_width=5
        )

        text_clip = text_clip.set_start(start_time)
        text_clip = text_clip.set_duration(duration)
        # Posição da legenda (centro da tela)
        text_clip = text_clip.set_position(('center', 'center'))
        
        subtitle_clips.append(text_clip)

    # 5. Combinar vídeo e legendas e exportar
    print("5/5 - Combinando vídeo e legendas e salvando o arquivo final...")
    final_clip = mp.CompositeVideoClip([video_clip] + subtitle_clips)
        
    final_clip.write_videofile(
        output_path, 
        codec="libx264", 
        audio_codec="aac",
        temp_audiofile='temp-audio.m4a', 
        remove_temp=True
    )
    
    print(f"✅ Vídeo final salvo em: {output_path}")


def main():
    # --- CONFIGURE AQUI ---
    input_video_file = "end_video.mp4" # Coloque o nome do seu arquivo de vídeo aqui
    output_video_file = "video_final.mp4"
    # ----------------------

    if not os.path.exists(input_video_file):
        print(f"Erro: O arquivo de vídeo '{input_video_file}' não foi encontrado.")
        print("Por favor, coloque o seu vídeo na mesma pasta que este script e atualize a variável 'input_video_file'.")
    else:
        create_subtitles(input_video_file, output_video_file)
        

if __name__ == '__main__':
    main()