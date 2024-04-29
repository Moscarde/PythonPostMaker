class TextProcessor:
    """
    Classe para processamento de texto.
    """

    @staticmethod
    def remove_emoji(text) -> str:
        """
        Remove emojis do texto.

        Parâmetros:
            text (str): O texto que pode conter emojis.

        Retorna:
            str: O texto sem emojis.
        """

        clean_text = ""
        for caractere in text:
            if not ord(caractere) > 0xFFFF:
                clean_text += caractere
        return clean_text

    @staticmethod
    def break_line(text, line_max=75) -> str:
        """
        Quebra o texto em várias linhas, limitando o comprimento máximo de cada linha.

        Parâmetros:
            text (str): O texto a ser quebrado em linhas.
            line_max (int, opcional): O comprimento máximo de cada linha. O padrão é 75.

        Retorna:
            str: O texto quebrado em várias linhas.
        """
        final_text = []

        for i, line in enumerate(text.split("\n")):
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
