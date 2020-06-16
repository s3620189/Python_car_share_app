# -*- coding:utf-8 -*-

import os
import qrcode
from PIL import Image
from pyzbar import pyzbar


def make_qr_code(content, save_path=None):
    qr_code_maker = qrcode.QRCode(version=5,
                                  error_correction=qrcode.constants.ERROR_CORRECT_M,
                                  box_size=8,
                                  border=4,
                                  )
    qr_code_maker.add_data(data=content)
    qr_code_maker.make(fit=True)
    img = qr_code_maker.make_image(fill_color="black", back_color="white")
    if save_path:
        img.save(save_path)
    else:
        img.show()  # no icon


def make_qr_code_with_icon(content, icon_path, save_path=None):
    if not os.path.exists(icon_path):
        raise FileExistsError(icon_path)

    # First, generate an usual QR Code image
    qr_code_maker = qrcode.QRCode(version=5,
                                  error_correction=qrcode.constants.ERROR_CORRECT_H,
                                  box_size=8,
                                  border=4,
                                  )
    qr_code_maker.add_data(data=content)
    qr_code_maker.make(fit=True)
    qr_code_img = qr_code_maker.make_image(
        fill_color="black", back_color="white").convert('RGBA')

    # Second, load icon image and resize it
    icon_img = Image.open(icon_path)
    code_width, code_height = qr_code_img.size
    icon_img = icon_img.resize(
        (code_width // 4, code_height // 4), Image.ANTIALIAS)

    # Last, add the icon to original QR Code
    qr_code_img.paste(icon_img, (code_width * 3 // 8, code_width * 3 // 8))

    if save_path:
        qr_code_img.save(save_path)  # save
        qr_code_img.show()  # show QRcode
    else:
        print("save error!")
def generate_profile():
    data=" Name: jack \n ID: 1 \n Email:  516539172@qq.com"
    make_qr_code(data, "qrcode.png")


if __name__ == "__main__":
    generate_profile()
    print(" generate qrcode.png")
    results = decode_qr_code("qrcode.png")
    
