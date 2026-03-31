from qgis.gui import QgsMapToolEmitPoint

class MapSelector:
    def __init__(self, canvas, ao_clicar_callback):
        self.canvas = canvas
        self.ao_clicar_callback = ao_clicar_callback

        self.map_tool = QgsMapToolEmitPoint(self.canvas)
        self.map_tool.canvasClicked.connect(self._capturar_ponto)

    def ativar(self):
        self.canvas.setMapTool(self.map_tool)

    def _capturar_ponto(self, ponto, botao):
        x = ponto.x()
        y = ponto.y()

        self.ao_clicar_callback(x, y)

        self.canvas.unsetMapTool(self.map_tool)