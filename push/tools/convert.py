class Convert:
    """所有转换器的基类，提供默认转换方法。"""
    @staticmethod
    def toTxt(content, newLine="\n", **kwargs) -> str:
        return f"{content}{newLine}"

    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return f"{content}{newLine}"

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        return f"<div>{content}</div>"


class OrderedList(Convert):
    @staticmethod
    def toTxt(content, newLine="\n", **kwargs) -> str:
        res = []
        for index, value in enumerate(content):
            res.append(f"{index+1}. {value}{newLine}")
        return "".join(res)

    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        res = []
        for index, value in enumerate(content):
            res.append(f"{index+1}. {value}{newLine}")
        return "".join(res)

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        items = "".join(f"<li>{item}</li>" for item in content)
        return f"<ol{style_attr}>{items}</ol>"


class UnOrderedList(Convert):
    @staticmethod
    def toTxt(content, newLine="\n", **kwargs) -> str:
        res = []
        for value in content:
            res.append(f"· {value}{newLine}")
        return "".join(res)

    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        res = []
        for value in content:
            res.append(f"- {value}{newLine}")
        return "".join(res)

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        items = "".join(f"<li>{item}</li>" for item in content)
        return f"<ul{style_attr}>{items}</ul>"


__H_HTML__ = ["", "h1", "h2", "h3", "h4", "h5", "h6"]
__H_MD__ = ["", "#", "##", "###", "####", "#####", "######"]


class H(Convert):
    """
    标题基类。子类应调用 toMd 和 toHtml 并传入正确的 level。
    注意: toTxt 直接继承自 Convert，无需重写。
    """
    @staticmethod
    def toMd(level: int, content, newLine="\n", **kwargs) -> str:
        if not 1 <= level <= 6:
            raise ValueError(f"标题级别 level 必须在 1-6 之间，当前为 {level}")
        tag = __H_MD__[level]
        return f"{tag} {content}{newLine}"

    @staticmethod
    def toHtml(level: int, content, **kwargs) -> str:
        if not 1 <= level <= 6:
            raise ValueError(f"标题级别 level 必须在 1-6 之间，当前为 {level}")
        tag = __H_HTML__[level]
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        return f"<{tag}{style_attr}>{content}</{tag}>"


class H1(H):
    """一级标题。所有方法均正确调用基类 H 的实现。"""
    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return H.toMd(1, content, newLine, **kwargs)

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        return H.toHtml(1, content, **kwargs)


class H2(H):
    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return H.toMd(2, content, newLine, **kwargs)

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        return H.toHtml(2, content, **kwargs)


class H3(H):
    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return H.toMd(3, content, newLine, **kwargs)

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        return H.toHtml(3, content, **kwargs)


class H4(H):
    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return H.toMd(4, content, newLine, **kwargs)

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        return H.toHtml(4, content, **kwargs)


class H5(H):
    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return H.toMd(5, content, newLine, **kwargs)

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        return H.toHtml(5, content, **kwargs)


class H6(H):
    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return H.toMd(6, content, newLine, **kwargs)

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        return H.toHtml(6, content, **kwargs)


class Img(Convert):
    """图像转换器。"""
    @staticmethod
    def toTxt(url, newLine="\n", **kwargs) -> str:
        alt = kwargs.get("alt", "link")
        return f"{alt}: {url}{newLine}"

    @staticmethod
    def toMd(url, newLine="\n", **kwargs) -> str:
        alt = kwargs.get("alt", "No alt")
        return f"![{alt}]({url}){newLine}"

    @staticmethod
    def toHtml(url, **kwargs) -> str:
        alt = kwargs.get("alt", "No alt")
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        return f"<img src=\"{url}\" alt=\"{alt}\"{style_attr} />"


class Link(Convert):
    """链接转换器。"""
    @staticmethod
    def toTxt(url, newLine="\n", **kwargs) -> str:
        content = kwargs.get("content", "link")
        return f"{content}: {url}{newLine}"

    @staticmethod
    def toMd(url, newLine="\n", **kwargs) -> str:
        content = kwargs.get("content", "link")
        return f"[{content}]({url}){newLine}"

    @staticmethod
    def toHtml(url, **kwargs) -> str:
        content = kwargs.get("content", "link")
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        return f"<a href=\"{url}\"{style_attr}>{content}</a>"


