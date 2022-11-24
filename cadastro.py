import imutils  # type: ignore
import cv2  # type: ignore
import funcoesComuns as func
import monitorar as m

def addFaixa(exibicao):
    return cv2.rectangle(exibicao, (0, 0), (1280,40), (200, 200, 200), -1)

def addInstrucao(imagem, texto):
    return cv2.putText(imagem, texto, (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (35, 35, 35), 2, cv2.LINE_AA)

def automatica(image, args):
    func.header()
    print("[Cadastrando vagas de modo semiautomático]")
    # Identificacao automatica
    # Select ROI
    exibicao = image.copy()
    addFaixa(exibicao)
    exibicao = cv2.addWeighted(exibicao, 0.7, image, 0.3, 0)
    info = "Selecione uma regiao e pressione [ENTER] para avancar"
    exibicao = addInstrucao(exibicao, info)

    roi = cv2.selectROI("Selecione a ROI", exibicao, False)
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
    exibicao = outputImg.copy()
    addFaixa(exibicao)
    info = "Pressione [ENTER] para confirmar cadastro de " + args["setor"] + " ou [R] para refazer o cadastro"
    exibicao = addInstrucao(exibicao, info)
    cv2.imshow("Vagas encontradas", exibicao)

    return coordenadas


def manual(image, armazenado, args):
    func.header()
    print("[Cadastrando vagas de modo manual]")
    coordenadas = None
    # if coordenadas is not None:
    exibicao = image.copy()
    addFaixa(exibicao)
    exibicao = cv2.addWeighted(exibicao, 0.7, image, 0.3, 0)
    info = "Selecione uma regiao e pressione [ENTER] para avancar"
    exibicao = addInstrucao(exibicao, info)
    roi = cv2.selectROI("Selecione a ROI", exibicao, False)

    xInicial = roi[0]
    yInicial = roi[1]
    altura = roi[3]
    largura = roi[2]

    cv2.rectangle(image, (xInicial, yInicial), (xInicial+largura, yInicial+altura), (255, 0, 0), 2)

    if armazenado is not None:
        armazenado = str(armazenado)
    coordenadas = armazenado + str(xInicial)+','+str(yInicial) + \
        ','+str(xInicial+largura)+','+str(yInicial+altura)+':'
        
    exibicao = image.copy()
    addFaixa(exibicao)
    info = "Pressione [ESPACO] para para adicionar mais uma vaga ou [ENTER] para avancar"
    exibicao = addInstrucao(exibicao, info)
    cv2.imshow("Selecione a ROI", exibicao)
    key = cv2.waitKey(0)
    if key == 32:
        coordenadas = manual(image, coordenadas, args)
        
    # cv2.destroyWindow("Selecione a ROI")
    exibicao = image.copy()
    addFaixa(exibicao)
    info = "Pressione [ENTER] para confirmar cadastro de " + args["setor"] + " ou [R] para refazer o cadastro"
    exibicao = addInstrucao(exibicao, info)
    cv2.imshow("Selecione a ROI", exibicao)
    return str(coordenadas)


def cadastrar(args):
    func.header()

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
    
    exibicao = image.copy()
    addFaixa(exibicao)
    info = "Pressione [A] para fazer o cadastro no modo semiautomatico [M] para fazer o cadastro manualmente"
    exibicao = addInstrucao(exibicao, info)
    
    cv2.imshow(msg, exibicao)
    key = cv2.waitKey(0)
    coordenadas = None
    cv2.destroyWindow(msg)
    tamanhoFrame = func.getTamanhoFrame()
    image = cv2.resize(image, tamanhoFrame)
    nomeJanela = None
    if key == 97 or key == 65:  # letra A = identificacao automatica
        nomeJanela = "Vagas encontradas"
        coordenadas = automatica(image, args)
    elif key == 109 or key == 77:   # letra M = identificacao manual
        nomeJanela = "Selecione a ROI"
        coord = ''
        coordenadas = manual(image, coord, args)
    else:
        exit(0)

    func.header()
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
    elif key == 114 or key == 82:   # letra R repete identificacao 
        cv2.destroyWindow(nomeJanela)
        cadastrar(args)
    else:
        exit(0)

    exibicao = image.copy()
    addFaixa(exibicao)
    info = "Pressione [ENTER] para comecar a monitorar "+args["setor"]+" ou [ESC] para sair"
    exibicao = addInstrucao(exibicao, info)
    cv2.imshow(nomeJanela, exibicao)
    key = cv2.waitKey(0)
    if key == 13:
        m.monitorar(args)
    else:
        exit(0)


def excluir():
    setores = []
    try:
        with open('setores.txt', 'r') as file:
            print("Lista de setores:")
            linhas = 0
            for l in file:
                print(l.split(';')[0]+" - "+l.split(';')[1])
                linhas += 1
            setor = int(input("Informe a id do setor a ser excluído: "))
            file.close()
    except:
        pass
        print("Arquivo nao encontrado!")
        exit(0)

    with open('setores.txt', 'r') as file:
        lines = file.readlines()
        ptr = 1

        if setor > linhas:
            print("Setor não encontrado")
            exit(0)
        with open('setores.txt', 'w') as fw:
            for line in lines:
                if ptr < setor:
                    fw.write(line)
                if ptr > setor:
                    corrigido = int(line.split(';')[0])-1
                    fw.write(str(corrigido)+";"+line.split(';')
                             [1]+";"+line.split(';')[2]+";"+line.split(';')[3])
                ptr += 1
            print("Deletado")
