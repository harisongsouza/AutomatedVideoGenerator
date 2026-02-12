import subprocess
import os
import json

import unicodedata
import re

import math
from math import ceil

import textwrap

import random
import shutil
from PIL import Image

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

from pathlib import Path
from automated_video_generator.config import BASE_DIR

#CONFIGURACAO

PROCESSED_DIR = BASE_DIR / "assets" / "topics_video" / "imagens" / "imagens_processadas"
TEMP_WORK_DIR = BASE_DIR / "assets" / "topics_video" / "videos" / "intervalo_entre_topicos" # Pasta para frames e vídeos intermediários

KB_ZOOM_START = 1.0
KB_ZOOM_END_RANGE = (1.15, 1.35)
KB_PAN_AMOUNT = 0.1 # % da dimensão da imagem para o pan

IMAGE_FOLDER = BASE_DIR / "assets" / "topics_video" / "imagens" / "imagens_camadas" / "imagens_sobreposta_camadas" # CRIE ESTA PASTA E COLOQUE SUAS IMAGENS AQUI

RESOLUCAO_VIDEO = '1920x1080'
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30

NARRACAO_AUDIO_FILE = BASE_DIR / "assets" / "topics_video" / "audio" / "narracao.wav"
MUSICA_BACKGROUND_FILE = BASE_DIR / "assets" / "topics_video" / "audio" / "musica_fundo.mp3"
AUDIO_FINAL_FILE_PATH = BASE_DIR / "assets" / "topics_video" / "audio" / "audio_final.mp3"

INTRO_VIDEO_PATH = BASE_DIR / "assets" / "topics_video" / "videos" / "camadas" / "video_original_intro_encerramento.mp4"
ENCERRAMENTO_VIDEO_PATH = BASE_DIR / "assets" / "topics_video" / "videos" / "camadas" / "video_original_intro_encerramento.mp4"


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
    if not texto and not imagem:
        comando = ["ffmpeg", "-y", "-i", input_video, "-map", "0", "-c", "copy", output_video]
        print("Executando FFmpeg (copia simples):")
        print(" ".join(comando))
        subprocess.run(comando, check=True)
        return

    inputs = ["-y", "-i", input_video]
    filter_parts = []  # Lista para construir a string do filter_complex

    current_video_input_label = "[0:v]"

    if imagem:
        inputs.extend(["-i", imagem]) # Adiciona a imagem como uma entrada

        imagem_pos_y = texto_y + fonte_tamanho + distancia_texto_imagem

        # 1. Redimensiona a imagem e nomeia o resultado como [img_scaled]
        filter_parts.append(f"[1:v]scale={imagem_largura}:{imagem_altura}[img_scaled]")

        margem = 10
        filter_parts.append(
            f"{current_video_input_label}[img_scaled]overlay="
            f"x=W-w-{margem}:y={margem}[video_com_imagem]"
        )
        # O próximo filtro (se houver, como o de texto) usará [video_com_imagem] como entrada.
        current_video_input_label = "[video_com_imagem]"

    # Adiciona o filtro drawtext apenas se um texto não vazio for fornecido.
    if texto:

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
    zoom_start=0.0,
    zoom_end=1.2,
    pan_amount=0.2,
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


def concatenar_videos_com_tempo(objetos, output_path, resolucao="1920x1080", fps=30):
    objetos = sorted(objetos, key=lambda x: x["inicio"])

    partes = []
    tempo_atual = 0.0

    for obj in objetos:
        if obj["inicio"] > tempo_atual:
            duracao_preto = obj["inicio"] - tempo_atual
            partes.append({
                "tipo": "preto",
                "duracao": duracao_preto
            })

        partes.append({
            "tipo": "video",
            "arquivo": obj["arquivo"],
            "duracao": obj["fim"] - obj["inicio"]
        })

        tempo_atual = obj["fim"]

    # Gerar filter_complex
    filter_lines = []
    inputs = []
    maps = []

    for idx, parte in enumerate(partes):
        if parte["tipo"] == "preto":
            inputs.append(f"-f lavfi -t {parte['duracao']} -i color=s={resolucao}:r={fps}:c=black")
            maps.append(f"[{idx}:v:0]")
        else:
            inputs.append(f"-i {parte['arquivo']}")
            maps.append(f"[{idx}:v:0]")

    concat_inputs = "".join(maps)
    filter_complex = f"{concat_inputs}concat=n={len(partes)}:v=1:a=0[outv]"

    cmd = [
        "ffmpeg", "-y",
        *" ".join(inputs).split(),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", "slow",     # Pode trocar para 'ultrafast' se estiver testando
        "-crf", "18",          # Pode usar '0' para lossless, mas o arquivo fica gigante
        output_path
    ]

    print("Rodando comando FFmpeg:")
    print(" ".join(cmd))

    subprocess.run(cmd, check=True)

    print("✅ Vídeo final gerado:", output_path)



import subprocess
import os
import json # Para ler a saída do ffprobe
import os
import json # Para ler a saída do ffprobe
import tempfile # Para criar arquivos temporários para o clipe cortado

def repetir_ate_duracao(input_path, output_path, duracao_desejada, fps_padrao=30):
    frames = round(duracao_desejada * fps_padrao)
    comando = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", input_path,
        "-vf", f"fps={fps_padrao}",
        "-frames:v", str(frames),
        "-c:v", "libx264",
        "-c:a", "aac",
        output_path
    ]
    try:
        subprocess.run(comando, check=True)
        return output_path
    except subprocess.CalledProcessError:
        return None


