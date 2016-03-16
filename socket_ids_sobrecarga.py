from socket import *
import string
import time
import collections

def enviarSobrecarga(ipControlador, mensagem):
        porta = 3000
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
        print mensagem
        socketBro.send(mensagem)
        socketBro.close()

while True:
        print 'Digite 0 para sobrecarga ou 1 para descarga'
        op = input()
        if(op == 0):
                enviarSobrecarga(ipControlador="69.69.69.1", mensagem="sobrecarga")
        elif(op == 1):
                enviarSobrecarga(ipControlador="69.69.69.1", mensagem="descarga")
        else:
                print 'Opcao invailida'
        time.sleep(1)

