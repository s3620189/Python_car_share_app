# -*- coding:utf-8 -*-

import os
import qrcode
from PIL import Image
from pyzbar import pyzbar




  
def decode_qr_code(code_img_path):
    if not os.path.exists(code_img_path):
        raise FileExistsError(code_img_path)

    # Here, set only recognize QR Code and ignore other type of code
    return pyzbar.decode(Image.open(code_img_path), symbols=[pyzbar.ZBarSymbol.QRCODE])



if __name__ == "__main__":

    print("Scan image by imported QRcode image")

    print(" Decode file name: qrcode.png")

    print(" decoding：")
    if len(results):
        print("results：")
        print(results[0].data.decode("utf-8"))
    else:
        print("Can not recognize.")

