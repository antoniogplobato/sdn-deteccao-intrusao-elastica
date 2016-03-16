from socket import *
import string
import time
import collections

def enviarIntrusoSocket(ipControlador, ipsIntrusos):
    porta = 5000
    for ip in ipsIntrusos:
        socketBro = socket(AF_INET, SOCK_STREAM)
        controlador = (ipControlador, porta)
        while True:
        	try:
                socketBro.connect(controlador)
                break
            except:
                    print 'Tentando conexao com controlador'
                    time.sleep(1)
        print 'Conexao estabelecida'
        print ip
        socketBro.send(ip)
        socketBro.close()

def lerArquivoIP(nomeArquivo):
    arquivo = open(nomeArquivo, 'r')
    ipsIntrusos = arquivo.read()
    arquivo.close()
    ipsIntrusos = ipsIntrusos.split('\n')
    ipsIntrusos.remove("")
    return ipsIntrusos

ipsIntrusosAnterior = []
while True:
    ipsIntrusosAtual = lerArquivoIP("./ataque.txt")
    compare = lambda x, y: collections.Counter(x) == collections.Counter(y)
    if (compare(ipsIntrusosAnterior, ipsIntrusosAtual) == False):
            enviarIntrusoSocket(ipControlador="69.69.69.1", ipsIntrusos=ipsIntrusosAtual)
    ipsIntrusosAnterior = ipsIntrusosAtual
    open("./ataque.txt", 'w').close
    time.sleep(1)