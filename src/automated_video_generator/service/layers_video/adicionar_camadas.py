import subprocess
import os
import json

import unicodedata
import re
import math
from math import ceil

import random
import shutil
from PIL import Image

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

#CONFIGURACAO
PROCESSED_DIR = 'C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_processadas/'

TEMP_WORK_DIR = 'C:/Users/souza/Downloads/VideoCreator/assets/videos/intervalo_entre_topicos/' # Pasta para frames e vídeos intermediários

KB_ZOOM_START = 1.0
KB_ZOOM_END_RANGE = (1.15, 1.35)
KB_PAN_AMOUNT = 0.08 # % da dimensão da imagem para o pan

IMAGE_FOLDER = "C:/Users/souza/Downloads/VideoCreator/assets/imagens/imagens_camadas/imagens_sobreposta_camadas/" # CRIE ESTA PASTA E COLOQUE SUAS IMAGENS AQUI

RESOLUCAO_VIDEO = '1920x1080'
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30

NARRACAO_AUDIO_FILE = 'C:/Users/souza/Downloads/VideoCreator/assets/audio/narracao.wav'
MUSICA_BACKGROUND_FILE = 'C:/Users/souza/Downloads/VideoCreator/assets/audio/musica_fundo.mp3'
AUDIO_FINAL_FILE_PATH = 'C:/Users/souza/Downloads/VideoCreator/assets/audio/audio_final.mp3'

INTRO_VIDEO_PATH = 'C:/Users/souza/Downloads/VideoCreator/assets/videos/video_intro.mp4'


def loop_audio(musica, target_length):
    """Repete a música até atingir o tempo desejado."""
    looped_audio = AudioSegment.empty()
    while len(looped_audio) < target_length:
        looped_audio += musica
    return looped_audio[:target_length]

def criar_audio_com_ducking():
    """Aplica ducking: abaixa a música durante a narração."""
    narracao_path = NARRACAO_AUDIO_FILE
    musica_path = MUSICA_BACKGROUND_FILE
    output_audio_path = AUDIO_FINAL_FILE_PATH
    
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

def gerar_video_com_videos_e_audio(audio_path, output_path, resolucao, fps, elementos, fade_out_duration=1.0):
    inputs = [
        f"-f lavfi -i color=c=black:s={resolucao}:r={fps}",
        f"-i {audio_path}",
    ]

    filter_lines = ["[0:v]null[base]"]
    current_overlay_input = "[base]"

    for el in elementos:
        inputs.append(f"-stream_loop -1 -i {el['arquivo']}")

    for i, el in enumerate(elementos):
        input_index = i + 2
        video_duration = get_video_duration(el['arquivo'])
        inicio = float(el['inicio'])
        fim = float(el['fim'])
        intervalo_duracao = fim - inicio

        loops_necessarios = ceil(intervalo_duracao / video_duration) if video_duration else 1

        video_element_label = f"[el{i}]"
        scaled_vid_label = f"[v_scaled_{i}]"
        time_shifted_vid_label = f"[v_shifted_{i}]"

        res_w, res_h = resolucao.split("x")
        largura = el.get("largura", res_w)
        altura = el.get("altura", res_h)
        x = el.get("x", 0)
        y = el.get("y", 0)

        filter_lines.append(
            f"[{input_index}:v]scale={largura}:{altura},format=yuv420p{scaled_vid_label}"
        )
        filter_lines.append(
            f"{scaled_vid_label}setpts=PTS-STARTPTS+{inicio:.3f}/TB{time_shifted_vid_label}"
        )

        actual_fade_duration = min(fade_out_duration, intervalo_duracao)
        if actual_fade_duration > 0.001:
            fade_start_time = fim - actual_fade_duration
            filter_lines.append(
                f"{time_shifted_vid_label}fade=type=out:start_time={fade_start_time:.3f}:duration={actual_fade_duration:.3f}{video_element_label}"
            )
        else:
            filter_lines.append(f"{time_shifted_vid_label}null{video_element_label}")

        overlay_output_label = f"[out{i}]"
        filter_lines.append(
            f"{current_overlay_input}{video_element_label}overlay=x={x}:y={y}:enable='between(t,{inicio:.3f},{fim:.3f})'{overlay_output_label}"
        )
        current_overlay_input = overlay_output_label

    filter_complex = ";".join(filter_lines)

    cmd = [
        "ffmpeg", "-y",
        *" ".join(inputs).split(),
        "-filter_complex", filter_complex,
        "-map", current_overlay_input,
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-shortest",
        output_path
    ]

    print("Comando FFmpeg gerado")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Vídeo gerado com sucesso!")
    except subprocess.CalledProcessError as e:
        print("Erro ao gerar o vídeo.")
        print("Comando:", e.cmd)
        print("Output:", e.stdout)
        print("Error:", e.stderr)


    
