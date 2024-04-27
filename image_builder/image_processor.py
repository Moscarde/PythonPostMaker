from PIL import Image, ImageDraw, ImageFont
from typing import Tuple


class ImageProcessor:
    """
    Classe para processar imagens.
    """

    @staticmethod
    def start_image(background_path: str) -> Tuple[Image.Image, ImageDraw.Draw]:
        """
        Inicia o processamento da imagem.

        Argumetos:
            background_path (str): O caminho para a imagem de fundo.

        Retorno:
            Tuple[Image.Image, ImageDraw.Draw]: Uma tupla contendo a imagem aberta e o objeto de desenho.
        """
        image = Image.open(background_path)
        draw = ImageDraw.Draw(image)
        return image, draw

    @staticmethod
    def place_frame(
        image, height, width=860, frame_path="backgrounds/white_frame.png"
    ) -> Tuple[Image.Image, dict]:
        """
        Posiciona o quadro dentro de uma imagem.

        Parâmetros:
            image (Image.Image): A imagem na qual o quadro será colocado.
            height (int): A altura do quadro.
            width (int, optional): A largura do quadro. Default 860.
            frame_path (str, optional): O caminho para o arquivo de imagem do quadro. Default "backgrounds/white_frame.png".

        Retorna:
            Tuple[Image.Image, dict]: Uma tupla contendo a imagem com o quadro adicionada e um dicionário contendo informações sobre a posição e o tamanho.
        """

        image, frame_pos = ImageProcessor.paste_image(
            image, frame_path, size=(width, height), center=True
        )

        frame_size = (width, height)
        frame = {}
        frame["width"] = width
        frame["height"] = height
        frame["x"] = frame_pos[0]
        frame["y"] = frame_pos[1]
        frame["end_x"] = frame_pos[0] + frame_size[0]
        frame["end_y"] = frame_pos[1] + frame_size[1]
        frame["pos"] = (frame["x"], frame["y"])
        return image, frame

    @staticmethod
    def create_circle_mask(size) -> Image.Image:
        """
        Cria uma máscara circular.

        Parâmetros:
            size (tuple): Uma tupla contendo a largura e a altura da máscara.

        Retorna:
            Image.Image: A máscara circular criada.
        """

        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        return mask

    @staticmethod
    def write_text(
        draw,
        text,
        pos=None,
        font="segoeui",
        font_size=24,
        color=(0, 0, 0),
        multline=False,
        spacing=5,
    ) -> ImageDraw.Draw:
        """
        Escreve texto na imagem.

        Parâmetros:
            draw (ImageDraw.Draw): O objeto de desenho da imagem.
            text (str): O texto a ser escrito.
            pos (tuple, opcional): A posição inicial para escrever o texto. Default None.
            font (str, opcional): O nome da fonte. Default "segoeui".
            font_size (int, opcional): O tamanho da fonte. Default 24.
            color (tuple, opcional): A cor do texto. Default (0, 0, 0) (preto).
            multline (bool, opcional): Indica se o texto deve ser escrito em várias linhas. Default False.
            spacing (int, opcional): O espaçamento entre as linhas de texto. Default 5.

        Retorna:
            ImageDraw.Draw: O objeto de desenho atualizado com o texto adicionado.
        """

        font = ImageFont.truetype(f"fonts/{font}.ttf", font_size)

        if not multline:
            draw.text(pos, text=text, font=font, fill=color)
        else:
            draw.multiline_text(pos, text=text, font=font, fill=color, spacing=spacing)

        return draw

    @staticmethod
    def place_content_media(
        image, path, border, frame_size, frame_pos, padding_bottom, padding_top
    )-> Image.Image:
        """
        Coloca conteúdo de mídia na imagem, realizando o redimensionamento e posicionamento condicional.

        Parâmetros:
            image (Image.Image): A imagem na qual o conteúdo de mídia será colocado.
            path (str): O caminho para o arquivo de mídia a ser adicionado.
            border (int): A largura da borda ao redor do conteúdo de mídia.
            frame_size (tuple): Uma tupla contendo a largura e a altura do quadro.
            frame_pos (tuple): Uma tupla contendo as coordenadas x e y do canto superior esquerdo do quadro.
            padding_bottom (int): O preenchimento inferior dentro do quadro.
            padding_top (int): O preenchimento superior dentro do quadro.

        Retorna:
            Image.Image: A imagem com o conteúdo de mídia adicionado.
        """

        new_image = Image.open(path)

        frame_size = (frame_size[0], frame_size[1] - padding_top - padding_bottom)
        frame_pos = (frame_pos[0], frame_pos[1] + padding_top)

        if new_image.width > new_image.height:
            new_image_max_width = frame_size[0] - 2 * border
            new_image_width = new_image_max_width
            new_image_height = int(
                new_image.height * new_image_max_width / new_image.width
            )

            new_image_pos = (
                frame_pos[0] + border,
                int((frame_pos[1]) + (frame_size[1] - new_image_height) / 2),
            )
        else:
            new_image_max_height = frame_size[1] - 2 * border
            new_image_width = int(
                new_image.width * new_image_max_height / new_image.height
            )
            new_image_height = new_image_max_height

            new_image_pos = (
                int((frame_pos[0]) + (frame_size[0] - new_image_width) / 2),
                frame_pos[1] + border,
            )

        new_image = new_image.resize((new_image_width, new_image_height))

        image.paste(new_image, new_image_pos, mask=new_image)

        return image

    @staticmethod
    def paste_image(image, path, pos=None, size=None, y=None, rounded=False, center=False)-> Tuple[Image.Image, tuple]:
        """
        Cola uma imagem na imagem principal.

        Parâmetros:
            image (Image.Image): A imagem principal na qual a outra imagem será colada.
            path (str): O caminho para o arquivo de imagem a ser colado.
            pos (tuple, opcional): A posição onde a imagem será colada. Padrão None.
            size (tuple, opcional): O tamanho da imagem. Padrão None.
            y (int, opcional): A coordenada y da posição onde a imagem será colada, caso seja, informado, será centralizada
            horizontalmente. Padrão None.
            rounded (bool, opcional): Indica se a imagem deve ser colada com bordas arredondadas. Padrão False.
            center (bool, opcional): Indica se a imagem deve ser colada no centro da imagem principal. Padrão False.

        Retorna:
            Tuple[Image.Image, tuple]: Uma tupla contendo a imagem principal atualizada e a posição onde a imagem foi colada.
        """

        new_image = Image.open(path)

        if not size:
            size = (new_image.width, new_image.height)
        new_image = new_image.resize(size)

        if center:
            pos = (
                (image.width - new_image.width) // 2,
                (image.height - new_image.height) // 2,
            )

        if y:
            pos = ((image.width - new_image.width) // 2, y)

        if rounded:
            mask = ImageProcessor.create_circle_mask(new_image.size)
            new_image.putalpha(mask)

        image.paste(new_image, pos, mask=new_image)

        return image, pos

    @staticmethod
    def save_image(image, path) -> int:
        """
        Salva a imagem em um arquivo.

        Parâmetros:
            image (Image.Image): A imagem a ser salva.
            path (str): O caminho para o arquivo de destino.

        Retorna:
            int: Se a imagem foi salva com sucesso.
        """
        image.save(path)
        return 1


if __name__ == "__main__":

    image, draw = ImageProcessor.start_image("backgrounds/3c.png")
    image, frame = ImageProcessor.place_frame(image=image, height=900)
    print(frame)
    image.save("debug.png")