# (A função get_video_duration permanece a mesma da resposta anterior)
def get_video_duration(video_path):
    """
    Obtém a duração de um arquivo de vídeo usando ffprobe.
    Retorna float: Duração em segundos, ou None.
    """
    if not os.path.exists(video_path):
        # print(f"Aviso: Arquivo não encontrado em {video_path} para obter duração.") # Já logado por quem chama se necessário
        return None

    cmd_ffprobe = [
        'ffprobe',
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        video_path
    ]
    try:
        result = subprocess.run(cmd_ffprobe, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        metadata = json.loads(result.stdout)

        if 'format' in metadata and 'duration' in metadata['format']:
            return float(metadata['format']['duration'])
        for stream in metadata.get('streams', []):
            if stream.get('codec_type') == 'video' and 'duration' in stream:
                return float(stream['duration'])
        # print(f"Aviso: Não foi possível determinar a duração de {video_path} a partir da saída do ffprobe.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar ffprobe para obter duração de {video_path}: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON do ffprobe para {video_path}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao obter duração de {video_path}: {e}")
        return None

def recortar_clip(input_path, output_path_corte, duracao_alvo_segundos, inicio_segundos=0.0,
                  preciso=True, fps_padrao=30):
    if not os.path.exists(input_path):
        print(f"Erro [recortar_clip]: Arquivo de entrada não encontrado em {input_path}")
        return None
    if duracao_alvo_segundos <= 0:
        print(f"Erro [recortar_clip]: Duração alvo deve ser positiva. Recebido: {duracao_alvo_segundos}")
        return None

    duracao_original = get_video_duration(input_path)
    if duracao_original is not None and (inicio_segundos + duracao_alvo_segundos > duracao_original):
        print(f"Aviso [recortar_clip]: Intervalo solicitado ({inicio_segundos:.2f}s até {(inicio_segundos + duracao_alvo_segundos):.2f}s) excede a duração original ({duracao_original:.2f}s).")

    inicio_str = f"{inicio_segundos:.3f}"
    duracao_str = f"{duracao_alvo_segundos:.3f}"

    # número de frames esperado
    frames = round(duracao_alvo_segundos * fps_padrao)

    if preciso:
        cmd_cut = [
            'ffmpeg',
            '-ss', inicio_str,
            '-i', input_path,
            '-vf', f"fps={fps_padrao}",
            '-frames:v', str(frames),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-y', output_path_corte
        ]
    else:
        cmd_cut = [
            'ffmpeg',
            '-ss', inicio_str,
            '-i', input_path,
            '-t', duracao_str,
            '-c', 'copy',
            '-y', output_path_corte
        ]

    try:
        print(f"Recortando {input_path} [{inicio_str}s por {duracao_str}s] -> {output_path_corte}...")
        subprocess.run(cmd_cut, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       text=True, encoding='utf-8')
        print(f"Clipe recortado salvo em: {output_path_corte}")
        return output_path_corte
    except subprocess.CalledProcessError as e:
        print(f"Erro ao recortar {input_path}:")
        print("Comando:", " ".join(e.cmd))
        print("Output (stdout):", e.stdout or "N/A")
        print("Erro (stderr):", e.stderr or "N/A")
        if os.path.exists(output_path_corte):
            try:
                os.remove(output_path_corte)
            except OSError:
                pass
        return None



def padronizar_clip_v1(input_path, output_path, duracao_clip=None,
                    largura_padrao=VIDEO_WIDTH, altura_padrao=VIDEO_HEIGHT,
                    fps_padrao=VIDEO_FPS, crf=18,
                    fade_in=False, fade_out=False, duracao_fade_segundos=1.0, inserir_texto=[], inserir_imagem=[]):  # <- nome correto agora

    if not os.path.exists(input_path):
        print(f"Erro [padronizar_clip]: Arquivo de entrada não encontrado em {input_path}")
        return None

    input_para_processamento = input_path
    arquivo_temporario = None

    try:
        duracao_original = get_video_duration(input_path)

        if duracao_clip is not None and duracao_clip > 0:
            print(f"Clip alvo deve durar {duracao_clip:.2f}s. Vídeo original tem {duracao_original:.2f}s.")

            if duracao_original > duracao_clip:
                print("Vídeo original é maior que o clipe desejado. Recortando...")
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4', prefix='cortado_')
                os.close(temp_fd)
                arquivo_temporario = temp_path

                clip_recortado_path = recortar_clip(input_path, arquivo_temporario, duracao_clip)

                if clip_recortado_path:
                    input_para_processamento = clip_recortado_path
                else:
                    print(f"Falha ao recortar o vídeo {input_path}. Abortando padronização.")
                    return None

            elif duracao_original < duracao_clip:
                print("Vídeo original é menor que o clipe desejado. Repetindo até atingir a duração...")
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4', prefix='repetido_')
                os.close(temp_fd)
                arquivo_temporario = temp_path

                clip_repetido_path = repetir_ate_duracao(input_path, arquivo_temporario, duracao_clip)

                if clip_repetido_path:
                    input_para_processamento = clip_repetido_path
                else:
                    print(f"Falha ao repetir o vídeo {input_path}. Abortando padronização.")
                    return None
            else:
                print("Duração original igual à duração desejada. Usando vídeo como está.")

        elif duracao_clip is not None and duracao_clip <= 0:
            print("Aviso [padronizar_clip]: 'duracao_clip' deve ser positiva. Ignorando ajuste de duração.")

        # Etapa 2: Aplicar fades e outras padronizações (resolução, FPS, etc.)
        if duracao_fade_segundos <= 0 and (fade_in or fade_out):
            print("Aviso [padronizar_clip]: Duração do fade deve ser positiva. Fades serão desabilitados.")
            fade_in = False
            fade_out = False

        video_filters = []
        audio_filters = []

        base_video_filter_string = f'scale={largura_padrao}:{altura_padrao}:force_original_aspect_ratio=decrease,pad={largura_padrao}:{altura_padrao}:(ow-iw)/2:(oh-ih)/2,fps={fps_padrao}'
        video_filters.append(base_video_filter_string)

        video_total_duration_para_fade = None
        if fade_out:
            # IMPORTANTE: Obter duração do clipe que será efetivamente processado (já cortado, se for o caso)
            video_total_duration_para_fade = get_video_duration(input_para_processamento)
            if video_total_duration_para_fade is None:
                print(f"Aviso [padronizar_clip]: Não foi possível obter a duração do vídeo {input_para_processamento}. Fade-out será desabilitado.")
                fade_out = False
            elif duracao_fade_segundos > video_total_duration_para_fade :
                print(f"Aviso [padronizar_clip]: Duração do fade-out ({duracao_fade_segundos}s) é maior que a duração do clipe processado ({video_total_duration_para_fade:.2f}s). O fade-out será aplicado desde o início ou ajustado pelo FFmpeg.")


        if fade_in:
            video_filters.append(f'fade=type=in:start_time=0:duration={duracao_fade_segundos}')
            audio_filters.append(f'afade=type=in:start_time=0:duration={duracao_fade_segundos}')

        if fade_out and video_total_duration_para_fade is not None:
            fade_out_start_time = video_total_duration_para_fade - duracao_fade_segundos
            if fade_out_start_time < 0:
                fade_out_start_time = 0

            video_filters.append(f'fade=type=out:start_time={fade_out_start_time:.3f}:duration={duracao_fade_segundos}')
            audio_filters.append(f'afade=type=out:start_time={fade_out_start_time:.3f}:duration={duracao_fade_segundos}')


####################### EDITAR ##############################################################################################

        if inserir_texto:
            "text:"
            "font:"
            "size:"
            "fadein"
            "fadeout=False"

        if inserir_imagem:
            "path:"
            "position:"
            "size:"
            "fadein"
            "fadeout=False"

####################### RENDERIZAR ############################################################s##################################


        cmd_standardize = ['ffmpeg']
        # Opções de entrada (como -ss, -t) devem vir ANTES de -i se aplicadas ao input globalmente.
        # No nosso caso, o recorte já foi feito, então input_para_processamento é o clipe já na duração (ou quase) correta.
        cmd_standardize.extend(['-i', input_para_processamento])

        if video_filters:
            cmd_standardize.extend(['-vf', ",".join(video_filters)])

        if audio_filters:
            cmd_standardize.extend(['-af', ",".join(audio_filters)])

        cmd_standardize.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', str(crf),
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-ac', '2',
            '-movflags', '+faststart',
            '-y', output_path
        ])

        print(f"Padronizando {input_para_processamento}...")
        # print(f"Comando FFmpeg [padronizar_clip]: {' '.join(cmd_standardize)}")
        process = subprocess.run(cmd_standardize, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        print(f"Clipe final padronizado salvo em: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"Erro ao padronizar {input_para_processamento}:")
        print("Comando:", " ".join(e.cmd))
        if e.stdout:
            print("Output (stdout):", e.stdout)
        if e.stderr:
            print("Erro (stderr):", e.stderr)
        return None
    except Exception as e: # Captura outras exceções inesperadas
        print(f"Erro inesperado em padronizar_clip: {e}")
        return None
    finally:
        if arquivo_temporario and os.path.exists(arquivo_temporario):
            os.remove(arquivo_temporario)





def padronizar_clip(input_path, output_path, duracao_clip=None,
                    largura_padrao=VIDEO_WIDTH, altura_padrao=VIDEO_HEIGHT,
                    fps_padrao=VIDEO_FPS, crf=18,
                    fade_in=False, fade_out=False,
                    inserir_texto=[], inserir_imagem=[]):

    if not os.path.exists(input_path):
        print(f"Erro [padronizar_clip]: Arquivo de entrada não encontrado em {input_path}")
        return None

    input_para_processamento = input_path
    arquivo_temporario = None

    try:
        #pega duracao do VIDEO INTRO que sera usado
        duracao_original = get_video_duration(input_path)

        if duracao_clip is not None and duracao_clip > 0:
            if duracao_original > duracao_clip:
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4', prefix='cortado_')
                os.close(temp_fd)
                arquivo_temporario = temp_path
                input_para_processamento = recortar_clip(input_path, temp_path, duracao_clip)
                if not input_para_processamento:
                    return None
            elif duracao_original < duracao_clip:
                temp_fd, temp_path = tempfile.mkstemp(suffix='.mp4', prefix='repetido_')
                os.close(temp_fd)
                arquivo_temporario = temp_path
                input_para_processamento = repetir_ate_duracao(input_path, temp_path, duracao_clip) #VIDEO INTRO, PATH DE SAIDA, TEMPO FIM - INICIO DO AUDIO FINAL
                if not input_para_processamento:
                    return None
        elif duracao_clip is not None and duracao_clip <= 0:
            print("Aviso: duração inválida ignorada.")

        duracao_final = get_video_duration(input_para_processamento)
        if duracao_final is None:
            print("Erro: duração final não pode ser obtida.")
            return None

        # Redimensionamento sempre como etapa inicial do filter_complex
        redimensionamento = (
            f"[0:v]scale={largura_padrao}:{altura_padrao}:force_original_aspect_ratio=decrease,"
            f"pad={largura_padrao}:{altura_padrao}:(ow-iw)/2:(oh-ih)/2,"
            f"fps={fps_padrao}[video_base]"
        )
        video_base_label = "[video_base]"
        filter_complex_parts = [redimensionamento]
        input_indices = ["-i", input_para_processamento]
        current_video_label = video_base_label

        audio_filters = []

        fade_dur = duracao_final * 0.2

        if fade_in:
            audio_filters.append(f"afade=type=in:start_time=0:duration={fade_dur}")
        if fade_out:
            start = duracao_final * 0.8
            audio_filters.append(f"afade=type=out:start_time={start}:duration={fade_dur}")

        # Adicionar imagem com fade
        if inserir_imagem:
            imagem_path = inserir_imagem[0].get("path")
            imagem_pos = inserir_imagem[0].get("position", "top-right")
            largura = inserir_imagem[0].get("width", 100)
            altura = inserir_imagem[0].get("height", 100)
            fadein = inserir_imagem[0].get("fadein", False)
            fadeout = inserir_imagem[0].get("fadeout", False)

            # Cálculo baseado em 20% da duração do vídeo
            fadein_dur = duracao_final * 0.2 if fadein is True else 0.0
            fadeout_dur = duracao_final * 0.2 if fadeout is True else 0.0

            # Cria vídeo temporário a partir da imagem
            temp_img_vid = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name

            # calcula frames exatos para evitar corte errado
            frames = round(duracao_final * fps_padrao)

            subprocess.run([
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", imagem_path,
                "-vf", f"scale={largura}:{altura},fps={fps_padrao}",
                "-c:v", "libx264", "-pix_fmt", "yuva420p", "-crf", str(crf),
                "-frames:v", str(frames),  # garante duração exata
                temp_img_vid
            ], check=True)

            input_indices.extend(["-i", temp_img_vid])

            # Aplicar fade apenas se necessário
            fade_filters = ["format=rgba"]
            if fadein_dur > 0:
                fade_filters.append(f"fade=t=in:st=0:d={fadein_dur}")
            if fadeout_dur > 0:
                fadeout_start = duracao_final * 0.8
                fade_filters.append(f"fade=t=out:st={fadeout_start}:d={fadeout_dur}")
            fade_filters.append(f"scale={largura}:{altura}")

            filter_complex_parts.append(
                f"[1:v]{','.join(fade_filters)}[img_fade]"
            )

            margem = 10
            pos_x = f"W-w-{margem}" if imagem_pos == "top-right" else f"{margem}"
            pos_y = f"{margem}"

            filter_complex_parts.append(
                f"{current_video_label}[img_fade]overlay=x={pos_x}:y={pos_y}[video_com_imagem]"
            )
            current_video_label = "[video_com_imagem]"

        # Adicionar texto com fade
        if inserir_texto:
            texto_original = inserir_texto[0].get("text", "")
            fonte = inserir_texto[0].get("font", "Arial")
            tamanho = inserir_texto[0].get("size", 70) # Certifique-se que é numérico para cálculos se necessário, mas drawtext aceita como string
            cor = inserir_texto[0].get("color", "white")
            box_color = inserir_texto[0].get("box_color", "black@0.5")
            box_border = inserir_texto[0].get("box_border", 10)
            fadein = inserir_texto[0].get("fadein", False)
            fadeout = inserir_texto[0].get("fadeout", False)

            # --- NOVO CÓDIGO PARA QUEBRA DE LINHA ---
            # Defina uma largura máxima de caracteres por linha (ajuste conforme necessário)
            # Este valor é uma estimativa. Fontes de largura variável podem exigir ajustes.
            largura_max_caracteres = 40  # Exemplo: 30 caracteres por linha

            # Cria um objeto TextWrapper
            # break_long_words=False evita quebrar palavras no meio, se possível
            # replace_whitespace=False mantém espaços existentes (exceto os usados para quebrar)
            wrapper = textwrap.TextWrapper(width=largura_max_caracteres,
                                           break_long_words=True,
                                           replace_whitespace=False,
                                           break_on_hyphens=False) # Evita quebrar em hífens se não for desejado

            # Quebra o texto original em uma lista de linhas
            linhas_quebradas = wrapper.wrap(text=texto_original)

            # Junta as linhas com o caractere de nova linha '\n'
            texto_formatado = "\n".join(linhas_quebradas)
            # --- FIM DO NOVO CÓDIGO ---

            fadein_dur = duracao_final * 0.2 if fadein is True else 0.0
            fadeout_dur = duracao_final * 0.2 if fadeout is True else 0.0
            fadeout_start = duracao_final * 0.8 if fadeout_dur > 0 else duracao_final

            if fadein_dur == 0 and fadeout_dur == 0:
                alpha_expr = "1"
            else:
                alpha_expr = (
                    f"if(lt(t,{fadein_dur}), t/{fadein_dur}, "
                    f"if(lt(t,{fadeout_start}), 1, "
                    f"max(0, ({duracao_final}-t)/{fadeout_dur})))"
                )

            drawtext = (
                f"text='{texto_formatado}':"  # <--- Use o texto_formatado aqui
                f"fontfile='{fonte}':" # É mais robusto usar fontfile se 'fonte' for um caminho
                f"fontcolor={cor}:"
                f"fontsize={tamanho}:"
                f"box=1:"
                f"boxcolor={box_color}:"
                f"boxborderw={box_border}:"
                f"x=(w-text_w)/2:"
                f"y=(h-text_h)/2:"
                f"alpha='{alpha_expr}'"
            )

            label_drawtext = "[video_com_texto]"
            filter_complex_parts.append(f"{current_video_label}drawtext={drawtext}{label_drawtext}")
            current_video_label = label_drawtext


        cmd_standardize = ['ffmpeg', '-y'] + input_indices

        if filter_complex_parts:
            cmd_standardize.extend(['-filter_complex', ";".join(filter_complex_parts)])
            cmd_standardize.extend(['-map', current_video_label])
        else:
            cmd_standardize.extend([
                '-vf',
                f"scale={largura_padrao}:{altura_padrao}:force_original_aspect_ratio=decrease,"
                f"pad={largura_padrao}:{altura_padrao}:(ow-iw)/2:(oh-ih)/2,"
                f"fps={fps_padrao}"
            ])

        if audio_filters:
            cmd_standardize.extend(['-af', ",".join(audio_filters)])

        cmd_standardize.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', str(crf),
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-ac', '2',
            '-movflags', '+faststart',
            output_path
        ])

        print(f"Executando FFmpeg para padronização com texto/imagem: {' '.join(str(cmd_standardize))}")
        subprocess.run(cmd_standardize, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        print(f"Clipe final padronizado salvo em: {output_path}")
        return output_path

    except subprocess.CalledProcessError as e:
        print(f"Erro ao padronizar: {e}")
        print("Comando:", " ".join(e.cmd))
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return None
    finally:
        if arquivo_temporario and os.path.exists(arquivo_temporario):
            os.remove(arquivo_temporario)



import subprocess
import os
import tempfile

# Se você tiver uma função get_video_duration, ela pode ser útil para verificações,
# mas não é estritamente necessária para a lógica de concatenação e adição de narração abaixo.
# def get_video_duration(filepath):
#     # ... sua implementação ...
#     pass

def concatenar_clips_com_narracao(lista_info_clips, caminho_narracao, output_path):
    if not lista_info_clips:
        print("Erro [concatenar_clips_com_narracao]: A lista de informações de clipes está vazia.")
        return None

    clip_paths = []
    for i, clip_info in enumerate(lista_info_clips):
        #print(clip_info)
        if 'arquivo' not in clip_info or not clip_info['arquivo']: # <--- CHAVE AJUSTADA
            print(f"Erro [concatenar_clips_com_narracao]: Dicionário do clipe na posição {i} não contém a chave 'arquivo' ou o valor está vazio.")
            return None
        if not os.path.exists(clip_info['arquivo']): # <--- CHAVE AJUSTADA
            print(f"Erro [concatenar_clips_com_narracao]: Arquivo de clipe não encontrado em {clip_info['arquivo']}")
            return None
        clip_paths.append(clip_info['arquivo']) # <--- CHAVE AJUSTADA

    if not os.path.exists(caminho_narracao):
        print(f"Erro [concatenar_clips_com_narracao]: Arquivo de narração não encontrado em {caminho_narracao}")
        return None

    # Garante que o diretório de saída exista
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"Diretório de saída criado: {output_dir}")
        except OSError as e:
            print(f"Erro [concatenar_clips_com_narracao]: Não foi possível criar o diretório de saída {output_dir}: {e}")
            return None

    temp_concat_list_fd, temp_concat_list_path = tempfile.mkstemp(text=True, suffix='.txt', prefix='ffmpeg_concat_list_')
    temp_concatenated_video_path = None  # Inicializa para o bloco finally

    try:
        # Escreve a lista de arquivos para o FFmpeg concat demuxer
        with os.fdopen(temp_concat_list_fd, 'w', encoding='utf-8') as f_list:
            for clip_path_item in clip_paths:
                # Usa path absoluto e escapa aspas simples no nome do arquivo para robustez
                escaped_path = os.path.abspath(clip_path_item).replace("'", "'\\''")
                f_list.write(f"file '{escaped_path}'\n")

        # Etapa 1: Concatenar os clipes de vídeo
        temp_video_fd, temp_concatenated_video_path_val = tempfile.mkstemp(suffix='.mp4', prefix='concatenated_')
        os.close(temp_video_fd)
        temp_concatenated_video_path = temp_concatenated_video_path_val

        cmd_concat = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', temp_concat_list_path,
            '-c', 'copy',
            temp_concatenated_video_path
        ]
        print(f"Executando FFmpeg para concatenação: {' '.join(cmd_concat)}")
        concat_process = subprocess.run(cmd_concat, capture_output=True, text=True, encoding='utf-8', check=False)

        if concat_process.returncode != 0:
            print("Erro ao concatenar vídeos.")
            print(f"Comando: {' '.join(cmd_concat)}")
            print(f"Código de Retorno: {concat_process.returncode}")
            print(f"stderr: {concat_process.stderr}")
            return None

        print(f"Vídeos concatenados temporariamente em: {temp_concatenated_video_path}")

        # Etapa 2: Adicionar narração ao vídeo concatenado
        cmd_add_narration = [
            'ffmpeg', '-y',
            '-i', temp_concatenated_video_path,
            '-i', caminho_narracao,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-ac', '2',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            '-movflags', '+faststart',
            output_path
        ]
        print(f"Executando FFmpeg para adicionar narração: {' '.join(cmd_add_narration)}")
        narration_process = subprocess.run(cmd_add_narration, capture_output=True, text=True, encoding='utf-8', check=False)

        if narration_process.returncode != 0:
            print("Erro ao adicionar narração.")
            print(f"Comando: {' '.join(cmd_add_narration)}")
            print(f"Código de Retorno: {narration_process.returncode}")
            print(f"stderr: {narration_process.stderr}")
            return None

        print(f"✅ Vídeo final com narração salvo em: {output_path}")
        return output_path

    except Exception as e:
        print(f"Ocorreu um erro inesperado [concatenar_clips_com_narracao]: {e}")
        return None
    finally:
        if os.path.exists(temp_concat_list_path):
            try:
                os.remove(temp_concat_list_path)
            except OSError as e:
                print(f"Aviso: não foi possível remover o arquivo temporário de lista {temp_concat_list_path}: {e}")

        if temp_concatenated_video_path and os.path.exists(temp_concatenated_video_path):
            try:
                os.remove(temp_concatenated_video_path)
            except OSError as e:
                print(f"Aviso: não foi possível remover o arquivo de vídeo concatenado temporário {temp_concatenated_video_path}: {e}")

