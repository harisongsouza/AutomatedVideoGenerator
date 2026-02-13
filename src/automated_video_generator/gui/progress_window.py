import os
from PySide6.QtCore import Qt, QThread, QSize
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QDialog,
    QSizePolicy,
    QApplication
)

# Assumindo que sua classe Worker está importada corretamente
from automated_video_generator.workers.video_worker import Worker
from automated_video_generator.config import BASE_DIR

class ProgressWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Processando Vídeo")
        self.setModal(True)

        # 1. Tamanho "Normal" (Maior)
        self.resize(600, 400)
        self.setMinimumSize(500, 350)  # Impede que fique muito pequena

        # Remove o botão de ajuda (?) da janela, mantendo fechar/minimizar
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Layout Principal
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        # 2. Área do GIF
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Configuração do GIF (QMovie)
        # DICA: Coloque um arquivo 'loading.gif' na pasta do seu projeto
        gif_path = str(BASE_DIR / "utils" / "nyan-cat.gif")

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.movie.setScaledSize(QSize(120, 120))  # Tamanho do GIF na tela
            self.gif_label.setMovie(self.movie)
            self.movie.start()
        else:
            self.gif_label.setText("[GIF não encontrado: adicione 'loading.gif']")
            self.gif_label.setStyleSheet("color: gray; font-style: italic;")

        layout.addWidget(self.gif_label)

        # Texto de Status (Fonte maior)
        self.statusLabel = QLabel("Aguardando início...")
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.statusLabel.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        layout.addWidget(self.statusLabel)

        # Barra de Progresso Estilizada
        self.progressBar = QProgressBar()
        self.progressBar.setTextVisible(True)
        self.progressBar.setRange(0, 100)
        self.progressBar.setFixedHeight(25)
        # Estilo CSS para deixar a barra moderna
        self.progressBar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 5px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 10px;
                margin: 0.5px;
            }
        """)
        layout.addWidget(self.progressBar)

    # 3. Método unificado para evitar repetição de código
    def _start_worker(self, filepath, tema, template_escolhido):
        self.statusLabel.setText("Iniciando processamento...")

        self.thread = QThread()
        self.worker = Worker(filepath, tema, template_escolhido)

        self.worker.moveToThread(self.thread)

        # Conexões
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.progress.connect(self.update_progress)

        # Limpeza
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

        # Executa a janela como Modal (bloqueia a janela de trás)
        self.exec()

    # Mantive seus nomes de métodos originais para compatibilidade
    def start_layer_video_processing(self, filepath, tema, template_escolhido):
        self._start_worker(filepath, tema, template_escolhido)

    def start_topics_video_processing(self, filepath, tema, template_escolhido):
        self._start_worker(filepath, tema, template_escolhido)

    def update_progress(self, value, message):
        self.progressBar.setValue(value)
        self.statusLabel.setText(message)

    def on_finished(self):
        # 1. Para o GIF e atualiza a interface
        if hasattr(self, 'movie'):
            self.movie.stop()

        self.statusLabel.setText("Processo concluído com sucesso!")
        self.progressBar.setValue(100)

        # 2. Abre o alerta. O Python vai PARAR aqui e esperar o clique no OK.
        QMessageBox.information(
            self,
            "Sucesso",
            "O vídeo foi gerado com sucesso!"
        )

        # 3. Esta linha SÓ EXECUTA quando o usuário clica no OK da mensagem acima.
        # Ela encerra todas as janelas e o loop do sistema.
        QApplication.instance().quit()

        # Opcional: Se quiser garantir que o processo do Windows/Linux morra na hora:
        # sys.exit()

    def on_error(self, title, message):
        # Para o GIF em caso de erro
        if hasattr(self, 'movie'):
            self.movie.stop()

        QMessageBox.critical(self, title, message)
        self.reject()