#----------------------

""" def adicionar_texto_e_imagem(
    input_video,
    output_video,
    texto,
    imagem=None,
    imagem_largura=200,
    imagem_altura=200,
    texto_y=200,
    distancia_texto_imagem=20,
    fonte_tamanho=24,
    cor_texto="white",
    cor_caixa="black@0.5",
    borda_caixa=10
):
    filtro = ""
    inputs = ["-y", "-i", input_video]
    
    if imagem:  # se uma imagem foi fornecida
        imagem_y = texto_y + fonte_tamanho + distancia_texto_imagem
        inputs += ["-i", imagem]
        filtro = (
            f"[1:v]scale={imagem_largura}:{imagem_altura}[img];"
            f"[0:v][img]overlay=x=(W-{imagem_largura})/2:y={imagem_y}[tmp];"
            f"[tmp]drawtext="
        )
        input_video_label = "[tmp]"
    else:
        filtro = f"[0:v]drawtext="
        input_video_label = "[0:v]"

    # texto
    filtro += (
        f"text='{texto}':"
        f"fontcolor={cor_texto}:"
        f"fontsize={fonte_tamanho}:"
        f"box=1:"
        f"boxcolor={cor_caixa}:"
        f"boxborderw={borda_caixa}:"
        f"x=(w-text_w)/2:"
        f"y={texto_y}"
    )

    comando = ["ffmpeg"] + inputs + ["-filter_complex", filtro, "-c:a", "copy", output_video]

    print("Executando FFmpeg:")
    print(" ".join(comando))
    subprocess.run(comando, check=True) """
    
