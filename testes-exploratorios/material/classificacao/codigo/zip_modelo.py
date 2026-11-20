import os
import zipfile

pasta = "/content/modelo"
saida = "/content/modelo.zip"
with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(pasta):
        for f in files:
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, "/content"))
print("ok", os.path.getsize(saida), "bytes")
