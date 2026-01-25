
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
    QDialog
)
from PySide6.QtGui import QFont

class TemplateSelectionScreen(QWidget):
    template_selected = Signal(str)
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TemplateSelectionScreen")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)

        lbl_titulo = QLabel("Select the Video Type")
        lbl_titulo.setFont(QFont("Segoe UI", 24, QFont.Bold))
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setObjectName("TituloLabel")

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(30)

        self.btn_template1 = QPushButton("Create a video in layers")
        self.btn_template1.setObjectName("TemplateCard")
        self.btn_template1.setCursor(Qt.PointingHandCursor)
        self.btn_template1.clicked.connect(lambda: self.template_selected.emit("camadas_1"))

        self.btn_template2 = QPushButton("Create a video in topics")
        self.btn_template2.setObjectName("TemplateCard")
        self.btn_template2.setCursor(Qt.PointingHandCursor)
        self.btn_template2.clicked.connect(lambda: self.template_selected.emit("camadas_2"))

        cards_layout.addStretch()
        cards_layout.addWidget(self.btn_template1)
        cards_layout.addWidget(self.btn_template2)
        cards_layout.addStretch()

        self.botao_voltar = QPushButton("Back")
        self.botao_voltar.setCursor(Qt.PointingHandCursor)
        self.botao_voltar.clicked.connect(self.back_requested.emit)

        main_layout.addWidget(lbl_titulo)
        main_layout.addSpacing(20)
        main_layout.addLayout(cards_layout)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.botao_voltar, alignment=Qt.AlignCenter)
