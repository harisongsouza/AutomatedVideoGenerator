# Importa os módulos necessários
import sys
import re
import os
import shutil
from PySide6.QtCore import Signal, Qt, QObject, QThread
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QLabel,
    QMessageBox,
    QStackedWidget,
    QProgressBar,
)
from PySide6.QtGui import QFont, QCursor

# =============================================================================
# IMPORTAÇÕES DO SEU PROJETO (main.py)
# =============================================================================
try:
    from tryyy import main as tryyy
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
def criar_video_ffmpeg(): print("Executando: criar_video_ffmpeg")
def processamento_de_imagem_shorts(): print("Executando: processamento_de_imagem_shorts")
def processamento_de_imagem(): print("Executando: processamento_de_imagem")
def criar_video_shorts(): print("Executando: criar_video_shorts")
def tryyy(): print("Executando: tryyy") """



# =============================================================================
# CONSTANTES E PALETA DE CORES
# =============================================================================
DESTINATION_DIR = os.path.join(os.path.expanduser("~"), "Downloads/VideoCreator/data/")
os.makedirs(DESTINATION_DIR, exist_ok=True)

COR_FUNDO_PRINCIPAL = "#0B0711"
COR_FUNDO_CONTAINER = "#171520"
COR_FUNDO_CARD = "#232027"
COR_BOTAO_BASE = "#201E2D"
COR_TEXTO_PRINCIPAL = "#DCDCDC"
COR_TEXTO_SECUNDARIO = "#D3D3D3"
COR_DESTAQUE = "#E2114A"
COR_HOVER = "#7053AA"
COR_DESTAQUE_HOVER = "#C10F40"
COR_BOTAO_DESABILITADO = "#404047"
COR_TEXTO_DESABILITADO = "#8A8A8A"
COR_PROGRESSBAR_FUNDO = "#201E2D"
COR_PROGRESSBAR_CHUNK = "#7053AA"
COR_TEXTO_COMPLETO = "#34A853"

# =============================================================================
# WORKER THREAD REUTILIZÁVEL (INTOCADO)
# =============================================================================
class Worker(QObject):
    progress = Signal(int, str, int)
    finished = Signal()
    error = Signal(str, str)

    def __init__(self, tasks, tema):
        super().__init__()
        self.tasks = tasks
        self.tema = tema
        self.is_running = True

    def run(self):
        total_steps = len(self.tasks)
        current_step_message = "Iniciando..."
        try:
            for i, (func, message) in enumerate(self.tasks):
                if not self.is_running: break
                current_step_message = message
                self.progress.emit(int((i / total_steps) * 100), current_step_message, i)
                if 'tema' in func.__code__.co_varnames: func(self.tema)
                else: func()
            if self.is_running:
                self.progress.emit(100, "Etapa concluída!", len(self.tasks))
                self.finished.emit()
        except Exception as e:
            error_title = f"Erro durante: {current_step_message}"
            error_details = f"Ocorreu uma exceção não tratada:\n\n{type(e).__name__}: {e}"
            self.error.emit(error_title, error_details)

    def stop(self):
        self.is_running = False

# =============================================================================
# LÓGICA DE VALIDAÇÃO (INTOCADA)
# =============================================================================
def validar_formato_iceberg(conteudo: str) -> tuple[bool, str]:
    # (O código de validação permanece o mesmo)
    camadas_obrigatorias = ['Camada Superfície Brilhante', 'Camada Congelada', 'Camada Submersa', 'Camada Gelo Profundo', 'Camada Núcleo Abissal', 'Espero que tenham gostado.']
    posicao_anterior = -1; posicoes_camadas = {}
    for camada in camadas_obrigatorias:
        posicao_atual = conteudo.find(camada)
        if posicao_atual == -1: return False, f"Erro: A seção obrigatória '{camada}' não foi encontrada."
        if posicao_atual < posicao_anterior: return False, f"Erro: A seção '{camada}' está fora da ordem esperada."
        posicao_anterior = posicao_atual; posicoes_camadas[camada] = posicao_atual
    if 'Camada Superfície Brilhante' not in posicoes_camadas or posicoes_camadas['Camada Superfície Brilhante'] == 0: return False, "Erro: Falta o texto de introdução."
    for i in range(len(camadas_obrigatorias) - 2):
        camada_atual, camada_seguinte = camadas_obrigatorias[i], camadas_obrigatorias[i+1]
        inicio_secao = posicoes_camadas[camada_atual] + len(camada_atual); fim_secao = posicoes_camadas[camada_seguinte]
        secao_texto = conteudo[inicio_secao:fim_secao]
        topicos_encontrados = re.findall(r'Número (\d)\.', secao_texto)
        if not (1 <= len(topicos_encontrados) <= 3): return False, f"Erro na '{camada_atual}': É necessário ter entre 1 e 3 tópicos. Encontrados: {len(topicos_encontrados)}."
        numeros_topicos = [int(n) for n in topicos_encontrados]
        if numeros_topicos != list(range(1, len(numeros_topicos) + 1)): return False, f"Erro na '{camada_atual}': Os tópicos não estão em ordem sequencial."
    posicao_final_esperada = posicoes_camadas['Espero que tenham gostado.'] + len('Espero que tenham gostado.')
    if len(conteudo.strip()) <= posicao_final_esperada: return False, "Erro: Falta o texto de encerramento."
    return True, "Sucesso! \nO arquivo está no formato correto."

# =============================================================================
# TELAS (HomeScreen, FileLoaderScreen, ProcessingScreen - INTOCADAS)
# =============================================================================
class HomeScreen(QWidget):
    start_requested = Signal()
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("HomeScreen")
        layout = QVBoxLayout(self); layout.setSpacing(20); layout.setAlignment(Qt.AlignCenter)
        titulo_label = QLabel("AutoVid Creator"); titulo_label.setFont(QFont("Segoe UI", 36, QFont.Bold)); titulo_label.setAlignment(Qt.AlignCenter); titulo_label.setObjectName("TituloLabel")
        subtitulo_label = QLabel("Crie vídeos de forma automatizada a partir de um roteiro."); subtitulo_label.setFont(QFont("Segoe UI", 12)); subtitulo_label.setAlignment(Qt.AlignCenter); subtitulo_label.setObjectName("SubtituloLabel")
        botao_iniciar = QPushButton("Carregar Roteiro e Iniciar"); botao_iniciar.clicked.connect(self.start_requested.emit); botao_iniciar.setObjectName("BotaoDestaque"); botao_iniciar.setCursor(Qt.PointingHandCursor)
        layout.addStretch(); layout.addWidget(titulo_label); layout.addWidget(subtitulo_label); layout.addSpacing(30); layout.addWidget(botao_iniciar); layout.addStretch()

class FileLoaderScreen(QWidget):
    back_requested = Signal()
    validation_success = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("FileLoaderScreen")
        self.valid_filepath = None
        layout_principal = QVBoxLayout(self); layout_principal.setContentsMargins(30, 30, 30, 30); layout_principal.setSpacing(15)
        self.caminho_arquivo_label = QLabel("Nenhum arquivo de roteiro selecionado."); self.caminho_arquivo_label.setFont(QFont("Segoe UI", 10)); self.caminho_arquivo_label.setWordWrap(True); self.caminho_arquivo_label.setObjectName("InfoLabel"); self.caminho_arquivo_label.setAlignment(Qt.AlignCenter)
        self.botao_carregar = QPushButton("Carregar e Validar Arquivo"); self.botao_carregar.clicked.connect(self.abrir_e_validar_arquivo); self.botao_carregar.setCursor(Qt.PointingHandCursor)
        self.botao_proximo = QPushButton("Iniciar Processamento"); self.botao_proximo.setEnabled(False); self.botao_proximo.setObjectName("BotaoProximo"); self.botao_proximo.setCursor(Qt.ArrowCursor)
        self.botao_proximo.clicked.connect(self.iniciar_processamento)
        botoes_acao_layout = QHBoxLayout(); botoes_acao_layout.addWidget(self.botao_carregar); botoes_acao_layout.addWidget(self.botao_proximo)
        self.botao_voltar = QPushButton("Voltar"); self.botao_voltar.clicked.connect(self.back_requested.emit); self.botao_voltar.setCursor(Qt.PointingHandCursor)
        layout_principal.addStretch(); layout_principal.addWidget(self.caminho_arquivo_label); layout_principal.addLayout(botoes_acao_layout); layout_principal.addStretch(); layout_principal.addWidget(self.botao_voltar, 0, Qt.AlignBottom | Qt.AlignRight)
    def abrir_e_validar_arquivo(self):
        self.botao_proximo.setEnabled(False); self.botao_proximo.setCursor(Qt.ArrowCursor); self.valid_filepath = None
        caminho_arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar um arquivo .txt", "", "Arquivos de Texto (*.txt)")
        if caminho_arquivo:
            self.caminho_arquivo_label.setText(f"Analisando arquivo:\n{caminho_arquivo}")
            try:
                with open(caminho_arquivo, 'r', encoding='utf-8') as f: conteudo = f.read()
                sucesso, mensagem = validar_formato_iceberg(conteudo)
                if sucesso:
                    try:
                        caminho_destino = os.path.join(DESTINATION_DIR, "roteiro.txt")
                        shutil.copy(caminho_arquivo, caminho_destino)
                        QMessageBox.information(self, "Sucesso", f"{mensagem}\nO arquivo foi salvo em 'data/roteiro.txt'.")
                        self.botao_proximo.setEnabled(True); self.botao_proximo.setCursor(Qt.PointingHandCursor); self.valid_filepath = caminho_destino
                    except Exception as copy_error:
                        QMessageBox.critical(self, "Erro ao Copiar Arquivo", f"Não foi possível copiar o roteiro.\n\nErro: {copy_error}")
                else: QMessageBox.warning(self, "Erro de Formato", mensagem)
            except Exception as e: QMessageBox.critical(self, "Erro de Leitura", f"Não foi possível ler o arquivo:\n{e}")
    def iniciar_processamento(self):
        if self.valid_filepath: self.validation_success.emit(self.valid_filepath)
    def reset(self):
        self.caminho_arquivo_label.setText("Nenhum arquivo de roteiro selecionado.")
        self.botao_proximo.setEnabled(False)
        self.botao_proximo.setCursor(Qt.ArrowCursor)
        self.valid_filepath = None

class ProcessingScreen(QWidget):
    next_step_requested = Signal()
    back_requested = Signal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ProcessingScreen")
        self.thread = None; self.worker = None; self.task_labels = []
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(30, 30, 30, 30); main_layout.setAlignment(Qt.AlignCenter)
        self.stage_label = QLabel(""); self.stage_label.setFont(QFont("Segoe UI", 18, QFont.Bold)); self.stage_label.setAlignment(Qt.AlignCenter); self.stage_label.setObjectName("StageLabel")
        self.statusLabel = QLabel("Aguardando início..."); self.statusLabel.setFont(QFont("Segoe UI", 14)); self.statusLabel.setAlignment(Qt.AlignCenter)
        self.progressBar = QProgressBar(); self.progressBar.setTextVisible(True); self.progressBar.setRange(0, 100); self.progressBar.setValue(0)
        self.tasks_list_container = QWidget(); self.tasks_list_container.setObjectName("TasksContainer")
        self.tasks_list_layout = QVBoxLayout(self.tasks_list_container); self.tasks_list_layout.setSpacing(5); self.tasks_list_layout.setAlignment(Qt.AlignCenter)
        self.botao_proximo = QPushButton("Próximo"); self.botao_proximo.setObjectName("BotaoProximo"); self.botao_proximo.setCursor(Qt.PointingHandCursor); self.botao_proximo.hide(); self.botao_proximo.clicked.connect(self.next_step_requested.emit)
        self.botao_voltar = QPushButton("Cancelar"); self.botao_voltar.setCursor(Qt.PointingHandCursor); self.botao_voltar.clicked.connect(self.cancel_processing)
        botoes_layout = QHBoxLayout(); botoes_layout.addStretch(); botoes_layout.addWidget(self.botao_voltar); botoes_layout.addWidget(self.botao_proximo); botoes_layout.addStretch()
        main_layout.addStretch(); main_layout.addWidget(self.stage_label); main_layout.addSpacing(10); main_layout.addWidget(self.statusLabel); main_layout.addSpacing(20); main_layout.addWidget(self.progressBar); main_layout.addSpacing(15); main_layout.addWidget(self.tasks_list_container); main_layout.addSpacing(20); main_layout.addLayout(botoes_layout); main_layout.addStretch()
    def set_stage_info(self, text): self.stage_label.setText(text)
    def start_processing(self, tasks, tema):
        self.reset_ui(tasks); self.thread = QThread(); self.worker = Worker(tasks, tema); self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run); self.worker.finished.connect(self.on_worker_finished); self.worker.error.connect(self.on_worker_error); self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit); self.worker.finished.connect(self.worker.deleteLater); self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
    def update_progress(self, value, message, current_task_index):
        self.progressBar.setValue(value); self.statusLabel.setText(message)
        for i, label in enumerate(self.task_labels):
            original_text = label.property("original_text")
            if i < current_task_index: label.setText(f"✓ {original_text}"); label.setStyleSheet(f"color: {COR_TEXTO_COMPLETO};")
            elif i == current_task_index: label.setText(f"► {original_text}"); label.setStyleSheet(f"color: {COR_TEXTO_PRINCIPAL}; font-weight: bold;")
            else: label.setText(original_text); label.setStyleSheet(f"color: {COR_TEXTO_SECUNDARIO};")
    def on_worker_finished(self):
        self.statusLabel.setText("Etapa concluída com sucesso!"); self.botao_proximo.show(); self.botao_voltar.setText("Voltar")
    def on_worker_error(self, title, message):
        QMessageBox.critical(self, title, message); self.statusLabel.setText(f"Erro! {title}"); self.botao_voltar.setText("Voltar"); self.back_requested.emit()
    def cancel_processing(self):
        if self.worker and self.worker.is_running:
            if QMessageBox.question(self, "Cancelar", "Tem certeza que deseja cancelar o processo atual?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.worker.stop(); self.thread.quit(); self.thread.wait(); self.statusLabel.setText("Processo cancelado pelo usuário."); self.botao_voltar.setText("Voltar"); self.back_requested.emit()
        else: self.back_requested.emit()
    def reset_ui(self, tasks=[]):
        self.statusLabel.setText("Iniciando processamento..."); self.progressBar.setValue(0); self.botao_proximo.hide(); self.botao_voltar.setText("Cancelar")
        while self.tasks_list_layout.count():
            child = self.tasks_list_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        self.task_labels.clear()
        for _, message in tasks:
            label = QLabel(message); label.setFont(QFont("Segoe UI", 10)); label.setProperty("original_text", message); label.setStyleSheet(f"color: {COR_TEXTO_SECUNDARIO};")
            self.tasks_list_layout.addWidget(label); self.task_labels.append(label)

# =============================================================================
# TELA FINAL ### MODIFICADO ###
# =============================================================================
class FinalScreen(QWidget):
    restart_requested = Signal()
    create_shorts_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FinalScreen")
        layout = QVBoxLayout(self); layout.setSpacing(20); layout.setAlignment(Qt.AlignCenter)
        
        titulo_label = QLabel("Processo Concluído!"); titulo_label.setFont(QFont("Segoe UI", 28, QFont.Bold)); titulo_label.setAlignment(Qt.AlignCenter)
        subtitulo_label = QLabel("Seu vídeo foi gerado com sucesso.\nVocê pode encontrar os arquivos na pasta de destino."); subtitulo_label.setFont(QFont("Segoe UI", 12)); subtitulo_label.setAlignment(Qt.AlignCenter)
        
        botao_reiniciar = QPushButton("Criar Novo Vídeo"); botao_reiniciar.clicked.connect(self.restart_requested.emit); botao_reiniciar.setCursor(Qt.PointingHandCursor)
        
        self.botao_criar_shorts = QPushButton("Criar Shorts"); self.botao_criar_shorts.clicked.connect(self.create_shorts_requested.emit); self.botao_criar_shorts.setObjectName("BotaoDestaque"); self.botao_criar_shorts.setCursor(Qt.PointingHandCursor)

        botoes_layout = QHBoxLayout(); botoes_layout.setSpacing(20); botoes_layout.addStretch(); botoes_layout.addWidget(botao_reiniciar); botoes_layout.addWidget(self.botao_criar_shorts); botoes_layout.addStretch()
        
        layout.addStretch(); layout.addWidget(titulo_label); layout.addWidget(subtitulo_label); layout.addSpacing(30); layout.addLayout(botoes_layout); layout.addStretch()

    # ### NOVO: Método para mostrar/ocultar o botão de shorts ###
    def set_shorts_option_visible(self, visible):
        """Controla a visibilidade do botão 'Criar Shorts'."""
        self.botao_criar_shorts.setVisible(visible)

# =============================================================================
# JANELA PRINCIPAL E EXECUÇÃO ### MODIFICADO ###
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("AutoVid Creator"); self.resize(800, 600)
        
        self.current_filepath = None
        self.current_tema = "imagens sobre "

        # Definição das tarefas
        self.tarefas_etapa_1 = [
            (criar_audio, "CRIANDO ÁUDIO..."), (cortes_audio, "REALIZANDO CORTES NO ÁUDIO..."),
            (transcricao_audio, "GERANDO TRANSCRIÇÃO..."), (pegar_camadas, "IDENTIFICANDO CAMADAS..."),
            (pegar_topicos, "EXTRAINDO TÓPICOS..."), (pegar_intervalos, "DEFININDO INTERVALOS DE TEMPO..."),
            (imagens_em_intervalos_topicos, "MAPEANDO IMAGENS PARA INTERVALOS..."),
            (get_frase_imagem_intervalo, "GERANDO FRASES DE BUSCA..."),
            (lambda tema: get_sentido_frase_imagens(tema), "ANALISANDO SENTIDO DAS FRASES...")
        ]
        self.tarefas_etapa_2 = [
            (pegar_imagens, "BAIXANDO IMAGENS DA INTERNET..."),
            (processamento_de_imagem, "PROCESSANDO IMAGENS..."),
            (criar_video_ffmpeg, "CRIANDO VÍDEO FINAL...")
        ]
        self.tarefas_etapa_3 = [
            (processamento_de_imagem_shorts, "PROCESSANDO IMAGENS PARA O SHORTS..."),
            (criar_video_shorts, "CRIANDO VIDEO SHORTS..."),
            (tryyy, "LEGENDANDO VIDEO SHORTS...")
        ]

        # Criação e adição das telas
        self.stacked_widget = QStackedWidget(); self.setCentralWidget(self.stacked_widget)
        self.home_screen = HomeScreen()
        self.file_loader_screen = FileLoaderScreen()
        self.processing_screen_1 = ProcessingScreen()
        self.processing_screen_2 = ProcessingScreen()
        self.processing_screen_shorts = ProcessingScreen()
        self.final_screen = FinalScreen()
        
        for screen in [self.home_screen, self.file_loader_screen, self.processing_screen_1, self.processing_screen_2, self.processing_screen_shorts, self.final_screen]:
            self.stacked_widget.addWidget(screen)
        
        # Conexões de Sinais e Slots
        self.home_screen.start_requested.connect(self.mostrar_tela_carregador)
        self.file_loader_screen.back_requested.connect(self.mostrar_tela_inicial)
        self.file_loader_screen.validation_success.connect(self.iniciar_etapa_1)
        
        self.processing_screen_1.next_step_requested.connect(self.iniciar_etapa_2)
        self.processing_screen_1.back_requested.connect(self.mostrar_tela_carregador)
        
        # ### MODIFICADO: Conexões para controlar a visibilidade do botão ###
        self.processing_screen_2.next_step_requested.connect(self.handle_video_completion)
        self.processing_screen_2.back_requested.connect(lambda: self.stacked_widget.setCurrentWidget(self.processing_screen_1))
        
        self.processing_screen_shorts.next_step_requested.connect(self.handle_shorts_completion)
        self.processing_screen_shorts.back_requested.connect(self.handle_shorts_completion)
        
        self.final_screen.restart_requested.connect(self.mostrar_tela_inicial)
        self.final_screen.create_shorts_requested.connect(self.iniciar_etapa_shorts)

    def mostrar_tela_inicial(self):
        self.file_loader_screen.reset()
        self.stacked_widget.setCurrentWidget(self.home_screen)

    def mostrar_tela_carregador(self): self.stacked_widget.setCurrentWidget(self.file_loader_screen)
    
    def mostrar_tela_final(self): self.stacked_widget.setCurrentWidget(self.final_screen)

    # ### NOVO: Método chamado quando o VÍDEO PRINCIPAL é concluído ###
    def handle_video_completion(self):
        """Mostra a tela final com a opção de criar shorts."""
        self.final_screen.set_shorts_option_visible(True)
        self.mostrar_tela_final()

    # ### NOVO: Método chamado quando os SHORTS são concluídos ###
    def handle_shorts_completion(self):
        """Mostra a tela final SEM a opção de criar shorts."""
        self.final_screen.set_shorts_option_visible(False)
        self.mostrar_tela_final()
        
    def iniciar_etapa_1(self, filepath):
        self.current_filepath = filepath
        self.stacked_widget.setCurrentWidget(self.processing_screen_1)
        self.processing_screen_1.set_stage_info("Etapa 1 de 2: Preparando Roteiro e Áudio")
        self.processing_screen_1.start_processing(self.tarefas_etapa_1, self.current_tema)
        
    def iniciar_etapa_2(self):
        self.stacked_widget.setCurrentWidget(self.processing_screen_2)
        self.processing_screen_2.set_stage_info("Etapa 2 de 2: Gerando o Vídeo Final")
        self.processing_screen_2.start_processing(self.tarefas_etapa_2, self.current_tema)

    def iniciar_etapa_shorts(self):
        self.stacked_widget.setCurrentWidget(self.processing_screen_shorts)
        self.processing_screen_shorts.set_stage_info("Etapa 3: Criando Shorts")
        self.processing_screen_shorts.start_processing(self.tarefas_etapa_3, self.current_tema)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QSS = f"""
        QMainWindow, QWidget {{ background-color: {COR_FUNDO_PRINCIPAL}; color: {COR_TEXTO_PRINCIPAL}; font-family: Segoe UI; }}
        #HomeScreen, #FileLoaderScreen, #ProcessingScreen, #FinalScreen, QDialog {{ background-color: {COR_FUNDO_CONTAINER}; }}
        QPushButton {{ background-color: {COR_BOTAO_BASE}; color: {COR_TEXTO_PRINCIPAL}; font-size: 14px; font-weight: bold; padding: 12px 24px; border: 1px solid {COR_HOVER}; border-radius: 8px; }}
        QPushButton:hover {{ background-color: {COR_HOVER}; border: 1px solid {COR_DESTAQUE}; }}
        QPushButton:disabled {{ background-color: {COR_BOTAO_DESABILITADO}; color: {COR_TEXTO_DESABILITADO}; border: 1px solid {COR_BOTAO_DESABILITADO}; }}
        #BotaoProximo {{ background-color: {COR_HOVER}; }} #BotaoProximo:hover {{ background-color: {COR_DESTAQUE}; }}
        #BotaoDestaque {{ background-color: {COR_DESTAQUE}; font-size: 16px; padding: 15px 30px; border: none; }}
        #BotaoDestaque:hover {{ background-color: {COR_DESTAQUE_HOVER}; }}
        QLabel {{ background-color: transparent; color: {COR_TEXTO_PRINCIPAL}; }}
        #TituloLabel {{ color: {COR_TEXTO_PRINCIPAL}; }} #SubtituloLabel {{ color: {COR_TEXTO_SECUNDARIO}; }}
        #InfoLabel {{ background-color: {COR_FUNDO_CARD}; border: 1px solid {COR_BOTAO_BASE}; border-radius: 8px; padding: 20px; color: {COR_TEXTO_SECUNDARIO}; }}
        QMessageBox {{ background-color: {COR_FUNDO_CONTAINER}; }}
        QMessageBox QLabel {{ color: {COR_TEXTO_PRINCIPAL}; background-color: transparent; }}
        QMessageBox QPushButton {{ background-color: {COR_HOVER}; color: {COR_TEXTO_PRINCIPAL}; border-radius: 5px; padding: 8px 16px; min-width: 80px; }}
        QMessageBox QPushButton:hover {{ background-color: {COR_DESTAQUE}; }}
        QProgressBar {{ border: 2px solid {COR_BOTAO_BASE}; border-radius: 5px; background-color: {COR_PROGRESSBAR_FUNDO}; text-align: center; color: {COR_TEXTO_PRINCIPAL}; font-size: 12px; font-weight: bold; }}
        QProgressBar::chunk {{ background-color: {COR_PROGRESSBAR_CHUNK}; border-radius: 3px; margin: 1px; }}
        #TasksContainer {{ border-radius: 8px; background-color: {COR_FUNDO_CARD}; padding: 10px; }}
    """
    app.setStyleSheet(QSS)
    janela = MainWindow()
    janela.show()
    sys.exit(app.exec())