import os
from shutil import copyfile


folder = "../assets/edekaData/"
accepted = ["578"]
txs = []
for file in os.listdir(folder):
    if file.endswith("-40.webp.json"):
        name = file.split("-40.webp.json")[0]
        if name.split("_")[1] not in accepted:
            tx = name.split("_")[0:2]
            tx = "".join([e+"_" for e in tx])
            if tx not in txs:
                txs.append(tx)
for tx in txs:
    one_name = folder + tx + "1-40.webp.json"
    two_name = folder + tx + "2-40.webp.json"

    one_size = os.path.getsize(one_name)
    two_size = os.path.getsize(two_name)
    if one_size < two_size:
        print("one: " + one_name)
        os.remove(one_name)
    else:
        print("two: " + two_name)
        os.remove(two_name)

#get all img files
folder = "../assets/edekaData/"
picFolder = "G:\\Meine Ablage\\10 Temporary File Transfer\\03 MHE\\transactions\\"
for file in os.listdir(folder):
    if file.endswith("-40.webp.json"):
        tx = file.split("-40.webp.json")[0]
        pic_path = picFolder+tx+".jpg"
        dest_path = folder+tx+".jpg"
        copyfile(pic_path, dest_path)