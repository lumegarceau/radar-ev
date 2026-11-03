from PIL import Image, ImageDraw

BLANCO = (255, 255, 255)
VERDE = (15, 157, 88)


def icono(n):
    im = Image.new("RGB", (n, n), VERDE)
    d = ImageDraw.Draw(im)
    c = n / 2
    ancho = max(2, int(n * 0.035))
    for r in (0.30, 0.19):
        rr = n * r
        d.ellipse([c - rr, c - rr, c + rr, c + rr], outline=BLANCO, width=ancho)
    rr = n * 0.06
    d.ellipse([c - rr, c - rr, c + rr, c + rr], fill=BLANCO)
    k = n * 0.30 * 0.7071
    d.line([c, c, c + k, c - k], fill=BLANCO, width=ancho)
    return im


for nombre, n in (("icon-192.png", 192), ("icon-512.png", 512), ("icon-180.png", 180)):
    icono(n).save(nombre)
    print("creado", nombre)
