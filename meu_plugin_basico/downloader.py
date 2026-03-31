import os
from qgis.core import QgsFileDownloader
from qgis.PyQt.QtCore import QUrl

class Downloader:
    def __init__(self, iface, ao_progresso_callback=None, ao_concluir_callback=None, ao_erro_callback=None):
        self.iface = iface
        self.ao_progresso_callback = ao_progresso_callback
        self.ao_concluir_callback = ao_concluir_callback
        self.ao_erro_callback = ao_erro_callback
        self.downloader = None

    def baixar(self, url, caminho_saida):
        self.downloader = QgsFileDownloader(QUrl(url), caminho_saida)

        self.downloader.downloadProgress.connect(
            lambda recebidos, total: self._progresso(recebidos, total)
        )

        self.downloader.downloadCompleted.connect(
            lambda: self._concluido(caminho_saida)
        )

        self.downloader.downloadError.connect(
            lambda erros: self._erro(erros)
        )

    def _progresso(self, recebidos, total):
        if self.ao_progresso_callback:
            self.ao_progresso_callback(recebidos, total)

    def _concluido(self, caminho_saida):
        camada = self.iface.addRasterLayer(caminho_saida, os.path.basename(caminho_saida))

        if self.ao_concluir_callback:
            self.ao_concluir_callback(caminho_saida, camada)

    def _erro(self, erros):
        if self.ao_erro_callback:
            self.ao_erro_callback(erros)