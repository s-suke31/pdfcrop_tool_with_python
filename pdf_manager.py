# -*- coding: utf-8 -*-
import fitz
import base64
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
        self.output_path = output_path
        self.input_pdf = fitz.open(input_path)
        self.output_pdf  = fitz.open()

    def crop(self, npage, coords):
        self.output_pdf.insert_pdf(self.input_pdf, npage, npage)
        crop_page = self.output_pdf[-1]
        cb = crop_page.cropbox
        x0 = cb.x0 + coords[0]
        y0 = cb.y0 + coords[1]
        x1 = cb.x0 + (coords[2] - coords[0])
        y1 = cb.y0 + (coords[3] - coords[1])
        crop_page.set_cropbox(fitz.Rect(x0, y0, x1, y1))

    def notcrop(self, npage):
        pass

    def save_pdf(self):
        self.output_pdf.save(self.output_path)
