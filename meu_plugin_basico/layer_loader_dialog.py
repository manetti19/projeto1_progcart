import os
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUi
from .map_selector import MapSelector
from .sentinel_service import SentinelService
from .downloader import Downloader

class LayerLoaderDialog(QDialog):

    def __init__(self, iface):

        super().__init__()

        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.item_encontrado = None

        self.x = None
        self.y = None

        caminho_ui = os.path.join(os.path.dirname(__file__), "janela1.ui")
        loadUi(caminho_ui, self)

        self.botao_selecionar_ponto.clicked.connect(self.ativar_selecao_ponto)
        self.botao_buscar_sentinel.clicked.connect(self.buscar_sentinel)
        self.botao_baixar_imagem.clicked.connect(self.baixar_imagem)

        self.map_selector = MapSelector(self.canvas, self.ponto_selecionado)
        self.sentinel_service = SentinelService(self.canvas)
        self.downloader_service = Downloader(
            self.iface,
            ao_progresso_callback=self.atualizar_progresso_download,
            ao_concluir_callback=self.download_concluido,
            ao_erro_callback=self.download_com_erro
        )

    def ativar_selecao_ponto(self):
        self.label_status.setText("Clique em um ponto no mapa...")
        self.map_selector.ativar()

    def ponto_selecionado(self, x, y):
        self.x = x
        self.y = y

        self.label_coordenada.setText(f"X: {self.x:.6f} | Y: {self.y:.6f}")
        self.label_status.setText("Ponto selecionado com sucesso.")

    def buscar_sentinel(self):
        self.label_status.setText("Buscando imagem Sentinel-2...")

        item, mensagem = self.sentinel_service.buscar_item(self.x, self.y)

        self.item_encontrado = item
        self.label_status.setText(mensagem)

    def baixar_imagem(self):
        if self.item_encontrado is None:
            self.label_status.setText("Busque uma imagem primeiro.")
            return

        url_recorte, erro = self.sentinel_service.montar_url_recorte_data_api(
            self.x,
            self.y,
            self.item_encontrado,
            self.combo_tamanho_recorte.currentText()
        )

        if url_recorte is None:
            self.label_status.setText(erro)
            return

        try:
            tamanho_pixels = self.sentinel_service.obter_tamanho_recorte(
                self.combo_tamanho_recorte.currentText()
            )

            pasta_saida = "D:/"
            nome_arquivo = f"recorte_sentinel_{tamanho_pixels}px.tif"
            caminho_saida = os.path.join(pasta_saida, nome_arquivo)

            self.label_status.setText("Iniciando download do recorte...")

            self.downloader_service.baixar(url_recorte, caminho_saida)

        except Exception as e:
            self.label_status.setText(f"Erro: {str(e)}")

    def atualizar_progresso_download(self, recebidos, total):
        self.label_status.setText(f"Baixando recorte: {recebidos}/{total}")

    def download_concluido(self, caminho_saida, camada):
        if camada:
            self.label_status.setText("Imagem carregada no QGIS com sucesso.")
        else:
            self.label_status.setText("Download concluído, mas falhou ao carregar no QGIS.")

    def download_com_erro(self, erros):
        self.label_status.setText(f"Erro no download: {erros}")