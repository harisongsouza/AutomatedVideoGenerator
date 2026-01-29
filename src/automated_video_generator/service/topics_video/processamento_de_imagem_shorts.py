import os
import cv2 # OpenCV para detecção de rosto
import numpy as np
from PIL import Image, ImageFilter, UnidentifiedImageError
import math
import json # Para salvar metadados

# --- Configurações ---
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_ASPECT_RATIO = TARGET_WIDTH / TARGET_HEIGHT

# Limite para considerar uma imagem "muito pequena" e aplicar blur padding
# Ex: Se menor que 50% da largura OU altura do vídeo, use blur padding. Ajuste conforme necessário.
VERY_SMALL_THRESHOLD_W = TARGET_WIDTH * 0.4
VERY_SMALL_THRESHOLD_H = TARGET_HEIGHT * 0.4

# Caminho para o classificador Haar Cascade (ajuste se necessário)
HAAR_CASCADE_PATH = 'haarcascade_frontalface_default.xml' # Garanta que este arquivo exista

# Força do blur para o fundo (ajuste o raio)
BLUR_RADIUS = 50
BACKGROUND_COLOR = (0, 0, 0) # Preto para letterbox/pillarbox

# Diretórios (mantenha ou ajuste)
INPUT_IMAGE_DIR = "C:/Users/souza/Videos/VideoCreatorHowTo/assets/imagens"
OUTPUT_IMAGE_DIR = "C:/Users/souza/Videos/VideoCreatorHowTo/assets/imagens/imagens_processadas/shorts"
os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)

# Carregar o classificador de rosto
if not os.path.exists(HAAR_CASCADE_PATH):
    print(f"ERRO CRÍTICO: Arquivo Haar Cascade não encontrado em: {HAAR_CASCADE_PATH}")
    exit()
face_cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)

def encontrar_imagem_por_path(json_data, caminho_buscado):
    for camada in json_data:
        for imagem in camada.get("imagens", []):
            path_info = imagem.get("path", {})
            #fff = path_info.get("path_da_imagem")
            #print(f"BALAAAA: {fff} 000000 {caminho_buscado}")
            if path_info.get("path_da_imagem") == caminho_buscado:
                return imagem  # Retorna o objeto imagem correspondente
    return None  # Caso não encontre

# --- Funções Auxiliares (find_main_face_center e create_blurred_background permanecem as mesmas) ---
def find_main_face_center(cv_image):
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
    if len(faces) == 0: return None
    largest_face = max(faces, key=lambda item: item[2] * item[3])
    x, y, w, h = largest_face
    center_x = x + w // 2
    center_y = y + h // 2
    # print(f"    -> Rosto principal detectado (original): ({center_x}, {center_y})") # Debug
    return (center_x, center_y)

def create_blurred_background(img_pil, target_w, target_h, blur_radius):
    resample_bg = Image.Resampling.BILINEAR if hasattr(Image, "Resampling") else Image.BILINEAR
    bg = img_pil.resize((target_w, target_h), resample_bg)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    return bg