def adicionar_texto_e_imagem(
    input_video,
    output_video,
    texto="",  # Permite não passar texto (string vazia por padrão)
    imagem=None,
    imagem_largura=100,
    imagem_altura=100,
    texto_y=200,
    distancia_texto_imagem=20,
    fonte_tamanho=70,
    cor_texto="white",
    cor_caixa="black@0.5",
    borda_caixa=10
):
    # Se nenhum texto (string vazia) e nenhuma imagem forem fornecidos,
    # copia o vídeo de entrada para a saída sem modificações.
    if not texto and not imagem:
        comando = ["ffmpeg", "-y", "-i", input_video, "-map", "0", "-c", "copy", output_video]
        print("Executando FFmpeg (copia simples):")
        print(" ".join(comando))
        subprocess.run(comando, check=True)
        return

    inputs = ["-y", "-i", input_video]
    filter_parts = []  # Lista para construir a string do filter_complex
    
    # Rótulo do stream de vídeo que será usado como entrada para o próximo filtro.
    # Começa com o vídeo de entrada principal [0:v].
    current_video_input_label = "[0:v]"

    if imagem:
        inputs.extend(["-i", imagem]) # Adiciona a imagem como uma entrada
        
        # Calcula a posição Y da imagem relativa à posição Y do texto.
        # A imagem ficará abaixo do texto.
        # Ambos (texto e imagem) são centralizados horizontalmente na tela,
        # o que os alinha horizontalmente.
        imagem_pos_y = texto_y + fonte_tamanho + distancia_texto_imagem
        
        # 1. Redimensiona a imagem e nomeia o resultado como [img_scaled]
        filter_parts.append(f"[1:v]scale={imagem_largura}:{imagem_altura}[img_scaled]")
        # 2. Sobrepõe a imagem redimensionada no stream de vídeo atual.
        # O resultado é nomeado [video_com_imagem].
        # A imagem é centralizada horizontalmente: x=(W-imagem_largura)/2
        margem = 10
        filter_parts.append(
            f"{current_video_input_label}[img_scaled]overlay="
            f"x=W-w-{margem}:y={margem}[video_com_imagem]"
        )
        # O próximo filtro (se houver, como o de texto) usará [video_com_imagem] como entrada.
        current_video_input_label = "[video_com_imagem]"

    # Adiciona o filtro drawtext apenas se um texto não vazio for fornecido.
    if texto:
        # Parâmetros do filtro drawtext para o texto.
        # O texto é centralizado horizontalmente: x=(w-text_w)/2
        # A posição Y do texto é definida por texto_y.
        drawtext_params = (
            f"text='{texto}':"
            f"font='Arial':"  # <-- Aqui
            f"fontcolor={cor_texto}:"
            f"fontsize={fonte_tamanho}:"
            f"box=1:"
            f"boxcolor={cor_caixa}:"
            f"boxborderw={borda_caixa}:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
        )
        # Adiciona o filtro drawtext ao stream de vídeo atual (que pode ser o original ou com imagem).
        filter_parts.append(f"{current_video_input_label}drawtext={drawtext_params}")
        
    comando = ["ffmpeg"] + inputs
    
    # Se houver partes de filtro (ou seja, se imagem ou texto foram adicionados),
    # monta a string do filter_complex e a adiciona ao comando.
    if filter_parts:
        comando.extend(["-filter_complex", ";".join(filter_parts)])
    
    # Copia o stream de áudio do original para o vídeo de saída.
    comando.extend(["-c:a", "copy", output_video])

    print("Executando FFmpeg:")
    print(" ".join(comando))
    subprocess.run(comando, check=True)
    

# 1. Sua função de easing
def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1) / 2

