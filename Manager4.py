import libvirt
import time
import operator
import threading
import pickle
from socket import *

from VirtualMachine import VirtualMachine
from PhysicalMachine import PhysicalMachine

import numpy as np
from matplotlib.colors import colorConverter
from pylab import *
import copy

#from xml.etree import ElementTree, parse
import xml.etree.ElementTree as xml

import os

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

class Manager:

	#initialization function
	def __init__(self):
		colorsLb=['BlueViolet','CadetBlue', 'DarkGreen', 'DarkOliveGreen', 'Chocolate', 'IndianRed', 'Crimson', 'Lime']
		colorsPda = ['DarkSlateGray', 'GoldenRod', 'HotPink', 'SaddleBrown', 'Aquamarine', 'green', 'Gray', 'Indigo']
		self.physicalMachines={}
		self.locks={}
		
		tree = xml.parse("config.xml")
		root=tree.getroot()
		parameters = root.find('parameters')
		print "parameters", parameters
		self.sampleInterval = parameters.find('sampleInterval').get('value')
		print "sampleInterval", self.sampleInterval
		self.windowSize = parameters.find('windowSize').get('value')
		print "windowSize", self.windowSize
		
		for child in root.iter('host'):
			hostName = child.get('name')
			self.locks[hostName]=threading.Lock()
			self.physicalMachines[hostName]=PhysicalMachine(hostName, sampleInterval, windowSize, self.locks[hostName], colorsLb)
			self.physicalMachines[hostName].connect()
			print self.physicalMachines[hostName].informations['name']

		self.chargedHost={'cpu':[],'memory':[],'cpuDomain0':[]}
		self.idleHost={'cpu':[],'memory':[],'cpuDomain0':[]}
		self.saveMode='w'

		#self.iniciarSocket("69.69.69.1")

	def iniciarSocket(self, ipControlador):
		porta = 4000
		self.socketBro = socket(AF_INET, SOCK_STREAM)
		controlador = (ipControlador, porta)
		while True:
			try:
				self.socketBro.connect(controlador)
				break
			except:
				print 'Tentando conexao com controlador'
				time.sleep(1)
		#print 'conectado'

	def enviarDicionario(self, dicionario):
		string = pickle.dumps(dicionario)
		#print 'enviando: ' + string
		self.socketBro.send(string)

	def startMonitoringAllHosts (self, sampleInterval, windowSize):
		for host in self.physicalMachines:
			self.physicalMachines[host].startMonitoringHost()
		
		self.windowSize=windowSize
		identifier = "monitoring"
		self.detThread = threading.Thread(name = identifier, target=self.monitoring, args=(windowSize, duration, sampleInterval,))
		self.detThread.start()

	def stopMonitoringAllHosts (self):
		for host in self.physicalMachines:
			print 'Parando maquinas virtuais do', self.physicalMachines[host].informations['name']
			self.physicalMachines[host].stopMonitoringAllVirtualNodes()
			#fazer funcao para parar os hosts

	def overChargedHost(self):
		idsMachines = ["sdn_firewall_dpi_bro", "sdn_firewall_dpi2"]
		processamento = {}
		for idsMachineName in idsMachines:
			for host in self.physicalMachines:
				if idsMachineName in self.physicalMachines[host].virtualMachines.keys():

					#print 'Guanabara'
					#print self.physicalMachines[host].status['overcharged']['cpu']
					#print self.physicalMachines[host].temporalProfile['cpu']

					#print 'Dom0'
					#print self.physicalMachines[host].virtualMachines['Domain-0'].temporalProfile['cpu']
					dom0PercentualTotal = []
					for i in self.physicalMachines[host].domain0.temporalProfile['cpu']:
						if len(dom0PercentualTotal) < 10:
							dom0PercentualTotal.append(i/float(self.physicalMachines[host].informations['totalTime']))
						else:
							dom0PercentualTotal = dom0PercentualTotal[1:]
							dom0PercentualTotal.append(i/float(self.physicalMachines[host].informations['totalTime']))
					#print dom0PercentualTotal

					#print idsMachineName
					#print self.physicalMachines[host].virtualMachines[idsMachineName].temporalProfile['cpu']
					idsPercentualTotal = []
					for i in self.physicalMachines[host].virtualMachines[idsMachineName].temporalProfile['cpu']:
						if len(idsPercentualTotal) < 10:
							idsPercentualTotal.append(i/float(self.physicalMachines[host].informations['totalTime']))
						else:
							idsPercentualTotal = idsPercentualTotal[1:]
							idsPercentualTotal.append(i/float(self.physicalMachines[host].informations['totalTime']))
					#print 'Percentual Total', idsMachineName
					#print idsPercentualTotal
					if self.physicalMachines[host].status['overcharged']['cpu'] == True:
						sobrecargaIds = 1
						# for i in idsPercentualTotal:
						# 	if idsPercentualTotal <= 30:
						# 		sobrecargaIds = 0
						# if sobrecargaIds == 1:
						# 	#limitar cpu para 30
						# 	#criar maquina nova
						# 	print 'sobrecarga'
						# else:
						# 	print 'Normal'
							#migrar
					idsPercentualRelativo = []
					#print self.physicalMachines[host].informations['cores']
					#print self.physicalMachines[host].virtualMachines[idsMachineName].informations['virtualCores']
					for i in idsPercentualTotal:
						if len(idsPercentualRelativo) < 10:
							idsPercentualRelativo.append(i*(self.physicalMachines[host].informations['cores']/self.physicalMachines[host].virtualMachines[idsMachineName].informations['virtualCores']))
						else:
							idsPercentualRelativo = idsPercentualRelativo[1:]
							idsPercentualRelativo.append(i*(self.physicalMachines[host].informations['cores']/self.physicalMachines[host].virtualMachines[idsMachineName].informations['virtualCores']))
						if idsPercentualRelativo[-1] > 100:
							idsPercentualRelativo[-1] = 100.0
					#print 'Percentual Relativo', idsMachineName
					#print idsPercentualRelativo
					#print len(idsPercentualRelativo)
					maximo = 0
					minimo = 100
					envio = []
					enviar = False
					if len(idsPercentualRelativo) >= 5:
						for proc in range(5):
							envio.append(idsPercentualRelativo[len(idsPercentualRelativo) - proc - 1])
							if envio[-1] > maximo:
								maximo = envio[-1]
							if envio[-1] < minimo:
								minimo = envio[-1]
						envio.remove(maximo)
						envio.remove(minimo)
						media = 0.0
						for proc in envio:
							media = media + proc
						media = float (media/len(envio))
						#print 'media: ' + str(media)
						processamento[idsMachineName] = media
						enviar = True
						if idsMachineName == 'sdn_firewall_dpi_bro':
							procM1 = []
							for proc in range(5):
								procM1.append(idsPercentualRelativo[len(idsPercentualRelativo) - proc - 1])
							if min(procM1) > 90:
								if idsMachines[1] not in self.physicalMachines[host].virtualMachines.keys():
									print 'sobrecarga mano'
									os.system('xm create /home/xen/cfgvms/sdn_firewall_dpi2.cfg')
									self.physicalMachines[host].refreshVmList()
									# while True:
									# 	try:
									# 		erro = os.system('ssh 69.69.69.9 screen -dmS BRO bro -i HUGAY682 local')
									# 		if erro == 0:
									# 			print "bro ligado"
									# 			break
									# 		print "iniciando o bro"
									# 		time.sleep(0.2)
									# 	except:
									# 		print "iniciando o bro"
									# 		time.sleep(0.2)
									enviarSobrecarga(ipControlador="69.69.69.1", mensagem="sobrecarga")
							if idsMachines[1] in self.physicalMachines[host].virtualMachines.keys():
								ids_maquina2_PercentualTotal = []
								for i in self.physicalMachines[host].virtualMachines[idsMachines[1]].temporalProfile['cpu']:
									if len(ids_maquina2_PercentualTotal) < 10:
										ids_maquina2_PercentualTotal.append(i/float(self.physicalMachines[host].informations['totalTime']))
									else:
										ids_maquina2_PercentualTotal = ids_maquina2_PercentualTotal[1:]
										ids_maquina2_PercentualTotal.append(i/float(self.physicalMachines[host].informations['totalTime']))
								ids_maquina2_PercentualRelativo = []
								for i in ids_maquina2_PercentualTotal:
									if len(ids_maquina2_PercentualRelativo) < 10:
										ids_maquina2_PercentualRelativo.append(i*(self.physicalMachines[host].informations['cores']/self.physicalMachines[host].virtualMachines[idsMachineName].informations['virtualCores']))
									else:
										ids_maquina2_PercentualRelativo = idsPercentualRelativo[1:]
										ids_maquina2_PercentualRelativo.append(i*(self.physicalMachines[host].informations['cores']/self.physicalMachines[host].virtualMachines[idsMachineName].informations['virtualCores']))
									if ids_maquina2_PercentualRelativo[-1] > 100:
										ids_maquina2_PercentualRelativo[-1] = 100.0
								procM2 = []
								for proc in range(5):
									procM2.append(ids_maquina2_PercentualRelativo[len(ids_maquina2_PercentualRelativo) - proc - 1])
								if max(procM2) + max(procM1) < 90:
									print 'descarga mano'
									os.system('ssh 69.69.69.9 /usr/local/bro/bin/broctl stop')
									enviarSobrecarga(ipControlador="69.69.69.1", mensagem="descarga")
									os.system('xm shutdown sdn_firewall_dpi2')
									self.physicalMachines[host].refreshVmList()

					# if idsMachineName == 'sdn_firewall_dpi_bro':
					# 	f1 = open('maquina_IDS1', 'a')
					# 	f1.write(str(idsPercentualRelativo[-1])+'\n')
					# 	f1.close()
					# else:
					# 	f2 = open('maquina_IDS2', 'a')
					# 	f2.write(str(idsPercentualRelativo[-1])+'\n')
					# 	f2.close()

					#string = pickle.dumps(dicionario)
		if enviar == True:
			self.iniciarSocket("69.69.69.1")
			self.enviarDicionario(processamento)
			self.socketBro.close()

	def monitoring (self, windowSize, duration, sampleInterval):
		while True:
			self.overChargedHost()
			time.sleep(float(sampleInterval*2))

sampleInterval=1 #seconds
windowSize=10	#samples
duration=400 #seconds

myManager=Manager()

myManager.startMonitoringAllHosts(sampleInterval, windowSize)
