from graphviz import Source
from io import BytesIO

def export_graphviz_image(dot_string, format="png"):
    graph = Source(dot_string)

    img_bytes = graph.pipe(format=format)

    buffer = BytesIO(img_bytes)
    return buffer