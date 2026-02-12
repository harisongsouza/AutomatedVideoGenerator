import os
import shutil
from pathlib import Path
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
    QLabel, QMessageBox, QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent

# --- IMPORTS DE SERVIÇO ---
from automated_video_generator.service.validate_files import validar_arquivos_formato_camadas
from automated_video_generator.service.validate_files import validar_arquivos_formato_topicos
from automated_video_generator.gui.progress_window import ProgressWindow

from automated_video_generator.config import BASE_DIR
# =================================================================
# CONFIGURAÇÃO DE DESTINOS - ALTERE AQUI PARA ONDE OS ARQUIVOS VÃO
# =================================================================

print(f"DIRETÓRIO BASE DETECTADO: {BASE_DIR}") # <--- ADICIONE ISSO PARA CONFERIR

FILE_CONFIG = {
    "roteiro": {
        "path": BASE_DIR / "data" / "topics_video",
        "save_name": "roteiro.txt"
    },
    "music": {
        "path": BASE_DIR / "assets" / "topics_video" / "audio",
        "save_name": "background_music"  # A extensão (.mp3) é adicionada automaticamente
    },
    "transition": {
        "path": BASE_DIR / "assets" / "topics_video" / "videos",
        "save_name": "possiveis_intro"  # A extensão (.gif) é adicionada automaticamente
        #"save_name": "transition_video"
},
    "intro": {
        "path": BASE_DIR / "assets" / "topics_video" / "videos" / "camadas",
        "save_name": "video_original_intro_encerramento"  # A extensão (.mp4) é adicionada automaticamente
    }
}
# =================================================================

STYLESHEET = """
    /* Aplica o fundo APENAS na tela principal e não nos filhos */
    QWidget#FileLoaderScreen {
        background-color: #1e1e1e;
    }

    /* Remove bordas e fundos de todos os textos e ícones */
    QLabel {
        background-color: transparent;
        border: none;
        color: #ffffff;
        font-family: 'Segoe UI', sans-serif;
    }

    /* --- CARDS DE ARQUIVO --- */
    QFrame#FileCard {
        background-color: #2d2d2d;
        border: 2px dashed #555555;
        border-radius: 12px;
    }
    QFrame#FileCard:hover {
        background-color: #353535;
        border-color: #0078D4;
    }
    QFrame#FileCard[status="success"] {
        border: 2px solid #4CAF50;
        background-color: #253326;
    }

    QLabel#CardTitle {
        font-weight: bold;
        font-size: 15px;
    }

    QLabel#FormatLabel {
        color: #0078D4;
        font-size: 11px;
        font-weight: bold;
        background-color: #1a2633; /* Fundo discreto apenas na etiqueta de formato */
        padding: 2px 8px;
        border-radius: 4px;
    }

    QLabel#CardInfo {
        color: #888888;
        font-size: 11px;
    }

    QLabel#IconLabel {
        font-size: 36px;
    }

/* --- BADGE DE PROGRESSO (ESTILIZAÇÃO BLINDADA) --- */
    QLabel#ProgressBadge {
        background-color: #333333; /* Fundo cinza escuro proposital */
        color: #aaaaaa;
        border-radius: 15px; /* Arredondado */
        border: 1px solid #444444; /* Borda sólida para evitar que o Windows crie a dele */
        font-weight: bold;
        font-size: 13px;
        padding: 2px; /* Garante que o texto não encoste na borda */
        outline: none;
    }

    /* Estado quando está tudo pronto */
    QLabel#ProgressBadge[complete="true"] {
        background-color: transparent;
        color: #4CAF50;
        border: 2px solid #4CAF50; /* Borda verde sólida */
    }

    /* --- BOTÕES --- */
    QPushButton {
        font-family: 'Segoe UI', sans-serif;
    }

/* --- BOTÃO VOLTAR --- */
    QPushButton#BackButton:hover {
        background-color: #333333;
        color: #ffffff;
        border-color: #888888;
    }
    QPushButton#BackButton:pressed {
        background-color: #444444;
    }

    /* --- BOTÃO INICIAR (Só reage se estiver "Ready") --- */
    QPushButton#ActionButton[ready="true"]:hover {
        background-color: #45a049; /* Verde levemente mais escuro */
        border: 1px solid #ffffff; /* Borda branca fina para destaque */
    }
    QPushButton#ActionButton[ready="true"]:pressed {
        background-color: #3d8b40; /* Verde ainda mais escuro para o clique */
    }

    /* Remove qualquer borda do container de botões */
    QWidget#FooterWidget {
        background-color: transparent;
        border: none;
    }
"""


