from .criar_audio import main as criar_audio_tp
from .transcricao_audio import main as transcricao_audio_tp
from .pegar_camadas import main as pegar_camadas_tp
from .pegar_topicos import main as pegar_topicos_tp
from .pegar_intervalos import main as pegar_intervalos_tp
from .imagens_em_intervalos_topicos import main as imagens_em_intervalos_topicos_tp
from .get_frase_imagem_intervalo import main as get_frase_imagem_intervalo_tp
from .get_sentido_frase_imagens import main as get_sentido_frase_imagens_tp
from .pegar_imagens import main as pegar_imagens_tp
from .processamento_de_imagem import main as processamento_de_imagem_tp
from .processamento_de_imagem_shorts import main as processamento_de_imagem_shorts_tp
from .criar_video_shorts import main as criar_video_shorts_tp
from .criar_video_ffmpeg import main as criar_video_ffmpeg_tp
from .cortes_audio import main as cortes_audio_tp

__all__ = [
    "criar_audio_tp",
    "transcricao_audio_tp",
    "pegar_camadas_tp",
    "pegar_topicos_tp",
    "pegar_intervalos_tp",
    "imagens_em_intervalos_topicos_tp",
    "get_frase_imagem_intervalo_tp",
    "get_sentido_frase_imagens_tp",
    "pegar_imagens_tp",
    "processamento_de_imagem_tp",
    "processamento_de_imagem_shorts_tp",
    "criar_video_shorts_tp",
    "criar_video_ffmpeg_tp",
    "cortes_audio_tp",
]
