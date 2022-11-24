# USAGE
# python vagas.py -v video [-s nome_do_setor] [-c 0 ou 1]

import cv2  # type: ignore
import numpy as np  # type: ignore
import funcoesComuns as func
from datetime import datetime

def listarCoordenadas(string, separador1, separador2):
    lista = []

    for vaga in string.split(separador1):
        li = list(map(int, vaga.split(separador2)))
        lista.append(li)

    return lista


def grid(lista):
    return cv2.vconcat([cv2.hconcat(im_list_h) for im_list_h in lista])


def monitorar(args):
    setores = []
    try:
        file = open('setores.txt', 'r+')
        for l in file:
            setor = {}
            setor['id'] = l.split(';')[0]
            setor['camera'] = cv2.VideoCapture(l.split(';')[1])
            setor['nomeSetor'] = l.split(';')[2]
            coordenadas = l.split(';')[3]
            coordenadas = coordenadas[0:len(coordenadas)-2]
            setor['coordenadas'] = listarCoordenadas(coordenadas, ':', ',')
            setor['grabbed'] = True
            setor['frame'] = None
            setor['isVideo'] = False
            setor['estado'] = True
            setores.append(setor)

            # Estados
            # True = monitorando
            # False = video nao encontrado/encerrado
        file.close()
    except:
        pass
        print("Arquivo nao encontrado!")
        exit(0)

    data = datetime.now().strftime("%d-%m-%Y")
    log = None
    if args["log"] == 1:
        try:
            log = open("logs/log_"+data+'.txt', 'w')
        except:
            pass
            print("Impossivel criar log!")

    camerasAtivas = len(setores)
    prevOcupadas = 0
    i = 0
    while True:
        data = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        tamanhoFrame = func.getTamanhoFrame()
        saida = []
        for setor in setores:
            (setor['grabbed'], setor['frame']) = setor['camera'].read()
            if setor['grabbed'] and setor['estado']:
                setor['isVideo'] = True
                camera = cv2.resize(setor['frame'], tamanhoFrame)
                gray = cv2.cvtColor(camera, cv2.COLOR_BGR2GRAY)

                ########################### AJUSTAR VALORES ###########################
                thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 25, 16)
                ########################### AJUSTAR VALORES ###########################

                blur = cv2.medianBlur(thresh, 5)
                kernel = np.ones((3, 3), np.int8)
                dilatada = cv2.dilate(blur, kernel)

                height = tamanhoFrame[1]
                width = tamanhoFrame[0]
                cv2.rectangle(camera, (-2, -2), (width-1, height-1), (0, 0, 0), 2)
                ocupadas = 0
                for x, y, w, h in setor['coordenadas']:
                    area = dilatada[y:h, x:w]
                    pixelsBranco = cv2.countNonZero(area)

                    areaNumerica = (h-y)*(w-x)
                    if pixelsBranco > areaNumerica*0.12:
                        # VAGA OCUPADA
                        ocupadas += 1
                        cv2.rectangle(camera, (x, y), (w, h), (0, 0, 255), 2)
                    else:
                        # VAGA LIVRE
                        cv2.rectangle(camera, (x, y), (w, h), (0, 255, 0), 2)

                # titulo do setor // faixa
                titulo = "#"+setor['id']+" "+setor['nomeSetor']
                cv2.rectangle(camera, (0, 0), (len(titulo)*18+20, 55), (255, 255, 255), -1)
                # numero de vagas ocupadas
                vagas = str(ocupadas)+"/"+str(len(setor['coordenadas']))
                cv2.rectangle(camera, (width-len(vagas)*18-50, 0), (width-4, 55), (255, 255, 255), -1)

                camera = cv2.putText(camera, titulo, (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (30, 15, 10), 2, cv2.LINE_AA)
                camera = cv2.putText(camera, vagas, (width-len(vagas)*18-30, 35), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (30, 15, 10), 2, cv2.LINE_AA)
                # cv2.imshow(titulo, camera)

                # adiciona dados ao registro
                if args["log"] is 1:
                    if prevOcupadas is not ocupadas and ocupadas is not 0 and i is not 0:
                        veiculos = abs(ocupadas - prevOcupadas)
                        acao = ''
                        if prevOcupadas > ocupadas:
                            if veiculos is 1:
                                acao = '1 veiculo saiu do setor'
                            else:
                                acao = str(veiculos) + ' veiculos sairam do setor'
                        else:
                            if veiculos is 1:
                                acao = '1 veiculo entrou no setor' 
                            else:
                                acao = str(veiculos) + ' veiculos entraram no setor'
                        try:
                            log.write(acao + ' ' + setor['nomeSetor'] + " em " + data + " - [" + vagas + "]\n")
                        except:
                            pass
                            print("Erro: Não foi possível criar log.")
                saida.append(camera)
                prevOcupadas = ocupadas
                i += 1
            else:
                if setor['estado']:
                    setor['estado'] = False
                    camerasAtivas -= 1
                    if setor['isVideo'] == False:
                        print("Imagem de vídeo não disponível.")
                    else:
                        print("Sinal de #" + setor['id'] + " - " + setor['nomeSetor'] + " encerrado")
                    if camerasAtivas == 0:
                        print("Nenhuma câmera ativa!")
                        if log is not None:
                            log.close()
                        exit(0)

        if camerasAtivas > 0:
            if camerasAtivas == 1:
                out = saida[0]
            else:
                n = 2
                total = 0
                tamanho = len(saida)
                while tamanho > (n ** 2):
                    n += 1
                total = (n ** 2)

                # cria uma tela em branco e preenche espaços vazios com ela
                width = tamanhoFrame[0]
                height = tamanhoFrame[1]
                bg = np.zeros((height, width, 3), dtype="uint8")
                bg[:] = (180, 180, 180)
                cv2.rectangle(bg, (-2, -2), (1280-1, 720-1), (0, 0, 0), 2)
                while len(saida) < total:
                    saida.append(bg)

                listaSaida = []
                f = 0
                l = n
                for j in range(0, n):
                    listaSaida.append(saida[f:l])
                    f += n
                    l += n
                out = grid(listaSaida)
            # tela inteira dinamica exibindo todas as cameras ativas
            out = cv2.resize(out, (1920, 1080))

            cv2.rectangle(out, (0, 1080), (300, 1040), (200, 200, 200), -1)
            out = cv2.putText(out, data, (20, 1068), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (35, 35, 35), 2, cv2.LINE_AA)

            nomeJanela = "Monitoramento"
            cv2.namedWindow(nomeJanela, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(nomeJanela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.imshow(nomeJanela, out)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # q (quit) encerra
            cv2.destroyAllWindows()
            if log is not None:
                log.close()
            break
