# USAGE
# python vagas.py -v video [-i imagem]  [-c cadastro]

import argparse
import time
import imutils  # type: ignore
import cv2  # type: ignore
import numpy as np  # type: ignore
import os

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to input video")
ap.add_argument("-c", "--cadastro", type=int, default=0,
                help="[0] - monitoramento das vagas | [1] - cadastra novo setor")
# ap.add_argument("-s", "--selecao", type=int, default=0, help="[0] - selecao automatica | [1] - selecao manual")
args = vars(ap.parse_args())


def cadastrar():
    # Leitura do primeiro frame da camera para identificacao das posicoes das vagas
    image = None
    camera = cv2.VideoCapture(args["video"])
    if args.get("video", None) is not None:
        camera = cv2.VideoCapture(args["video"])
        (grabbed, frame) = camera.read()
        if not grabbed:
            print("Impossível proseguir com o cadastro! - Erro na leitura do vídeo!")
            exit(0)
        image = frame
    else:
        print("Erro na leitura de arquivo! (Vídeo não encontrado)")
        exit(0)
    # cv2.imshow("Image", image)

    # Identificacao automatica
    # Select ROI
    roi = cv2.selectROI("Selecione a ROI", image, False)
    # Crop image
    xInicial = roi[0]
    yInicial = roi[1]
    altura = roi[3]
    largura = roi[2]
    cropped_image = image[int(roi[1]):int(yInicial+altura),
                          int(roi[0]):int(xInicial+largura)]

    # converte pra escala de cinza
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    # cv2.imshow("Gray", gray)
    # cv2.waitKey(0)

    # threshold
    ret, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    # cv2.imshow("Thresh", thresh)
    # cv2.waitKey(0)

    # buscar contornos
    contornos = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_SIMPLE)
    contornos = imutils.grab_contours(contornos)
    output = thresh.copy()
    outputImg = image.copy()

    # loop dos contornos
    vagas = 0
    for contorno in contornos:
        # desenha retangulos nas multiplas areas de interesse encontradas
        if cv2.contourArea(contorno) > 1800:
            x, y, w, h = cv2.boundingRect(contorno)
            vagas += 1
            cv2.rectangle(output, (x+20, y), (x+w-20, y+h), (255, 0, 0), 2)
            cv2.rectangle(outputImg, (x+20+xInicial, y+yInicial),
                          (x+w-20+xInicial, y+h+yInicial), (255, 0, 0), 2)

    # cv2.imshow("Contours", output)
    cv2.destroyWindow("Selecione a ROI")
    cv2.imshow("Vagas encontradas", outputImg)
    cv2.waitKey(0)


def main():
    os.system('cls')
    print("--------------- TEM VAGA ALI! ---------------")
    print("----- Sistema de monitoramento de vagas -----\n")
    if (args["cadastro"] == 1):
        print("[1] - Cadastre um novo setor")
        cadastrar()
    else:
        cadastrar()
        # monitorar()


if __name__ == '__main__':
    main()
