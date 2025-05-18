import pytesseract
import platform
import ui_setup

if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = 'Z:\\dev\\vcpkg\\installed\\x64-windows-static\\tools\\tesseract\\tesseract.exe'

if __name__ == '__main__':
    ui_setup.setup()