# 2. Função para gerar frames com Ken Burns
def generate_ken_burns_frames(
    image_path,
    output_frames_dir,
    duration_sec,
    fps,
    video_width,
    video_height,
    focal_point_orig=None,
    zoom_start=1.0,
    zoom_end=1.2,
    pan_amount=0.1,
    ease_func=ease_in_out_sine
):
    """
    Gera quadros para um efeito Ken Burns em uma imagem e os salva em output_frames_dir.
    A imagem de entrada é primeiro redimensionada para video_width x video_height.
    """
    if not os.path.exists(output_frames_dir):
        os.makedirs(output_frames_dir)

    try:
        img_original = Image.open(image_path).convert("RGB") # Converter para RGB
    except FileNotFoundError:
        print(f"Erro: Imagem não encontrada em {image_path}")
        return 0
    except Exception as e:
        print(f"Erro ao abrir a imagem {image_path}: {e}")
        return 0

    # Redimensiona a imagem base para as dimensões do vídeo
    # O efeito Ken Burns será aplicado nesta imagem redimensionada
    img_base = img_original.resize((video_width, video_height), Image.Resampling.LANCZOS)
    w, h = video_width, video_height # Dimensões para os cálculos de Ken Burns

    focal_point = focal_point_orig if focal_point_orig else (w // 2, h // 2)
    
    # Ajuste o pan_amount para ser relativo às dimensões do vídeo
    max_pan_x = w * pan_amount
    max_pan_y = h * pan_amount
    
    pan_start_x = random.uniform(-max_pan_x / 2, max_pan_x / 2)
    pan_start_y = random.uniform(-max_pan_y / 2, max_pan_y / 2)
    pan_end_x = random.uniform(-max_pan_x / 2, max_pan_x / 2)
    pan_end_y = random.uniform(-max_pan_y / 2, max_pan_y / 2)

    num_frames = int(duration_sec * fps)

    for i in range(num_frames):
        progress = i / (num_frames -1) if num_frames > 1 else 1.0 # Evita divisão por zero se num_frames == 1
        eased = ease_func(progress)
        
        current_zoom = zoom_start + (zoom_end - zoom_start) * eased
        if current_zoom == 0: current_zoom = 1e-6 # Evita divisão por zero

        current_pan_x = pan_start_x + (pan_end_x - pan_start_x) * eased
        current_pan_y = pan_start_y + (pan_end_y - pan_start_y) * eased
        
        crop_w = int(w / current_zoom)
        crop_h = int(h / current_zoom)

        if crop_w <= 0: crop_w = 1
        if crop_h <= 0: crop_h = 1

        center_x = focal_point[0] + current_pan_x
        center_y = focal_point[1] + current_pan_y
        
        left = max(0, min(center_x - crop_w / 2, w - crop_w))
        top = max(0, min(center_y - crop_h / 2, h - crop_h))
        
        left = int(left)
        top = int(top)
        right = int(left + crop_w)
        bottom = int(top + crop_h)

        # Correções para garantir que o crop esteja dentro dos limites da imagem base
        if right > w: right = w; left = max(0, w - crop_w)
        if bottom > h: bottom = h; top = max(0, h - crop_h)
        if left < 0: left = 0
        if top < 0: top = 0
        
        final_crop_w = right - left
        final_crop_h = bottom - top

        if final_crop_w <=0 or final_crop_h <=0:
            # Se crop inválido, usa a imagem base inteira (já redimensionada para video_width, video_height)
            frame_image = img_base.copy()
        else:
            cropped = img_base.crop((left, top, right, bottom))
            frame_image = cropped.resize((video_width, video_height), Image.Resampling.LANCZOS)
        
        frame_filename = os.path.join(output_frames_dir, f"frame_{i:05d}.png")
        frame_image.save(frame_filename)
        
    return num_frames

# 3. Função para criar vídeo a partir de frames usando ffmpeg
def create_video_from_frames(frames_dir, output_video_path, fps):
    """
    Cria um vídeo a partir de frames PNG em frames_dir usando ffmpeg.
    """
    ffmpeg_cmd = [
        'ffmpeg',
        '-y',  # Sobrescrever arquivo de saída se existir
        '-r', str(fps),
        '-i', os.path.join(frames_dir, 'frame_%05d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-vf', f'fps={fps}', # Garante o FPS de saída
        output_video_path
    ]
    try:
        print(f"Executando ffmpeg para criar vídeo: {' '.join(ffmpeg_cmd)}")
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        print(f"Vídeo intermediário criado: {output_video_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar ffmpeg para criar vídeo:")
        print(f"Comando: {' '.join(e.cmd)}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        return False
    except FileNotFoundError:
        print("Erro: ffmpeg não encontrado. Verifique se está instalado e no PATH.")
        return False


def get_video_duration(path):
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "json", path
    ], capture_output=True, text=True)
    
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def redimensionar_video(input_path, output_path, largura, altura):
    comando = [
        "ffmpeg",
        "-i", input_path,
        "-vf", f"scale={largura}:{altura}",
        "-c:a", "copy",  # copia o áudio sem reencodar
        output_path
    ]
    subprocess.run(comando, check=True)
    

def adicionar_texto_e_imagem_sem_imagens_sobreposta(
    input_video,
    output_video,
    duracao_total,  # <-- Corrigido nome do parâmetro
    texto="",
    imagem=None,
    imagem_largura=200,
    imagem_altura=200,
    texto_y=200,  # Não está mais sendo usado, mas deixei se quiser reaproveitar
    distancia_texto_imagem=20,
    fonte_tamanho=70,
    cor_texto="white",
    cor_caixa="black@0.5",
    borda_caixa=10
):
    if not texto and not imagem:
        comando = ["ffmpeg", "-y", "-i", input_video, "-map", "0", "-c", "copy", output_video]
        print("Executando FFmpeg (copia simples):")
        print(" ".join(comando))
        subprocess.run(comando, check=True)
        return

    fadein_dur = 1.0
    fadeout_dur = 1.0

    inputs = ["-y", "-i", input_video]
    filter_parts = []
    current_video_input_label = "[0:v]"

    if imagem:
        inputs.extend(["-i", imagem])

        # Aplica fade in/out e escala na imagem
        filter_parts.append(
            f"[1:v]format=rgba,"
            f"fade=t=in:st=0:d={fadein_dur},"
            f"fade=t=out:st={duracao_total - fadeout_dur}:d={fadeout_dur},"
            f"scale={imagem_largura}:{imagem_altura}[img_fade]"
        )

        margem = 10
        filter_parts.append(
            f"{current_video_input_label}[img_fade]overlay="
            f"x=W-w-{margem}:y={margem}[video_com_imagem]"
        )
        current_video_input_label = "[video_com_imagem]"

    if texto:
        drawtext_params = (
            f"text='{texto}':"
            f"font='Arial':"
            f"fontcolor={cor_texto}:"
            f"fontsize={fonte_tamanho}:"
            f"box=1:"
            f"boxcolor={cor_caixa}:"
            f"boxborderw={borda_caixa}:"
            f"x=(w-text_w)/2:"
            f"y=(h-text_h)/2:"
            f"alpha='if(lt(t,{fadein_dur}), t/{fadein_dur}, "
            f"if(lt(t,{duracao_total - fadeout_dur}), 1, "
            f"max(0, ({duracao_total}-t)/{fadeout_dur})))'"
        )
        filter_parts.append(f"{current_video_input_label}drawtext={drawtext_params}")

    comando = ["ffmpeg"] + inputs
    if filter_parts:
        comando.extend(["-filter_complex", ";".join(filter_parts)])
    comando.extend(["-c:a", "copy", output_video])

    print("Executando FFmpeg:")
    print(" ".join(comando))
    subprocess.run(comando, check=True)
    

def adicionar_camadas_ao_video_base(
    video_base_path,
    camadas,
    output_path,
    resolucao,
    fps
):
    inputs = [f"-i {video_base_path}"]
    filter_lines = []
    current_overlay_input = "[0:v]"

    for i, el in enumerate(camadas):
        inputs.append(f"-stream_loop -1 -i {el['arquivo']}")

    for i, el in enumerate(camadas):
        input_index = i + 1  # [1:v], [2:v], etc.

        inicio = float(el["inicio"])
        fim = float(el["fim"])
        duracao = fim - inicio

        res_w, res_h = map(int, resolucao.split("x"))
        largura = el.get("largura", res_w)
        altura = el.get("altura", res_h)
        x = el.get("x", 0)
        y = el.get("y", 0)

        # Cálculo automático dos fades
        fade_frac = 0.2  # 20% da duração
        fadein_dur = min(duracao * fade_frac, 1.0)
        fadeout_dur = min(duracao * fade_frac, 1.0)
        fadeout_start = duracao - fadeout_dur

        # Nomes intermediários
        raw = f"[v_raw_{i}]"
        fadedin = f"[v_fadedin_{i}]"
        time_shifted = f"[v_shifted_{i}]"
        fadedout = f"[v_fadedout_{i}]"
        output_vid = f"[out{i}]"

        # 1. Escala + formato
        filter_lines.append(
            f"[{input_index}:v]scale={largura}:{altura},format=rgba{raw}"
        )

        # 2. Fade in no início da camada
        filter_lines.append(
            f"{raw}fade=t=in:st=0:d={fadein_dur}{fadedin}"
        )

        # 3. Deslocamento temporal da camada
        filter_lines.append(
            f"{fadedin}setpts=PTS-STARTPTS+{inicio:.3f}/TB{time_shifted}"
        )

        # 4. Fade out no final da camada (internamente)
        filter_lines.append(
            f"{time_shifted}fade=t=out:st={fadeout_start:.3f}:d={fadeout_dur}{fadedout}"
        )

        # 5. Overlay com tempo ativado
        filter_lines.append(
            f"{current_overlay_input}{fadedout}overlay=x={x}:y={y}:enable='between(t,{inicio:.3f},{fim:.3f})'{output_vid}"
        )

        current_overlay_input = output_vid

    filter_complex = ";".join(filter_lines)

    cmd = [
        "ffmpeg", "-y",
        *" ".join(inputs).split(),
        "-filter_complex", filter_complex,
        "-map", current_overlay_input,
        "-map", "0:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-shortest",
        output_path
    ]

    print("🔧 Executando FFmpeg para adicionar camadas ao vídeo base...")
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Vídeo com camadas adicionado: {output_path}")
    except subprocess.CalledProcessError as e:
        print("❌ Erro ao gerar o vídeo.")
        print("Comando:", e.cmd)
        print("Output:", e.stdout)
        print("Error:", e.stderr)
    
# Exemplo de uso
if __name__ == "__main__":
    
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
    
    clips = []
    
    # --- ÁUDIO ---
    print("Gerando áudio...")
    try:
        criar_audio_com_ducking()
    except Exception as e_audio:
        print(f"Erro ao gerar áudio: {e_audio}")
        
    with open("C:/Users/souza/Downloads/VideoCreator/data/intervalos_entre_camadas.json", 'r', encoding="utf-8") as f:
        intervalos_camadas = json.load(f)
    
    with open("C:/Users/souza/Downloads/VideoCreator/data/camadas.json", 'r', encoding="utf-8") as f:
        camadas_tempos = json.load(f)
        
    with open("C:/Users/souza/Downloads/VideoCreator/data/topicos.json", 'r', encoding="utf-8") as f:
        topicos_tempos = json.load(f)
        
    with open("C:/Users/souza/Downloads/VideoCreator/data/intervalos_entre_topicos.json", 'r', encoding="utf-8") as f:
        intervalo_entre_topicos_tempos = json.load(f)
    
         
    # --- CAMADAS ---
    for i, camada in enumerate(camadas_tempos):
        camada_formatada = "camada_" + camada["word"].lower().replace(' ', '_')
        
        #camada_formatada = "camada_" + camada["word"].lower().replace(' ', '_')
        texto = unicodedata.normalize('NFD', camada["word"])
        texto = ''.join([c for c in texto if unicodedata.category(c) != 'Mn'])
        texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
        camada_formatada = texto.lower().replace(' ', '_')
        
        path_video_editado = f"C:/Users/souza/Downloads/VideoCreator/assets/videos/camadas/editadas/{camada_formatada}.mp4"
        video_duracao = get_video_duration(camada["video_path_base"])
        duracao_intervalo = camada["end"] - camada["start"]

        video_redimensionado_path = f"C:/Users/souza/Downloads/VideoCreator/assets/videos/camadas/editadas/video_temp_{camada_formatada}_redimensionado.mp4"
        redimensionar_video(camada["video_path_base"], video_redimensionado_path, VIDEO_WIDTH, VIDEO_HEIGHT)  # ou a largura/altura que você quiser


        adicionar_texto_e_imagem(
            input_video=video_redimensionado_path,
            output_video=path_video_editado,
            texto=camada["word"].upper(),
            imagem=camada["img_sobreposta"],
            texto_y=200,
            imagem_largura=200,
            imagem_altura=200,
            distancia_texto_imagem=20
        )
        
        camada_obj = {
                "arquivo": path_video_editado,
                "inicio": camada["start"],
                "fim": camada["end"],
                "x": 0,
                "y": 0,
                "largura": VIDEO_WIDTH,
                "altura": VIDEO_HEIGHT,
                "loop": video_duracao < duracao_intervalo
            }
        
        clips.append(camada_obj)
            
        
    # --- RENDER ---    
    adicionar_camadas_ao_video_base(
        video_base_path="C:/Users/souza/Downloads/VideoCreator/assets/videos/video_exemplo_final.mp4",
        camadas=clips,
        output_path="video_final_com_mais_camadas.mp4",
        resolucao=RESOLUCAO_VIDEO,
        fps=VIDEO_FPS
    )
