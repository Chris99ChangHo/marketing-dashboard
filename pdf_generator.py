# pdf_generator.py: PDF generation utilities for the backend application
#
# This module encapsulates all logic related to generating PDF reports.
# It handles the conversion of HTML content to PDF, dynamic creation of
# cover images, and generation of chart images from data. It integrates
# various libraries to provide comprehensive PDF reporting capabilities,
# including multi-language font support and image processing.
#
# Dependencies:
# - xhtml2pdf (for HTML to PDF conversion)
# - reportlab (for font registration)
# - PIL (Pillow, for image manipulation)
# - matplotlib.pyplot, pandas, seaborn, numpy (for chart generation)
# - Standard library modules: os, io, logging, base64, tempfile, pathlib
# - Internal modules: config (for font paths)
#
# Key Functions:
# - FontManager class: Manages font files, validates their existence, provides
#   a font finder for xhtml2pdf, and sets up fonts for matplotlib.
# - _fit_and_crop_center(): Helper for image scaling and cropping.
# - _resolve_canvas(): Helper for determining canvas size and preparing background for text rendering.
# - generate_cover_image_base64(): Generates the front cover image with dynamic text.
# - generate_back_cover_image_base64(): Generates the back cover image with contact information.
# - create_chart_image_base64(): Generates various chart images (bar, donut,
#   comparison bar) and returns them as Base64 strings.
# - generate_pdf_from_html(): The main function to convert HTML content into a PDF,
#   handling font registration and linking.

import os
import io
import logging
import base64
import tempfile
from pathlib import Path
from xhtml2pdf import pisa
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from config import FONT_BASE_PATH, FONT_PATHS

# Logger configuration
logger = logging.getLogger(__name__)

# Set environment variables for multi-threaded libraries
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'

# Set temporary directory for xhtml2pdf
TEMP_DIR = tempfile.mkdtemp()
os.environ['XHTML2PDF_TEMP_DIR'] = TEMP_DIR
logger.info(f"XHTML2PDF_TEMP_DIR set to: {TEMP_DIR}")

# Set Matplotlib backend to 'Agg' for non-interactive environments
plt.switch_backend('Agg')

# ====================================================================================================
# FontManager Class
# ====================================================================================================

class FontManager:
    """Class to manage font files for PDF and image generation."""

    def __init__(self):
        self.font_base_path = FONT_BASE_PATH
        self.font_paths = FONT_PATHS
        self._validated = False

    def validate_fonts(self):
        """Verifies the existence of font files."""
        if self._validated:
            return True

        missing_fonts = []
        for font_name, font_path in self.font_paths.items():
            if not font_path.exists():
                missing_fonts.append(f"{font_name}: {font_path}")

        if missing_fonts:
            logger.error(f"Missing font files: {missing_fonts}")
            return False

        self._validated = True
        logger.info(f"All fonts validated successfully at: {self.font_base_path}")
        return True

    def get_font_finder(self):
        """Returns a font finder function for xhtml2pdf."""
        def font_finder(uri, rel):
            # Only handle font files, ignore others (like base64 images)
            if uri.lower().endswith(('.ttf', '.otf')):
                if uri.startswith('file://'):
                    return uri[7:]
                if os.path.isabs(uri):
                    return uri

                # Try to resolve relative paths based on the font base path
                font_path = self.font_base_path / Path(uri).name
                if font_path.exists():
                    logger.info(f"[FONT] Resolved via callback: {uri} -> {font_path}")
                    return str(font_path)

                logger.warning(f"[FONT] Callback could not resolve font: {uri}")
            
            # For all other URIs (including base64), return them as is
            return uri
        return font_finder

    def setup_matplotlib_font(self):
        """Configures the font for Matplotlib."""
        try:
            noto_sans_path = self.font_paths['noto_sans_kr']
            if noto_sans_path.exists():
                from matplotlib.font_manager import fontManager
                fontManager.addfont(str(noto_sans_path))
                plt.rcParams['font.family'] = 'Noto Sans KR'
                logger.info(f"[CHART] Matplotlib font set to Noto Sans KR: {noto_sans_path}")
                return True
        except Exception as e:
            logger.warning(f"Could not set Matplotlib font to Noto Sans KR: {e}")
            
        # Fallback font
        plt.rcParams['font.family'] = 'DejaVu Sans'
        return False

# Global FontManager instance
font_manager = FontManager()

# ====================================================================================================
# Helper utilities for image scaling/cropping
# ====================================================================================================

