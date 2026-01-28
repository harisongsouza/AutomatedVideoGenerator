"""Main module."""

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget
)

from automated_video_generator.gui.file_loader_screen import FileLoaderScreen
from automated_video_generator.gui.home_screen import HomeScreen
from automated_video_generator.gui.template_selection_screen import TemplateSelectionScreen

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

        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.template_screen)
        self.stacked_widget.addWidget(self.file_loader_screen)

        self.home_screen.start_requested.connect(self.mostrar_tela_templates)

        self.template_screen.back_requested.connect(self.mostrar_tela_inicial)

        self.template_screen.template_selected.connect(self.mostrar_tela_carregador)

        self.file_loader_screen.back_requested.connect(self.mostrar_tela_templates)

    def mostrar_tela_inicial(self):
        self.stacked_widget.setCurrentWidget(self.home_screen)

    def mostrar_tela_templates(self):
        self.stacked_widget.setCurrentWidget(self.template_screen)

    def mostrar_tela_carregador(self, template_escolhido):
        print(f"Template escolhido: {template_escolhido}")

        self.file_loader_screen.set_template(template_escolhido)

        self.stacked_widget.setCurrentWidget(self.file_loader_screen)
