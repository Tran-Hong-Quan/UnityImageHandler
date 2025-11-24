# ImageProcessor.spec
# Build GUI + PyQt5 + Numpy + Pillow

import sys
from PyInstaller.utils.hooks import collect_submodules

hidden = []
hidden += collect_submodules("PyQt5")
hidden += collect_submodules("PIL")
hidden += collect_submodules("numpy")

block = [
    "torch", "tensorflow", "matplotlib", "sklearn",
    "scipy", "cv2", "notebook", "IPython",
]

a = Analysis(
    ['main.py'],          # tên file python của bạn
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    excludes=block,
    noarchive=False
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='ImageProcessor',
    console=True,         
    icon='icon.ico',        # nếu không có icon thì XOÁ dòng này
    debug=False,
    strip=False,
    upx=False,
    onefile=True            # build 1 file duy nhất
)