class FileCard(QFrame):
    file_validated = Signal(bool, str)

    def __init__(self, title, allowed_extensions, format_text, file_type_id, parent=None):
        super().__init__(parent)
        self.setObjectName("FileCard")
        self.setProperty("status", "pending")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(170)
        self.title, self.allowed_extensions, self.file_type_id = title, allowed_extensions, file_type_id
        self.file_path = None

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.icon_label = QLabel("📁")
        self.icon_label.setObjectName("IconLabel")
        self.icon_label.setAttribute(Qt.WA_TranslucentBackground)
        self.title_label = QLabel(title)
        self.title_label.setObjectName("CardTitle")
        self.title_label.setAttribute(Qt.WA_TranslucentBackground)
        self.format_label = QLabel(f"FORMATO: {format_text}")
        self.format_label.setObjectName("FormatLabel")
        self.format_label.setAttribute(Qt.WA_TranslucentBackground)
        self.info_label = QLabel("Clique ou arraste o arquivo")
        self.info_label.setObjectName("CardInfo")
        self.info_label.setAttribute(Qt.WA_TranslucentBackground)


        for w in [self.icon_label, self.title_label, self.format_label, self.info_label]:
            w.setAlignment(Qt.AlignCenter)
            layout.addWidget(w)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: self.open_file_dialog()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files: self.process_file(files[0])

    def open_file_dialog(self):
        filtro = f"Arquivos ({self.allowed_extensions})"
        caminho, _ = QFileDialog.getOpenFileName(self, f"Selecionar {self.title}", "", filtro)
        if caminho: self.process_file(caminho)

    def process_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        allowed = [e.replace("*", "").lower() for e in self.allowed_extensions.split()]
        if any(a in ext for a in allowed):
            self.file_path = file_path
            self.file_validated.emit(True, self.file_type_id)
        else:
            QMessageBox.warning(self, "Formato Inválido", f"Aceito apenas: {self.allowed_extensions}")

    def set_success_state(self, filename):
        self.setProperty("status", "success")
        self.style().unpolish(self);
        self.style().polish(self)
        self.icon_label.setText("✅")
        self.info_label.setText(filename)
        self.info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        self.format_label.hide()

    def reset_state(self, msg="Arquivo inválido"):
        self.setProperty("status", "pending")
        self.style().unpolish(self);
        self.style().polish(self)
        self.icon_label.setText("📁");
        self.info_label.setText(msg)
        self.info_label.setStyleSheet("color: #FF5555;");
        self.format_label.show()


