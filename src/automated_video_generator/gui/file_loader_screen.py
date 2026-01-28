import re
import os
import shutil
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFileDialog,
    QLabel,
    QMessageBox
)
from PySide6.QtGui import QFont

from automated_video_generator.gui.progress_window import ProgressWindow

DESTINATION_DIR = os.path.join("C:/Users/souza/Downloads/VideoCreator/", "data/")


class FileLoaderScreen(QWidget):
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent);
        self.template_escolhido = None
        self.setObjectName("FileLoaderScreen");
        self.valid_filepath = None
        layout_principal = QVBoxLayout(self);
        layout_principal.setContentsMargins(30, 30, 30, 30);
        layout_principal.setSpacing(15)
        self.caminho_arquivo_label = QLabel("Nenhum arquivo de roteiro selecionado.");
        self.caminho_arquivo_label.setFont(QFont("Segoe UI", 10));
        self.caminho_arquivo_label.setWordWrap(True);
        self.caminho_arquivo_label.setObjectName("InfoLabel");
        self.caminho_arquivo_label.setAlignment(Qt.AlignCenter)
        self.botao_carregar = QPushButton("Upload and Validate File");
        self.botao_carregar.clicked.connect(self.abrir_e_validar_arquivo);
        self.botao_carregar.setCursor(Qt.PointingHandCursor)
        self.botao_proximo = QPushButton("Start Process");
        self.botao_proximo.setEnabled(False);
        self.botao_proximo.setObjectName("BotaoProximo");
        self.botao_proximo.setCursor(Qt.ArrowCursor)
        self.botao_proximo.clicked.connect(self.iniciar_processamento)
        botoes_acao_layout = QHBoxLayout();
        botoes_acao_layout.addWidget(self.botao_carregar);
        botoes_acao_layout.addWidget(self.botao_proximo)
        self.botao_voltar = QPushButton("Back");
        self.botao_voltar.clicked.connect(self.back_requested.emit);
        self.botao_voltar.setCursor(Qt.PointingHandCursor)
        layout_principal.addStretch();
        layout_principal.addWidget(self.caminho_arquivo_label);
        layout_principal.addLayout(botoes_acao_layout);
        layout_principal.addStretch();
        layout_principal.addWidget(self.botao_voltar)

    def set_template(self, template_id):
        self.template_escolhido = template_id

    def abrir_e_validar_arquivo(self):
        if self.template_escolhido == "camadas":
            print(f"Template escolhido: CAMADAS")
            self.botao_proximo.setEnabled(False);
            self.botao_proximo.setCursor(Qt.ArrowCursor);
            self.valid_filepath = None
            caminho_arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar um arquivo .txt", "",
                                                             "Arquivos de Texto (*.txt)")
            if caminho_arquivo:
                self.caminho_arquivo_label.setText(f"analyzing file:\n{caminho_arquivo}")
                try:
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()
                    sucesso, mensagem = validar_arquivos_formato_camadas(conteudo)
                    if sucesso:

                        try:
                            os.makedirs(DESTINATION_DIR, exist_ok=True)

                            caminho_destino = os.path.join(DESTINATION_DIR, "roteiro.txt")

                            shutil.copy(caminho_arquivo, caminho_destino)

                            mensagem_completa = f"{mensagem}\nE o arquivo foi salvo como 'roteiro.txt'."
                            QMessageBox.information(self, "Sucesso", mensagem_completa)

                            self.botao_proximo.setEnabled(True);
                            self.botao_proximo.setCursor(Qt.PointingHandCursor);
                            self.valid_filepath = caminho_destino

                        except Exception as copy_error:
                            QMessageBox.critical(self, "Erro ao Copiar Arquivo",
                                                 f"Não foi possível copiar o roteiro para o destino.\n\nErro: {copy_error}")

                    else:
                        QMessageBox.warning(self, "Erro de Formato", mensagem)
                except Exception as e:
                    QMessageBox.critical(self, "Erro de Leitura", f"Não foi possível ler o arquivo:\n{e}")
        elif self.template_escolhido == "topicos":
            print(f"Template escolhido: TOPICOS")
            self.botao_proximo.setEnabled(False)
            self.botao_proximo.setCursor(Qt.ArrowCursor)
            self.valid_filepath = None

            # 1. Abre o seletor de arquivos
            caminho_arquivo, _ = QFileDialog.getOpenFileName(self, "Selecionar um arquivo .txt (Tópicos)", "",
                                                             "Arquivos de Texto (*.txt)")

            if caminho_arquivo:
                self.caminho_arquivo_label.setText(f"analyzing file:\n{caminho_arquivo}")
                try:
                    # 2. Lê o arquivo
                    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                        conteudo = f.read()

                    # 3. Chama a NOVA função de validação criada acima
                    sucesso, mensagem = validar_arquivos_formato_topicos(conteudo)

                    if sucesso:
                        try:
                            # 4. Salva o arquivo validado
                            os.makedirs(DESTINATION_DIR, exist_ok=True)
                            caminho_destino = os.path.join(DESTINATION_DIR, "roteiro.txt")

                            shutil.copy(caminho_arquivo, caminho_destino)

                            mensagem_completa = f"{mensagem}\nE o arquivo foi salvo como 'roteiro.txt'."
                            QMessageBox.information(self, "Sucesso", mensagem_completa)

                            self.botao_proximo.setEnabled(True)
                            self.botao_proximo.setCursor(Qt.PointingHandCursor)
                            self.valid_filepath = caminho_destino

                        except Exception as copy_error:
                            QMessageBox.critical(self, "Erro ao Copiar Arquivo",
                                                 f"Não foi possível copiar o roteiro para o destino.\n\nErro: {copy_error}")
                    else:
                        # Falha na validação lógica (estrutura do texto incorreta)
                        QMessageBox.warning(self, "Erro de Formato - Tópicos", mensagem)

                except Exception as e:
                    # Falha técnica (arquivo corrompido, erro de permissão, etc)
                    QMessageBox.critical(self, "Erro de Leitura", f"Não foi possível ler o arquivo:\n{e}")

        else:
            QMessageBox.warning(self, "Erro", "Template não suportado.")

    def iniciar_processamento(self):
        if self.template_escolhido == "camadas":
            if self.valid_filepath:
                print(f"Iniciando Processo: CAMADAS")
                tema_do_video = "imagens sobre "
                progress_dialog = ProgressWindow(self)
                progress_dialog.start_layer_video_processing(self.valid_filepath, tema_do_video, self.template_escolhido)
        elif self.template_escolhido == "topicos":
            if self.valid_filepath:
                print(f"Iniciando Processo: TOPICOS")
                tema_do_video = "imagens sobre "
                progress_dialog = ProgressWindow(self)
                progress_dialog.start_topics_video_processing(self.valid_filepath, tema_do_video, self.template_escolhido)

