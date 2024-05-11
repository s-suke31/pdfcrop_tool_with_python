import flet as ft
import flet.canvas as cv
from pdf_manager import PDFMiner, PDFCropper
from os.path import basename

class Parameter:
    WINDOW_WIDTH         = 920
    WINDOW_HEIGHT        = 150
    WINDOW_HEIGHT_EXPAND = 750
    MIN_WINDOW_WIDTH     = 920
    MIN_WINDOW_HEIGHT    = 450
    BOTTOM_PADDING       = 230
    PATH_FIELD_WIDTH     = 650
    CROP_AREA_WIDTH      = 600
    CROP_LIST_WIDTH      = 200
    MAX_IMAGE_WIDTH      = 600

param = Parameter()

class App(ft.UserControl):
    def __init__(self, page):
        super().__init__()
        self.page = page

        self.set_page()
        self.build()

    def build(self):
        self.pdf_selector = SelectFile(self)
        self.page.add(self.pdf_selector, ft.Divider())
        self.cropping_frame = None

    def set_page(self):
        self.page.title = "Flet App"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.window_width  = param.WINDOW_WIDTH
        self.page.window_height = param.WINDOW_HEIGHT
        self.page.window_min_width  = param.MIN_WINDOW_WIDTH
        # self.page.window_min_height = param.MIN_WINDOW_HEIGHT
        self.page.update()


