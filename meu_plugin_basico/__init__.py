def classFactory(iface):
    from .layer_loader import LayerLoader
    return LayerLoader(iface)