import os
import shutil
import zipfile

dest = "/content/medicao"
if os.path.exists(dest):
    shutil.rmtree(dest)
os.makedirs(dest, exist_ok=True)
with zipfile.ZipFile("/content/dados_medicao.zip") as z:
    z.extractall(dest)
print("ok", len(os.listdir(os.path.join(dest, "recortes"))), "imagens")
