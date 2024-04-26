import json
import os

from PIL import Image, ImageDraw, ImageFont


class ImageBuilder:
    def __init__(self, path):
        self.path = path
        self.output_path = self.path + "/processed_images"
        self.data = self.read_file(os.path.join(path, "data.json"))
        self.height_line = 29

    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)

            return data
        except Exception as e:
            print("Erro ao ler o arquivo:", e)
            return None

    def build(self, anonymous=False):
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

        if anonymous:
            self.data = self.anonimous_data()

        self.paginate_post_images(data=self.data)
        if len(self.data["content"]["img_filenames"]) > 0:
            self.paginate_content_images(data=self.data)
        if len(self.data["comments"]) > 0:
            self.paginate_comments_images(data=self.data)

    def anonimous_data(self):
        data = self.data
        data["author"]["name"] = "Usuário do LinkedIn"
        data["author"]["img_filename"] = "default"

        for comment in data["comments"]:
            comment["author"] = "Usuário do LinkedIn"
            comment["img_filename"] = "default"

        return data

    def paginate_post_images(self, data, output_count=1):
        max_lines_per_image = 26

        text = break_line(data["content"]["text"])

        text_splited = text.split("\n")
        n_lines = len(text_splited)
        print(n_lines)

        if n_lines > max_lines_per_image:
            text = "\n".join(text_splited[: max_lines_per_image - 4])

            page_text = "\n".join(text_splited[max_lines_per_image - 4 :])
            new_data = data.copy()
            new_data["content"]["text"] = page_text
            self.paginate_post_images(data=new_data, output_count=output_count + 1)

        text_to_build = "\n".join(
            text_splited
            if n_lines <= max_lines_per_image
            else text_splited[: max_lines_per_image - 4]
        )
        height = (200 if output_count == 1 else 280) + len(
            text_to_build.split("\n")
        ) * self.height_line

        print("Output count:", output_count, "Height:", height)
        self.build_post_image(
            text=text_to_build,
            output_count=output_count,
            continued=output_count > 1,
            end=n_lines < max_lines_per_image,
            height=height,
        )

    def build_post_image(self, text, output_count, continued, end, height):
        image = Image.open("backgrounds/3c.png")
        draw = ImageDraw.Draw(image)

        rectangle_size = (860, height)
        rectangle_pos = (
            int((image.width - rectangle_size[0]) / 2),
            int((image.height - rectangle_size[1]) / 2),
        )

        image = self.paste_image(
            image, "backgrounds/rectangle.png", size=rectangle_size, pos=rectangle_pos
        )
        content_top_y = rectangle_pos[1] + 20

        self.place_author_header(image, draw, content_top_y)

        if continued:
            image = self.paste_image(
                image,
                "backgrounds/header_ellipsis.png",
                pos=(
                    int((image.width - 800) / 2),
                    rectangle_pos[1] + 110,
                ),
            )

        content_text_padding_top = (
            content_top_y + 97 if output_count == 1 else content_top_y + 165
        )

        # content text
        self.write_text(
            draw,
            text,
            (136, content_text_padding_top),
            multline=True,
            font_size=22,
            font_="seguiemj",
            spacing=12,
        )

        # footer
        if end:
            self.paste_image(
                image,
                "backgrounds/action_bar.png",
                size=(int(800 * 1), int(65 * 1)),
                pos=(
                    int((image.width - 800) / 2),
                    rectangle_pos[1] + rectangle_size[1] - 80,
                ),
            )

            self.paste_image(
                image,
                "backgrounds/reaction_icon_3.png",
                pos=(
                    int((image.width - 800) / 2),
                    rectangle_pos[1] + rectangle_size[1] - 94,
                ),
            )

            reactions = self.data["content"]["reactions"]
            if len(reactions) > 0:
                reactions_text = (
                    f"{reactions[0]} · {reactions[1]}"
                    if len(reactions) > 1
                    else reactions[0]
                )
                self.write_text(
                    draw,
                    text_=reactions_text,
                    pos=(
                        206,
                        rectangle_pos[1] + rectangle_size[1] - 98,
                    ),
                    font_size=18,
                    color=(130, 130, 130),
                )

        else:
            self.paste_image(
                image,
                "backgrounds/action_bar_ellipsis_continue.png",
                pos=(
                    int((image.width - 800) / 2),
                    rectangle_pos[1] + rectangle_size[1] - 72,
                ),
            )

        image.save(f"{self.output_path}/square_post_{output_count}.png")

    def paginate_content_images(self, data, output_count=1):

        max_height = 800  # 900
        for index, content_image_filename in enumerate(data["content"]["img_filenames"]):
            height_frame = 900
            image = Image.open("backgrounds/3c.png")

            frame_size = (860, height_frame)
            frame_pos = (
                int((image.width - frame_size[0]) / 2),
                int((image.height - frame_size[1]) / 2),
            )

            self.paste_image(
                image, "backgrounds/rectangle.png", size=frame_size, pos=frame_pos
            )

            image = self.processe_and_paste_image(
                image,
                f"{self.path}/{content_image_filename}",
                border=40,
                frame_size=(frame_size[0], frame_size[1] - 40),
                frame_pos=frame_pos,
            )

            image = self.paste_image(
                image,
                "backgrounds/action_bar_ellipsis_continue.png",
                pos=(
                    int((image.width - 800) / 2),
                    frame_pos[1] + height_frame - 70,
                ),
            )

            image.save(f"{self.output_path}/square_content_{index}.png")

    def paginate_comments_images(self, data, output_count=1):

        max_height = 800  # 900
        height_comment_header = 120  # espaçamentos

        staged_comments = []
        height_frame = 110  # seria o header

        for i, comment in enumerate(data["comments"]):

            comment_text = break_line(
                remove_emoji(comment["comment_text"]), line_max=65
            )
            n_lines = len(comment_text.split("\n"))

            # ignorando comentários muito grandes ou sem texto
            if n_lines > 23 or comment_text == "":
                continue

            comment_height = n_lines * self.height_line + height_comment_header

            if height_frame + comment_height > max_height:
                new_data = data.copy()
                new_data["comments"] = data["comments"][i:]
                self.paginate_comments_images(
                    data=new_data,
                    output_count=output_count + 1,
                )
                break
            else:
                height_frame += comment_height
                staged_comments.append(comment)

        last_image = staged_comments[-1] == data["comments"][-1]
        self.build_comments_image(
            comments=staged_comments,
            height_frame=height_frame if last_image else height_frame + 50,
            output_count=output_count,
            end=last_image,
        )
        return 1

    def build_comments_image(self, comments, height_frame, output_count=1, end=False):

        image = Image.open("backgrounds/3c.png")
        draw = ImageDraw.Draw(image)

        # frame
        frame_size = (860, height_frame)
        frame_pos = (
            int((image.width - frame_size[0]) / 2),
            int((image.height - frame_size[1]) / 2),
        )

        # frame
        self.paste_image(
            image, "backgrounds/rectangle.png", size=frame_size, pos=frame_pos
        )

        # ellipsis continued
        self.paste_image(
            image,
            "backgrounds/header_ellipsis.png",
            pos=(
                int((image.width - 800) / 2),
                frame_pos[1] + 10,
            ),
        )

        comment_bg = "backgrounds/comment_bg.png"
        # comment 0

        comment_top_y = frame_pos[1] + 80

        for comment in comments:
            author = remove_emoji(comment["author"])

            headline = (
                comment["headline"][:65] + "..."
                if len(comment["headline"]) > 65
                else comment["headline"]
            )

            age = comment["comment_age"]

            img_path = f"{self.path}/{comment['img_filename']}"

            if not os.path.exists(img_path):
                img_path = "backgrounds/default_profile_photo.png"

            text = break_line(remove_emoji(comment["comment_text"]), line_max=65)

            n_lines = len(text.split("\n"))
            background_size = 100 + int(30 * n_lines)

            # bg
            self.paste_image(
                image, comment_bg, pos=(215, comment_top_y), size=(720, background_size)
            )

            # image author
            self.paste_image(
                image,
                img_path,
                pos=(135, comment_top_y),
                size=(65, 65),
                rounded=True,
            )

            # name
            self.write_text(
                draw,
                author,
                (230, comment_top_y + 10),
                font_="seguisb",
                font_size=22,
            )

            # headline
            self.write_text(
                draw,
                headline,
                (230, comment_top_y + 40),
                font_size=20,
                color=(130, 130, 130),
                font_="segoeuil",
            )

            # age
            self.write_text(
                draw,
                age,
                (880, comment_top_y + 10),
                font_size=20,
                color=(130, 130, 130),
            )

            # text
            self.write_text(
                draw,
                text,
                (230, comment_top_y + 80),
                font_size=22,
                font_="seguiemj",
                multline=True,
                spacing=15,
            )

            comment_top_y += background_size + 30

        if not end:
            self.paste_image(
                image=image,
                path="backgrounds/action_bar_ellipsis_continue.png",
                pos=(
                    int((image.width - 800) / 2),
                    frame_pos[1] + height_frame - 70,
                ),
            )
        image.save(f"{self.output_path}/comments_{output_count}.png")

    def place_author_header(self, image, draw, content_top_y):
        author_name = self.data["author"]["name"]
        author_subtitle = (
            self.data["author"]["headline"][:65] + "..."
            if len(self.data["author"]["headline"]) > 65
            else self.data["author"]["headline"]
        )
        post_time_stamp = self.data["author"]["post_age"]

        author_image_path = self.path + "/author_img.png"

        image = self.paste_image(
            image,
            author_image_path,
            pos=(135, content_top_y),
            size=(75, 75),
            rounded=True,
        )

        self.write_text(draw, author_name, (225, content_top_y), font_="seguisb")
        self.write_text(
            draw,
            author_subtitle,
            (225, content_top_y + 30),
            font_size=20,
            color=(130, 130, 130),
        )
        self.write_text(
            draw,
            post_time_stamp,
            (225, content_top_y + 55),
            font_size=20,
            color=(130, 130, 130),
        )
        return image

    def paste_image(self, image, path, pos, size=(), rounded=False):
        new_image = Image.open(path)

        if not size:
            size = (new_image.width, new_image.height)

        if rounded:
            mask = create_circle_mask(new_image.size)
            new_image.putalpha(mask)

        new_image = new_image.resize(size)

        image.paste(new_image, pos, mask=new_image)

        return image

    def processe_and_paste_image(self, image, path, border, frame_size, frame_pos):
        new_image = Image.open(path)
        new_image_width, new_image_height = new_image.size

        if new_image_width > new_image_height:
            new_image_max_width = frame_size[0] - 2 * border
            new_image_height = new_image_height * new_image_max_width / new_image_width
            new_image_width = new_image_max_width

            new_image_pos = (
                frame_pos[0] + border,
                int((frame_pos[1]) + (frame_size[1] - new_image_height) / 2),
            )
        else:
            new_image_max_height = frame_size[1] - 2 * border
            new_image_width = new_image_width * new_image_max_height / new_image_height
            new_image_height = new_image_max_height

            new_image_pos = (
                int((frame_pos[0]) + (frame_size[0] - new_image_width) / 2),
                frame_pos[1] + border,
            )

        new_image = new_image.resize((int(new_image_width), int(new_image_height)))
        image.paste(new_image, new_image_pos, mask=new_image)

        return image

    def write_text(
        self,
        draw,
        text_,
        pos=(),
        font_="segoeui",
        font_size=24,
        color=(0, 0, 0),
        multline=False,
        spacing=5,
    ):
        font = ImageFont.truetype(f"fonts/{font_}.ttf", font_size)
        if not multline:
            draw.text(pos, text_, font=font, fill=color)
        else:
            draw.multiline_text(pos, text_, font=font, fill=color, spacing=spacing)


def remove_emoji(text):
    text_clean = ""
    for caractere in text:
        if not ord(caractere) > 0xFFFF:
            text_clean += caractere
    return text_clean


def break_line(texto, line_max=75):
    text_splited = texto.split("\n")

    final_text = []
    for i, line in enumerate(text_splited):
        if len(line) > line_max:
            words = line.split()
            line_text = words[0]

            # links
            if len(line_text) > line_max:
                line_text = line_text[: line_max - 3] + "..."

            cursor = len(words[0])
            for word in words[1:]:
                if cursor + len(word) + 1 > line_max:
                    final_text.append(line_text)
                    line_text = ""
                    cursor = 0
                else:
                    line_text += " "
                    cursor += 1
                line_text += word
                cursor += len(word)

            final_text.append(line_text)

        else:
            final_text.append(line)

    final_text_str = "\n".join(final_text)
    return final_text_str


def create_circle_mask(size):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    return mask


if __name__ == "__main__":
    image_builder = ImageBuilder(path="last_scrap")
    # print(image_builder.data["comments"])
    image_builder.build()