class Table(Convert):
    """表格转换器。"""
    @staticmethod
    def toTxt(contents, newLine="\n", **kwargs) -> str:
        # 调整格式：每列用制表符分隔，每行换行
        rows = []
        for row in contents:
            rows.append("\t".join(str(item) for item in row))
        return "\n" + newLine.join(rows) + "\n"

    @staticmethod
    def toMd(contents, newLine="\n", **kwargs) -> str:
        res = ["\n"]
        # 表头
        for i in contents[0]:
            res.append(f"|{i}")
        res.append(f"|{newLine}")

        # 对齐方式
        position = kwargs.get("position", "center")
        if position == "center":
            s = ":--:"
        elif position == "left":
            s = ":--"
        else:
            s = "--:"

        for _ in range(len(contents[0])):
            res.append(f"|{s}")
        res.append(f"|{newLine}")

        # 表格数据
        for tuple_ in contents[1:]:
            for i in tuple_:
                res.append(f"|{i}")
            res.append(f"|{newLine}")

        return "".join(res) + "\n"

    @staticmethod
    def toHtml(contents, **kwargs) -> str:
        style = kwargs.get(
            "style", "width: 100%; border-collapse: collapse; margin-bottom: 10px;"
        )
        thStyle = kwargs.get(
            "thStyle",
            "text-align: center; border: 1px solid #e6e6e6; background-color: #F5F5F5;"
        )
        tdStyle = kwargs.get(
            "tdStyle", "text-align: center; border: 1px solid #e6e6e6;"
        )

        # 构建表头
        headers = "".join(f"<th style=\"{thStyle}\">{cell}</th>" for cell in contents[0])
        # 构建数据行
        rows = ""
        for row in contents[1:]:
            rows += "<tr>" + "".join(f"<td style=\"{tdStyle}\">{cell}</td>" for cell in row) + "</tr>"

        return f"<table style=\"{style}\"><tr>{headers}</tr>{rows}</table>"


class Txt(Convert):
    """纯文本转换器。无需重写，完全继承 Convert 的默认行为。"""
    pass


class Bold(Convert):
    @staticmethod
    def toMd(content, newLine="", **kwargs) -> str:
        return f"**{content}**{newLine}"

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        return f"<strong{style_attr}>{content}</strong>"


class Italic(Convert):
    @staticmethod
    def toMd(content, newLine="", **kwargs) -> str:
        return f"*{content}*{newLine}"

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        return f"<i{style_attr}>{content}</i>"


class Strikethrough(Convert):
    @staticmethod
    def toMd(content, newLine="", **kwargs) -> str:
        return f"~~{content}~~{newLine}"

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        return f"<del{style_attr}>{content}</del>"


class BlockQuote(Convert):
    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return f"> {content}{newLine}"

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        style_attr = f" style=\"{kwargs.get('style')}\"" if kwargs.get("style") else ""
        return f"<blockquote{style_attr}>{content}</blockquote>"


class TaskList(Convert):
    """
    任务列表转换器。
    数据格式: [{"content": "任务1", "complete": True, "style": "color: red"}, ...]
    """
    @staticmethod
    def toTxt(contents, newLine="\n", **kwargs) -> str:
        # 复用 Markdown 格式进行文本表示
        return TaskList.toMd(contents, newLine, **kwargs)

    @staticmethod
    def toMd(contents, newLine="\n", **kwargs) -> str:
        res = []
        for item in contents:
            completed = item.get("complete", False)
            content = item.get("content", "")
            checkbox = "[x]" if completed else "[ ]"
            res.append(f"- {checkbox} {content}{newLine}")
        return "".join(res)

    @staticmethod
    def toHtml(contents, **kwargs) -> str:
        items = []
        for item in contents:
            completed = item.get("complete", False)
            content = item.get("content", "")
            style_attr = f" style=\"{item.get('style')}\"" if item.get("style") else ""
            checked = " checked" if completed else ""
            items.append(f"<label><input type=\"checkbox\" disabled=\"true\"{style_attr}{checked}/>{content}</label>")
        return " ".join(items)


class Code(Convert):
    @staticmethod
    def toTxt(content, newLine="\n", **kwargs) -> str:
        return f"{content}{newLine}"

    @staticmethod
    def toMd(content, newLine="\n", **kwargs) -> str:
        return f"`{content}`{newLine}"

    @staticmethod
    def toHtml(content, **kwargs) -> str:
        # 使用 <code> 标签表示内联代码，更语义化
        return f"<code>{content}</code>"