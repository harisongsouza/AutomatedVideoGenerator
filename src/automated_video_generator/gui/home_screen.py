
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel
)
from PySide6.QtGui import QFont

class HomeScreen(QWidget):
    start_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HomeScreen")
        layout = QVBoxLayout(self)
        layout.setSpacing(20);
        layout.setAlignment(Qt.AlignCenter)
        titulo_label = QLabel("AutoVid Creator");
        titulo_label.setFont(QFont("Segoe UI", 36, QFont.Bold));
        titulo_label.setAlignment(Qt.AlignCenter);
        titulo_label.setObjectName("TituloLabel")
        subtitulo_label = QLabel("Create videos automatically from a script.");
        subtitulo_label.setFont(QFont("Segoe UI", 12));
        subtitulo_label.setAlignment(Qt.AlignCenter);
        subtitulo_label.setObjectName("SubtituloLabel")
        botao_iniciar = QPushButton("Start New Project");
        botao_iniciar.clicked.connect(self.start_requested.emit);
        botao_iniciar.setObjectName("BotaoDestaque");
        botao_iniciar.setCursor(Qt.PointingHandCursor)
        layout.addStretch();
        layout.addWidget(titulo_label);
        layout.addWidget(subtitulo_label);
        layout.addSpacing(30);
        layout.addWidget(botao_iniciar);
        layout.addStretch()
