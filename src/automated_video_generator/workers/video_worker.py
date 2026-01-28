from PySide6.QtCore import Signal, QObject

"""
try:
    from criar_audio import main as criar_audio
    from transcricao_audio import main as transcricao_audio
    from pegar_camadas import main as pegar_camadas
    from pegar_topicos import main as pegar_topicos
    from pegar_intervalos import main as pegar_intervalos
    from imagens_em_intervalos_topicos import main as imagens_em_intervalos_topicos
    from get_frase_imagem_intervalo import main as get_frase_imagem_intervalo
    from get_sentido_frase_imagens import main as get_sentido_frase_imagens
    from pegar_imagens import main as pegar_imagens
    from processamento_de_imagem import main as processamento_de_imagem
    from processamento_de_imagem_shorts import main as processamento_de_imagem_shorts
    from criar_video_shorts import main as criar_video_shorts
    from criar_video_ffmpeg import main as criar_video_ffmpeg
    from cortes_audio import main as cortes_audio
except ImportError as e:
    print(f"ERRO DE IMPORTAÇÃO: {e}")
    print("Certifique-se que todos os arquivos de processamento (.py) estão na mesma pasta.") """

# Mock functions para permitir que a UI rode sem os arquivos de backend
# USAR SE QUISER TESTAR SOMENTE A PARTE GRAFICA SEM GERAR NADA
def criar_audio(): print("Executando: criar_audio")
def cortes_audio(): print("Executando: cortes_audio")
def transcricao_audio(): print("Executando: transcricao_audio")
def pegar_camadas(): print("Executando: pegar_camadas")
def pegar_topicos(): print("Executando: pegar_topicos")
def pegar_intervalos(): print("Executando: pegar_intervalos")
def imagens_em_intervalos_topicos(): print("Executando: imagens_em_intervalos_topicos")
def get_frase_imagem_intervalo(): print("Executando: get_frase_imagem_intervalo")
def get_sentido_frase_imagens(tema): print(f"Executando: get_sentido_frase_imagens com tema: {tema}")
def pegar_imagens(): print("Executando: pegar_imagens")
def processamento_de_imagem(): print("Executando: processamento_de_imagem")
def criar_video_ffmpeg(): print("Executando: criar_video_ffmpeg")

class Worker(QObject):
    progress = Signal(int, str)
    finished = Signal()
    error = Signal(str, str)

    def __init__(self, filepath, tema, template_escolhido):
        super().__init__()
        self.filepath = filepath
        self.tema = tema
        self.template_escolhido = template_escolhido

    def run(self):
        if self.template_escolhido == "camadas":
            print(f"Executando scripts de: CAMADAS")
            tarefas = [
                (criar_audio, "CRIANDO AUDIO..."),
                (cortes_audio, "CRIANDO TRANSCRICAO..."),
                (transcricao_audio, "CRIANDO TRANSCRICAO WORDS..."),
                (pegar_camadas, "PEGANDO CAMADAS..."),
                (pegar_topicos, "PEGANDO TOPICOS..."),
                (pegar_intervalos, "PEGANDO INTERVALOS..."),
                (imagens_em_intervalos_topicos, "MONTANDO JSON IMAGENS DOS INTERVALOS..."),
                (get_frase_imagem_intervalo, "MONTANDO JSON INTERVALO DE CADA IMAGENS..."),
                (lambda: get_sentido_frase_imagens(self.tema), "MONTANDO A FRASE DE BUSCA DE CADA IMAGEM..."),

                (pegar_imagens, "PEGANDO IMAGENS DA INTERNET..."),
                (processamento_de_imagem, "PROCESSANDO IMAGENS..."),
                (criar_video_ffmpeg, "CRIANDO VIDEO FINAL..."),

                # (processamento_de_imagem_shorts, "PROCESSANDO IMAGENS PARA O SHORTS..."),
                # (criar_video_shorts, "CRIANDO VIDEO SHORTS..."),
                # (tryyy, "LEGENDANDO VIDEO SHORTS...")
            ]
            total_steps = len(tarefas)
            current_step_message = "Iniciando..."
            try:
                for i, (func, message) in enumerate(tarefas):
                    current_step_message = message
                    self.progress.emit(int((i / total_steps) * 100), current_step_message)
                    func()
                self.progress.emit(100, "Processo concluído!")
                self.finished.emit()
            except Exception as e:
                error_title = f"Erro durante: {current_step_message}"
                error_details = f"Ocorreu uma exceção não tratada:\n\n{type(e).__name__}: {e}"
                self.error.emit(error_title, error_details)
        elif self.template_escolhido == "topicos":
            print(f"Executando scripts de: TOPICOS")
            tarefas = [
                (criar_audio, "CRIANDO AUDIO..."),
                (cortes_audio, "CRIANDO TRANSCRICAO..."),
                (transcricao_audio, "CRIANDO TRANSCRICAO WORDS..."),
                (pegar_camadas, "PEGANDO CAMADAS..."),
                (pegar_topicos, "PEGANDO TOPICOS..."),
                (pegar_intervalos, "PEGANDO INTERVALOS..."),
                (imagens_em_intervalos_topicos, "MONTANDO JSON IMAGENS DOS INTERVALOS..."),
                (get_frase_imagem_intervalo, "MONTANDO JSON INTERVALO DE CADA IMAGENS..."),
                (lambda: get_sentido_frase_imagens(self.tema), "MONTANDO A FRASE DE BUSCA DE CADA IMAGEM..."),

                (pegar_imagens, "PEGANDO IMAGENS DA INTERNET..."),
                (processamento_de_imagem, "PROCESSANDO IMAGENS..."),
                (criar_video_ffmpeg, "CRIANDO VIDEO FINAL..."),

                # (processamento_de_imagem_shorts, "PROCESSANDO IMAGENS PARA O SHORTS..."),
                # (criar_video_shorts, "CRIANDO VIDEO SHORTS..."),
                # (tryyy, "LEGENDANDO VIDEO SHORTS...")
            ]
            total_steps = len(tarefas)
            current_step_message = "Iniciando..."
            try:
                for i, (func, message) in enumerate(tarefas):
                    current_step_message = message
                    self.progress.emit(int((i / total_steps) * 100), current_step_message)
                    func()
                self.progress.emit(100, "Processo concluído!")
                self.finished.emit()
            except Exception as e:
                error_title = f"Erro durante: {current_step_message}"
                error_details = f"Ocorreu uma exceção não tratada:\n\n{type(e).__name__}: {e}"
                self.error.emit(error_title, error_details)
        else:
            return False, "Executar as funções para produção do video."