def _fit_and_crop_center(img, target_w, target_h):
    """
    Scale image to cover target size while preserving aspect ratio, then center-crop.
    Similar to CSS background-size: cover + background-position: center.
    """
    src_w, src_h = img.size
    if src_w == 0 or src_h == 0:
        return img.resize((target_w, target_h), Image.LANCZOS)

    src_ratio = src_w / src_h
    tgt_ratio = target_w / target_h

    if src_ratio > tgt_ratio:
        # Source is wider -> fit by height, then crop width
        scale = target_h / src_h
        new_w = int(round(src_w * scale))
        new_h = target_h
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - target_w) // 2
        box = (left, 0, left + target_w, target_h)
        return resized.crop(box)
    else:
        # Source is taller or equal/narrower -> fit by width, then crop height
        scale = target_w / src_w
        new_w = target_w
        new_h = int(round(src_h * scale))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        top = (new_h - target_h) // 2
        box = (0, top, target_w, top + target_h)
        return resized.crop(box)

def _resolve_canvas(img, target_size=None, scale=None, fit_mode="cover"):
    """
    Decide final canvas size and produce background raster prepared for text rendering.
    - target_size=(w,h) in px has priority.
    - else, scale factor applies.
    - fit_mode: "cover" (preserve aspect ratio, fill, center-crop) or "stretch" (resample to exact size).
    Returns: (canvas_image_rgba, width, height, scale_factor_for_typography)
    """
    orig_w, orig_h = img.size
    if target_size is not None:
        tgt_w, tgt_h = int(target_size[0]), int(target_size[1])
        tgt_w = max(1, tgt_w)
        tgt_h = max(1, tgt_h)
        if fit_mode == "cover":
            fitted = _fit_and_crop_center(img, tgt_w, tgt_h)
        else:
            fitted = img.resize((tgt_w, tgt_h), Image.LANCZOS)
        # Use min of width/height scale as typography scale to avoid over-scaling in extreme aspect changes
        scale_w = tgt_w / max(orig_w, 1)
        scale_h = tgt_h / max(orig_h, 1)
        scale_factor = min(scale_w, scale_h)
        return fitted.convert("RGBA"), tgt_w, tgt_h, scale_factor
    elif scale is not None and scale > 0:
        new_w = max(1, int(round(orig_w * scale)))
        new_h = max(1, int(round(orig_h * scale)))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        return resized.convert("RGBA"), new_w, new_h, float(scale)
    else:
        return img.convert("RGBA"), orig_w, orig_h, 1.0

def _scaled_pt(pt, scale_factor):
    return max(1, int(pt * 1.333333 * scale_factor))

def _scaled_px(px, scale_factor):
    return max(1, int(px * scale_factor))

def _scaled_stroke(px, scale_factor):
    return max(1, int(px * scale_factor))

# ====================================================================================================
# Pillow-based Image Generation Functions
# ====================================================================================================

def generate_cover_image_base64(
    base_image_base64,
    client_name,
    report_title,
    domain,
    period,
    target_size=None,     # e.g., (4770, 3318) for A3 landscape content area @300dpi
    scale=None,           # alternatively, a scalar like 2.0
    fit_mode="cover",     # "cover" (recommended) or "stretch"
    overlay_alpha=0.3     # 0.0~1.0
):
    """
    Generate a cover image:
    - Prepare background by scaling to target_size (or scale), preserving ratio ("cover") and center-cropping.
    - Apply semi-transparent overlay.
    - Render texts with typography scaled to canvas.
    """
    try:
        img_data = base64.b64decode(base_image_base64)
        bg = Image.open(io.BytesIO(img_data))

        canvas, width, height, scale_factor = _resolve_canvas(
            bg, target_size=target_size, scale=scale, fit_mode=fit_mode
        )

        # Overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, int(255 * overlay_alpha)))
        canvas = Image.alpha_composite(canvas, overlay)

        draw = ImageDraw.Draw(canvas)

        # Fonts
        try:
            font_path = str(font_manager.font_paths['noto_sans_kr'])
            font_client = ImageFont.truetype(font_path, _scaled_pt(42, scale_factor))
            font_title  = ImageFont.truetype(font_path, _scaled_pt(46, scale_factor))
            font_domain = ImageFont.truetype(font_path, _scaled_pt(30, scale_factor))
            font_period = ImageFont.truetype(font_path, _scaled_pt(26, scale_factor))
        except IOError:
            logger.warning("Font file not found, using default font.")
            font_client = ImageFont.load_default()
            font_title  = ImageFont.load_default()
            font_domain = ImageFont.load_default()
            font_period = ImageFont.load_default()

        # Spacing and strokes
        gap_20 = _scaled_px(20, scale_factor)
        gap_30 = _scaled_px(30, scale_factor)
        gap_15 = _scaled_px(15, scale_factor)
        stroke_2 = _scaled_stroke(2, scale_factor)
        stroke_1 = _scaled_stroke(1, scale_factor)

        # Measure
        client_bbox = draw.textbbox((0, 0), client_name, font=font_client)
        title_bbox  = draw.textbbox((0, 0), report_title, font=font_title)
        domain_bbox = draw.textbbox((0, 0), domain, font=font_domain)
        period_bbox = draw.textbbox((0, 0), period, font=font_period)

        total_h = (client_bbox[3]-client_bbox[1]) + gap_20 + \
                  (title_bbox[3]-title_bbox[1])  + gap_30 + \
                  (domain_bbox[3]-domain_bbox[1]) + gap_15 + \
                  (period_bbox[3]-period_bbox[1])

        start_y = (height - total_h) / 2

        def draw_centered(y, text, font, fill, stroke_w, stroke_fill):
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2]-bbox[0]
            x = (width - tw) / 2
            draw.text((x, y), text, font=font, fill=fill,
                      stroke_width=stroke_w, stroke_fill=stroke_fill)
            return bbox[3]-bbox[1]

        y = start_y
        y += draw_centered(y, client_name, font_client, (255, 255, 255), stroke_2, (34, 34, 34)) + gap_20
        y += draw_centered(y, report_title, font_title, (255, 255, 255), stroke_2, (34, 34, 34)) + gap_30
        y += draw_centered(y, domain, font_domain, (238, 238, 238), stroke_1, (17, 17, 17)) + gap_15
        draw_centered(y, period, font_period, (204, 204, 204), stroke_1, (34, 34, 34))

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    except Exception as e:
        logger.error(f"Error generating cover image: {e}", exc_info=True)
        return None

