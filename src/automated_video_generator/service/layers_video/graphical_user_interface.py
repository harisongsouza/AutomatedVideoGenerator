# Importa os módulos necessários
import sys
import re
import os       # Novo: para criar diretórios
import shutil   # Novo: para copiar arquivos
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
    QDialog,
    QFrame
)
from PySide6.QtGui import QFont, QCursor

# =============================================================================
# IMPORTAÇÕES DO SEU PROJETO (main.py)
# =============================================================================
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
#USAR SE QUISER TESTAR SOMENTE A PARTE GRAFICA SEM GERAR NADA
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

# =============================================================================
# CONSTANTES E PALETA DE CORES
# =============================================================================
DESTINATION_DIR = os.path.join("C:/Users/souza/Downloads/VideoCreator/", "data/") # Novo: Caminho padrão para o roteiro

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

# =============================================================================
# WORKER THREAD COM A LÓGICA REAL DO SEU main.py
# =============================================================================
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
            
            #(processamento_de_imagem_shorts, "PROCESSANDO IMAGENS PARA O SHORTS..."),
            #(criar_video_shorts, "CRIANDO VIDEO SHORTS..."),
            #(tryyy, "LEGENDANDO VIDEO SHORTS...")
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

# =============================================================================
# JANELA DE PROGRESSO (INTOCADA)
# =============================================================================
class ProgressWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processando Vídeo"); self.setModal(True); self.resize(450, 150); self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.progressBar = QProgressBar(); self.progressBar.setTextVisible(True); self.progressBar.setRange(0, 100)
        self.statusLabel = QLabel("Iniciando processamento..."); self.statusLabel.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self); layout.addWidget(self.statusLabel); layout.addWidget(self.progressBar)
    def start_processing(self, filepath, tema):
        self.thread = QThread(); self.worker = Worker(filepath, tema); self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run); self.worker.finished.connect(self.on_finished); self.worker.error.connect(self.on_error); self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit); self.worker.finished.connect(self.worker.deleteLater); self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start(); self.exec()
    def update_progress(self, value, message): self.progressBar.setValue(value); self.statusLabel.setText(message)
    def on_finished(self): self.statusLabel.setText("Processo concluído com sucesso!"); self.progressBar.setValue(100); QMessageBox.information(self, "Sucesso", "O vídeo foi gerado com sucesso!"); self.accept()
    def on_error(self, title, message): QMessageBox.critical(self, title, message); self.reject()

# =============================================================================
# LÓGICA DE VALIDAÇÃO (INTOCADA)
# =============================================================================
def validar_formato_iceberg(conteudo: str) -> tuple[bool, str]:
    camadas_obrigatorias = ['Camada Superfície Brilhante', 'Camada Congelada', 'Camada Submersa', 'Camada Gelo Profundo', 'Camada Núcleo Abissal', 'Espero que tenham gostado.']
    posicao_anterior = -1; posicoes_camadas = {}
    for camada in camadas_obrigatorias:
        posicao_atual = conteudo.find(camada)
        if posicao_atual == -1: return False, f"Erro: A seção obrigatória '{camada}' não foi encontrada."
        if posicao_atual < posicao_anterior: return False, f"Erro: A seção '{camada}' está fora da ordem esperada."
        posicao_anterior = posicao_atual; posicoes_camadas[camada] = posicao_atual
    if posicoes_camadas['Camada Superfície Brilhante'] == 0: return False, "Erro: Falta o texto de introdução."
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
# TELA INICIAL (INTOCADA)
# =============================================================================
class HomeScreen(QWidget):
    start_requested = Signal()
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("HomeScreen")
        layout = QVBoxLayout(self); layout.setSpacing(20); layout.setAlignment(Qt.AlignCenter)
        titulo_label = QLabel("AutoVid Creator"); titulo_label.setFont(QFont("Segoe UI", 36, QFont.Bold)); titulo_label.setAlignment(Qt.AlignCenter); titulo_label.setObjectName("TituloLabel")
        subtitulo_label = QLabel("Create videos automatically from a script."); subtitulo_label.setFont(QFont("Segoe UI", 12)); subtitulo_label.setAlignment(Qt.AlignCenter); subtitulo_label.setObjectName("SubtituloLabel")
        botao_iniciar = QPushButton("Start New Project"); botao_iniciar.clicked.connect(self.start_requested.emit); botao_iniciar.setObjectName("BotaoDestaque"); botao_iniciar.setCursor(Qt.PointingHandCursor)
        layout.addStretch(); layout.addWidget(titulo_label); layout.addWidget(subtitulo_label); layout.addSpacing(30); layout.addWidget(botao_iniciar); layout.addStretch()

