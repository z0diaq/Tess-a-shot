pip install pytesseract
pip install Pillow
pip install pyperclip

configure pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path if necessary


best option to install Tesseract for Windows OS:
vcpkg install tesseract:x64-windows-static