# --- Função Principal de Processamento Atualizada ---
def process_and_validate_image_revised(image_path, output_dir):
    try:
        img_pil_original = Image.open(image_path)
        img_pil_original = img_pil_original.convert("RGB")

        original_width, original_height = img_pil_original.size
        print(f"\nProcessando: {os.path.basename(image_path)} - Original: {original_width}x{original_height}")

        # 1. Detectar ponto de interesse na imagem ORIGINAL
        img_cv = np.array(img_pil_original)
        img_cv = img_cv[:, :, ::-1].copy() # RGB (PIL) para BGR (OpenCV)
        interest_center_original = find_main_face_center(img_cv)
        if interest_center_original is None:
            interest_center_original = (original_width // 2, original_height // 2) # Fallback para o centro
            # print("    -> Usando centro da imagem original como ponto de interesse.") # Debug

        processed_img_pil = None
        focal_point_on_target_canvas = None # Coordenadas (x,y) no canvas final 1920x1080

        # --- Decisão: Blur Padding para imagens muito pequenas vs. Redimensionar com Letterbox/Pillarbox ---
        if original_width < VERY_SMALL_THRESHOLD_W or original_height < VERY_SMALL_THRESHOLD_H:
            print(f"  -> Estratégia: Blur Padding (imagem original {original_width}x{original_height} é muito pequena).")
            try:
                background = create_blurred_background(img_pil_original, TARGET_WIDTH, TARGET_HEIGHT, BLUR_RADIUS)
                paste_x = (TARGET_WIDTH - original_width) // 2
                paste_y = (TARGET_HEIGHT - original_height) // 2
                background.paste(img_pil_original, (paste_x, paste_y))
                processed_img_pil = background

                # Calcula o ponto focal no canvas final
                # (ponto de interesse original transladado pela posição de colagem)
                focal_point_on_target_canvas = (
                    interest_center_original[0] + paste_x,
                    interest_center_original[1] + paste_y
                )
                print(f"    -> Imagem original ({original_width}x{original_height}) centralizada em fundo borrado.")
            except Exception as e_blur:
                 print(f"  -> ERRO durante blur padding: {e_blur}.")
                 img_pil_original.close()
                 return None
        else:
            print(f"  -> Estratégia: Redimensionar para caber em {TARGET_WIDTH}x{TARGET_HEIGHT} com letter/pillar-box.")
            try:
                # Calcula as novas dimensões mantendo a proporção para caber no target
                ratio_w = TARGET_WIDTH / original_width
                ratio_h = TARGET_HEIGHT / original_height
                scaling_ratio = min(ratio_w, ratio_h) # Garante que caiba em ambas as dimensões

                new_width = int(original_width * scaling_ratio)
                new_height = int(original_height * scaling_ratio)

                # Redimensiona a imagem original
                resample_method = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
                resized_image = img_pil_original.resize((new_width, new_height), resample_method)
                print(f"    -> Redimensionada para: {new_width}x{new_height} (ratio: {scaling_ratio:.3f})")

                # Cria o canvas de fundo (preto por padrão)
                final_canvas = Image.new("RGB", (TARGET_WIDTH, TARGET_HEIGHT), BACKGROUND_COLOR)

                # Calcula a posição para colar a imagem redimensionada no centro do canvas
                paste_x = (TARGET_WIDTH - new_width) // 2
                paste_y = (TARGET_HEIGHT - new_height) // 2
                final_canvas.paste(resized_image, (paste_x, paste_y))
                processed_img_pil = final_canvas

                # Calcula o ponto focal no canvas final
                # (ponto de interesse original escalado e transladado)
                focal_point_on_target_canvas = (
                    int(interest_center_original[0] * scaling_ratio) + paste_x,
                    int(interest_center_original[1] * scaling_ratio) + paste_y
                )
                # print(f"    -> Ponto focal original: {interest_center_original}") # Debug
                # print(f"    -> Ponto focal no canvas {TARGET_WIDTH}x{TARGET_HEIGHT}: {focal_point_on_target_canvas}") # Debug

                if resized_image: resized_image.close()

            except Exception as e_resize:
                print(f"  -> ERRO durante redimensionamento/letterboxing: {e_resize}")
                img_pil_original.close()
                return None

        # --- Salvar Imagem Processada e Metadados ---
        if processed_img_pil:
            base_name = os.path.basename(image_path)
            name, ext = os.path.splitext(base_name)
            output_filename_jpg = f"{name}_processed.jpg"
            #output_path_jpg = os.path.join(output_dir, output_filename_jpg)
            output_path_jpg = f"{output_dir}/{output_filename_jpg}"
            
            # Salva a imagem JPG
            processed_img_pil.save(output_path_jpg, quality=95)
            print(f"  -> SUCESSO: Imagem salva em {output_path_jpg}")

            # Salva os metadados JSON com o ponto focal no canvas final
            output_filename_json = f"{name}_processed.json"
            #output_path_json = os.path.join(output_dir, output_filename_json)
            output_path_json = f"{output_dir}/{output_filename_json}"
            
            metadata = {
                "focal_point_on_target_canvas": [int(focal_point_on_target_canvas[0]), int(focal_point_on_target_canvas[1])]
                if focal_point_on_target_canvas else [TARGET_WIDTH // 2, TARGET_HEIGHT // 2] # Fallback para centro do canvas
            }
            
            json_path = "C:/Users/souza/Videos/VideoCreatorHowTo/data/add_img_path_img_interv_SHORTS.json"
            with open(json_path, "r", encoding="utf-8") as f:
                tra = json.load(f)
            
            obj_da_imagem = encontrar_imagem_por_path(tra, image_path)
            
            if obj_da_imagem:
                metadata['start'] = obj_da_imagem['start']
                metadata['end'] = obj_da_imagem['end']
                print("✅ Objeto atualizado:")
            else:
                print("❌ Imagem não encontrada.")
            
            try:
                with open(output_path_json, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"  -> Metadados salvos em {output_path_json}")
            except Exception as e_json_save:
                print(f"  AVISO: Falha ao salvar metadados JSON: {e_json_save}")

            if processed_img_pil: processed_img_pil.close()
            img_pil_original.close()
            return output_path_jpg
        else:
            print(f"  -> FALHA: Não foi possível processar a imagem.")
            img_pil_original.close()
            return None

    except FileNotFoundError:
        print(f"ERRO: Arquivo não encontrado: {image_path}")
        return None
    except UnidentifiedImageError:
        print(f"ERRO: Não foi possível identificar/abrir imagem: {image_path}")
        return None
    except cv2.error as e_cv: # Especificamente para erros do OpenCV
        print(f"ERRO OpenCV ao processar {image_path}: {e_cv}")
        if 'img_pil_original' in locals() and hasattr(img_pil_original, 'close'): img_pil_original.close()
        return None
    except Exception as e:
        print(f"ERRO inesperado ao processar {image_path}: {e}")
        if 'img_pil_original' in locals() and hasattr(img_pil_original, 'close'): img_pil_original.close()
        return None

# --- Execução Principal (Exemplo - chame a nova função) ---
def main():
    valid_image_paths = []
    image_files = []
    liss = []
    
    entrada_path = "C:/Users/souza/Videos/VideoCreatorHowTo/data/add_img_path_img_interv_SHORTS.json"

    # Carregar os intervalos entre tópicos
    with open(entrada_path, "r", encoding="utf-8") as f:
        termos_chaves = json.load(f)

    for d in termos_chaves:
        for dd in d["imagens"]:
            liss.append(dd["path"].get("path_da_imagem"))
                        
        
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')
    try:
        for filename in os.listdir(INPUT_IMAGE_DIR):
            if filename.lower().endswith(supported_extensions):
                #image_files.append(os.path.join(INPUT_IMAGE_DIR, filename))
                image_files.append(f"{INPUT_IMAGE_DIR}/{filename}")
    except FileNotFoundError:
        print(f"ERRO: Diretório de entrada não encontrado: {INPUT_IMAGE_DIR}")
        exit()

    if not image_files:
        print(f"Nenhum arquivo de imagem encontrado em {INPUT_IMAGE_DIR}")
    else:
        print(f"Encontradas {len(image_files)} imagens para processar.")
        for img_path in liss:
            # CHAME A FUNÇÃO REVISADA AQUI
            processed_path = process_and_validate_image_revised(img_path, OUTPUT_IMAGE_DIR)
            if processed_path:
                valid_image_paths.append(processed_path)

        print("\n--- Resumo ---")
        print(f"Total de imagens processadas com sucesso: {len(valid_image_paths)}")
        print("Imagens válidas salvas em:", OUTPUT_IMAGE_DIR)
        # print("Lista de caminhos válidos:", valid_image_paths)

    # A lista `valid_image_paths` contém os caminhos prontos para MoviePy.
    
if __name__ == "__main__":
    main()