class FileLoaderScreen(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.template_escolhido = None
        self.files_status = {"roteiro": None, "music": None, "transition": None, "intro": None}
        self.setup_ui()
        self.setStyleSheet(STYLESHEET)
        self.update_progress_indicator()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # --- Top Bar ---
        top_bar = QHBoxLayout()
        header_layout = QVBoxLayout()
        header = QLabel("Configuração do Projeto")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header_layout.addWidget(header)
        header_layout.addWidget(QLabel("Selecione os recursos obrigatórios."))
        top_bar.addLayout(header_layout)
        top_bar.addStretch()

        self.progress_badge = QLabel("0/4");
        self.progress_badge.setObjectName("ProgressBadge")
        self.progress_badge.setFixedSize(120, 40);
        self.progress_badge.setAlignment(Qt.AlignCenter)
        top_bar.addWidget(self.progress_badge)
        main_layout.addLayout(top_bar)

        # --- Grid de Cards ---
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)

        self.card_roteiro = FileCard("1. Roteiro", "*.txt", ".TXT", "roteiro")
        self.card_music = FileCard("2. Música de Fundo", "*.mp3", ".MP3", "music")
        self.card_transition = FileCard("3. Transição", "*.gif", ".GIF", "transition")
        self.card_intro = FileCard("4. Intro/Vídeo", "*.mp4 *.avi *.mov", ".MP4 / .AVI", "intro")

        # Conectar sinais
        self.card_roteiro.file_validated.connect(self.handle_roteiro_validation)
        self.card_music.file_validated.connect(self.generic_file_handler)
        self.card_transition.file_validated.connect(self.generic_file_handler)
        self.card_intro.file_validated.connect(self.generic_file_handler)

        self.grid_layout.addWidget(self.card_roteiro, 0, 0)
        self.grid_layout.addWidget(self.card_music, 0, 1)
        self.grid_layout.addWidget(self.card_transition, 1, 0)
        self.grid_layout.addWidget(self.card_intro, 1, 1)

        # Adiciona o grid ao layout principal (UMA ÚNICA VEZ)
        main_layout.addLayout(self.grid_layout)

        # Espaçador para empurrar os botões para o rodapé
        main_layout.addStretch()

        # --- Footer (Botões) ---
        self.footer_widget = QWidget()
        self.footer_widget.setObjectName("FooterWidget")  # Nomeamos para o CSS
        footer_layout = QHBoxLayout(self.footer_widget)
        footer_layout.setContentsMargins(0, 10, 0, 0)

        self.btn_back = QPushButton("Voltar")
        self.btn_back.setObjectName("BackButton")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.clicked.connect(self.back_requested.emit)

        self.btn_start = QPushButton("Aguardando...")
        self.btn_start.setObjectName("ActionButton")
        self.btn_start.setMinimumWidth(280)
        self.btn_start.clicked.connect(self.iniciar_processamento)

        footer_layout.addWidget(self.btn_back)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_start)

        # Adicionamos o widget de rodapé
        main_layout.addWidget(self.footer_widget)

    def update_progress_indicator(self):
        total = 4
        current = sum(1 for v in self.files_status.values() if v is not None)
        all_loaded = (current == total)

        # --- Ajuste do Badge ---
        self.progress_badge.setText("PRONTO" if all_loaded else f"{current}/{total}")
        self.progress_badge.setProperty("complete", all_loaded)
        self.progress_badge.style().unpolish(self.progress_badge)
        self.progress_badge.style().polish(self.progress_badge)

        # --- AJUSTE DOS BOTÕES (Onde estava o problema) ---
        self.btn_start.setEnabled(all_loaded)
        self.btn_start.setProperty("ready", all_loaded)

        if all_loaded:
            self.btn_start.setText("GERAR VÍDEO")
            self.btn_start.setCursor(Qt.PointingHandCursor)  # Força o cursor aqui
        else:
            self.btn_start.setText(f"Faltam {total - current} arquivos...")
            self.btn_start.setCursor(Qt.ForbiddenCursor)  # Cursor de "não pode" enquanto falta arquivo

        # Garante que o Voltar sempre tenha a mãozinha
        self.btn_back.setCursor(Qt.PointingHandCursor)

        # Atualiza o CSS para refletir as mudanças visuais
        self.btn_start.style().unpolish(self.btn_start)
        self.btn_start.style().polish(self.btn_start)

    def handle_roteiro_validation(self, valid, type_id):
        filepath = self.card_roteiro.file_path
        if not valid or not filepath: return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                conteudo = f.read()

            # Validação
            validador = validar_arquivos_formato_camadas if self.template_escolhido == "camadas" else validar_arquivos_formato_topicos
            sucesso, mensagem = validador(conteudo)

            if sucesso:
                dest_info = FILE_CONFIG["roteiro"]

                # Conversão explícita para string para evitar erros de biblioteca
                dest_dir = str(dest_info["path"])
                os.makedirs(dest_dir, exist_ok=True)

                final_path = dest_info["path"] / dest_info["save_name"]

                # Copia convertendo tudo para string
                shutil.copy2(str(filepath), str(final_path))

                print(f"Roteiro salvo em: {final_path}")  # Debug

                self.files_status["roteiro"] = str(final_path)
                self.card_roteiro.set_success_state(os.path.basename(filepath))
            else:
                QMessageBox.warning(self, "Erro de Formato", mensagem)
                self.card_roteiro.reset_state("Conteúdo Inválido")
        except Exception as e:
            import traceback
            traceback.print_exc()  # Mostra o erro real no console
            self.card_roteiro.reset_state(f"Erro: {e}")
        self.update_progress_indicator()

    def generic_file_handler(self, valid, type_id):
        card = {"music": self.card_music, "transition": self.card_transition, "intro": self.card_intro}.get(type_id)
        if valid and card:
            self.files_status[type_id] = card.file_path
            card.set_success_state(os.path.basename(card.file_path))
        else:
            self.files_status[type_id] = None
        self.update_progress_indicator()

    def iniciar_processamento(self):
        try:
            print("--- Iniciando cópia dos arquivos multimídia ---")
            # Copia arquivos multimídia baseados na configuração
            for key in ["music", "transition", "intro"]:
                src = self.files_status[key]

                # Verifica se existe um arquivo de origem selecionado e se ele realmente existe no disco
                if src and os.path.exists(src):
                    conf = FILE_CONFIG[key]

                    # Garante criação da pasta de destino
                    dest_dir = conf["path"]
                    os.makedirs(str(dest_dir), exist_ok=True)

                    # Define extensão e nome final
                    ext = os.path.splitext(src)[1]
                    final_filename = f"{conf['save_name']}{ext}"
                    dest_file_path = dest_dir / final_filename

                    # Copia com segurança (str) e metadata (copy2)
                    shutil.copy2(str(src), str(dest_file_path))
                    print(f"Arquivo [{key}] copiado de '{src}' para '{dest_file_path}'")
                else:
                    print(f"Pulei [{key}]: Fonte inválida ou não selecionada.")

            # Inicia Janela de Progresso
            print("--- Iniciando Processamento de Vídeo ---")
            progress_dialog = ProgressWindow(self)

            # Verifica se o roteiro foi salvo corretamente antes de passar
            path_roteiro = self.files_status["roteiro"]
            if not path_roteiro or not os.path.exists(path_roteiro):
                raise FileNotFoundError(f"O arquivo de roteiro não foi encontrado em: {path_roteiro}")

            if self.template_escolhido == "camadas":
                progress_dialog.start_layer_video_processing(path_roteiro, "", self.template_escolhido)
            else:
                progress_dialog.start_topics_video_processing(path_roteiro, "", self.template_escolhido)

        except Exception as e:
            import traceback
            traceback.print_exc()  # Isso vai imprimir o erro exato no seu terminal
            QMessageBox.critical(self, "Erro Fatal", f"Erro no processamento:\n{str(e)}")

    def set_template(self, tid):
        self.template_escolhido = tid


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    w = FileLoaderScreen();
    w.set_template("topicos");
    w.resize(900, 700);
    w.show()
    sys.exit(app.exec())
