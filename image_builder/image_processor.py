from PIL import Image, ImageDraw, ImageFont


class ImageProcessor:
    @staticmethod
    def start_image(background_path):
        image = Image.open(background_path)
        draw = ImageDraw.Draw(image)
        return image, draw

    @staticmethod
    def place_frame(image, height, width=860, frame_path="backgrounds/white_frame.png"):
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
    def create_circle_mask(size):
        mask = Image.new("L", size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        return mask

    @staticmethod
    def write_text(
        draw,
        text,
        pos=(),
        font="segoeui",
        font_size=24,
        color=(0, 0, 0),
        multline=False,
        spacing=5,
    ):
        font = ImageFont.truetype(f"fonts/{font}.ttf", font_size)

        if not multline:
            draw.text(pos, text=text, font=font, fill=color)
        else:
            draw.multiline_text(pos, text=text, font=font, fill=color, spacing=spacing)

        return draw

    @staticmethod
    def place_content_image(
        image, path, border, frame_size, frame_pos, padding_bottom, padding_top
    ):
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
    def paste_image(image, path, pos=(), size=(), y=None, rounded=False, center=False):
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


if __name__ == "__main__":

    image, draw = ImageProcessor.start_image("backgrounds/3c.png")
    image, frame = ImageProcessor.place_frame(image=image, height=900)
    print(frame)
    image.save("debug.png")