def generate_back_cover_image_base64(
    base_image_base64,
    contact_info,
    target_size=None,   # e.g., (4770, 3318)
    scale=None,
    fit_mode="cover",   # "cover" (recommended) or "stretch"
    overlay_alpha=0.4
):
    """
    Generate a back cover image:
    - Background prepared with ratio-preserving cover+center-crop to target_size (or scale).
    - Apply overlay, then render multiline contact text centered.
    """
    try:
        img_data = base64.b64decode(base_image_base64)
        bg = Image.open(io.BytesIO(img_data))

        canvas, width, height, scale_factor = _resolve_canvas(
            bg, target_size=target_size, scale=scale, fit_mode=fit_mode
        )

        overlay = Image.new('RGBA', (width, height), (0, 0, 0, int(255 * overlay_alpha)))
        canvas = Image.alpha_composite(canvas, overlay)

        draw = ImageDraw.Draw(canvas)

        try:
            font_path = str(font_manager.font_paths['noto_sans_kr'])
            font_contact = ImageFont.truetype(font_path, _scaled_pt(28, scale_factor))
        except IOError:
            logger.warning("Font file not found, using default font.")
            font_contact = ImageFont.load_default()

        lines = contact_info.split('\n')
        line_height_multiplier = 1.6
        stroke_1 = _scaled_stroke(1, scale_factor)

        # Measure lines
        line_heights = []
        line_widths = []
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_contact)
            line_heights.append(bbox[3]-bbox[1])
            line_widths.append(bbox[2]-bbox[0])

        spacing = int(line_heights[0] * (line_height_multiplier - 1)) if line_heights else 0
        total_h = sum(line_heights) + max(0, len(lines)-1) * spacing
        y = (height - total_h) / 2

        for i, line in enumerate(lines):
            lw = line_widths[i]
            x = (width - lw) / 2
            draw.text((x, y), line, font=font_contact,
                      fill=(255, 255, 255),
                      stroke_width=stroke_1, stroke_fill=(34, 34, 34))
            y += line_heights[i] + (spacing if i < len(lines)-1 else 0)

        buf = io.BytesIO()
        canvas.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')

    except Exception as e:
        logger.error(f"Error generating back cover image: {e}", exc_info=True)
        return None

# ====================================================================================================
# Chart Generation Function
# ====================================================================================================

