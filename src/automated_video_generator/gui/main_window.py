"""Main module."""

import re
from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QStackedWidget
)

from automated_video_generator.gui.file_loader_screen import FileLoaderScreen
from automated_video_generator.gui.home_screen import HomeScreen
from automated_video_generator.gui.template_selection_screen import TemplateSelectionScreen

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
    print("Certifique-se que todos os arquivos de processamento (.py) estão na mesma pasta.")

# Mock functions para permitir que a UI rode sem os arquivos de backend
# USAR SE QUISER TESTAR SOMENTE A PARTE GRAFICA SEM GERAR NADA
""" def criar_audio(): print("Executando: criar_audio")
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
def criar_video_ffmpeg(): print("Executando: criar_video_ffmpeg") """




class Worker(QObject):
    progress = Signal(int, str)
    finished = Signal()
    error = Signal(str, str)

    def __init__(self, filepath, tema):
        super().__init__()
        self.filepath = filepath
        self.tema = tema

    def run(self):
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



def validar_formato_iceberg(conteudo: str) -> tuple[bool, str]:
    camadas_obrigatorias = ['Camada Superfície Brilhante', 'Camada Congelada', 'Camada Submersa',
                            'Camada Gelo Profundo', 'Camada Núcleo Abissal', 'Espero que tenham gostado.']
    posicao_anterior = -1
    posicoes_camadas = {}
    for camada in camadas_obrigatorias:
        posicao_atual = conteudo.find(camada)
        if posicao_atual == -1: return False, f"Erro: A seção obrigatória '{camada}' não foi encontrada."
        if posicao_atual < posicao_anterior: return False, f"Erro: A seção '{camada}' está fora da ordem esperada."
        posicao_anterior = posicao_atual
        posicoes_camadas[camada] = posicao_atual
    if posicoes_camadas['Camada Superfície Brilhante'] == 0: return False, "Erro: Falta o texto de introdução."
    for i in range(len(camadas_obrigatorias) - 2):
        camada_atual, camada_seguinte = camadas_obrigatorias[i], camadas_obrigatorias[i + 1]
        inicio_secao = posicoes_camadas[camada_atual] + len(camada_atual)
        fim_secao = posicoes_camadas[camada_seguinte]
        secao_texto = conteudo[inicio_secao:fim_secao]
        topicos_encontrados = re.findall(r'Número (\d)\.', secao_texto)
        if not (1 <= len(
            topicos_encontrados) <= 3): return False, f"Erro na '{camada_atual}': É necessário ter entre 1 e 3 tópicos. Encontrados: {len(topicos_encontrados)}."
        numeros_topicos = [int(n) for n in topicos_encontrados]
        if numeros_topicos != list(range(1,
                                         len(numeros_topicos) + 1)): return False, f"Erro na '{camada_atual}': Os tópicos não estão em ordem sequencial."
    posicao_final_esperada = posicoes_camadas['Espero que tenham gostado.'] + len('Espero que tenham gostado.')
    if len(conteudo.strip()) <= posicao_final_esperada: return False, "Erro: Falta o texto de encerramento."
    return True, "Sucesso! \nO arquivo está no formato correto."





class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoVid Creator")
        self.resize(900, 650)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.home_screen = HomeScreen()
        self.template_screen = TemplateSelectionScreen()
        self.file_loader_screen = FileLoaderScreen()

        # Tela B (para "Create a video about topics") - NOVA TELA
        self.topic_screen = QWidget()  # Substitua pela sua classe real, ex: TopicScreen()
        self.topic_screen.setStyleSheet("background-color: lightblue;")  # Só para diferenciar visualmente agora

        # adiciona ao stackedWidget (a ordem importa para o índice, mas usaremos referências)
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.template_screen)
        self.stacked_widget.addWidget(self.file_loader_screen)
        self.stacked_widget.addWidget(self.topic_screen)  # Index 3

        self.home_screen.start_requested.connect(self.mostrar_tela_templates)

        self.template_screen.back_requested.connect(self.mostrar_tela_inicial)

        self.template_screen.template_selected.connect(self.rotear_escolha_template)

        self.file_loader_screen.back_requested.connect(self.mostrar_tela_templates)

    def mostrar_tela_inicial(self):
        self.stacked_widget.setCurrentWidget(self.home_screen)

    def mostrar_tela_templates(self):
        self.stacked_widget.setCurrentWidget(self.template_screen)

    def mostrar_tela_carregador(self, template_escolhido):
        # aqui você pode salvar qual template foi escolhido se precisar usar depois
        print(f"Template escolhido: {template_escolhido}")
        self.stacked_widget.setCurrentWidget(self.file_loader_screen)

    def rotear_escolha_template(self, template_type):
        print(f"Template escolhido: {template_type}")  # Debug para confirmar

        if template_type == "camadas_1":
            # Se for o vídeo de camadas, vai para a tela de carregar arquivo
            self.stacked_widget.setCurrentWidget(self.file_loader_screen)

        elif template_type == "camadas_2":
            # Se for o vídeo de tópicos, vai para a NOVA tela específica
            # Certifique-se de ter adicionado essa tela ao stacked_widget antes
            self.stacked_widget.setCurrentWidget(self.topic_screen)
