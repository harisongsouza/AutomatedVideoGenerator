"""Console script for automated_video_generator."""

import sys
import os
from PySide6.QtWidgets import (
    QApplication
)

from automated_video_generator.gui.main_window import MainWindow

DESTINATION_DIR = os.path.join("C:/Users/souza/Downloads/VideoCreator/", "data/")

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


def main():
    app = QApplication(sys.argv)
    QSS = f"""
        QMainWindow, QWidget {{ background-color: {COR_FUNDO_PRINCIPAL}; color: {COR_TEXTO_PRINCIPAL}; font-family: Segoe UI; }}
        #HomeScreen, #FileLoaderScreen, #TemplateSelectionScreen, QDialog {{ background-color: {COR_FUNDO_CONTAINER}; }}

        QPushButton {{ background-color: {COR_BOTAO_BASE}; color: {COR_TEXTO_PRINCIPAL}; font-size: 14px; font-weight: bold; padding: 12px 24px; border: 1px solid {COR_HOVER}; border-radius: 8px; }}
        QPushButton:hover {{ background-color: {COR_HOVER}; border: 1px solid {COR_DESTAQUE}; }}
        QPushButton:disabled {{ background-color: {COR_BOTAO_DESABILITADO}; color: {COR_TEXTO_DESABILITADO}; border: 1px solid {COR_BOTAO_DESABILITADO}; }}

        #TemplateCard {{
            background-color: {COR_FUNDO_CARD};
            border: 2px solid {COR_HOVER};
            border-radius: 15px;
            font-size: 18px;
            min-width: 200px;
            min-height: 350px;
            margin: 10px;
        }}
        #TemplateCard:hover {{
            background-color: {COR_HOVER};
            border: 2px solid {COR_DESTAQUE};
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



if __name__ == "__main__":
    main()
