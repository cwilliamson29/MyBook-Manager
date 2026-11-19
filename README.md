# MyBook-Manager


## Build on windows
python -m PyInstaller --onedir --windowed --name "MyBook Manager" --icon="assets/icon/MyBook_Manager_Icon.png" --add-data "assets;assets"--collect-all customtkinter --collect-all CTkColorPicker --hidden-import darkdetect --hidden-import PIL._tkinter_finder main.py  