def validar_arquivos_formato_camadas(conteudo: str) -> tuple[bool, str]:
    camadas_obrigatorias = ['Camada Superfície Brilhante', 'Camada Congelada', 'Camada Submersa',
                            'Camada Gelo Profundo', 'Camada Núcleo Abissal', 'Espero que tenham gostado.']
    posicao_anterior = -1
    posicoes_camadas = {}
    for camada in camadas_obrigatorias:
        posicao_atual = conteudo.find(camada)
        if posicao_atual == -1: return False, f"Erro: A seção obrigatória '{camada}' não foi encontrada."
        if posicao_atual < posicao_anterior: return False, f"Erro: A seção '{camada}' está fora da ordem esperada."
        posicao_anterior = posicao_atual
        posicoes_camadas[camada] = posicao_atual
    if posicoes_camadas['Camada Superfície Brilhante'] == 0: return False, "Erro: Falta o texto de introdução."
    for i in range(len(camadas_obrigatorias) - 2):
        camada_atual, camada_seguinte = camadas_obrigatorias[i], camadas_obrigatorias[i + 1]
        inicio_secao = posicoes_camadas[camada_atual] + len(camada_atual)
        fim_secao = posicoes_camadas[camada_seguinte]
        secao_texto = conteudo[inicio_secao:fim_secao]
        topicos_encontrados = re.findall(r'Número (\d)\.', secao_texto)
        if not (1 <= len(
            topicos_encontrados) <= 3): return False, f"Erro na '{camada_atual}': É necessário ter entre 1 e 3 tópicos. Encontrados: {len(topicos_encontrados)}."
        numeros_topicos = [int(n) for n in topicos_encontrados]
        if numeros_topicos != list(range(1,
                                         len(numeros_topicos) + 1)): return False, f"Erro na '{camada_atual}': Os tópicos não estão em ordem sequencial."
    posicao_final_esperada = posicoes_camadas['Espero que tenham gostado.'] + len('Espero que tenham gostado.')
    if len(conteudo.strip()) <= posicao_final_esperada: return False, "Erro: Falta o texto de encerramento."
    return True, "Sucesso! \nO arquivo está no formato correto."

def validar_arquivos_formato_topicos(conteudo):
    frase_divisoria = "Espero que tenham gostado."
    if frase_divisoria not in conteudo:
        return False, f"O arquivo deve conter a frase exata: '{frase_divisoria}'"

    partes = conteudo.rsplit(frase_divisoria, 1)
    conteudo_antes_divisoria = partes[0]
    conteudo_encerramento = partes[1]

    palavras_encerramento = conteudo_encerramento.split()
    if len(palavras_encerramento) < 10:
        return False, f"O encerramento (após '{frase_divisoria}') deve ter no mínimo 10 palavras. Encontradas: {len(palavras_encerramento)}"

    padrao_topico = r"Número \d+\.\s+.*?\."

    topicos_encontrados = re.findall(padrao_topico, conteudo_antes_divisoria)

    if len(topicos_encontrados) < 3:
        return False, f"O arquivo deve ter no mínimo 3 tópicos no formato 'Número X. Título.'. Encontrados: {len(topicos_encontrados)}"

    match_primeiro_topico = re.search(padrao_topico, conteudo_antes_divisoria)

    if match_primeiro_topico:
        indice_inicio_topicos = match_primeiro_topico.start()
        texto_intro = conteudo_antes_divisoria[:indice_inicio_topicos]
        palavras_intro = texto_intro.split()

        if len(palavras_intro) < 10:
            return False, f"A introdução (antes do primeiro tópico 'Número X...') deve ter no mínimo 10 palavras. Encontradas: {len(palavras_intro)}"
    else:
        return False, "Não foi possível identificar o início dos tópicos para validar a introdução."

    return True, "Arquivo de Tópicos válido."
