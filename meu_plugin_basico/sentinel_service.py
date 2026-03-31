import urllib.parse
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject

class SentinelService:
    def __init__(self, canvas):
        self.canvas = canvas

    def buscar_item(self, x, y):
        from pystac_client import Client
        import planetary_computer

        if x is None or y is None:
            return None, "Selecione um ponto no mapa primeiro."

        try:
            crs_origem = self.canvas.mapSettings().destinationCrs()
            crs_destino = QgsCoordinateReferenceSystem("EPSG:4326")

            transformador = QgsCoordinateTransform(
                crs_origem,
                crs_destino,
                QgsProject.instance()
            )

            ponto_wgs84 = transformador.transform(x, y)

            lon = ponto_wgs84.x()
            lat = ponto_wgs84.y()

            delta = 0.05
            bbox = [lon - delta, lat - delta, lon + delta, lat + delta]

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
                return None, "Nenhuma imagem encontrada."

            return item, f"Imagem encontrada: {item.id}"

        except Exception as e:
            return None, f"Erro: {str(e)}"

    def obter_tamanho_recorte(self, texto):
        texto = texto.strip()

        if texto == "512 x 512":
            return 512
        elif texto == "1024 x 1024":
            return 1024
        elif texto == "2048 x 2048":
            return 2048
        else:
            return 512

    def montar_url_recorte_data_api(self, x, y, item_encontrado, tamanho_texto):
        if item_encontrado is None:
            return None, "Nenhuma imagem encontrada para montar o recorte."

        if x is None or y is None:
            return None, "Selecione um ponto no mapa primeiro."

        crs_mapa = self.canvas.mapSettings().destinationCrs()

        if not crs_mapa.isValid() or crs_mapa.isGeographic():
            return None, "Use um CRS projetado em metros para recorte correto."

        tamanho_pixels = self.obter_tamanho_recorte(tamanho_texto)

        resolucao_m = 10
        lado_m = tamanho_pixels * resolucao_m
        metade = lado_m / 2

        xmin_proj = x - metade
        xmax_proj = x + metade
        ymin_proj = y - metade
        ymax_proj = y + metade

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

        collection_id = item_encontrado.collection_id
        item_id = item_encontrado.id

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

        return f"{base_url}?{query_string}", None