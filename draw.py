import io
import os
import textwrap
from typing import Dict, List, Any, Optional

from PIL import Image, ImageDraw, ImageFont
from astrbot.api import logger


FONT_PATH = os.path.join(os.path.dirname(__file__), "DouyinSansBold.otf")


class QuotaDrawer:
    COLOR_BACKGROUND = (255, 255, 255)
    COLOR_HEADER_BG = (245, 247, 250)
    COLOR_CARD_BG = (255, 255, 255)
    COLOR_CARD_BORDER = (220, 225, 235)
    COLOR_TEXT_TITLE = (30, 30, 30)
    COLOR_TEXT_SUBTITLE = (100, 100, 100)
    COLOR_TEXT_MODEL = (0, 60, 130)
    COLOR_TEXT_USAGE = (50, 50, 50)
    COLOR_TEXT_LABEL = (120, 120, 120)
    COLOR_ACCENT = (0, 120, 220)
    COLOR_PROGRESS_BG = (230, 235, 242)
    COLOR_PROGRESS_FILL = (0, 120, 220)
    COLOR_PROGRESS_HIGH = (60, 180, 100)
    COLOR_PROGRESS_MED = (240, 180, 60)
    COLOR_PROGRESS_LOW = (220, 60, 60)
    COLOR_FOOTER = (130, 130, 130)

    IMG_WIDTH = 600
    PADDING = 25
    CARD_PADDING_X = 15
    CARD_PADDING_Y = 12
    CARD_SPACING = 15
    CARD_CORNER_RADIUS = 12
    CARD_WIDTH = IMG_WIDTH - PADDING * 2
    SECTION_SPACING = 20
    FOOTER_HEIGHT = 35

    def __init__(self) -> None:
        self._load_fonts()

    def _load_fonts(self) -> None:
        try:
            self.font_title = ImageFont.truetype(FONT_PATH, 28)
            self.font_subtitle = ImageFont.truetype(FONT_PATH, 14)
            self.font_model = ImageFont.truetype(FONT_PATH, 16)
            self.font_usage = ImageFont.truetype(FONT_PATH, 22)
            self.font_label = ImageFont.truetype(FONT_PATH, 12)
            self.font_footer = ImageFont.truetype(FONT_PATH, 11)
        except Exception as e:
            logger.error(f"加载字体失败: {e}")
            self.font_title = ImageFont.load_default()
            self.font_subtitle = self.font_title
            self.font_model = self.font_title
            self.font_usage = self.font_title
            self.font_label = self.font_title
            self.font_footer = self.font_title

    def _get_text_size(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple:
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except AttributeError:
            return draw.textlength(text, font=font), font.size

    def _draw_rounded_rect(self, draw: ImageDraw.ImageDraw, xy: tuple, radius: int, fill=None, outline=None, width: int = 1):
        x1, y1, x2, y2 = xy
        if x1 >= x2 or y1 >= y2:
            return
        radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
        if fill:
            draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill)
            draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill)
            draw.pieslice((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=fill)
            draw.pieslice((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=fill)
            draw.pieslice((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=fill)
            draw.pieslice((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=fill)
        if outline and width > 0:
            draw.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=outline, width=width)
            draw.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=outline, width=width)
            draw.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=outline, width=width)
            draw.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=outline, width=width)
            draw.line([(x1 + radius, y1), (x2 - radius, y1)], fill=outline, width=width)
            draw.line([(x1 + radius, y2), (x2 - radius, y2)], fill=outline, width=width)
            draw.line([(x1, y1 + radius), (x1, y2 - radius)], fill=outline, width=width)
            draw.line([(x2, y1 + radius), (x2, y2 - radius)], fill=outline, width=width)

    def _get_progress_color(self, percent: float) -> tuple:
        if percent >= 60:
            return self.COLOR_PROGRESS_HIGH
        elif percent >= 30:
            return self.COLOR_PROGRESS_MED
        return self.COLOR_PROGRESS_LOW

    def _draw_card(self, draw: ImageDraw.ImageDraw, x: int, y: int, width: int, model_name: str,
                   intv_used: int, intv_total: int, intv_label: str,
                   week_used: int, week_total: int, has_week_limit: bool):
        card_h = 120 if has_week_limit else 90
        self._draw_rounded_rect(draw, (x, y, x + width, y + card_h), self.CARD_CORNER_RADIUS,
                                fill=self.COLOR_CARD_BG, outline=self.COLOR_CARD_BORDER, width=1)

        draw.text((x + self.CARD_PADDING_X, y + 12), model_name, font=self.font_model, fill=self.COLOR_TEXT_MODEL)

        y_offset = y + 38
        intv_remain = intv_total - intv_used
        intv_percent = (intv_remain / intv_total * 100) if intv_total > 0 else 0

        if intv_total == 0:
            draw.text((x + self.CARD_PADDING_X, y_offset), f"{intv_label}：无限额", font=self.font_label, fill=self.COLOR_TEXT_LABEL)
        else:
            draw.text((x + self.CARD_PADDING_X, y_offset), f"{intv_label}", font=self.font_label, fill=self.COLOR_TEXT_LABEL)
            y_offset += 16
            draw.text((x + self.CARD_PADDING_X, y_offset), f"{intv_remain} / {intv_total}", font=self.font_usage, fill=self.COLOR_TEXT_USAGE)

            bar_x = x + self.CARD_PADDING_X
            bar_y = y_offset + 26
            bar_w = width - self.CARD_PADDING_X * 2
            bar_h = 8

            draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=4, fill=self.COLOR_PROGRESS_BG)
            fill_w = int(bar_w * min(intv_percent / 100, 1.0))
            if fill_w > 0:
                progress_color = self._get_progress_color(intv_percent)
                draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=4, fill=progress_color)

        if has_week_limit:
            y_offset = y + 80 if intv_total == 0 else y + 100
            week_remain = week_total - week_used
            week_percent = (week_remain / week_total * 100) if week_total > 0 else 0

            draw.text((x + self.CARD_PADDING_X, y_offset), f"周使用/总额", font=self.font_label, fill=self.COLOR_TEXT_LABEL)
            draw.text((x + self.CARD_PADDING_X + 75, y_offset), f"{week_remain} / {week_total}", font=self.font_usage, fill=self.COLOR_TEXT_USAGE)

            bar_x = x + self.CARD_PADDING_X
            bar_y = y_offset + 18
            bar_w = width - self.CARD_PADDING_X * 2
            bar_h = 8

            draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=4, fill=self.COLOR_PROGRESS_BG)
            fill_w = int(bar_w * min(week_percent / 100, 1.0))
            if fill_w > 0:
                draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=4, fill=self.COLOR_PROGRESS_MED)

    def draw_quota_image(self, plan_name: str, model_cards: List[Dict[str, Any]], 
                        period_text: str, week_period_text: str, reset_text: str) -> bytes:
        temp_img = Image.new("RGB", (self.IMG_WIDTH, 100), color=self.COLOR_BACKGROUND)
        draw = ImageDraw.Draw(temp_img)

        y_offset = self.PADDING

        header_h = 60
        draw.rounded_rectangle((0, y_offset, self.IMG_WIDTH, y_offset + header_h), 
                               radius=10, fill=self.COLOR_HEADER_BG)
        draw.text((self.PADDING + 10, y_offset + 15), f"MiniMax Token Plan {plan_name}", 
                  font=self.font_title, fill=self.COLOR_TEXT_TITLE)
        y_offset += header_h + self.SECTION_SPACING

        for card in model_cards:
            self._draw_card(draw, self.PADDING, y_offset, self.CARD_WIDTH,
                          card["model_name"], card["intv_used"], card["intv_total"],
                          card["intv_label"], card["week_used"], card["week_total"],
                          card["has_week_limit"])
            card_h = 120 if card["has_week_limit"] else 90
            y_offset += card_h + self.CARD_SPACING

        info_h = 75
        self._draw_rounded_rect(draw, (self.PADDING, y_offset, self.IMG_WIDTH - self.PADDING, y_offset + info_h),
                               radius=10, fill=self.COLOR_HEADER_BG)
        draw.text((self.PADDING + 15, y_offset + 10), period_text, font=self.font_label, fill=self.COLOR_TEXT_LABEL)
        draw.text((self.PADDING + 15, y_offset + 28), week_period_text, font=self.font_label, fill=self.COLOR_TEXT_LABEL)
        draw.text((self.PADDING + 15, y_offset + 46), reset_text, font=self.font_label, fill=self.COLOR_ACCENT)
        y_offset += info_h + self.SECTION_SPACING

        footer_text = "查询完成"
        bbox = draw.textbbox((0, 0), footer_text, font=self.font_footer)
        fw = bbox[2] - bbox[0]
        draw.text(((self.IMG_WIDTH - fw) // 2, y_offset + 8), footer_text, font=self.font_footer, fill=self.COLOR_FOOTER)
        y_offset += self.FOOTER_HEIGHT + self.PADDING

        img = Image.new("RGB", (self.IMG_WIDTH, y_offset), color=self.COLOR_BACKGROUND)
        draw = ImageDraw.Draw(img)

        y_offset = self.PADDING

        draw.rounded_rectangle((0, y_offset, self.IMG_WIDTH, y_offset + header_h), 
                               radius=10, fill=self.COLOR_HEADER_BG)
        draw.text((self.PADDING + 10, y_offset + 15), f"MiniMax Token Plan {plan_name}", 
                  font=self.font_title, fill=self.COLOR_TEXT_TITLE)
        y_offset += header_h + self.SECTION_SPACING

        for card in model_cards:
            self._draw_card(draw, self.PADDING, y_offset, self.CARD_WIDTH,
                          card["model_name"], card["intv_used"], card["intv_total"],
                          card["intv_label"], card["week_used"], card["week_total"],
                          card["has_week_limit"])
            card_h = 120 if card["has_week_limit"] else 90
            y_offset += card_h + self.CARD_SPACING

        self._draw_rounded_rect(draw, (self.PADDING, y_offset, self.IMG_WIDTH - self.PADDING, y_offset + info_h),
                               radius=10, fill=self.COLOR_HEADER_BG)
        draw.text((self.PADDING + 15, y_offset + 10), period_text, font=self.font_label, fill=self.COLOR_TEXT_LABEL)
        draw.text((self.PADDING + 15, y_offset + 28), week_period_text, font=self.font_label, fill=self.COLOR_TEXT_LABEL)
        draw.text((self.PADDING + 15, y_offset + 46), reset_text, font=self.font_label, fill=self.COLOR_ACCENT)
        y_offset += info_h + self.SECTION_SPACING

        draw.text(((self.IMG_WIDTH - fw) // 2, y_offset + 8), footer_text, font=self.font_footer, fill=self.COLOR_FOOTER)

        with io.BytesIO() as output:
            img.save(output, format="PNG", optimize=True)
            return output.getvalue()


def draw_quota_image(plan_name: str, model_cards: List[Dict[str, Any]], 
                     period_text: str, week_period_text: str, reset_text: str) -> bytes:
    drawer = QuotaDrawer()
    return drawer.draw_quota_image(plan_name, model_cards, period_text, week_period_text, reset_text)