def ordenar_json_por_inicio(caminho_entrada, caminho_saida=None):
    with open(caminho_entrada, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    # Ordena pela chave "inicio"
    dados_ordenados = sorted(dados, key=lambda x: x.get('inicio', 0))

    # Salva de volta (no mesmo arquivo ou em outro)
    caminho_saida = caminho_saida or caminho_entrada
    with open(caminho_saida, 'w', encoding='utf-8') as f:
        json.dump(dados_ordenados, f, ensure_ascii=False, indent=2)

    print(f"Arquivo ordenado salvo em: {caminho_saida}")


def get_audio_duration_1(audio_path):
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def criar_video_fundo_preto_e_audio(audio_path, output_path):
    # Parâmetros
    duration = get_audio_duration_1(audio_path)  # duração do vídeo em segundos (ajuste conforme o áudio)

    # Comando FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:s=1920x1080:d={duration}",  # vídeo preto 1080p
        "-i", audio_path,                                              # áudio externo
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",  # para parar quando o áudio ou vídeo acabar
        output_path
    ]

    subprocess.run(cmd, check=True)
    print("Vídeo com fundo preto criado:", output_path)


def criar_video_fundo_preto(audio_path, output_path):
    # Parâmetros
    duration = get_audio_duration_1(audio_path)  # duração do vídeo em segundos (ajuste conforme o áudio)

    # Comando FFmpeg
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=black:s=1920x1080:d={duration}",  # vídeo preto 1080p
        "-c:v", "libx264",
        "-t", str(duration),  # duração total
        output_path
    ]

    subprocess.run(cmd, check=True)
    print("Vídeo com fundo preto criado:", output_path)