# =============================================================================
# NOVA TELA: SELEÇÃO DE TEMPLATE
# =============================================================================
class TemplateSelectionScreen(QWidget):
    template_selected = Signal(str) # Emite qual template foi escolhido
    back_requested = Signal()       # Para voltar para home

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplateSelectionScreen")
        
        # Layout Principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        
        # Título
        lbl_titulo = QLabel("Selecione o Tipo de Vídeo")
        lbl_titulo.setFont(QFont("Segoe UI", 24, QFont.Bold))
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setObjectName("TituloLabel")
        
        # Layout dos Cartões (Horizontal)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)
        
        # Template 1
        self.btn_template1 = QPushButton("criar video de camadas")
        self.btn_template1.setObjectName("TemplateCard") # Identificador para o CSS
        self.btn_template1.setCursor(Qt.PointingHandCursor)
        self.btn_template1.clicked.connect(lambda: self.template_selected.emit("camadas_1"))
        
        # Template 2
        self.btn_template2 = QPushButton("criar video de topicos")
        self.btn_template2.setObjectName("TemplateCard") # Identificador para o CSS
        self.btn_template2.setCursor(Qt.PointingHandCursor)
        self.btn_template2.clicked.connect(lambda: self.template_selected.emit("camadas_2"))
        
        cards_layout.addStretch()
        cards_layout.addWidget(self.btn_template1)
        cards_layout.addWidget(self.btn_template2)
        cards_layout.addStretch()
        
        # Botão Voltar
        self.botao_voltar = QPushButton("Back")
        self.botao_voltar.setCursor(Qt.PointingHandCursor)
        self.botao_voltar.clicked.connect(self.back_requested.emit)
        
        # Adiciona tudo ao layout principal
        main_layout.addWidget(lbl_titulo)
        main_layout.addSpacing(20)
        main_layout.addLayout(cards_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.botao_voltar, alignment=Qt.AlignCenter)

# =============================================================================
# TELA DE CARREGAMENTO DE ARQUIVO (MODIFICADA)
# =============================================================================
class FileLoaderScreen(QWidget):
    back_requested = Signal()
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("FileLoaderScreen"); self.valid_filepath = None
        layout_principal = QVBoxLayout(self); layout_principal.setContentsMargins(30, 30, 30, 30); layout_principal.setSpacing(15)
        self.caminho_arquivo_label = QLabel("Nenhum arquivo de roteiro selecionado."); self.caminho_arquivo_label.setFont(QFont("Segoe UI", 10)); self.caminho_arquivo_label.setWordWrap(True); self.caminho_arquivo_label.setObjectName("InfoLabel"); self.caminho_arquivo_label.setAlignment(Qt.AlignCenter)
        self.botao_carregar = QPushButton("Upload and Validate File"); self.botao_carregar.clicked.connect(self.abrir_e_validar_arquivo); self.botao_carregar.setCursor(Qt.PointingHandCursor)
        self.botao_proximo = QPushButton("Start Process"); self.botao_proximo.setEnabled(False); self.botao_proximo.setObjectName("BotaoProximo"); self.botao_proximo.setCursor(Qt.ArrowCursor)
        self.botao_proximo.clicked.connect(self.iniciar_processamento)
        botoes_acao_layout = QHBoxLayout(); botoes_acao_layout.addWidget(self.botao_carregar); botoes_acao_layout.addWidget(self.botao_proximo)
        self.botao_voltar = QPushButton("Back"); self.botao_voltar.clicked.connect(self.back_requested.emit); self.botao_voltar.setCursor(Qt.PointingHandCursor)
        layout_principal.addStretch(); layout_principal.addWidget(self.caminho_arquivo_label); layout_principal.addLayout(botoes_acao_layout); layout_principal.addStretch(); layout_principal.addWidget(self.botao_voltar)

    def abrir_e_validar_arquivo(self):
        self.botao_proximo.setEnabled(False); self.botao_proximo.setCursor(Qt.ArrowCursor); self.valid_filepath = None
        caminho_arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar um arquivo .txt", "", "Arquivos de Texto (*.txt)")
        if caminho_arquivo:
            self.caminho_arquivo_label.setText(f"analyzing file:\n{caminho_arquivo}")
            try:
                with open(caminho_arquivo, 'r', encoding='utf-8') as f: conteudo = f.read()
                sucesso, mensagem = validar_formato_iceberg(conteudo)
                if sucesso:
                    # --- INÍCIO DA NOVA LÓGICA ---
                    try:
                        # 1. Garante que o diretório de destino exista
                        os.makedirs(DESTINATION_DIR, exist_ok=True)
                        
                        # 2. Define o caminho completo do arquivo de destino
                        caminho_destino = os.path.join(DESTINATION_DIR, "roteiro.txt")
                        
                        # 3. Copia o arquivo selecionado para o destino, substituindo se existir
                        shutil.copy(caminho_arquivo, caminho_destino)
                        
                        # 4. Informa o usuário sobre o sucesso da validação e da cópia
                        mensagem_completa = f"{mensagem}\nE o arquivo foi salvo como 'roteiro.txt'."
                        QMessageBox.information(self, "Sucesso", mensagem_completa)
                        
                        # 5. Habilita o botão para o próximo passo
                        self.botao_proximo.setEnabled(True); self.botao_proximo.setCursor(Qt.PointingHandCursor); self.valid_filepath = caminho_destino

                    except Exception as copy_error:
                        QMessageBox.critical(self, "Erro ao Copiar Arquivo", f"Não foi possível copiar o roteiro para o destino.\n\nErro: {copy_error}")
                    # --- FIM DA NOVA LÓGICA ---
                else: 
                    QMessageBox.warning(self, "Erro de Formato", mensagem)
            except Exception as e: 
                QMessageBox.critical(self, "Erro de Leitura", f"Não foi possível ler o arquivo:\n{e}")

    def iniciar_processamento(self):
        if self.valid_filepath:
            tema_do_video = "imagens sobre "; progress_dialog = ProgressWindow(self); progress_dialog.start_processing(self.valid_filepath, tema_do_video)

