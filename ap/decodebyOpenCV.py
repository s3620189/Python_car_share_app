
import cv2
import pyzbar.pyzbar as pyzbar

def decodeDisplay(image):
    barcodes = pyzbar.decode(image)
    for barcode in barcodes:
        # get location
        
        (x, y, w, h) = barcode.rect
        cv2.rectangle(image, (x, y), (x + w, y + h), (225, 225, 225), 2)

        # to string
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type

        # get image type
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    .5, (225, 225, 225), 2)

        # show code image type
        print("[INFO] Found {} barcode: {}".format(barcodeType, barcodeData))
    return image


def detect():
    camera = cv2.VideoCapture(0)

    while True:
        # get frame
        ret, frame = camera.read()
        # change color
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        im = decodeDisplay(gray)

        cv2.waitKey(5)
        cv2.imshow("camera", im)
        # quit
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    camera.release()
    cv2.destroyAllWindows()
    
if __name__ == '__main__':
    detect()

