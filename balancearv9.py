from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
from pox.lib.revent import *
from pox.lib.addresses import EthAddr, IPAddr
import pox.lib.packet as pkt

class Maquina():
	def __init__(self, nome, porta, processamento = 0.1):
		self.nome = nome
		self.porta = porta
		self.fluxos = []
		self.processamento = processamento


def inserirFluxo(listaMaquinas,fluxo):
	novo=fluxo
	lugarAtual=0
	pesoRef=100
	porta = None
	limite = 90
	listaIPdest=[]
	listaIPorig=[]
	if len(listaMaquinas) > 1:
		for i in range(len(listaMaquinas)):
			pesoAtual = listaMaquinas[i].processamento
			if (novo.nw_src == IPAddr('192.168.6.2')) or (novo.nw_src == IPAddr('192.168.7.2')):
				lugarRef = 0
				break
			elif (novo.nw_src == IPAddr('192.168.8.2')) or (novo.nw_src == IPAddr('192.168.9.2')):
				lugarRef = 1
				break
			if (pesoAtual<pesoRef):
				pesoRef=pesoAtual
				lugarRef=i
			for match in listaMaquinas[i].fluxos:
				listaIPorig.append(match.nw_src)
				listaIPdest.append(match.nw_dst)
			if ((novo.nw_src in listaIPorig) or ((novo.nw_src in listaIPdest) and (novo.nw_dst in listaIPorig))) and (pesoAtual<limite):
				# for ipOrigem in listaMaquinas[i][0]:
				# 	# if (ipOrigem!=novo):
				# 	# 	listaMaquinas[i][0].remove(ipOrigem)
				# 	# 	inserirFluxo(listaMaquinas,ipOrigem)
				lugarRef=i
				break
	else:
		lugarRef = 0
	listaMaquinas[lugarRef].fluxos.append(novo)
	porta = listaMaquinas[lugarRef].porta
	# print 'fluxo incluido'
	# for i in listaMaquinas:
	# 	print i.nome
	# 	print i.processamento
	# 	for j in i.fluxos:
	# 		print j.nw_src
	return porta

def removerFluxo(listaMaquinas,fluxo):
	for maquinas in range(len(listaMaquinas)):
		if fluxo in listaMaquinas[maquinas].fluxos:
			listaMaquinas[maquinas].fluxos.remove(fluxo)
			break

def removerTodosFluxos(listaMaquinas):
	for maquina in range(len(listaMaquinas)):
		listaMaquinas[maquina].fluxos = []
				

def inserirMaquina(listaMaquinas, nome, porta):
	listaMaquinas.append(Maquina(nome, porta))

def removerMaquina(listaMaquinas, porta):
	achou = 0
	maquina = 0
	for maquina in range(len(listaMaquinas)):
		if(listaMaquinas[maquina].porta == porta):
			achou = 1
			break
	if(achou == 1):
		novaLista = listaMaquinas[maquina].fluxos
		del listaMaquinas[maquina]
		# print novaLista
		for fluxo in novaLista:
			# print fluxo
			inserirFluxo(listaMaquinas,fluxo)


def zero():
	print ('maquina com quantos fluxos de capacidade?')
	aux=int(raw_input())
	inserirMaquina(maquinas,aux, 0)

def um():
	print ('Digite o novo IP')
	aux=raw_input()
	inserirFluxo(maquinas,aux)

def dois():
	print ('Digite o IP para ser removido')
	aux=raw_input()
	print ('Digite a maquina onde tem esse IP')
	aux2=int(raw_input())
	removerFluxo(maquinas,aux2,aux)

def tres():
	print ('Digite a maquina que voce quer remover')
	aux=int(raw_input())
	removerMaquina(maquinas,aux)

# maquinas={}
# limite=0.8

# opcoes={0:zero,1:um,2:dois,3:tres}


# while(1):
# 	print ('Digite:\n[0] Para inserir uma maquina\n[1] Para inserir um fluxo\n[2] Para remover um fluxo\n[3] Para remover uma maquina')
# 	aux=int(raw_input())
# 	opcoes[aux]()
# 	print(maquinas)
