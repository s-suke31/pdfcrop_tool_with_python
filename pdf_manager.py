# -*- coding: utf-8 -*-
import fitz
import base64
from pypdf import PdfReader, PdfWriter
from PIL import Image
from io import BytesIO

class PDFMiner():
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.pdf      = fitz.open(self.pdf_path)

    def get_numPages(self):
        return self.pdf.page_count

    def get_page(self, page_no):
        page = self.pdf.load_page(page_no)
        pix  = page.get_pixmap()
        px1  = fitz.Pixmap(pix, 0) if pix.alpha else pix
        img  = px1.tobytes("PNG")

        binary = BytesIO(img)
        pil_img = Image.open(binary)
        buffer = BytesIO()
        pil_img.save(buffer, "png")
        img_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")

        return img_b64, (page.rect.width, page.rect.height)

class PDFCropper():
    def __init__(self, input_path, output_path):
        self.input_path  = input_path
        self.output_path = output_path
        self.output_pdf  = PdfWriter()

    def crop(self, npage, coords):
        self.input_pdf = PdfReader(self.input_path)
        crop_page = self.input_pdf.pages[npage]
        height = crop_page.cropbox.upper_right[1] - crop_page.cropbox.lower_left[1]

        base = crop_page.cropbox.lower_left
        lower_left  = (coords[0] + base[0], height - coords[3] + base[1])
        upper_right = (coords[2] + base[0], height - coords[1] + base[1])

        crop_page.trimbox.lower_left  = lower_left
        crop_page.trimbox.upper_right = upper_right
        crop_page.cropbox.lower_left  = lower_left
        crop_page.cropbox.upper_right = upper_right

        self.output_pdf.add_page(crop_page)

    def notcrop(self, npage):
        page = self.input_pdf.pages[npage]
        self.output_pdf.add_page(page)

    def save_pdf(self):
        with open(self.output_path, "wb") as fp:
            self.output_pdf.write(fp)
