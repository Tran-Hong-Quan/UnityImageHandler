import sys, os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QCheckBox, QPushButton, QMessageBox, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PIL import Image
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# ===== Image processing =====
import numpy as np
from PIL import Image

def ensure_divisible_by_4(img: Image.Image) -> Image.Image:
    w, h = img.size
    new_w = w + (4 - w % 4) if w % 4 != 0 else w
    new_h = h + (4 - h % 4) if h % 4 != 0 else h

    if new_w == w and new_h == h:
        return img

    arr = np.array(img)

    # Nếu là ảnh 1 kênh → chuyển thành dạng 3 chiều
    if len(arr.shape) == 2:
        arr = arr[:, :, np.newaxis]

    h_pad = new_h - h
    w_pad = new_w - w

    # Pad hàng dưới bằng cách lặp hàng cuối
    if h_pad > 0:
        last_row = arr[-1:, :, :]
        pad_bottom = np.repeat(last_row, h_pad, axis=0)
        arr = np.concatenate([arr, pad_bottom], axis=0)

    # Pad cột phải bằng cách lặp cột cuối
    if w_pad > 0:
        last_col = arr[:, -1:, :]
        pad_right = np.repeat(last_col, w_pad, axis=1)
        arr = np.concatenate([arr, pad_right], axis=1)

    # Nếu ảnh grayscale thì bỏ chiều dư
    arr = arr.squeeze() if arr.shape[2] == 1 else arr

    return Image.fromarray(arr.astype(np.uint8), mode=img.mode)


def process_image(path, scale, force_div4):
    try:
        img = Image.open(path)
        if scale < 1.0:
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)
        if force_div4:
            img = ensure_divisible_by_4(img)
        img.save(path)
        print(f"Processed: {path}")
    except Exception as e:
        print(f"Error with {path}: {e}")

def find_images_recursive(folder):
    result = []
    for root, dirs, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                result.append(os.path.join(root, f))
    return result

# ===== UI Widget =====
class ImageProcessorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Processor")
        self.setAcceptDrops(True)
        self.resize(550, 360)
        self.center_on_screen()

        self.image_paths = []

        layout = QVBoxLayout()

        # Drag-and-drop area
        self.drop_area = QLabel("DROP IMAGES OR FOLDERS HERE", self)
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setStyleSheet(
            "border: 3px dashed #aaa; background-color: #f9f9f9; color: #444; font-size: 18px; padding: 40px;"
        )
        layout.addWidget(self.drop_area)

        # Buttons to select folder/files
        button_layout = QHBoxLayout()
        self.btn_select_folder = QPushButton("Select Folder")
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_select_images = QPushButton("Select Images")
        self.btn_select_images.clicked.connect(self.select_images)
        button_layout.addWidget(self.btn_select_folder)
        button_layout.addWidget(self.btn_select_images)
        layout.addLayout(button_layout)

        self.scale_input = QLineEdit("0.5")
        layout.addWidget(QLabel("Scale ratio (e.g. 0.5 to reduce size by half):"))
        layout.addWidget(self.scale_input)

        self.checkbox_div4 = QCheckBox("Ensure image width and height are divisible by 4")
        layout.addWidget(self.checkbox_div4)

        self.info_label = QLabel("No images selected.")
        layout.addWidget(self.info_label)

        self.button_process = QPushButton("Process Images")
        self.button_process.clicked.connect(self.process_images)
        layout.addWidget(self.button_process)

        self.setLayout(layout)

    def center_on_screen(self):
        screen = QApplication.desktop().screenGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_area.setStyleSheet(
                "border: 3px dashed #3a9; background-color: #e0fff0; color: #256; font-size: 18px; padding: 40px;"
            )

    def dragLeaveEvent(self, event):
        self.reset_drop_area_style()

    def dropEvent(self, event):
        self.reset_drop_area_style()
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.load_images_from_paths(paths)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.load_images_from_paths([folder])

    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if files:
            self.load_images_from_paths(files)

    def load_images_from_paths(self, paths):
        all_images = []
        for path in paths:
            if os.path.isdir(path):
                all_images.extend(find_images_recursive(path))
            elif os.path.isfile(path) and path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                all_images.append(path)

        self.image_paths = all_images
        if all_images:
            print("Loaded images:")
            for img in all_images:
                print(" •", img)
            self.info_label.setText(f"{len(all_images)} images loaded.")
        else:
            self.info_label.setText("No valid images found.")

    def reset_drop_area_style(self):
        self.drop_area.setStyleSheet(
            "border: 3px dashed #aaa; background-color: #f9f9f9; color: #444; font-size: 18px; padding: 40px;"
        )

    def process_images(self):
        if not self.image_paths:
            QMessageBox.warning(self, "Error", "No images to process.")
            return
        try:
            scale = float(self.scale_input.text())
            assert 0 < scale <= 1.0
        except:
            QMessageBox.warning(self, "Error", "Scale must be a number between 0 and 1.")
            return

        force_div4 = self.checkbox_div4.isChecked()

        print("Starting image processing...\n")
        with ThreadPoolExecutor() as executor:
            for img_path in self.image_paths:
                executor.submit(process_image, img_path, scale, force_div4)

        QMessageBox.information(self, "Done", f"Processed {len(self.image_paths)} images.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessorWidget()
    window.show()
    sys.exit(app.exec_())
