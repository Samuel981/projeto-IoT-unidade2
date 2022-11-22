# USAGE
# python vagas.py -v video [-s nome_do_setor] [-c 0 ou 1]

import argparse
import time
import imutils  # type: ignore
import cv2  # type: ignore
import numpy as np  # type: ignore
import os

ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to input video")
ap.add_argument("-s", "--setor", help="informa o nome do setor")
ap.add_argument("-c", "--cadastro", type=int, default=0,
                help="[0] - monitoramento das vagas | [1] - cadastra novo setor")
args = vars(ap.parse_args())


def automatica(image):
    header()
    print("[Cadastrando vagas de modo semiautomático]")
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
    coordenadas = None
    for contorno in contornos:
        # desenha retangulos nas multiplas areas de interesse encontradas
        if cv2.contourArea(contorno) > 1800:
            x, y, w, h = cv2.boundingRect(contorno)
            vagas += 1
            cv2.rectangle(outputImg, (x+20+xInicial, y+yInicial),
                          (x+w-20+xInicial, y+h+yInicial), (255, 0, 0), 2)
            armazenado = ''
            if coordenadas is not None:
                armazenado = str(coordenadas)
            coordenadas = armazenado + \
                str(x+20+xInicial)+','+str(y+yInicial) + ',' + \
                str(x+w-20+xInicial)+','+str(y+h+yInicial)+':'

    # cv2.imshow("Contours", output)
    cv2.destroyWindow("Selecione a ROI")
    cv2.imshow("Vagas encontradas", outputImg)

    return coordenadas


def manual(image, armazenado):
    header()
    print("[Cadastrando vagas de modo manual]")
    coordenadas = None
    # if coordenadas is not None:
    roi = cv2.selectROI("Selecione a ROI", image, False)

    xInicial = roi[0]
    yInicial = roi[1]
    altura = roi[3]
    largura = roi[2]

    cv2.rectangle(image, (xInicial, yInicial),
                  (xInicial+largura, yInicial+altura), (255, 0, 0), 2)

    if armazenado is not None:
        armazenado = str(armazenado)
    coordenadas = armazenado + str(xInicial+20)+','+str(yInicial) + \
        ','+str(xInicial+largura-20)+','+str(yInicial+altura)+':'
    cv2.imshow("Selecione a ROI", image)
    print(
        "Pressione\n[ESPAÇO] para para adicionar mais uma vaga\n[ENTER] para avançar")
    key = cv2.waitKey(0)
    if key == 32:
        coordenadas = manual(image, coordenadas)
    else:
        print(coordenadas)
    return str(coordenadas)


def cadastrar():
    header()
    print(
        "Pressione\n[A] para fazer o cadastro do modo semiautomático\n[M] para fazer o cadastro manualmente")

    # Leitura do primeiro frame da camera para identificacao das posicoes das vagas
    image = None
    camera = cv2.VideoCapture(args["video"])
    if args.get("video", None) is not None:
        (grabbed, frame) = camera.read()
        if not grabbed:
            print("Impossível proseguir com o cadastro! - Erro na leitura do vídeo!")
            exit(0)
        image = frame
    else:
        print("Erro na leitura de arquivo! (Vídeo não encontrado)")
        exit(0)

    msg = "Escolher modo de identificacao"
    cv2.imshow(msg, image)
    key = cv2.waitKey(0)
    coordenadas = None
    cv2.destroyWindow(msg)
    image = cv2.resize(image, (1280, 720))
    if key == 97 or key == 65:  # letra A = identificacao automatica
        coordenadas = automatica(image)
    elif key == 109 or key == 77:   # letra M = identificacao manual
        coord = ''
        coordenadas = manual(image, coord)
    else:
        exit(0)

    header()
    print(
        "Pressione\n[ENTER] para confirmar cadastro de "+args["setor"]+"\n[R] para refazer o cadastro")
    key = cv2.waitKey(0)
    if key == 32 or key == 13:  # espaco ou enter insere dados no arquivo
        linhas = 0
        try:
            file = open('setores.txt', 'r')
            linhas = sum(1 for l in file)
            file.close()
        except:
            pass

        with open('setores.txt', 'a+') as file:
            id = linhas+1
            file.write(str(id)+';'+args["video"]+';' +
                       args["setor"]+';'+str(coordenadas)+'\n')
    elif key == 114 or key == 82:   # letra R repete identificacao automatica
        cv2.destroyWindow("Vagas encontradas")
        cadastrar()
    else:
        exit(0)

    print(
        "Pressione\n[ENTER] para começar a monitorar "+args["setor"]+"\n[ESC] para sair")
    key = cv2.waitKey(0)
    if key == 13:
        monitorar()
    else:
        exit(0)


def listar(string, char1, char2):

    lista = []
    for vaga in string.split(char1):
        li = list(vaga.split(char2))
        for i in range(0, len(li)):
            li[i] = int(li[i])
        lista.append(li)

    return lista


def monitorar():
    # try:
    file = open('setores.txt', 'r+')
    for l in file:
        id = l.split(';')[0]
        camera = l.split(';')[1]
        setor = l.split(';')[2]
        coordenadas = l.split(';')[3]
        coordenadas = coordenadas[0:len(coordenadas)-2]
        coordenadas = listar(coordenadas, ':', ',')
        # print(id)
        # print(camera)
        # print(setor)
        # print(coordenadas)

        # camera = cv2.VideoCapture(camera)
        # if camera is not None:
        #     (grabbed, frame) = camera.read()
        #     if not grabbed:
        #         print("Impossível proseguir com o cadastro! - Erro na leitura do vídeo!")
        #         exit(0)
        #     image = frame

        camera = cv2.imread('vagas2.png')
        camera = cv2.resize(camera, (1280, 720))
        gray = cv2.cvtColor(camera, cv2.COLOR_BGR2GRAY)
        # ret, thresh = cv2.threshold(gray, 30, 20, cv2.THRESH_BINARY_INV)

        ########################### AJUSTAR VALORES ###########################
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
        ########################### AJUSTAR VALORES ###########################

        blur = cv2.medianBlur(thresh, 5)
        kernel = np.ones((3, 3), np.int8)
        dilatada = cv2.dilate(blur, kernel)

        vaga = len(coordenadas)
        for x, y, w, h in coordenadas:
            area = dilatada[y:h, x:w]
            pixelsBranco = cv2.countNonZero(area)

            cv2.imwrite('images/vaga'+str(vaga)+".jpg", area)
            vaga -= 1
            if pixelsBranco > 3000:
                cv2.rectangle(camera, (x, y), (w, h), (0, 0, 255), 2)
            else:
                cv2.rectangle(camera, (x, y), (w, h), (0, 255, 0), 2)

        titulo = "#"+id+" - "+setor
        cv2.imshow(titulo, camera)

        # else:
        #     print("Erro na leitura de arquivo! (Vídeo não encontrado)")
        #     exit(0)
    cv2.waitKey(0)
    file.close()
    # except:
    #     pass


def header():
    os.system('cls')
    print("--------------- TEM VAGA ALI! ---------------")
    print("----- Sistema de monitoramento de vagas -----\n")


def main():
    header()
    if (args["cadastro"] == 1):
        print("[1] - Cadastre um novo setor")
        cadastrar()
    else:
        monitorar()


if __name__ == '__main__':
    main()
