import os
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt.uic import loadUi
from qgis.gui import QgsMapToolEmitPoint
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsFileDownloader
from qgis.PyQt.QtCore import QUrl
import urllib.parse

class DialogoBasico(QDialog):

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

        self.map_tool = QgsMapToolEmitPoint(self.canvas)
        self.map_tool.canvasClicked.connect(self.capturar_ponto)

    def ativar_selecao_ponto(self):
        self.label_status.setText("Clique em um ponto no mapa...")
        self.canvas.setMapTool(self.map_tool)

    def capturar_ponto(self, ponto, botao):
        self.x = ponto.x()
        self.y = ponto.y()

        self.label_coordenada.setText(f"X: {self.x:.6f} | Y: {self.y:.6f}")
        self.label_status.setText("Ponto selecionado com sucesso.")

        self.canvas.unsetMapTool(self.map_tool)

    def buscar_sentinel(self):
        from pystac_client import Client
        import planetary_computer

        if self.x is None or self.y is None:
            self.label_status.setText("Selecione um ponto no mapa primeiro.")
            return

        try:
            crs_origem = self.canvas.mapSettings().destinationCrs()
            crs_destino = QgsCoordinateReferenceSystem("EPSG:4326")

            transformador = QgsCoordinateTransform(
                crs_origem,
                crs_destino,
                QgsProject.instance()
            )

            ponto_wgs84 = transformador.transform(self.x, self.y)

            lon = ponto_wgs84.x()
            lat = ponto_wgs84.y()

            delta = 0.05
            bbox = [lon - delta, lat - delta, lon + delta, lat + delta]

            self.label_status.setText("Buscando imagem Sentinel-2...")

            catalog = Client.open(
                "https://planetarycomputer.microsoft.com/api/stac/v1",
                modifier=planetary_computer.sign_inplace,
            )

            search = catalog.search(
                collections=["sentinel-2-l2a"],
                bbox=bbox,
                datetime="2024-01-01/2024-12-31",
                limit=1
            )

            item = next(search.items(), None)

            if item is None:
                self.item_encontrado = None
                self.label_status.setText("Nenhuma imagem encontrada.")
            else:
                self.item_encontrado = item
                self.label_status.setText(f"Imagem encontrada: {item.id}")

        except Exception as e:
            self.label_status.setText(f"Erro: {str(e)}")


    def obter_tamanho_recorte(self):
        texto = self.combo_tamanho_recorte.currentText().strip()

        if texto == "512 x 512":
            return 512
        elif texto == "1024 x 1024":
            return 1024
        elif texto == "2048 x 2048":
            return 2048
        else:
            return 512
    
    def montar_url_recorte_data_api(self):
        if self.item_encontrado is None:
            return None

        if self.x is None or self.y is None:
            return None

        # CRS do projeto/mapa
        crs_mapa = self.canvas.mapSettings().destinationCrs()

        # Este método funciona corretamente se o projeto estiver em CRS projetado (metros)
        if not crs_mapa.isValid() or crs_mapa.isGeographic():
            self.label_status.setText("Use um CRS projetado em metros para recorte correto.")
            return None

        # Tamanho do recorte em pixels
        tamanho_pixels = self.obter_tamanho_recorte()

        # Sentinel-2 RGB em 10 m
        resolucao_m = 10
        lado_m = tamanho_pixels * resolucao_m
        metade = lado_m / 2

        # Quadrado real em METROS ao redor do ponto clicado
        xmin_proj = self.x - metade
        xmax_proj = self.x + metade
        ymin_proj = self.y - metade
        ymax_proj = self.y + metade

        # Converter os cantos para WGS84
        crs_wgs84 = QgsCoordinateReferenceSystem("EPSG:4326")
        transformador = QgsCoordinateTransform(
            crs_mapa,
            crs_wgs84,
            QgsProject.instance()
        )

        canto_inf_esq = transformador.transform(xmin_proj, ymin_proj)
        canto_sup_dir = transformador.transform(xmax_proj, ymax_proj)

        minx = canto_inf_esq.x()
        miny = canto_inf_esq.y()
        maxx = canto_sup_dir.x()
        maxy = canto_sup_dir.y()

        collection_id = self.item_encontrado.collection_id
        item_id = self.item_encontrado.id

        base_url = (
            f"https://planetarycomputer.microsoft.com/api/data/v1/item/"
            f"bbox/{minx},{miny},{maxx},{maxy}/"
            f"{tamanho_pixels}x{tamanho_pixels}.tif"
        )

        params = [
            ("collection", collection_id),
            ("item", item_id),
            ("assets", "B04"),
            ("assets", "B03"),
            ("assets", "B02"),
            ("asset_as_band", "true"),
        ]

        query_string = urllib.parse.urlencode(params, doseq=True)

        return f"{base_url}?{query_string}"

    def baixar_imagem(self):
        if self.item_encontrado is None:
            self.label_status.setText("Busque uma imagem primeiro.")
            return

        url_recorte = self.montar_url_recorte_data_api()

        if url_recorte is None:
            self.label_status.setText("Não foi possível montar a URL do recorte.")
            return

        try:
            tamanho_pixels = self.obter_tamanho_recorte()

            pasta_saida = "D:/"
            nome_arquivo = f"recorte_sentinel_{tamanho_pixels}px.tif"
            caminho_saida = os.path.join(pasta_saida, nome_arquivo)

            self.label_status.setText("Iniciando download do recorte...")

            self.downloader = QgsFileDownloader(QUrl(url_recorte), caminho_saida)

            self.downloader.downloadProgress.connect(
                lambda recebidos, total: self.label_status.setText(
                    f"Baixando recorte: {recebidos}/{total}"
                )
            )

            self.downloader.downloadCompleted.connect(
                lambda: self.download_concluido(caminho_saida)
            )

            self.downloader.downloadError.connect(
                lambda erros: self.label_status.setText(f"Erro no download: {erros}")
            )

        except Exception as e:
            self.label_status.setText(f"Erro: {str(e)}")

    def download_concluido(self, caminho_saida):
        self.label_status.setText("Download concluído. Carregando no QGIS...")

        camada = self.iface.addRasterLayer(caminho_saida, os.path.basename(caminho_saida))

        if camada:
            self.label_status.setText("Imagem carregada no QGIS com sucesso.")
        else:
            self.label_status.setText("Download concluído, mas falhou ao carregar no QGIS.")