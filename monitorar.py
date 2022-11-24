# USAGE
# python vagas.py -v video [-s nome_do_setor] [-c 0 ou 1]

import cv2  # type: ignore
import numpy as np  # type: ignore
import funcoesComuns as func
from datetime import datetime


def listar(string, char1, char2):

    lista = []
    for vaga in string.split(char1):
        li = list(vaga.split(char2))
        for i in range(0, len(li)):
            li[i] = int(li[i])
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
            setor['coordenadas'] = listar(coordenadas, ':', ',')
            setor['grabbed'] = True
            setor['frame'] = None
            setor['frames'] = False
            setor['estado'] = True
            setores.append(setor)
            # print(setor['id'])
            # print(setor['camera'])
            # print(setor['nomeSetor'])
            # print(setor['coordenadas'])

            # Estados
            # T - monitorando
            # F = video nao encontrado/encerrado
        file.close()
    except:
        pass
        print("Arquivo nao encontrado!")
        exit(0)

    now = datetime.now()
    data = now.strftime("%d-%m-%Y_%H-%M-%S")
    log = None
    if args["log"] == 1:
        try:
            log = open("logs/log_"+data+'.txt', 'w')
        except:
            pass
            print("Impossivel criar log!")

    camerasAtivas = len(setores)
    while True:
        now = datetime.now()
        data = now.strftime("%d/%m/%Y %H:%M:%S")
        saida = []
        for set in setores:
            (set['grabbed'], set['frame']) = set['camera'].read()
            if set['grabbed'] and set['estado']:
                set['frames'] = True
                camera = cv2.resize(set['frame'], (1280, 720))
                gray = cv2.cvtColor(camera, cv2.COLOR_BGR2GRAY)

                ########################### AJUSTAR VALORES ###########################
                thresh = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 16)
                ########################### AJUSTAR VALORES ###########################

                blur = cv2.medianBlur(thresh, 5)
                kernel = np.ones((3, 3), np.int8)
                dilatada = cv2.dilate(blur, kernel)

                height = camera.shape[0]
                width = camera.shape[1]
                cv2.rectangle(camera, (-2, -2),
                              (width-1, height-1), (0, 0, 0), 2)
                ocupadas = 0
                for x, y, w, h in set['coordenadas']:
                    area = dilatada[y:h, x:w]
                    pixelsBranco = cv2.countNonZero(area)

                    areaNumerica = (h-y)*(w-x)
                    if pixelsBranco > areaNumerica*0.095:
                        # VAGA OCUPADA
                        ocupadas += 1
                        cv2.rectangle(camera, (x, y), (w, h), (0, 0, 255), 2)
                    else:
                        # VAGA LIVRE
                        cv2.rectangle(camera, (x, y), (w, h), (0, 255, 0), 2)

                original = camera.copy()
                # titulo do setor // faixa
                titulo = "#"+set['id']+" "+set['nomeSetor']
                cv2.rectangle(camera, (0, 0),
                              (len(titulo)*20+20, 55), (255, 255, 255), -1)
                # titulo do setor // faixa
                vagas = str(ocupadas)+"/"+str(len(set['coordenadas']))
                cv2.rectangle(camera, (width-len(vagas)*18-50, 0),
                              (width-4, 55), (255, 255, 255), -1)

                # camera = cv2.addWeighted(camera, 0.9, original, 0.1, 0)
                camera = cv2.putText(camera, titulo, (20, 35), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (30, 15, 10), 2, cv2.LINE_AA)
                camera = cv2.putText(camera, vagas, (width-len(vagas)*18-30, 35), cv2.FONT_HERSHEY_SIMPLEX,
                                     1, (30, 15, 10), 2, cv2.LINE_AA)
                # cv2.imshow(titulo, camera)

                # adiciona dados ao registro
                if args["log"] == 1:
                    try:
                        log.write("Dado\n")
                    except:
                        pass
                        print("Impossivel criar log!")
                saida.append(camera)
            else:
                if set['estado']:
                    set['estado'] = False
                    camerasAtivas -= 1
                    if set['frames'] == False:
                        print("Vídeo não encontrado.")
                    else:
                        print("Sinal de #"+set['id'] +
                              " - "+set['nomeSetor']+" encerrado")
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
                bg = np.zeros((720, 1280, 3), dtype="uint8")
                bg[:] = (180, 180, 180)
                cv2.rectangle(bg, (-2, -2),
                              (1280-1, 720-1), (0, 0, 0), 2)
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
            out = cv2.putText(out, data, (20, 1068), cv2.FONT_HERSHEY_SIMPLEX,
                              0.7, (35, 35, 35), 2, cv2.LINE_AA)

            nomeJanela = "Monitoramento"
            cv2.namedWindow(nomeJanela, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(
                nomeJanela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.imshow(nomeJanela, out)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:  # q (quit) encerra
            cv2.destroyAllWindows()
            if log is not None:
                log.close()
            break
