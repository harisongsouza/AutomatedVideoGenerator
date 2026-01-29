import os
import json
import random
import math
import numpy as np
from moviepy.editor import *
from PIL import Image
from moviepy.config import change_settings
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

# Ajuste se necessário
change_settings({"IMAGEMAGICK_BINARY": r"C:/Program Files/ImageMagick-7.1.1-Q16-HDRI/magick.exe"})

def loop_audio(musica, target_length):
    """Repete a música até atingir o tempo desejado."""
    looped_audio = AudioSegment.empty()
    while len(looped_audio) < target_length:
        looped_audio += musica
    return looped_audio[:target_length]

def aplicar_ducking(narracao_path, musica_path, output_audio_path):
    """Aplica ducking: abaixa a música durante a narração."""
    narracao = AudioSegment.from_file(narracao_path)
    musica = AudioSegment.from_file(musica_path)
    musica = loop_audio(musica, len(narracao))
    musica = musica - 20  # Volume base

    nonsilent_ranges = detect_nonsilent(narracao, min_silence_len=500, silence_thresh=-40)
    for start, end in nonsilent_ranges:
        end = min(end, len(musica))
        musica = musica.overlay(musica[start:end] - 10, position=start)

    audio_final = musica.overlay(narracao).fade_out(3000)
    audio_final.export(output_audio_path, format="mp3")
    return output_audio_path

# --- CONFIGURAÇÕES ---
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
TRANSITION_DURATION = 1.0

PROCESSED_DIR = 'C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_processadas'
NARRACAO_AUDIO_FILE = 'C:/Users/souza/Downloads/VideoCreator/assets/audio/narracao.wav'
MUSICA_BACKGROUND_FILE = 'C:/Users/souza/Downloads/VideoCreator/assets/audio/musica_fundo.mp3'
OUTPUT_VIDEO_FILE = 'video_final_profissional.mp4'

# Ken Burns
KB_ZOOM_START = 1.0
KB_ZOOM_END_RANGE = (1.1, 1.3)
KB_PAN_AMOUNT = 0.1

# Texto
TEXT_FONT = 'Arial'
TEXT_FONTSIZE = 70
TEXT_COLOR = 'white'
TEXT_STROKE_COLOR = 'black'
TEXT_STROKE_WIDTH = 2
TEXT_POSITION = ('center', 'center')
TEXT_MARGIN_V = 50

# --- FUNÇÕES AUXILIARES ---
def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

def apply_ken_burns(clip, duration, focal_point_orig=None, zoom_start=1.0, zoom_end=1.2, pan_amount=0.1, ease_func=ease_in_out_sine):
    w, h = clip.size
    focal_point = focal_point_orig if focal_point_orig else (w // 2, h // 2)
    max_pan_x = w * pan_amount
    max_pan_y = h * pan_amount
    pan_start_x = random.uniform(-max_pan_x / 2, max_pan_x / 2)
    pan_start_y = random.uniform(-max_pan_y / 2, max_pan_y / 2)
    pan_end_x = random.uniform(-max_pan_x / 2, max_pan_x / 2)
    pan_end_y = random.uniform(-max_pan_y / 2, max_pan_y / 2)

    def fl(gf, t):
        img = Image.fromarray(gf(t))
        progress = t / duration
        eased = ease_func(progress)
        current_zoom = zoom_start + (zoom_end - zoom_start) * eased
        current_pan_x = pan_start_x + (pan_end_x - pan_start_x) * eased
        current_pan_y = pan_start_y + (pan_end_y - pan_start_y) * eased
        crop_w = int(w / current_zoom)
        crop_h = int(h / current_zoom)
        center_x = focal_point[0] + current_pan_x
        center_y = focal_point[1] + current_pan_y
        left = max(0, min(center_x - crop_w / 2, w - crop_w))
        top = max(0, min(center_y - crop_h / 2, h - crop_h))
        cropped = img.crop((int(left), int(top), int(left + crop_w), int(top + crop_h)))
        resized = cropped.resize((w, h), Image.Resampling.LANCZOS)
        return np.array(resized)

    return clip.fl(fl, apply_to=['mask']).set_duration(duration)

def create_text_overlay(text, duration, fontsize, position, margin_v):
    txt_clip = TextClip(text,
                        fontsize=fontsize,
                        font=TEXT_FONT,
                        color=TEXT_COLOR,
                        stroke_color=TEXT_STROKE_COLOR,
                        stroke_width=TEXT_STROKE_WIDTH,
                        method='caption',
                        size=(VIDEO_WIDTH * 0.8, None),
                        align='center')
    y = VIDEO_HEIGHT - txt_clip.h - margin_v if position[1] == 'bottom' else margin_v
    txt_clip = txt_clip.set_position((position[0], y)).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip

#SEM IMAGEM DE FUNDO E SEM IMAGEM COM EXPRESSAO SOBREPOSTA
def create_text_overlay_v2(text, duration, fontsize, position='center', margin_v=0):
    # Cria o texto
    txt_clip = TextClip(
        text,
        fontsize=fontsize,
        font=TEXT_FONT,
        color=TEXT_COLOR,
        stroke_color=TEXT_STROKE_COLOR,
        stroke_width=TEXT_STROKE_WIDTH,
        method='caption',
        size=(VIDEO_WIDTH * 0.8, None),
        align='center'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)

    # Cria o fundo preto do tamanho da tela
    fundo_preto = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0), duration=duration, ismask=False)

    # Centraliza o texto na tela
    txt_clip = txt_clip.set_position('center')

    # Composição do fundo com o texto por cima
    composed = CompositeVideoClip([fundo_preto.set_opacity(0.1), txt_clip])

    return composed

