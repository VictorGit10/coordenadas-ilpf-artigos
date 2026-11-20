import os
import shutil
import zipfile

dest = "/content/ensino"
if os.path.exists(dest):
    shutil.rmtree(dest)
os.makedirs(dest, exist_ok=True)
with zipfile.ZipFile("/content/dados_ensino.zip") as z:
    z.extractall(dest)
print("ok", len(os.listdir(os.path.join(dest, "recortes"))), "imagens")
