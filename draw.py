import io
import os
from typing import Dict, List, Any

from PIL import Image, ImageDraw, ImageFont
from astrbot.api import logger


FONT_PATH = os.path.join(os.path.dirname(__file__), "DouyinSansBold.otf")


class QuotaDrawer:
    COLOR_BACKGROUND = (255, 255, 255)
    COLOR_HEADER_BG = (245, 247, 250)
    COLOR_CARD_BG = (255, 255, 255)
    COLOR_CARD_BORDER = (220, 225, 235)
    COLOR_TEXT_TITLE = (30, 30, 30)
    COLOR_TEXT_MODEL = (0, 60, 130)
    COLOR_TEXT_USAGE = (50, 50, 50)
    COLOR_TEXT_LABEL = (120, 120, 120)
    COLOR_ACCENT = (0, 120, 220)
    COLOR_PROGRESS_BG = (230, 235, 242)
    COLOR_PROGRESS_HIGH = (60, 180, 100)
    COLOR_PROGRESS_MED = (240, 180, 60)
    COLOR_PROGRESS_LOW = (220, 60, 60)
    COLOR_FOOTER = (130, 130, 130)

    IMG_WIDTH = 800
    PADDING = 30
    CARD_PADDING_X = 20
    CARD_SPACING = 20
    CARD_CORNER_RADIUS = 14
    CARD_WIDTH = IMG_WIDTH - PADDING * 2
    SECTION_SPACING = 25
    FOOTER_HEIGHT = 40

    def __init__(self) -> None:
        self._load_fonts()

    def _load_fonts(self) -> None:
        try:
            self.font_title = ImageFont.truetype(FONT_PATH, 36)
            self.font_model = ImageFont.truetype(FONT_PATH, 20)
            self.font_usage = ImageFont.truetype(FONT_PATH, 26)
            self.font_label = ImageFont.truetype(FONT_PATH, 13)
            self.font_footer = ImageFont.truetype(FONT_PATH, 12)
        except Exception as e:
            logger.error(f"加载字体失败: {e}")
            self.font_title = ImageFont.load_default()
            self.font_model = self.font_title
            self.font_usage = self.font_title
            self.font_label = self.font_title
            self.font_footer = self.font_title

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
        card_h = 146 if has_week_limit else 100
        self._draw_rounded_rect(draw, (x, y, x + width, y + card_h), self.CARD_CORNER_RADIUS,
                                fill=self.COLOR_CARD_BG, outline=self.COLOR_CARD_BORDER, width=1)

        draw.text((x + self.CARD_PADDING_X, y + 15), model_name, font=self.font_model, fill=self.COLOR_TEXT_MODEL)

        y_offset = y + 45
        intv_remain = intv_total - intv_used
        intv_percent = (intv_remain / intv_total * 100) if intv_total > 0 else 0

        if intv_total == 0:
            draw.text((x + self.CARD_PADDING_X, y_offset), f"{intv_label}：无限额", font=self.font_label, fill=self.COLOR_TEXT_LABEL)
        else:
            draw.text((x + self.CARD_PADDING_X, y_offset), intv_label, font=self.font_label, fill=self.COLOR_TEXT_LABEL)
            percent_text = f"{intv_percent:.1f}%"
            bbox_label = draw.textbbox((0, 0), intv_label, font=self.font_label)
            label_w = bbox_label[2] - bbox_label[0]
            bbox_percent = draw.textbbox((0, 0), percent_text, font=self.font_usage)
            percent_w = bbox_percent[2] - bbox_percent[0]
            draw.text((x + width - self.CARD_PADDING_X - percent_w, y_offset), percent_text, font=self.font_usage, fill=self.COLOR_TEXT_USAGE)

            y_offset += 28
            bar_x = x + self.CARD_PADDING_X
            bar_y = y_offset
            bar_w = width - self.CARD_PADDING_X * 2
            bar_h = 10

            self._draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), 5, fill=self.COLOR_PROGRESS_BG)
            fill_w = int(bar_w * min(intv_percent / 100, 1.0))
            if fill_w > 0:
                progress_color = self._get_progress_color(intv_percent)
                self._draw_rounded_rect(draw, (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), 5, fill=progress_color)

        if has_week_limit:
            intv_end_y = y + 45 + 28 + 10
            week_start_y = intv_end_y + 15
            week_percent_y = intv_end_y + 17
            week_remain = week_total - week_used
            week_percent = (week_remain / week_total * 100) if week_total > 0 else 0

            draw.text((x + self.CARD_PADDING_X, week_start_y), "周使用/总额", font=self.font_label, fill=self.COLOR_TEXT_LABEL)
            percent_text = f"{week_percent:.1f}%"
            bbox_label = draw.textbbox((0, 0), "周使用/总额", font=self.font_label)
            label_w = bbox_label[2] - bbox_label[0]
            bbox_percent = draw.textbbox((0, 0), percent_text, font=self.font_usage)
            percent_w = bbox_percent[2] - bbox_percent[0]
            draw.text((x + width - self.CARD_PADDING_X - percent_w, week_percent_y), percent_text, font=self.font_usage, fill=self.COLOR_TEXT_USAGE)

            y_offset = week_start_y + 28
            bar_x = x + self.CARD_PADDING_X
            bar_y = y_offset
            bar_w = width - self.CARD_PADDING_X * 2
            bar_h = 10

            self._draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), 5, fill=self.COLOR_PROGRESS_BG)
            fill_w = int(bar_w * min(week_percent / 100, 1.0))
            if fill_w > 0:
                self._draw_rounded_rect(draw, (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), 5, fill=self.COLOR_PROGRESS_MED)

    def _calculate_height(self, model_cards: List[Dict]) -> int:
        header_h = 70
        info_h = 90
        card_heights = [146 if c["has_week_limit"] else 100 for c in model_cards]
        total_cards_h = sum(card_heights) + len(card_heights) * self.CARD_SPACING if card_heights else 0
        return (self.PADDING + header_h + self.SECTION_SPACING +
                total_cards_h + self.SECTION_SPACING +
                info_h + self.SECTION_SPACING +
                self.FOOTER_HEIGHT + self.PADDING)

    def _draw_all(self, draw: ImageDraw.ImageDraw, plan_name: str, model_cards: List[Dict],
                  period_text: str, week_period_text: str, reset_text: str):
        y_offset = self.PADDING

        header_h = 70
        self._draw_rounded_rect(draw, (0, y_offset, self.IMG_WIDTH, y_offset + header_h),
                               radius=12, fill=self.COLOR_HEADER_BG)
        draw.text((self.PADDING + 15, y_offset + 18), f"MiniMax Token Plan {plan_name}",
                  font=self.font_title, fill=self.COLOR_TEXT_TITLE)
        y_offset += header_h + self.SECTION_SPACING

        for card in model_cards:
            self._draw_card(draw, self.PADDING, y_offset, self.CARD_WIDTH,
                          card["model_name"], card["intv_used"], card["intv_total"],
                          card["intv_label"], card["week_used"], card["week_total"],
                          card["has_week_limit"])
            card_h = 146 if card["has_week_limit"] else 100
            y_offset += card_h + self.CARD_SPACING

        info_h = 90
        self._draw_rounded_rect(draw, (self.PADDING, y_offset, self.IMG_WIDTH - self.PADDING, y_offset + info_h),
                               radius=12, fill=self.COLOR_HEADER_BG)
        draw.text((self.PADDING + 20, y_offset + 15), period_text, font=self.font_label, fill=self.COLOR_TEXT_LABEL)
        draw.text((self.PADDING + 20, y_offset + 38), week_period_text, font=self.font_label, fill=self.COLOR_TEXT_LABEL)
        draw.text((self.PADDING + 20, y_offset + 61), reset_text, font=self.font_label, fill=self.COLOR_ACCENT)
        y_offset += info_h + self.SECTION_SPACING

        footer_text = "查询完成"
        bbox = draw.textbbox((0, 0), footer_text, font=self.font_footer)
        fw = bbox[2] - bbox[0]
        draw.text(((self.IMG_WIDTH - fw) // 2, y_offset + 10), footer_text, font=self.font_footer, fill=self.COLOR_FOOTER)

    def draw_quota_image(self, plan_name: str, model_cards: List[Dict[str, Any]], 
                        period_text: str, week_period_text: str, reset_text: str) -> bytes:
        total_height = self._calculate_height(model_cards)
        
        img = Image.new("RGB", (self.IMG_WIDTH, total_height), color=self.COLOR_BACKGROUND)
        draw = ImageDraw.Draw(img)
        
        self._draw_all(draw, plan_name, model_cards, period_text, week_period_text, reset_text)

        with io.BytesIO() as output:
            img.save(output, format="PNG", optimize=True)
            return output.getvalue()


def draw_quota_image(plan_name: str, model_cards: List[Dict[str, Any]], 
                     period_text: str, week_period_text: str, reset_text: str) -> bytes:
    drawer = QuotaDrawer()
    return drawer.draw_quota_image(plan_name, model_cards, period_text, week_period_text, reset_text)