def create_text_overlay_with_image_v3(text, image_path, duration, fontsize):
    # Cria o texto
    txt_clip = TextClip(
        text,
        fontsize=fontsize,
        font=TEXT_FONT,
        color=TEXT_COLOR,
        stroke_color=TEXT_STROKE_COLOR,
        stroke_width=TEXT_STROKE_WIDTH,
        method='caption',
        size=(VIDEO_WIDTH * 0.8, None),
        align='center'
    ).set_duration(duration)

    # Define posição do texto (centralizado horizontalmente, um pouco acima do centro vertical)
    text_x = (VIDEO_WIDTH - txt_clip.w) // 2
    text_y = (VIDEO_HEIGHT // 2) - txt_clip.h - 20  # 20px acima do centro
    txt_clip = txt_clip.set_position((text_x, text_y))

    # Cria a imagem redimensionada para 200x200
    image_clip = ImageClip(image_path).resize((200, 200)).set_duration(duration)

    # Centraliza horizontalmente e posiciona logo abaixo do texto
    image_x = (VIDEO_WIDTH - 200) // 2
    image_y = text_y + txt_clip.h + 20  # 20px abaixo do texto
    image_clip = image_clip.set_position((image_x, image_y))

    # Fundo preto
    fundo_preto = ColorClip(size=(VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0), ismask=False, duration=duration)

    # Composição
    composed = CompositeVideoClip([fundo_preto.set_opacity(0.1), txt_clip, image_clip]).fadein(0.5).fadeout(0.5)

    return composed

# --- MAIN ---
def main():
    print("Carregando imagens e metadados...")
    image_data = []
    for filename in sorted(os.listdir(PROCESSED_DIR)):
        base, ext = os.path.splitext(filename)
        if ext.lower() in ['.jpg', '.jpeg', '.png']:
            img_path = os.path.join(PROCESSED_DIR, filename)
            json_path = os.path.join(PROCESSED_DIR, base + '.json')
            focal_point = None
            start, end = None, None
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r') as f:
                        meta = json.load(f)
                        focal_point = meta.get("focal_point_original_coords")
                        start = meta.get("start")
                        end = meta.get("end")
                except Exception as e:
                    print(f"Erro ao ler {json_path}: {e}")
            if start is not None and end is not None:
                image_data.append({
                    "img_path": img_path,
                    "focal_point": focal_point,
                    "start": float(start),
                    "end": float(end),
                    "duration": float(end) - float(start)
                })

    if not image_data:
        print("Nenhuma imagem com metadados de tempo encontrada.")
        exit()

    # Ordena por tempo de início
    image_data.sort(key=lambda x: x["start"])

    # Cria clipes
    clips = []
    final_clips = []
    
    video_intro_path = "C:/Users/souza/Downloads/VideoCreator/assets/videos/video_intro.mp4"
    video_encerramento_path = "C:/Users/souza/Downloads/VideoCreator/assets/videos/video_intro.mp4"
    
    with open("C:/Users/souza/Downloads/VideoCreator/data/intervalos_entre_camadas.json", 'r', encoding="utf-8") as f:
        intervalos_camadas = json.load(f)
    
    with open("C:/Users/souza/Downloads/VideoCreator/data/camadas.json", 'r', encoding="utf-8") as f:
        camadas_tempos = json.load(f)
    
    with open("C:/Users/souza/Downloads/VideoCreator/data/topicos.json", 'r', encoding="utf-8") as f:
        topicos_tempos = json.load(f)
    
    with open("C:/Users/souza/Downloads/VideoCreator/data/intervalos_entre_topicos.json", 'r', encoding="utf-8") as f:
        intervalo_entre_topicos_tempos = json.load(f)
            
    #INTRO
    for intervalo_camada in intervalos_camadas:
        string_intervalo = "intervalo_introducao"
        if intervalo_camada["nome"] == string_intervalo:
            inicio = intervalo_camada["start"]
            fim = intervalo_camada["end"]
            intro_intervalo_tempo = fim - inicio
            video_clip = VideoFileClip(video_intro_path).set_duration(intro_intervalo_tempo).set_start(inicio).resize((VIDEO_WIDTH, VIDEO_HEIGHT))
            final_clips.append(video_clip)
            
    #CAMADAS
    for i, camada in enumerate(camadas_tempos):
        inicio = camada["start"]
        fim = camada["end"]
        camada_intervalo_duracao = fim - inicio
        video_clip = VideoFileClip(camada["video_path_base"]).set_duration(camada_intervalo_duracao).set_start(inicio).resize((VIDEO_WIDTH, VIDEO_HEIGHT)).fadein(TRANSITION_DURATION).fadeout(TRANSITION_DURATION)
        final_clips.append(video_clip)
              
        title = camada["word"].upper()
        text_overlay = create_text_overlay_with_image_v3(title, camada["img_sobreposta"], camada_intervalo_duracao, TEXT_FONTSIZE)
        text_start = inicio
        clip = CompositeVideoClip([video_clip, text_overlay.set_start(text_start)])
        final_clips.append(clip)
            
    #TOPICOS
    for i, topico in enumerate(topicos_tempos):
        camada_do_topico = []
        midia_path = []
        for topico_intervalo in intervalo_entre_topicos_tempos:
            if topico_intervalo["topico_atual"] == topico["word"]:
                camada_do_topico.append(topico_intervalo["camada"])
        for camada in camadas_tempos:
            camada_formatada = "intervalo_" + camada["word"].lower().replace(' ', '_')
            if camada_formatada == camada_do_topico[0]:
                midia_path.append(camada["video_path_base"])
        inicio = topico["start"]
        fim = topico["end"]
        topico_intervalo_duracao = fim - inicio
        video_clip = VideoFileClip(midia_path[0]).set_duration(topico_intervalo_duracao).set_start(inicio).resize((VIDEO_WIDTH, VIDEO_HEIGHT))
        
        #ADD TEXT
        title = topico["word"].upper().title()
        text_overlay = create_text_overlay_v2(title, topico_intervalo_duracao, TEXT_FONTSIZE)
        text_start = inicio
        clip = CompositeVideoClip([video_clip, text_overlay.set_start(text_start)])
        final_clips.append(clip)

    #CLIPS                       
    for i, data in enumerate(image_data):
        print(f"Processando imagem {i+1}/{len(image_data)}: {os.path.basename(data['img_path'])}")
        
        base_clip = ImageClip(data["img_path"]).set_duration(data["duration"]).set_start(data["start"])
        if base_clip.size != [VIDEO_WIDTH, VIDEO_HEIGHT]:
            base_clip = base_clip.resize(newsize=(VIDEO_WIDTH, VIDEO_HEIGHT))
        kb_clip = apply_ken_burns(base_clip, data["duration"], data["focal_point"],
                                  zoom_start=KB_ZOOM_START,
                                  zoom_end=random.uniform(*KB_ZOOM_END_RANGE),
                                  pan_amount=KB_PAN_AMOUNT)

        clips.append(kb_clip)
    
    #ENCERRAMENTO
    for intervalo_camada in intervalos_camadas:
        string_intervalo = "intervalo_espero_que_tenham_gostado."
        if intervalo_camada["nome"] == string_intervalo:
            inicio = intervalo_camada["start"]
            fim = intervalo_camada["end"]
            intro_intervalo_tempo = fim - inicio
            video_clip = VideoFileClip(video_encerramento_path).set_duration(intro_intervalo_tempo).set_start(inicio).resize((VIDEO_WIDTH, VIDEO_HEIGHT))
            final_clips.append(video_clip)
                        
    # Adiciona transições e usa os tempos predefinidos
    print("Aplicando transições e concatenando...")
        
    #CONTEUDO EFEITO CROSSFADEIN
    for i, clip in enumerate(clips):
        if i > 0:
            clip = clip.crossfadeout(TRANSITION_DURATION)
        final_clips.append(clip)
        
    # Define duração final baseada no último frame
    video_duration = max(clip.end for clip in final_clips)

    final_video = CompositeVideoClip(final_clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT)).set_duration(video_duration)

    # --- ÁUDIO ---
    print("Adicionando áudio...")
    try:
        narracao_path = NARRACAO_AUDIO_FILE
        musica_path = MUSICA_BACKGROUND_FILE
        output_audio_path = 'C:/Users/souza/Downloads/VideoCreator/assets/audio/audio_final.mp3'

        aplicar_ducking(narracao_path, musica_path, output_audio_path)

        audio_final = AudioFileClip(output_audio_path)
        final_video = final_video.set_audio(audio_final)
    except Exception as e_audio:
        print(f"Erro ao adicionar áudio: {e_audio}")

    # --- RENDER ---
    print(f"Renderizando vídeo final em: {OUTPUT_VIDEO_FILE}")
    try:
        final_video.write_videofile(OUTPUT_VIDEO_FILE,
                                    fps=VIDEO_FPS,
                                    codec='libx264',
                                    audio_codec='aac',
                                    preset='medium',
                                    threads=4,
                                    logger='bar')
        print("Renderização concluída com sucesso!")
    except Exception as e_render:
        print(f"Erro ao renderizar: {e_render}")
        
if __name__ == "__main__":
    main()
