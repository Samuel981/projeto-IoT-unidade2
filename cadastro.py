import imutils  # type: ignore
import cv2  # type: ignore
import funcoesComuns as func
import monitorar as m

def automatica(image):
    func.header()
    print("[Cadastrando vagas de modo semiautomático]")
    # Identificacao automatica
    # Select ROI
    roi = cv2.selectROI("Selecione a ROI", image, False)
    # Crop image
    xInicial = roi[0]
    yInicial = roi[1]
    altura = roi[3]
    largura = roi[2]
    cropped_image = image[int(roi[1]):int(yInicial+altura), int(roi[0]):int(xInicial+largura)]

    # converte pra escala de cinza
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

    # threshold
    ret, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # buscar contornos
    contornos = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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
            cv2.rectangle(outputImg, (x+20+xInicial, y+yInicial), (x+w-20+xInicial, y+h+yInicial), (255, 0, 0), 2)
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
    func.header()
    print("[Cadastrando vagas de modo manual]")
    coordenadas = None
    # if coordenadas is not None:
    roi = cv2.selectROI("Selecione a ROI", image, False)

    xInicial = roi[0]
    yInicial = roi[1]
    altura = roi[3]
    largura = roi[2]

    cv2.rectangle(image, (xInicial, yInicial), (xInicial+largura, yInicial+altura), (255, 0, 0), 2)

    if armazenado is not None:
        armazenado = str(armazenado)
    coordenadas = armazenado + str(xInicial)+','+str(yInicial) + \
        ','+str(xInicial+largura)+','+str(yInicial+altura)+':'
    cv2.imshow("Selecione a ROI", image)
    print("Pressione\n[ESPAÇO] para para adicionar mais uma vaga\n[ENTER] para avançar")
    key = cv2.waitKey(0)
    if key == 32:
        coordenadas = manual(image, coordenadas)
    else:
        print(coordenadas)
    return str(coordenadas)


def cadastrar(args):
    func.header()
    print("Pressione\n[A] para fazer o cadastro do modo semiautomático\n[M] para fazer o cadastro manualmente")

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
    tamanhoFrame = func.getTamanhoFrame()
    image = cv2.resize(image, tamanhoFrame)
    if key == 97 or key == 65:  # letra A = identificacao automatica
        coordenadas = automatica(image)
    elif key == 109 or key == 77:   # letra M = identificacao manual
        coord = ''
        coordenadas = manual(image, coord)
    else:
        exit(0)

    func.header()
    print( "Pressione\n[ENTER] para confirmar cadastro de " + args["setor"] + "\n[R] para refazer o cadastro")
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
        cadastrar(args)
    else:
        exit(0)

    print(
        "Pressione\n[ENTER] para começar a monitorar "+args["setor"]+"\n[ESC] para sair")
    key = cv2.waitKey(0)
    if key == 13:
        m.monitorar(args)
    else:
        exit(0)
