""""Main module."""

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget
)

from automated_video_generator.gui.file_loader_screen import FileLoaderScreen
from automated_video_generator.gui.home_screen import HomeScreen
# Removido: import da TemplateSelectionScreen
from automated_video_generator.config import BASE_DIR
from automated_video_generator.utils.clear_directories import clear_directories


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Limpeza de diretórios (mantida igual)
        pasta_de_arquivos = BASE_DIR / "data" / "topics_video"
        clear_directories(pasta_de_arquivos)

        pasta_de_midias = BASE_DIR / "assets" / "topics_video"
        clear_directories(pasta_de_midias)

        self.setWindowTitle("AutoVid Creator")
        self.resize(900, 650)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Instancia apenas a Home e o Loader
        self.home_screen = HomeScreen()
        self.file_loader_screen = FileLoaderScreen()

        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.file_loader_screen)

        # --- CONEXÕES ATUALIZADAS ---

        # 1. A Home agora chama uma função que define o template padrão e vai para o loader
        self.home_screen.start_requested.connect(self.iniciar_carregador)

        # 2. O botão voltar do Loader agora vai direto para a Home
        self.file_loader_screen.back_requested.connect(self.mostrar_tela_inicial)

    def mostrar_tela_inicial(self):
        self.stacked_widget.setCurrentWidget(self.home_screen)

    def iniciar_carregador(self):
        """
        Função intermediária para definir o tipo de vídeo padrão,
        já que a tela de seleção foi removida.
        """
        template_padrao = "topicos"
        self.mostrar_tela_carregador(template_padrao)

    def mostrar_tela_carregador(self, template_escolhido):
        print(f"Template definido automaticamente: {template_escolhido}")

        self.file_loader_screen.set_template(template_escolhido)
        self.stacked_widget.setCurrentWidget(self.file_loader_screen)
