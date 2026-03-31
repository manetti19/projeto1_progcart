import os
from qgis.PyQt.QtGui import QAction, QIcon
from .layer_loader_dialog import LayerLoaderDialog

class LayerLoader:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialogo = None

    def initGui(self):
        caminho_icone = os.path.join(os.path.dirname(__file__), "icon.png")

        self.action = QAction(QIcon(caminho_icone), "Abrir Layer Loader", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        self.iface.addPluginToMenu("Meu Layer Loader", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removePluginMenu("Meu Layer Loader", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        if self.dialogo is None:
            self.dialogo = LayerLoaderDialog(self.iface)

        self.dialogo.show()
        self.dialogo.raise_()
        self.dialogo.activateWindow()