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
    QDialog
)
from PySide6.QtGui import QFont


class ProgressWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processando Vídeo");
        self.setModal(True);
        self.resize(450, 150);
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.progressBar = QProgressBar();
        self.progressBar.setTextVisible(True);
        self.progressBar.setRange(0, 100)
        self.statusLabel = QLabel("Iniciando processamento...");
        self.statusLabel.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self);
        layout.addWidget(self.statusLabel);
        layout.addWidget(self.progressBar)

    def start_processing(self, filepath, tema):
        self.thread = QThread();
        self.worker = Worker(filepath, tema);
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run);
        self.worker.finished.connect(self.on_finished);
        self.worker.error.connect(self.on_error);
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.thread.quit);
        self.worker.finished.connect(self.worker.deleteLater);
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        self.exec()

    def update_progress(self, value, message): self.progressBar.setValue(value);  self.statusLabel.setText(message)

    def on_finished(self): self.statusLabel.setText("Processo concluído com sucesso!");  self.progressBar.setValue(
        100);  QMessageBox.information(self, "Sucesso", "O vídeo foi gerado com sucesso!");  self.accept()

    def on_error(self, title, message): QMessageBox.critical(self, title, message);  self.reject()