def adicionar_audio_ao_video(video_sem_audio: str, audio_path: str, output_path: str):
    """
    Adiciona uma trilha de áudio a um vídeo que não tem som.
    O áudio será cortado ou estendido para coincidir com a duração do vídeo.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_sem_audio,
        "-i", audio_path,
        "-shortest",                  # Corta o áudio se for maior que o vídeo
        "-c:v", "copy",               # Copia o vídeo sem reprocessar
        "-c:a", "aac",                # Codifica o áudio em AAC
        "-b:a", "192k",               # Qualidade razoável
        output_path
    ]

    subprocess.run(cmd, check=True)
    print(f"Áudio adicionado ao vídeo: {output_path}")


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
        "-map", "0:a?",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        "-shortest",
        output_path
    ]

    print("🔧 Executando FFmpeg para adicionar camadas ao vídeo base...")
    try:
        print(cmd)
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Vídeo com camadas adicionado: {output_path}")
    except subprocess.CalledProcessError as e:
        print("❌ Erro ao gerar o vídeo.")
        print("Comando:", e.cmd)
        print("Output:", e.stdout)
        print("Error:", e.stderr)

import json
import subprocess
import os
import uuid # Para gerar nomes de arquivo únicos

def preencher_lacunas_temporais(
    caminho_arquivo_json: str,
    diretorio_clips_gerados: str = "generated_black_clips",
    x_preenchimento: int = 0,
    y_preenchimento: int = 0,
    largura_preenchimento: int = 1920,
    altura_preenchimento: int = 1080,
    fps_preenchimento: int = 30
) -> list:
    """
    Analisa um arquivo JSON contendo uma lista de clipes de vídeo. Identifica
    lacunas temporais entre clipes consecutivos. Se uma lacuna for maior que 0.2s,
    gera dinamicamente um vídeo preto que começa 0.1s após o fim do clipe anterior
    e termina 0.1s antes do início do clipe seguinte.
    Este vídeo é salvo e referenciado no novo objeto de clipe inserido.

    Args:
        caminho_arquivo_json (str): O caminho para o arquivo JSON a ser analisado.
        diretorio_clips_gerados (str): O diretório (relativo ao arquivo JSON ou absoluto)
                                       onde os vídeos de preenchimento gerados serão salvos.
                                       Será criado se não existir.
        x_preenchimento (int): A coordenada X para o objeto do clipe de preenchimento.
        y_preenchimento (int): A coordenada Y para o objeto do clipe de preenchimento.
        largura_preenchimento (int): A largura para o vídeo e objeto do clipe de preenchimento.
        altura_preenchimento (int): A altura para o vídeo e objeto do clipe de preenchimento.
        fps_preenchimento (int): A taxa de quadros (FPS) para os vídeos de preenchimento gerados.

    Returns:
        list: Uma nova lista de dicionários de clipes com as lacunas (maiores que 0.2s)
              preenchidas por vídeos pretos gerados dinamicamente e com tempos ajustados.
              Retorna a lista original de clipes se o FFmpeg não for encontrado
              ou se houver erros críticos na configuração inicial.
    """
    try:
        with open(caminho_arquivo_json, 'r', encoding='utf-8') as f:
            clipes = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo JSON não encontrado em '{caminho_arquivo_json}'")
        return []
    except json.JSONDecodeError:
        print(f"Erro: Falha ao decodificar o JSON do arquivo '{caminho_arquivo_json}'")
        return []

    if not isinstance(clipes, list):
        print(f"Erro: O conteúdo do JSON em '{caminho_arquivo_json}' não é uma lista.")
        return []

    if not clipes:
        return []

    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Erro: FFmpeg não encontrado ou não está funcionando corretamente. "
              "Esta função requer FFmpeg para gerar os vídeos de preenchimento. "
              "Verifique a instalação do FFmpeg e se está no PATH do sistema.")
        return clipes

    if os.path.isabs(diretorio_clips_gerados):
        diretorio_saida_absoluto = diretorio_clips_gerados
    else:
        base_dir_json = os.path.dirname(os.path.abspath(caminho_arquivo_json))
        diretorio_saida_absoluto = os.path.join(base_dir_json, diretorio_clips_gerados)

    try:
        os.makedirs(diretorio_saida_absoluto, exist_ok=True)
        print(f"Clipes de preenchimento serão salvos em: {diretorio_saida_absoluto}")
    except OSError as e:
        print(f"Erro ao criar o diretório de saída '{diretorio_saida_absoluto}': {e}")
        return clipes

    def criar_video_preto_dinamico(duracao_segundos: float, largura: int, altura: int, fps: int, caminho_saida_video: str) -> bool:
        duracao_formatada = f"{duracao_segundos:.3f}"
        comando_ffmpeg = [
            'ffmpeg', '-y', '-f', 'lavfi',
            '-i', f'color=c=black:s={largura}x{altura}:d={duracao_formatada}',
            '-an', '-r', str(fps), '-loglevel', 'error', caminho_saida_video
        ]
        print(f"Executando FFmpeg para criar '{os.path.basename(caminho_saida_video)}' com duração {duracao_formatada}s...")
        try:
            resultado = subprocess.run(comando_ffmpeg, capture_output=True, text=True, check=True, encoding='utf-8')
            if resultado.stdout: print(f"FFmpeg stdout: {resultado.stdout.strip()}")
            if resultado.stderr: print(f"FFmpeg stderr: {resultado.stderr.strip()}")
            print(f"Vídeo '{os.path.basename(caminho_saida_video)}' criado com sucesso.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar FFmpeg para criar '{os.path.basename(caminho_saida_video)}':")
            if e.cmd: print(f"  Comando: {' '.join(e.cmd)}")
            if e.returncode: print(f"  Código de retorno: {e.returncode}")
            if e.stdout: print(f"  Saída: {e.stdout.strip()}")
            if e.stderr: print(f"  Erro: {e.stderr.strip()}")
            return False

    if len(clipes) < 2:
        return clipes

    nova_lista_de_clipes = []
    nova_lista_de_clipes.append(clipes[0])

    offset_tempo = 0.1  # Ajuste de 0.1 segundos em cada extremidade da lacuna

    for i in range(len(clipes) - 1):
        clipe_atual = clipes[i]
        clipe_seguinte = clipes[i+1]

        if not all(k in clipe_atual for k in ['fim']) or \
           not all(k in clipe_seguinte for k in ['inicio']):
            print("Aviso: Clipe atual ou seguinte está com chaves 'fim' ou 'inicio' ausentes. Pulando.")
            nova_lista_de_clipes.append(clipe_seguinte)
            continue

        if not isinstance(clipe_atual['fim'], (int, float)) or \
           not isinstance(clipe_seguinte['inicio'], (int, float)):
            print("Aviso: 'fim' do clipe atual ou 'inicio' do clipe seguinte não são numéricos. Pulando.")
            nova_lista_de_clipes.append(clipe_seguinte)
            continue

        fim_atual = clipe_atual['fim']
        inicio_seguinte = clipe_seguinte['inicio']

        if fim_atual < inicio_seguinte:  # Verifica se existe uma lacuna
            duracao_lacuna_original = inicio_seguinte - fim_atual

            # Verifica se a lacuna original é grande o suficiente para o ajuste
            if duracao_lacuna_original > (2 * offset_tempo):
                novo_inicio_clipe_lacuna = fim_atual + offset_tempo
                novo_fim_clipe_lacuna = inicio_seguinte - offset_tempo
                duracao_video_efetiva = novo_fim_clipe_lacuna - novo_inicio_clipe_lacuna

                # Confirmação adicional, embora a condição anterior já deva garantir isso
                if duracao_video_efetiva <= 0:
                    print(f"Aviso: Cálculo resultou em duração não positiva ({duracao_video_efetiva:.3f}s) para lacuna entre {fim_atual:.3f} e {inicio_seguinte:.3f}. Não será preenchida.")
                    nova_lista_de_clipes.append(clipe_seguinte)
                    continue

                print(f"Lacuna original detectada: {fim_atual:.3f} -> {inicio_seguinte:.3f} (Duração: {duracao_lacuna_original:.3f}s).")
                print(f"  Aplicando ajuste de {offset_tempo:.1f}s: Novo clipe terá Início: {novo_inicio_clipe_lacuna:.3f}, Fim: {novo_fim_clipe_lacuna:.3f}, Duração do vídeo: {duracao_video_efetiva:.3f}s.")

                nome_arquivo_lacuna = f"black_video_gap_{str(uuid.uuid4())}.mp4"
                caminho_completo_clipe_lacuna = os.path.join(diretorio_saida_absoluto, nome_arquivo_lacuna)

                if criar_video_preto_dinamico(duracao_video_efetiva, largura_preenchimento, altura_preenchimento, fps_preenchimento, caminho_completo_clipe_lacuna):
                    clipe_de_lacuna = {
                        "arquivo": caminho_completo_clipe_lacuna,
                        "inicio": novo_inicio_clipe_lacuna, # Usa o início ajustado
                        "fim": novo_fim_clipe_lacuna,       # Usa o fim ajustado
                        "x": x_preenchimento,
                        "y": y_preenchimento,
                        "largura": largura_preenchimento,
                        "altura": altura_preenchimento
                    }
                    nova_lista_de_clipes.append(clipe_de_lacuna)
                else:
                    print(f"Falha ao criar o vídeo de preenchimento para a lacuna ajustada (original: {fim_atual:.3f} a {inicio_seguinte:.3f}). Esta lacuna não será preenchida com vídeo.")
            else:
                # A lacuna existe, mas é <= 0.2s, então não pode ser ajustada e preenchida pela nova regra.
                print(f"Lacuna detectada entre {fim_atual:.3f} e {inicio_seguinte:.3f} (duração: {duracao_lacuna_original:.3f}s) "
                      f"é muito curta (<= {2 * offset_tempo:.1f}s) para aplicar o ajuste de {offset_tempo:.1f}s em cada extremidade. "
                      "Esta lacuna não será preenchida com um novo clipe.")

        nova_lista_de_clipes.append(clipe_seguinte)

    return nova_lista_de_clipes


def gif_to_mp4(input_path, output_path=None):
    if output_path is None:
        output_path = os.path.splitext(input_path)[0] + ".mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-movflags", "faststart",
        output_path
    ]

    subprocess.run(cmd, check=True)
    return output_path



# Exemplo de uso
def main():
    print("Carregando imagens e metadados...")
    gif_to_mp4(BASE_DIR / "assets" / "topics_video" / "videos" / "transition_video.gif")
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
    clips_lista = []


    # --- ÁUDIO ---
    print("Gerando áudio...")
    try:
        criar_audio_com_ducking()
    except Exception as e_audio:
        print(f"Erro ao gerar áudio: {e_audio}") #descomente se quiser audio narracao com musica de fundo

    with open(BASE_DIR / "data" / "topics_video" / "topicos.json", 'r', encoding="utf-8") as f:
        topicos_tempos = json.load(f)

    with open(BASE_DIR / "data" / "topics_video" / "intervalos_entre_topicos.json", 'r', encoding="utf-8") as f:
        intervalo_entre_topicos_tempos = json.load(f)

    # --- INTRO ---
    for intervalo_camada in intervalo_entre_topicos_tempos:
        if intervalo_camada["nome"] == "intervalo_introducao":
            inicio = intervalo_camada["start"]
            fim = intervalo_camada["end"]
            duracao_intervalo = fim - inicio

            clip_padronizado = padronizar_clip(
                input_path=INTRO_VIDEO_PATH,
                output_path=BASE_DIR / "assets" / "topics_video" / "videos" / "camadas" / "videos_padronizado" / "video_introducao_padronizado.mp4",
                duracao_clip=duracao_intervalo,
                fade_in=True,
                fade_out=True
            )

            camada_obj = {
                "arquivo": clip_padronizado,
                "inicio": inicio,
                "fim": fim,
                "x": 0,
                "y": 0,
                "largura": VIDEO_WIDTH,
                "altura": VIDEO_HEIGHT
            }
            #intro_lista.append(camada_obj)
            clips.append(camada_obj)


    #TOPICOS
    for i, topico in enumerate(topicos_tempos):
        path_video_editado = BASE_DIR / "assets" / "topics_video" / "videos" / f"topicos/{i}.mp4"
        #path_video_editado = f"C:/Users/souza/Videos/VideoCreator/{i}.mp4"

        intervalo_duracao = topico["end"] - topico["start"]

        txt = [{
            "text": topico["word"].title().replace('"', '').replace(":", '').replace("'", ''),
            "font": "Arial",
            "size": "60",
            "color": "white",
            "box_color": "black@0.5",
            "box_border": 10,
            "fadein": True,
            "fadeout": True
        }]

        clip_padronizado = padronizar_clip(
            input_path=BASE_DIR / "assets" / "topics_video" / "videos" / "transition_video.mp4",
            output_path=path_video_editado,
            duracao_clip=intervalo_duracao,
            fade_in=False,
            fade_out=False,
            inserir_texto=txt

        )

        camada_obj = {
            "arquivo": clip_padronizado,
            "inicio": topico["start"],
            "fim": topico["end"],
            "x": 0,
            "y": 0,
            "largura": VIDEO_WIDTH,
            "altura": VIDEO_HEIGHT
        }
        #topicos_lista.append(camada_obj)
        clips.append(camada_obj)


    #CLIPS
    for i, data in enumerate(image_data):
        print(f"\nProcessando imagem {i+1}/{len(image_data)}: {os.path.basename(data['img_path'])}")

        clip_frames_dir = os.path.join(TEMP_WORK_DIR, f"clip_{i}_frames")
        intermediate_video_path = os.path.join(TEMP_WORK_DIR, f"clip_{i}.mp4")

        # 1. Gerar frames para o clipe atual
        print(f"Gerando frames em: {clip_frames_dir}")
        num_generated_frames = generate_ken_burns_frames(
            image_path=data["img_path"],
            output_frames_dir=clip_frames_dir,
            duration_sec=data["duration"],
            fps=VIDEO_FPS,
            video_width=VIDEO_WIDTH,
            video_height=VIDEO_HEIGHT,
            focal_point_orig=data["focal_point"],
            zoom_start=KB_ZOOM_START,
            zoom_end=random.uniform(*KB_ZOOM_END_RANGE),
            pan_amount=KB_PAN_AMOUNT,
            ease_func=ease_in_out_sine
        )

        if num_generated_frames > 0:
            # 2. Criar vídeo a partir dos frames gerados
            if create_video_from_frames(clip_frames_dir, intermediate_video_path, VIDEO_FPS):
                camada_obj = {
                    "arquivo": intermediate_video_path,
                    "inicio": data["start"],
                    "fim": data["end"],
                    "x": 0,
                    "y": 0,
                    "largura": VIDEO_WIDTH,
                    "altura": VIDEO_HEIGHT
                }
                clips_lista.append(camada_obj)
                clips.append(camada_obj)

                # Limpar frames após criar o vídeo do clipe para economizar espaço
                shutil.rmtree(clip_frames_dir) # Descomente se quiser limpar frames imediatamente
            else:
                print(f"Falha ao criar vídeo para {data['img_path']}. Pulando.")
        else:
            print(f"Nenhum frame gerado para {data['img_path']}. Pulando.")

    # --- ENCERRAMENTO ---
    for intervalo_camada in intervalo_entre_topicos_tempos:
        if intervalo_camada["nome"] == "intervalo_conclusao":
            inicio = intervalo_camada["start"]
            fim = intervalo_camada["end"]
            duracao_intervalo = fim - inicio

            clip_padronizado = padronizar_clip(
                input_path=ENCERRAMENTO_VIDEO_PATH,
                output_path=BASE_DIR / "assets" / "topics_video" / "videos" / "camadas" / "videos_padronizado" / "video_encerramento_padronizado.mp4",
                duracao_clip=duracao_intervalo,
                fade_in=True,
                fade_out=True
            )

            camada_obj = {
                "arquivo": clip_padronizado,
                "inicio": inicio,
                "fim": fim,
                "x": 0,
                "y": 0,
                "largura": VIDEO_WIDTH,
                "altura": VIDEO_HEIGHT
            }
            #intro_lista.append(camada_obj)
            clips.append(camada_obj)


    # --- RENDER ---

    with open(BASE_DIR / "data" / "topics_video" / "final_list_render.json", "w", encoding="utf-8") as f:
        json.dump(clips, f, ensure_ascii=False, indent=2, default=str)

    ordenar_json_por_inicio(BASE_DIR / "data" / "topics_video" / "final_list_render.json", BASE_DIR / "data" / "topics_video" / "final_list_render.json")

    lista_com_lacunas_preenchidas = preencher_lacunas_temporais(BASE_DIR / "data" / "topics_video" / "final_list_render.json")

    with open(BASE_DIR / "data" / "topics_video" / "dados_video_corrigido.json", "w", encoding="utf-8") as f_out:
        json.dump(lista_com_lacunas_preenchidas, f_out, indent=2, ensure_ascii=False, default=str)

    print("\nResultado salvo em 'dados_video_corrigido.json'")

    with open(BASE_DIR / "data" / "topics_video" / "dados_video_corrigido.json", 'r', encoding="utf-8") as f:
        intervalos_final_list = json.load(f)

    concatenar_clips_com_narracao(intervalos_final_list, str(AUDIO_FINAL_FILE_PATH), str(BASE_DIR / "assets" / "topics_video" / "videos" / "output" / "end_video.mp4"))
    #concatenar_clips_com_narracao(intervalos_final_list, NARRACAO_AUDIO_FILE, "C:/Users/souza/Videos/VideoCreator/end_video.mp4") #sem audio de fundo


if __name__ == "__main__":
    main()
