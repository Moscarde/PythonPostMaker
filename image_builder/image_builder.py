import json
import os

from PIL import Image, ImageDraw, ImageFont
from image_builder.image_processor import ImageProcessor
from image_builder.text_processor import TextProcessor


class ImageBuilder:
    CONTENT_TEXT_PADDING_LEFT = 136
    CONTENT_TEXT_SIZE = 22
    CONTENT_TEXT_FONT = "seguiemj"

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
            self.paginate_content_media(data=self.data)
        
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

        text = TextProcessor.break_line(data["content"]["text"])

        text_splited = text.split("\n")
        n_lines = len(text_splited)

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

        self.build_post_image(
            text=text_to_build,
            output_count=output_count,
            continued=output_count > 1,
            end=n_lines < max_lines_per_image,
            height=height,
        )

    def build_post_image(self, text, output_count, continued, end, height):
        image, draw = ImageProcessor.start_image("backgrounds/3c.png")

        image, frame = ImageProcessor.place_frame(
            image,
            height=height,
        )

        # content_top_y = y + 20

        self.place_author_header(image, draw, frame["y"] + 20)

        if continued:
            image = ImageProcessor.paste_image(
                image,
                "backgrounds/header_ellipsis.png",
                y=frame["y"] + 110,
            )

            content_text_padding_top = frame["y"] + 185

        else:
            content_text_padding_top = frame["y"] + 117

        # content text
        ImageProcessor.write_text(
            draw=draw,
            text=text,
            pos=(self.CONTENT_TEXT_PADDING_LEFT, content_text_padding_top),
            multline=True,
            font_size=self.CONTENT_TEXT_SIZE,
            font=self.CONTENT_TEXT_FONT,
            spacing=12,
        )

        # footer
        if not end:
            ImageProcessor.paste_image(
                image,
                "backgrounds/ellipsis_continue.png",
                y=frame["end_y"] - 72,
            )

        else:
            ImageProcessor.paste_image(
                image,
                "backgrounds/action_bar.png",
                size=(int(800 * 1), int(65 * 1)),
                y=frame["end_y"] - 80,
            )

            ImageProcessor.paste_image(
                image,
                "backgrounds/reaction_icon_3.png",
                y=frame["end_y"] - 94,
            )

            reactions = self.data["content"]["reactions"]
            if len(reactions) > 0:
                reactions_text = (
                    f"{reactions[0]} · {reactions[1]}"
                    if len(reactions) > 1
                    else reactions[0]
                )
                ImageProcessor.write_text(
                    draw,
                    text=reactions_text,
                    pos=(
                        206,
                        frame["end_y"] - 98,
                    ),
                    font_size=18,
                    color=(130, 130, 130),
                )

        ImageProcessor.save_image(
            image, f"{self.output_path}/square_post_{output_count}.png"
        )

    def paginate_content_media(self, data):
        for index, content_image_filename in enumerate(
            data["content"]["img_filenames"]
        ):
            if index == len(data["content"]["img_filenames"]) - 1:
                end = True
            else:
                end = False

            self.build_content_media_image(content_image_filename, index, end=end)

    def build_content_media_image(self, content_image_filename, index, end):
        height_frame = 900
        image, draw = ImageProcessor.start_image("backgrounds/3c.png")

        image, frame = ImageProcessor.place_frame(
            image,
            height=height_frame,
        )

        image = self.place_author_header(
            image=image, draw=draw, content_top_y=frame["y"] + 20
        )

        padding_bottom = 40
        padding_top = 80
        image = ImageProcessor.place_content_media(
            image,
            f"{self.path}/{content_image_filename}",
            border=40,
            frame_size=(frame["width"], frame["height"]),
            frame_pos=(frame["pos"]),
            padding_bottom=padding_bottom,
            padding_top=padding_top,
        )

        if end:
            image, pos = ImageProcessor.paste_image(
                image,
                "backgrounds/ellipsis_continue.png",
                y=frame["end_y"] - 70,
            )

        else:
            image, pos = ImageProcessor.paste_image(
                image,
                "backgrounds/action_bar.png",
                y=frame["end_y"] - 75,
            )

        ImageProcessor.save_image(
            image, f"{self.output_path}/square_content_{index}.png"
        )

    def paginate_comments_images(self, data, output_count=1):
        max_height = 800  # 900
        height_comment_header = 120  # espaçamentos

        staged_comments = []
        height_frame = 110  # seria o header

        for i, comment in enumerate(data["comments"]):

            comment_text = TextProcessor.break_line(
                comment["comment_text"], line_max=65
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

        image, draw = ImageProcessor.start_image("backgrounds/3c.png")

        # frame
        image, frame = ImageProcessor.place_frame(image, height=height_frame)

        # ellipsis continued
        ImageProcessor.paste_image(
            image,
            "backgrounds/header_ellipsis.png",
            y=(frame["y"] + 10,),
        )

        comment_bg = "backgrounds/comment_bg.png"
        # comment 0

        comment_start_y = frame["y"] + 80
        acummulated_height = 0
        padding_top = 30
        for comment in comments:
            comment_y = comment_start_y + acummulated_height
            author = TextProcessor.remove_emoji(comment["author"])

            headline = (
                comment["headline"][:65] + "..."
                if len(comment["headline"]) > 65
                else comment["headline"]
            )

            age = comment["comment_age"]

            if 'default' in comment["img_filename"]:
                img_path = "backgrounds/default_profile_photo.png"
            else:
                img_path = f"{self.path}/{comment['img_filename']}"


            text = TextProcessor.break_line(comment["comment_text"], line_max=65)

            n_lines = len(text.split("\n"))
            background_size = 100 + int(30 * n_lines)

            # bg
            ImageProcessor.paste_image(
                image, comment_bg, pos=(215, comment_y), size=(720, background_size)
            )

            # image author
            ImageProcessor.paste_image(
                image,
                path=img_path,
                pos=(135, comment_y + 10),
                size=(65, 65),
                rounded=True,
            )

            # name
            ImageProcessor.write_text(
                draw,
                author,
                (230, comment_y + 10),
                font="seguisb",
                font_size=22,
            )

            # headline
            ImageProcessor.write_text(
                draw,
                text=headline,
                pos=(230, comment_y + 40),
                font_size=20,
                color=(130, 130, 130),
                font="segoeuil",
            )

            # age
            ImageProcessor.write_text(
                draw,
                text=age,
                pos=(880, comment_y + 10),
                font_size=20,
                color=(130, 130, 130),
            )

            # text
            ImageProcessor.write_text(
                draw,
                text=text,
                pos=(230, comment_y + 80),
                font_size=22,
                font="seguiemj",
                multline=True,
                spacing=15,
            )

            acummulated_height += background_size + padding_top

        if not end:
            ImageProcessor.paste_image(
                image=image,
                path="backgrounds/ellipsis_continue.png",
                y=frame["end_y"] - 70,
            )
        ImageProcessor.save_image(
            image, f"{self.output_path}/comments_{output_count}.png"
        )

    def place_author_header(self, image, draw, content_top_y):
        author_name = self.data["author"]["name"]
        author_headline = (
            self.data["author"]["headline"][:65] + "..."
            if len(self.data["author"]["headline"]) > 65
            else self.data["author"]["headline"]
        )
        post_time_stamp = self.data["author"]["post_age"]

        if "default" in self.data["author"]["img_filename"]:
            author_image_path = "backgrounds/default_profile_photo.png"
        else:
            author_image_path = f"{self.path}/{self.data['author']['img_filename']}"

        image, pos = ImageProcessor.paste_image(
            image,
            author_image_path,
            pos=(135, content_top_y),
            size=(75, 75),
            rounded=True,
        )

        draw = ImageProcessor.write_text(
            draw, text=author_name, pos=(225, content_top_y), font="seguisb"
        )
        draw = ImageProcessor.write_text(
            draw,
            text=author_headline,
            pos=(225, content_top_y + 30),
            font_size=20,
            color=(130, 130, 130),
        )
        draw = ImageProcessor.write_text(
            draw,
            text=post_time_stamp,
            pos=(225, content_top_y + 55),
            font_size=20,
            color=(130, 130, 130),
        )

        return image


if __name__ == "__main__":
    image_builder = ImageBuilder(path="last_scrap")
    # print(image_builder.data["comments"])
    image_builder.build()
