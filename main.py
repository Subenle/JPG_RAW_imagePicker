      
import sys
import os
import shutil
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QFileDialog, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, 
    QComboBox, QSizePolicy, QSplitter, QTextEdit
)
from PyQt6.QtGui import QPixmap, QTransform, QShortcut, QKeySequence
from PyQt6.QtCore import Qt, QSettings
from PyQt6 import QtGui
from PIL import Image
from PIL.ExifTags import TAGS
from send2trash import send2trash

class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JPG and RAW Image Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(400, 300)

        self.settings = QSettings("io.github.subenle", "ImageViewerApp")
        self.jpg_dir = self.settings.value("jpg_dir", "")
        self.raw_dir = self.settings.value("raw_dir", "")
        self.deleted_dir = os.path.join(self.jpg_dir, "deleted_images") if self.jpg_dir else ""
        self.deleted_files = []
        self.current_pixmap = None
        self.exif_data = {}

        # 允许选择的后缀
        self.jpg_extensions = ["jpg", "jpeg", "png"]
        self.raw_extensions = ["arw", "cr2", "cr3", "dng", "nef", "raf"]

        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        # 选择目录的操作框
        dir_layout = QVBoxLayout()
        jpg_dir_layout = QHBoxLayout()
        raw_dir_layout = QHBoxLayout()

        # JPG后缀选择列表
        self.jpg_ext_list = QComboBox(self)
        self.jpg_ext_list.addItems(self.jpg_extensions)
        self.jpg_ext_list.setEditable(True)
        self.jpg_ext_list.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)

        self.jpg_dir_input = QLineEdit(self)
        self.jpg_dir_input.setPlaceholderText("Select JPG Directory")
        self.jpg_dir_input.setText(self.jpg_dir)
        jpg_button = QPushButton("Browse JPG", self)
        jpg_button.clicked.connect(self.select_jpg_directory)

        # RAW后缀选择列表
        self.raw_ext_list = QComboBox(self)
        self.raw_ext_list.addItems(self.raw_extensions)
        self.raw_ext_list.setEditable(True)
        self.raw_ext_list.setInsertPolicy(QComboBox.InsertPolicy.InsertAtBottom)

        self.raw_dir_input = QLineEdit(self)
        self.raw_dir_input.setPlaceholderText("Select RAW Directory")
        self.raw_dir_input.setText(self.raw_dir)
        raw_button = QPushButton("Browse RAW", self)
        raw_button.clicked.connect(self.select_raw_directory)

        self.delete_unexist_raw_btn = QPushButton("DeleteUnMatchedRaw", self)
        self.delete_unexist_raw_btn.clicked.connect(self.delete_unmatched_raws)
        self.delete_unexist_raw_btn.setToolTip("仅有raw，没有对应的jpg，删除raw")
        self.delete_unexist_jpg_btn = QPushButton("DeleteUnMatchedJPG", self)
        self.delete_unexist_jpg_btn.clicked.connect(self.delete_unmatched_jpgs)
        self.delete_unexist_jpg_btn.setToolTip("仅有jpg，没有对应的raw，删除jpg")

        jpg_dir_layout.addWidget(self.jpg_ext_list)
        jpg_dir_layout.addWidget(self.jpg_dir_input)
        jpg_dir_layout.addWidget(jpg_button)
        jpg_dir_layout.addWidget(self.delete_unexist_jpg_btn)

        raw_dir_layout.addWidget(self.raw_ext_list)
        raw_dir_layout.addWidget(self.raw_dir_input)
        raw_dir_layout.addWidget(raw_button)
        raw_dir_layout.addWidget(self.delete_unexist_raw_btn)

        dir_layout.addLayout(jpg_dir_layout)
        dir_layout.addLayout(raw_dir_layout)
        dir_layout.setSpacing(0)
        layout.addLayout(dir_layout)

        # layout.addLayout(jpg_dir_layout)
        # layout.addLayout(raw_dir_layout)

        image_splitter = QSplitter(Qt.Orientation.Horizontal)  # 使用水平分割器
        image_splitter.setMinimumWidth(150)  # 根据需要设置合适的最小宽度
        image_splitter.setMaximumWidth(250)  # 根据需要设置合适的最小宽度
        image_splitter.setHandleWidth(5)  # 设置分隔器的宽度，便于拖动
        image_splitter.setChildrenCollapsible(False) # 不允许子窗口折叠
        image_splitter.splitterMoved.connect(self.on_splitter_moved)

        # 设置缩略图预览宽度
        self.thumbnail_list = QListWidget(self)
        self.thumbnail_list.setMinimumWidth(150)  # 设置最小宽度
        self.thumbnail_list.itemClicked.connect(self.show_image)
        self.thumbnail_list.currentItemChanged.connect(self.update_image_display_from_list)

        if getattr(sys, 'frozen', False):
            # 如果是打包后的可执行文件
            resource_path = os.path.join(sys._MEIPASS, 'resources', 'weChat.JPEG')
        else:
            # 在开发环境中
            resource_path = os.path.join('resources', 'weChat.JPEG')
        self.money_image_label = QLabel(self)
        self.money_image_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.money_pixmap = QPixmap(resource_path)
        self.money_image_label.setPixmap(self.money_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio ))

        self.introduction = QLabel(self)
        self.introduction.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.introduction.setText('<a href="https://github.com/Subenle/JPG_RAW_imagePicker">Introduction</a>')
        self.introduction.setOpenExternalLinks(True)  # 允许打开外部链接

        thumbnail_layout = QSplitter(Qt.Orientation.Vertical)
        thumbnail_layout.setChildrenCollapsible(False) # 不允许子窗口折叠
        thumbnail_layout.addWidget(self.thumbnail_list)
        thumbnail_layout.addWidget(self.money_image_label)
        thumbnail_layout.addWidget(self.introduction)
        thumbnail_layout.setStretchFactor(0, 1)
        thumbnail_layout.setStretchFactor(1, 0)
        thumbnail_layout.setStretchFactor(2, 0)

        image_splitter.addWidget(thumbnail_layout)

        # 显示选中图像的区域
        self.image_details_layout = QVBoxLayout()

        self.filename_label = QLabel("Filename:", self)
        self.raw_filename_label = QLabel("RAW Filename: None", self)
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # 显示EXIF信息的Label
        self.exif_label = QTextEdit(self)
        self.exif_label.setReadOnly(True)  # 设置为只读
        self.exif_label.setAcceptRichText(False)  # 禁用富文本格式
        self.exif_label.setStyleSheet("border: none; background-color: transparent;")

        # 切换完整EXIF信息的按钮
        self.toggle_exif_button = QPushButton("Show Full EXIF", self)
        self.toggle_exif_button.clicked.connect(self.toggle_exif_display)

        # 新增表格用于显示完整EXIF信息
        self.exif_table = QTableWidget(self)
        self.exif_table.setColumnCount(2)
        self.exif_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.exif_table.setVisible(False)

        delete_layout = QHBoxLayout()
        self.delete_button = QPushButton("Delete Image", self)
        self.delete_button.setToolTip("删除当前选择的图片")
        self.delete_button.clicked.connect(self.delete_image)

        self.move_to_trash_button = QPushButton("MoveToTrash", self)
        self.move_to_trash_button.setToolTip("将所有已删除照片移到垃圾桶")
        self.move_to_trash_button.clicked.connect(self.move_to_trash)

        delete_layout.addWidget(self.delete_button)
        delete_layout.addWidget(self.move_to_trash_button)


        # 修改布局间距
        # self.image_details_layout.setSpacing(10)  # 设置上下组件间距为5像素

        self.image_details_layout.addWidget(self.filename_label)
        self.image_details_layout.addWidget(self.raw_filename_label)
        self.image_details_layout.addWidget(self.image_label)
        self.image_details_layout.addWidget(self.exif_label)
        self.image_details_layout.addWidget(self.toggle_exif_button)
        self.image_details_layout.addWidget(self.exif_table)
        self.image_details_layout.addLayout(delete_layout)
        # self.image_details_layout.addStretch(1)
        image_details_widget = QWidget()

        # image_layout.addLayout(self.image_details_layout)
        image_details_widget.setLayout(self.image_details_layout)
        # image_details_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        image_splitter.addWidget(image_details_widget)
        image_splitter.setStretchFactor(0, 0)  # 缩略图部件
        image_splitter.setStretchFactor(1, 1)  # 详细信息部件
        image_splitter.setOpaqueResize(True)
        # layout.addLayout(image_layout)
        layout.addWidget(image_splitter)

        # 连接 Enter 键事件
        self.jpg_dir_input.returnPressed.connect(self.on_jpg_input_enter)
        self.raw_dir_input.returnPressed.connect(self.on_raw_input_enter)

        delete_shortcut = QShortcut(QKeySequence("Backspace"), self)
        delete_shortcut.activated.connect(self.delete_image)

        self.resize(800, 600)
        if self.jpg_dir != "":
            self.update_jpg_directory(self.jpg_dir)


    def update_jpg_directory(self, new_dir):
        if os.path.exists(new_dir):
            self.jpg_dir = new_dir
            self.jpg_dir_input.setText(self.jpg_dir)
            self.deleted_dir = os.path.join(self.jpg_dir, "deleted_images")
            if not os.path.exists(self.deleted_dir):
                os.makedirs(self.deleted_dir)
            self.raw_dir = self.raw_dir or self.jpg_dir  # 如果 raw_dir 为空，设置为 jpg_dir
            self.raw_dir_input.setText(self.raw_dir)
            self.load_thumbnails()
        else:
            QMessageBox.warning(self, "Invalid Directory", "The JPG directory does not exist.")

    def update_raw_directory(self, new_dir):
        if os.path.exists(new_dir):
            self.raw_dir = new_dir
            self.raw_dir_input.setText(self.raw_dir)
        else:
            QMessageBox.warning(self, "Invalid Directory", "The RAW directory does not exist.")

    def on_jpg_input_enter(self):
        new_dir = self.jpg_dir_input.text()
        self.update_jpg_directory(new_dir)

    def on_raw_input_enter(self):
        new_dir = self.raw_dir_input.text()
        self.update_raw_directory(new_dir)

    def select_jpg_directory(self):
        jpg_dir = QFileDialog.getExistingDirectory(self, "Select JPG Directory", self.jpg_dir)
        if jpg_dir:
            self.update_jpg_directory(jpg_dir)

    def select_raw_directory(self):
        raw_dir = QFileDialog.getExistingDirectory(self, "Select RAW Directory", self.raw_dir)
        if raw_dir:
            self.update_raw_directory(raw_dir)

    def load_thumbnails(self):
        self.thumbnail_list.clear()
        if not self.jpg_dir:
            return

        # 获取选中的 JPG 后缀
        jpg_extension = self.jpg_ext_list.currentText()

        for file in os.listdir(self.jpg_dir):
            if file.lower().endswith(jpg_extension.lower()):
                self.thumbnail_list.addItem(file)

    def toggle_exif_display(self):
        if self.exif_table.isVisible():
            self.exif_table.setVisible(False)
            self.toggle_exif_button.setText("Show Full EXIF")
        else:
            self.populate_exif_table()
            self.exif_table.setVisible(True)
            self.toggle_exif_button.setText("Hide Full EXIF")

    def populate_exif_table(self):
        self.exif_table.setRowCount(len(self.exif_data))
        for row, (key, value) in enumerate(self.exif_data.items()):
            self.exif_table.setItem(row, 0, QTableWidgetItem(key))
            self.exif_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def show_image(self, item):
        filename = item.text()
        full_path = os.path.join(self.jpg_dir, filename)
        self.filename_label.setText(f"Filename: {filename}")
        # print(os.path.join(self.jpg_dir, filename), flush=True)

        # 获取选中的 RAW 后缀
        raw_extension = self.raw_ext_list.currentText()
        raw_found = False
        raw_filename = os.path.splitext(filename)[0]+f".{raw_extension}"
        # print(f"raw filename with ext: {raw_filename} ", flush=True)

        # 查找对应的 RAW 文件

        if os.path.exists(os.path.join(self.raw_dir, raw_filename)):
            raw_found = True

        if raw_found:
            self.raw_filename_label.setStyleSheet("color: black;")
            self.raw_filename_label.setText(f"RAW Filename: {raw_filename}")
        else:
            self.raw_filename_label.setStyleSheet("color: red;")
            self.raw_filename_label.setText("RAW Filename: None")

        self.exif_data = self.get_exif(full_path)
        image_orientation = self.exif_data.get("Orientation", 1)
        
        self.current_pixmap = QPixmap(full_path)
        if image_orientation != 1:
            self.current_pixmap = self.current_pixmap.transformed(QTransform().rotate(90*(image_orientation-1)))
        self.update_image_display()

        self.display_basic_exif_info()

    def update_image_display(self):
        if self.current_pixmap:
            scaled_pixmap = self.current_pixmap.scaled(self.image_label.size(), 
                                                        Qt.AspectRatioMode.KeepAspectRatio, 
                                                        Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        # 当窗口调整大小时更新图像显示
        super().resizeEvent(event)
        self.image_label.updateGeometry()
        self.update_image_display()
        

    def display_basic_exif_info(self):
        basic_info = [
            # line 1
            ("Make", self.exif_data.get("Make", "N/A")),
            ("Model", self.exif_data.get("Model", "N/A")),
            ("DateTimeOriginal", self.exif_data.get("DateTimeOriginal", "N/A")),
            ("ExifImageWidth", self.exif_data.get("ExifImageWidth", "N/A")),
            ("ExifImageHeight", self.exif_data.get("ExifImageHeight", "N/A")),
            # line 2
            ("FocalLengthIn35mmFilm", self.exif_data.get("FocalLengthIn35mmFilm", "N/A")),
            ("FNumber", self.exif_data.get("FNumber", "N/A")),
            ("ExposureTime", self.exif_data.get("ExposureTime", "N/A")),
            ("ISOSpeedRatings", self.exif_data.get("ISOSpeedRatings", "N/A")),
            
        ]
        exif_text = "" # "\n".join(f"{key}: {value}" for key, value in basic_info)
        for key, value in basic_info:
            if key == "ExifImageHeight":
                exif_text += f"x {value}\n"
            elif key == "FocalLengthIn35mmFilm":
                exif_text += f"{value}mm "
            elif key == "FNumber":
                exif_text += f"f/{value} "
            elif key == "ExposureTime":
                if value == "N/A":
                    exif_text += f"N/A "
                else:
                    exposureTime = 1 / value
                    exif_text += f"1/{exposureTime} "
            elif key == "ISOSpeedRatings":
                exif_text += f"ISO{value}"
            else:
                exif_text += f"{value} "
        self.update_exif_text(f"EXIF Info:\n{exif_text}")

    def update_exif_text(self, exif_text):
        self.exif_label.setPlainText(exif_text)  # 设置文本
        self.adjust_text_edit_height()  # 调整高度

    def adjust_text_edit_height(self):
        # 获取内容高度并设置为QTextEdit的高度
        height = self.exif_label.document().size().height() + 5  # 加10以添加一些边距
        self.exif_label.setFixedHeight(int(height))

    def get_exif(self, img_path):
        exif_data = {}
        try:
            image = Image.open(img_path)
            if hasattr(image, '_getexif'):
                exif_info = image._getexif()
                if exif_info is not None:
                    for tag, value in exif_info.items():
                        tag_name = TAGS.get(tag, tag)
                        exif_data[tag_name] = value
                    
                        # exif_text += f"{tag_name} : {value} \n"
                        # if tag_name != "MakerNote":
                        #     print(f"{tag_name} : {value}", flush=True)
        except Exception as e:
            print(f"Error retrieving EXIF data: {e}")
        return exif_data

    def delete_image(self):
        reply = QMessageBox.question(self, 'Message',
                                       "Are you sure you want to DELETE?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
        current_item = self.thumbnail_list.currentItem()
        if current_item:
            filename = current_item.text()
            full_path = os.path.join(self.jpg_dir, filename)
            if os.path.exists(full_path):
                shutil.move(full_path, self.deleted_dir)
                self.thumbnail_list.takeItem(self.thumbnail_list.currentRow())
                # QMessageBox.information(self, "Deleted", f"{filename} has been moved to deleted_images.")
            else:
                QMessageBox.warning(self, "Error", f"{filename} File does not exist.")

            raw_filename = os.path.splitext(filename)[0]+f".{self.raw_ext_list.currentText()}"
            raw_full_path = os.path.join(self.raw_dir, raw_filename)
            if os.path.exists(raw_full_path):
                shutil.move(raw_full_path, self.deleted_dir)
                # self.thumbnail_list.takeItem(self.thumbnail_list.currentRow())
                # QMessageBox.information(self, "Deleted", f"{raw_filename} has been moved to deleted_images.")
            else:
                QMessageBox.warning(self, "Error", f"{raw_filename} File does not exist.")

    def delete_unmatched_raws(self):
        if not self.jpg_dir:
            QMessageBox.warning(self, "Error", f"jpg dir is not set")
            pass # 警告

        if not self.raw_dir:
            QMessageBox.warning(self, "Error", f"raw dir is not set")
            pass
        # 获取jpg文件名（不包括扩展名）
        jpg_files = {os.path.splitext(f)[0] for f in os.listdir(self.jpg_dir) if f.lower().endswith(self.jpg_ext_list.currentText().lower())}
        to_be_deleted_files = []
        matched_files_count = 0
        # 遍历raw目录中的文件，检查是否有匹配的jpg文件
        for raw_file in os.listdir(self.raw_dir):
            if raw_file.lower().endswith(self.raw_ext_list.currentText().lower()):
                raw_filename = os.path.splitext(raw_file)[0]
                if raw_filename not in jpg_files:
                    # 没有对应的jpg文件，将raw文件移动到deleted_dir
                    to_be_deleted_files.append(raw_file)
                else:
                    matched_files_count += 1

        message = f"MatchedFiles    : {matched_files_count}\n ToBeDeletedFiles: {len(to_be_deleted_files)}\n DELETE?"
        reply = QMessageBox.question(self, 'Message',
           message,
           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        for raw_file in to_be_deleted_files:
            raw_path = os.path.join(self.raw_dir, raw_file)
            shutil.move(raw_path, self.deleted_dir)
            # print(f'Moved {raw_file} to {self.deleted_dir}')

    def delete_unmatched_jpgs(self):
        # 获取raw文件名（不包括扩展名）
        raw_files = {os.path.splitext(f)[0] for f in os.listdir(self.raw_dir) if f.lower().endswith(self.raw_ext_list.currentText().lower())}
        
        to_be_deleted_files = []
        matched_files_count = 0
        # 遍历jpg目录中的文件，检查是否有匹配的raw文件
        for jpg_file in os.listdir(self.jpg_dir):
            if jpg_file.lower().endswith(self.jpg_ext_list.currentText().lower()):
                jpg_filename = os.path.splitext(jpg_file)[0]
                if jpg_filename not in raw_files:
                    # 没有对应的raw文件，将jpg文件移动到deleted_dir
                    to_be_deleted_files.append(jpg_file)
                else:
                    matched_files_count += 1

        message = f"MatchedFiles    : {matched_files_count}\n ToBeDeletedFiles: {len(to_be_deleted_files)}\n DELETE?"
        reply = QMessageBox.question(self, 'Message',
           message,
           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        for jpg_file in to_be_deleted_files:
            raw_path = os.path.join(self.jpg_dir, jpg_file)
            shutil.move(raw_path, self.deleted_dir)
            # print(f'Moved {jpg_file} to {self.deleted_dir}')

        self.load_thumbnails()


    def on_splitter_moved(self, pos, index):
        # pos 是新位置，index 是移动的 widget 的索引
        thumbnail_size = self.thumbnail_list.size()  # 获取缩略图列表的当前尺寸
        image_details_size = self.image_label.size()  # 获取详细信息部分的当前尺寸
        self.image_label.updateGeometry()
        self.update_image_display()

    def update_image_display_from_list(self, current, previous):
        if current:
            self.show_image(current)  # 使用当前选中的项更新图像

    def move_to_trash(self):
        normpath = os.path.normpath(self.deleted_dir)
        message = f"DELETE {normpath} ?"
        reply = QMessageBox.question(self, 'Message',
           message,
           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        if os.path.exists(normpath):
            send2trash(normpath)
        pass
        
    def closeEvent(self, event):
        self.jpg_dir = self.settings.setValue("jpg_dir", self.jpg_dir)
        self.raw_dir = self.settings.setValue("raw_dir", self.raw_dir)
        # reply = QMessageBox.question(self, 'Message',
        #                                "Are you sure you want to quit?",
        #                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        # if reply == QMessageBox.StandardButton.Yes:
        #     event.accept()  # 允许窗口关闭
        # else:
        #     event.ignore()  # 忽略关闭事件

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = ImageViewer()
    viewer.show()
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        icon_path = os.path.join(sys._MEIPASS, 'resources', 'icon.ico')
    else:
        # 在开发环境中
        icon_path = os.path.join('resources', 'icon.ico')
    app.setWindowIcon(QtGui.QIcon(icon_path))
    viewer.setWindowIcon(QtGui.QIcon(icon_path))
    sys.exit(app.exec())

    