class SelectFile(ft.UserControl):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.pdf_path = ""
        self.is_reopen = False

    def build(self):
        def pick_files_result(e: ft.FilePickerResultEvent):
            if e.files:
                path_field.value = e.files[0].path
                path_field.update()

        def close_modal(e):
            self.is_reopen = True
            confirm_modal.open = False
            self.page.update()

        confirm_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Please confirm."),
            content=ft.Text("Do you open new file?"),
            actions=[
                ft.TextButton("Yes", on_click=close_modal),
                ft.TextButton("No", on_click=lambda x: x.page.close_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def open_pdf(e):
            load_path = path_field.value
            if load_path != "" and self.pdf_path != load_path:
                if self.master.cropping_frame is not None:
                    self.page.dialog = confirm_modal
                    confirm_modal.open = True
                    self.page.update()
                    while confirm_modal.open:
                        pass
                    if self.is_reopen:
                        self.is_reopen = False
                        self.page.controls.pop()
                    else:
                        return
                else:
                    self.master.page.window_height = param.WINDOW_HEIGHT_EXPAND
                    self.master.page.window_min_height = param.MIN_WINDOW_HEIGHT
                self.pdf_path = load_path
                self.master.cropping_frame = ImageCanvas(self, self.pdf_path)
                self.page.add(self.master.cropping_frame)
                self.update()

        path_field = ft.TextField(
            label = "Path to PDF file",
            width = param.PATH_FIELD_WIDTH,
            height = 50
        )

        load_dialog = ft.FilePicker(on_result=pick_files_result)
        self.master.page.overlay.append(load_dialog)

        return ft.Row(
            [
                path_field,
                ft.FilledButton(
                    "Select",
                    # icon=ft.icons.PICTURE_AS_PDF,
                    on_click = lambda _: load_dialog.pick_files(
                        allowed_extensions = ["pdf"],
                        allow_multiple = False
                    )
                ),
                ft.FilledButton(
                  "Open",
                  # icon=ft.icons.FILE_OPEN,
                  on_click = open_pdf
                ),
            ],
            alignment = ft.MainAxisAlignment.CENTER,
        )


class ImageCanvas(ft.UserControl):
    def __init__(self, master, pdf_path):
        super().__init__()

        if pdf_path == "": return
        self.master = master
        self.page = self.master.master.page
        self.pdf_path = pdf_path
        self.pdf_name = basename(pdf_path)

        self.miner = PDFMiner(self.pdf_path)
        self.numPages = self.miner.get_numPages()
        self.now_page = 0
        self.rec_no = 1
        self.init_image_canvas()

    def build(self):
        def page_resize(e):
            self.crop_area.height  = self.page.window_height - param.BOTTOM_PADDING
            self.crop_list.height = self.page.window_height - param.BOTTOM_PADDING
            self.update()

        def click_prev(e):
            if self.now_page > 0:
                self.now_page -= 1
                now_page_txt.value = "%d / %d" % (self.now_page+1, self.numPages)
                self.crop_area.controls[self.now_page+1].visible = False
                self.crop_area.controls[self.now_page].visible   = True
                self.update()

        def click_next(e):
            if self.now_page < self.numPages-1:
                self.now_page += 1
                now_page_txt.value = "%d / %d" % (self.now_page+1, self.numPages)
                self.crop_area.controls[self.now_page-1].visible = False
                self.crop_area.controls[self.now_page].visible   = True
                self.update()

        def get_all_areas():
            ret = []
            for i in range(len(self.canvases)):
                page_i = [i, []]
                for j in range(0, len(self.canvases[i].shapes), 2):
                    rect = self.canvases[i].shapes[j]
                    s_x, s_y = rect.x, rect.y
                    e_x, e_y = (s_x + rect.width), (s_y + rect.height)
                    if rect.width  < 0: s_x, e_x = e_x, s_x
                    if rect.height < 0: s_y, e_y = e_y, s_y
                    coords = list(map(lambda x: x / self.zoomout[i], [s_x, s_y, e_x, e_y]))
                    page_i[1].append(coords)
                ret.append(page_i)
            return ret

        def create_crop_pdf(e):
            if e.path is None: return

            save_path = e.path
            if '.pdf' not in save_path: save_path += '.pdf'

            pdfcrop = PDFCropper(self.pdf_path, save_path)
            crop_areas = get_all_areas()
            for p in crop_areas:
                npage = p[0]
                if len(p[1]) == 0:
                    # pdfcrop.notcrop(npage)
                    pass
                else:
                    for coord in p[1]:
                        pdfcrop.crop(npage, coord)
            pdfcrop.save_pdf()

        self.page.on_resize = page_resize

        self.save_dialog = ft.FilePicker(on_result=create_crop_pdf)
        self.master.master.page.overlay.append(self.save_dialog)

        now_page_txt = ft.Text(value="%d / %d" % (self.now_page+1, self.numPages), size=20)

        self.crop_area = ft.Column(
            self.image_canvas,
            width=param.CROP_AREA_WIDTH,
            height=self.page.window_height - param.BOTTOM_PADDING,
            scroll=ft.ScrollMode.ALWAYS,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        self.crop_list = ft.Column(
            width=param.CROP_LIST_WIDTH,
            height=self.page.window_height - param.BOTTOM_PADDING,
            scroll=ft.ScrollMode.ALWAYS,
            auto_scroll=True,
            spacing=0
        )

        self.save_btn = ft.FilledButton(
            "Save",
            icon=ft.icons.SAVE_AS,
            on_click=lambda _: self.save_dialog.save_file(
                allowed_extensions=["pdf"],
                file_type=ft.FilePickerFileType.CUSTOM,
                file_name=self.pdf_name.replace('.pdf', '-crop.pdf'),
            ),
            visible=False,
        )

        self.save_btn_dis = ft.FilledButton(
            "Save",
            icon=ft.icons.SAVE_AS,
            disabled=True,
            visible=True
        )

        return ft.Row(
            [
                ft.Container(
                    content=ft.Column([
                        self.crop_area,
                        ft.Row(
                            [
                                ft.FilledButton(content=ft.Icon(name=ft.icons.KEYBOARD_ARROW_LEFT), on_click=click_prev),
                                now_page_txt,
                                ft.FilledButton(content=ft.Icon(name=ft.icons.KEYBOARD_ARROW_RIGHT), on_click=click_next),
                            ],
                        ),
                    ], horizontal_alignment = ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.colors.GREY_300,
                    padding=10,
                    border_radius=10,
                ),
                ft.Container(
                    content=ft.Column([
                        self.crop_list,
                        self.save_btn,
                        self.save_btn_dis
                    ], horizontal_alignment = ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.colors.GREY_300,
                    padding=10,
                    border_radius=10,
                )
            ],
            alignment = ft.MainAxisAlignment.CENTER,
            spacing=10
        )

    def delete_area(self, info):
        l = self.crop_list.controls
        for i in range(l.index(info)+1, len(l)):
            if l[i].pg == info.pg:
                l[i].idx -= 2
        self.canvases[info.pg].shapes.pop(info.idx+1)
        self.canvases[info.pg].shapes.pop(info.idx)
        self.crop_list.controls.remove(info)
        if not self.crop_list.controls:
            self.save_btn.visible = False
            self.save_btn_dis.visible = True
            self.save_btn.update()
        self.update()

    class State:
        x: float
        y: float

    class AreaInfo(ft.UserControl):
        def __init__(self, master, idx):
            super().__init__()
            self.pg = master.now_page
            self.no = master.rec_no
            self.idx = idx
            self.delete_area = master.delete_area

            self.info_txt = ft.Text("Page.%2d  No.%2d" % (self.pg+1, self.no), width=100)

        def build(self):
            def click_delete(e):
                self.delete_area(self)

            return ft.Row([
                self.info_txt,
                ft.IconButton(
                    icon=ft.icons.DELETE_FOREVER_ROUNDED,
                    on_click=click_delete
                )
            ], alignment = ft.MainAxisAlignment.CENTER)

    def init_image_canvas(self):
        self.state = self.State()

        def pan_start(e: ft.DragStartEvent):
            self.state.x = e.local_x
            self.state.y = e.local_y
            self.canvases[self.now_page].shapes.append(
                cv.Rect(self.state.x, self.state.y, 0, 0, paint=ft.Paint(
                    color=ft.colors.with_opacity(0.4, ft.colors.PRIMARY),
                ))
            )

        def pan_update(e: ft.DragUpdateEvent):
            pg = self.now_page
            x = max(e.local_x, 0.0)
            y = max(e.local_y, 0.0)
            x = min(x, self.image_canvas[pg].width)
            y = min(y, self.image_canvas[pg].height)
            self.canvases[pg].shapes[-1].width  = (x - self.state.x)
            self.canvases[pg].shapes[-1].height = (y - self.state.y)
            self.canvases[pg].update()

        def pan_end(e: ft.DragEndEvent):
            pg = self.now_page
            rect = self.canvases[pg].shapes[-1]
            if abs(rect.width) <= 20 or abs(rect.height) <= 20:
                self.canvases[pg].shapes.pop()
            else:
                idx = len(self.canvases[pg].shapes)-1
                self.crop_list.controls.append(self.AreaInfo(self, idx))
                self.save_btn_dis.visible = False
                self.save_btn.visible = True

                s_x, s_y = rect.x, rect.y
                e_x, e_y = (s_x + rect.width), (s_y + rect.height)
                if rect.width  < 0: s_x, e_x = e_x, s_x
                if rect.height < 0: s_y, e_y = e_y, s_y
                self.canvases[pg].shapes.append(
                    cv.Text(
                        s_x+5, s_y, self.rec_no,
                        ft.TextStyle(size=16),
                        text_align=ft.TextAlign.RIGHT
                    )
                )
                self.rec_no += 1
            self.update()

        self.zoomout = [1.0] * self.numPages
        self.canvases = []
        self.image_canvas = []
        for i in range(self.numPages):
            self.canvases.append(
                cv.Canvas(
                    content=ft.GestureDetector(
                        on_pan_start=pan_start,
                        on_pan_update=pan_update,
                        on_pan_end=pan_end,
                        drag_interval=10,
                    ),
                    expand=False,
                )
            )
            img, size = self.miner.get_page(i)
            max_w = param.MAX_IMAGE_WIDTH
            if size[0] > max_w: self.zoomout[i] = max_w / size[0]
            st = ft.Stack(
                [
                    ft.Row(
                        [
                            ft.Image(src_base64=img, width=min(size[0], max_w)),
                        ],
                        alignment = ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Row([self.canvases[i]], alignment = ft.MainAxisAlignment.CENTER)
                ],
                width = min(size[0], max_w),
                height = size[1] * self.zoomout[i]
            )
            if i > 0: st.visible = False
            self.image_canvas.append(st)


def main(page: ft.Page):
    App(page)

ft.app(main)