# =============================================================================
# JANELA PRINCIPAL E EXECUÇÃO
# =============================================================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoVid Creator")
        self.resize(900, 650) # Aumentei um pouco para acomodar os templates
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Inicializa as telas
        self.home_screen = HomeScreen()
        self.template_screen = TemplateSelectionScreen() # Nova tela instanciada
        self.file_loader_screen = FileLoaderScreen()
        
        # Adiciona ao StackedWidget (a ordem importa para o índice, mas usaremos referências)
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.template_screen)
        self.stacked_widget.addWidget(self.file_loader_screen)
        
        # --- CONEXÃO DE SINAIS (FLUXO DE NAVEGAÇÃO) ---
        
        # 1. Home -> Templates
        self.home_screen.start_requested.connect(self.mostrar_tela_templates)
        
        # 2. Templates -> Home (Voltar)
        self.template_screen.back_requested.connect(self.mostrar_tela_inicial)
        
        # 3. Templates -> File Loader (Ao selecionar um layout)
        self.template_screen.template_selected.connect(self.mostrar_tela_carregador)
        
        # 4. File Loader -> Templates (Voltar) - Mudado para voltar para templates em vez de home
        self.file_loader_screen.back_requested.connect(self.mostrar_tela_templates)
        
    def mostrar_tela_inicial(self):
        self.stacked_widget.setCurrentWidget(self.home_screen)
        
    def mostrar_tela_templates(self):
        self.stacked_widget.setCurrentWidget(self.template_screen)

    def mostrar_tela_carregador(self, template_escolhido):
        # Aqui você pode salvar qual template foi escolhido se precisar usar depois
        print(f"Template escolhido: {template_escolhido}")
        self.stacked_widget.setCurrentWidget(self.file_loader_screen)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QSS = f"""
        QMainWindow, QWidget {{ background-color: {COR_FUNDO_PRINCIPAL}; color: {COR_TEXTO_PRINCIPAL}; font-family: Segoe UI; }}
        #HomeScreen, #FileLoaderScreen, #TemplateSelectionScreen, QDialog {{ background-color: {COR_FUNDO_CONTAINER}; }}
        
        QPushButton {{ background-color: {COR_BOTAO_BASE}; color: {COR_TEXTO_PRINCIPAL}; font-size: 14px; font-weight: bold; padding: 12px 24px; border: 1px solid {COR_HOVER}; border-radius: 8px; }}
        QPushButton:hover {{ background-color: {COR_HOVER}; border: 1px solid {COR_DESTAQUE}; }}
        QPushButton:disabled {{ background-color: {COR_BOTAO_DESABILITADO}; color: {COR_TEXTO_DESABILITADO}; border: 1px solid {COR_BOTAO_DESABILITADO}; }}
        
        /* ESTILO PARA OS RETÂNGULOS COMPRIDOS (TEMPLATES) */
        #TemplateCard {{
            background-color: {COR_FUNDO_CARD};
            border: 2px solid {COR_HOVER};
            border-radius: 15px;
            font-size: 18px;
            min-width: 200px;  /* Largura do cartão */
            min-height: 350px; /* Altura do cartão (comprido) */
            margin: 10px;
        }}
        #TemplateCard:hover {{
            background-color: {COR_HOVER};
            border: 2px solid {COR_DESTAQUE};
            /* Removida a linha 'transform' que causava erro no terminal */
        }}

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
        
        QProgressBar {{ border: 2px solid {COR_BOTAO_BASE}; border-radius: 5px; background-color: {COR_PROGRESSBAR_FUNDO}; text-align: center; color: {COR_TEXTO_PRINCIPAL}; }}
        QProgressBar::chunk {{ background-color: {COR_PROGRESSBAR_CHUNK}; border-radius: 3px; margin: 1px; }}
    """
    app.setStyleSheet(QSS)
    janela = MainWindow()
    janela.show()
    sys.exit(app.exec())