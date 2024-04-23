from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import json
import os

def quebra_linha(texto):
    texto_filtrado = []
    for line in texto.split("\n"):
        texto_filtrado.append(line)

    texto_final = []
    for i, line in enumerate(texto_filtrado):
        if len(line) > 80:
            palavras = line.split()
            texto_linha = palavras[0]
            cursor = len(palavras[0])
            for palavra in palavras[1:]:
                if cursor + len(palavra) + 1 > 80:  # Verificar se a próxima palavra cabe na linha
                    texto_final.append(texto_linha)
                    texto_linha = ""
                    cursor = 0
                else:
                    texto_linha += " "
                    cursor += 1
                texto_linha += palavra
                cursor += len(palavra)
            texto_final.append(texto_linha)
        else:
            texto_final.append(line)


    texto_final_str = '\n'.join(texto_final)
    return texto_final_str

def image_builder(json_file):

    data = read_file(json_file)

    image = Image.open("backgrounds/2.png")
    draw = ImageDraw.Draw(image)

    autor_name = data["autor_name"]
    autor_subtitle = data["autor_subtitle"][: 70 - 3] + "..."
    post_time_stamp = data["time_stamp"]
    conteudo_texto = quebra_linha(data["conteudo_texto"])
    write_text(draw, autor_name, 225, 85, font_="segoeuib") 
    write_text(draw, autor_subtitle, 225, 115, font_size=20, color=(130, 130, 130))
    write_text(draw, post_time_stamp, 225, 140, font_size=20, color=(130, 130, 130))
    write_text(draw, conteudo_texto, 136, 182, multline= True, font_size = 22)


    autor_image_path = "scraped/op_photo.png"
    paste_image(image, autor_image_path, 135, 85, size = 75, rounded=True)
    image.save(f"image_output/debug2.png")

def read_file(path):
    # Abre o arquivo JSON
    with open(path, 'r', encoding="UTF-8") as f:
        # Carrega o conteúdo do arquivo JSON em um dicionário Python
        data = json.load(f )

    # Agora 'data' contém o conteúdo do arquivo JSON como um dicionário Python
    data["time_stamp"] = "9h"

    return data

def create_circle_mask(size):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    return mask


def write_text(
    draw,
    text_,
    posx,
    posy,
    font_="segoeui",
    font_size=24,
    color=(0, 0, 0),
    multline = False
):
    font = ImageFont.truetype(f"fonts/{font_}.ttf", font_size)
    if not multline:
        draw.text((posx, posy), text_, font=font, fill=color)
    else:
        draw.multiline_text((posx, posy), text_, font=font, fill = color, spacing= 5)

def paste_image(image, path, posx, posy, size, rounded = False):
    new_image = Image.open(path)

    if rounded:
        mask = create_circle_mask(new_image.size)
        new_image.putalpha(mask)
    
    new_image = new_image.resize((size, size))

    image.paste(new_image, (posx, posy), mask=new_image)