def create_chart_image_base64(current_data, previous_data=None, chart_type='bar', title='', figsize=(11, 5.5), y_label='', show_percentage=False, colors=None):
    """Generates a chart and returns its Base64 string."""
    if not current_data and not previous_data:
        return None
    if chart_type == 'comparison_bar' and (not current_data or not previous_data):
        logger.warning(f"Comparison chart requested for '{title}' but current or previous data is missing.")
        return None
    if chart_type == 'donut' and not current_data:
        logger.warning(f"Donut chart requested for '{title}' but current_data is missing.")
        return None

    font_manager.setup_matplotlib_font()
    plt.rcParams['axes.unicode_minus'] = False

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=figsize)

    if chart_type == 'bar':
        labels = list(current_data.keys())
        values = list(current_data.values())
        palette = colors if colors else sns.color_palette("pastel", len(labels))
        bars = sns.barplot(x=labels, y=values, ax=ax, palette=palette)
        ax.set_ylabel(y_label)
        ax.set_xlabel('')
        ax.bar_label(bars.containers[0], fmt='%.0f', fontsize=10, color='black')

    elif chart_type == 'donut':
        labels = list(current_data.keys())
        values = list(current_data.values())

        if sum(values) == 0:
            return None

        filtered_data = {label: value for label, value in current_data.items() if value > 0}
        labels = list(filtered_data.keys())
        values = list(filtered_data.values())

        if colors:
            palette = colors[:len(labels)]
        else:
            custom_colors = ['#4285F4', '#808080', '#FFA500', '#9370DB', '#A9A9A9']
            palette = custom_colors[:len(labels)]

        def autopct_format_func(pct, values):
            absolute_value = int(pct/100.*sum(values))
            if pct < 1.0 or absolute_value == 0:
                return ""
            return f"{pct:.1f}%"

        wedges, texts, autotexts = ax.pie(
            values,
            autopct=lambda pct: autopct_format_func(pct, values),
            startangle=90,
            colors=palette,
            wedgeprops=dict(width=0.4, edgecolor='white'),
            pctdistance=0.85
        )

        for autotext in autotexts:
            if autotext.get_text() != "":
                autotext.set_color('black')
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')

        plt.axis('equal')
        fig.legend(wedges, labels, loc="lower center", bbox_to_anchor=(0.5, -0.1),
                   title="Sources", frameon=False, fontsize=12, ncol=len(labels))
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20, loc='center')
        fig.subplots_adjust(bottom=0.2)
        plt.tight_layout()

    elif chart_type == 'comparison_bar':
        labels = list(current_data.keys())
        current_values = list(current_data.values())
        previous_values = [previous_data.get(label, 0) for label in labels]

        x = np.arange(len(labels))
        width = 0.35

        bars1 = ax.bar(x - width/2, previous_values, width, label='Previous Period', color='#FFD700')
        bars2 = ax.bar(x + width/2, current_values, width, label='Current Period', color='#20B2AA')

        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.set_ylabel(y_label)
        ax.set_xlabel('')
        ax.bar_label(bars1, fmt='%.0f', fontsize=10, color='black')
        ax.bar_label(bars2, fmt='%.0f', fontsize=10, color='black')
        ax.legend(title='', loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=2, frameon=False)
        ax.set_title(title, fontsize=16, fontweight='bold', pad=40)
        plt.tight_layout(rect=[0, 0, 1, 0.95])

    else:
        ax.set_title(title, fontsize=16, fontweight='bold', pad=40)
        plt.tight_layout(rect=[0, 0, 1, 1])

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    buf.seek(0)

    return base64.b64encode(buf.getvalue()).decode('utf-8')

# ====================================================================================================
# PDF Generation Function
# ====================================================================================================

def generate_pdf_from_html(html_content):
    """Converts HTML to PDF, including font management."""
    pdf_buffer = io.BytesIO()

    try:
        if not font_manager.validate_fonts():
            logger.warning("Some fonts are missing, PDF generation may have font issues.")

        # Register fonts with xhtml2pdf
        font_mappings = {
            'noto_sans': 'NotoSans-Regular',
            'noto_sans_kr': 'NotoSansKR-Regular',
            'noto_sans_sc': 'NotoSansSC-Regular',
        }

        for font_key, css_font_name in font_mappings.items():
            font_path_obj = FONT_PATHS.get(font_key)
            if font_path_obj and font_path_obj.exists():
                try:
                    pdfmetrics.registerFont(TTFont(css_font_name, str(font_path_obj)))
                    logger.debug(f"[FONT REGISTER] Registered {css_font_name} via pdfmetrics: {font_path_obj}")
                except Exception as e:
                    logger.error(f"[FONT REGISTER ERROR] Failed to register font {css_font_name} ({font_path_obj}): {e}")
            else:
                logger.warning(f"[FONT REGISTER] Font file not found for registration: {font_key} at {font_path_obj}")

        # PDF creation
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_buffer,
            encoding='utf-8',
            link_callback=font_manager.get_font_finder()
        )

        if pisa_status.err:
            logger.error(f"PDF generation error: {pisa_status.err}")
            raise Exception("Could not generate PDF from HTML.")

        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()

    except Exception as e:
        logger.error(f"Error generating PDF from HTML: {e}", exc_info=True)
        raise
    finally:
        pdf_buffer.close()

def generate_pdf_report(data, ga4_data, seranking_data, selected_client):
    """
    This function is no longer used.
    Use generate_pdf_from_html instead.
    """
    raise NotImplementedError("Use generate_pdf_from_html instead")
