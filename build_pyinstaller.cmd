pyinstaller --onefile ^
  --add-data "icon.ico;." ^
  swap.py
echo Press enter to exit
set /p input=