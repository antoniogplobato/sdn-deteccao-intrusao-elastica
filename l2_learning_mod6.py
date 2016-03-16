from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str
from pox.lib.util import str_to_bool
import time
from pox.lib.revent import *
from pox.lib.addresses import EthAddr, IPAddr
from collections import namedtuple
import pox.lib.packet as pkt
import os
import string
from socket import *
import thread
from balancearv9 import *
import pickle

log = core.getLogger()

# We don't want to flood immediately when a switch connects.
# Can be overriden on commandline.
_flood_delay = 0

def listarFluxosIp(event):
	global fluxosIp
	global listaIDS
	fluxosIp = []
	if ipBro != None:
		for fluxo in event.stats:
			#print 'Um dos Fluxos Atuais'
			#print fluxo.match
			if fluxo.match.nw_src == IPAddr(ipBro):
				fluxosIp.append(fluxo.match)
				msg = of.ofp_flow_mod()
				msg.match = fluxo.match
				msg.idle_timeout = 60
				msg.hard_timeout = 60
				msg.priority = 65535
				event.connection.send(msg)
				removerFluxo(listaIDS, fluxo.match)
				print 'Fluxo barrado'
				print listaIDS
				#print fluxo.match
			msg = of.ofp_flow_mod()
			msg.match.dl_type = 0x800
			msg.match.nw_src = IPAddr(ipBro)
			msg.idle_timeout = 60
			msg.hard_timeout = 60
			msg.priority = 65535
			event.connection.send(msg)
			#print 'Ip barrado', ipBro
		#print fluxosIp

def redistribuirFluxos(event):
	global listaIDS
	global listaIDSold
	global pronto
	if mensagem != None:
		removerTodosFluxos(listaIDS)
		#print 'limpou'
		for fluxo in event.stats:
			#print 'fluxo'
			msg = of.ofp_flow_mod()
			msg.match = fluxo.match
			msg.idle_timeout = 60
			msg.hard_timeout = 60
			msg.priority = 65535
			portas = []
			for i in listaIDSold:
				portas.append(i.porta)
			#print portas
			for action in fluxo.actions:
				#print action.port
				if action.port not in portas:
					msg.actions.append(of.ofp_action_output(port = action.port))
				else:
					pronto = False
					while True:
						if pronto == True:
							# time.sleep(2)
							# print 'esperando'
							break
					#print 'Mundanca'
					#print action.port
					for maquina in listaIDS:
						print maquina.nome
						print maquina.processamento
					portaDesvio = inserirFluxo(listaIDS, fluxo.match)
					#print portaDesvio
					if portaDesvio != None:
						msg.actions.append(of.ofp_action_output(port = portaDesvio))
						msg.flags = of.OFPFF_SEND_FLOW_REM
			event.connection.send(msg)

def servidorSocket():
	global ipBro
	global mensagem
	porta = 5000
	socketControlador = socket(AF_INET,SOCK_STREAM)
	socketControlador.bind(('',porta))
	socketControlador.listen(1)
	#print 'O servidor esta funcionando'
	while 1:
		conexao, endereco = socketControlador.accept()
		mensagem = None
		ipBro = conexao.recv(1024)
		#print 'IPs atacando: \n', ipBro
		conexao.close()
		for switchControlado in core.openflow.connections:
			switchControlado.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
	thread.exit()

def servidorSocketSobrecarga():
	global listaIDS
	global listaIDSold
	global ipBro
	global mensagem
	global pronto
	CAPACIDADE = 50
	listaIDS=[]
	inserirMaquina(listaIDS, 'sdn_firewall_dpi_bro', 6)
	porta = 3000
	socketControlador = socket(AF_INET,SOCK_STREAM)
	socketControlador.bind(('',porta))
	socketControlador.listen(1)
	#print 'O servidor esta funcionando'
	while 1:
		conexao, endereco = socketControlador.accept()
		ipBro = None
		listaIDSold = listaIDS[:]
		mensagem = conexao.recv(1024)
		#print 'Alarme recebido\n'
		if mensagem == "sobrecarga":
			inserirMaquina(listaIDS, 'sdn_firewall_dpi2', 4)
			pronto=False
			while True:
				#print 'peeeera'
				if pronto == True:
					break
		elif mensagem == "descarga":
			removerMaquina(listaIDS, 4)
		conexao.close()
		for switchControlado in core.openflow.connections:
			switchControlado.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))
	thread.exit()

def servidorProcessamento():
	global listaIDS
	global pronto
	pronto = False
	porta = 4000
	socketControlador = socket(AF_INET,SOCK_STREAM)
	socketControlador.bind(('',porta))
	socketControlador.listen(1)
	print 'O servidor esta funcionando'
	while 1:
		conexao, endereco = socketControlador.accept()
		processamentoStr = conexao.recv(1024)
		processamento = pickle.loads(processamentoStr)
		#print 'processamento: \n', processamento
		for maquina in listaIDS:
			if maquina.nome in processamento.keys():
				maquina.processamento = processamento[maquina.nome]
		#if pronto == False:
		# print "salvando processamento"
		# for i in listaIDS:
		# 	print i.nome
		# 	print i.processamento
		# print "salvo"
		pronto = True
		conexao.close()
	thread.exit()

class LearningSwitch (object):
	def __init__ (self, connection, transparent):
		# Switch we'll be adding L2 learning switch capabilities to
		self.connection = connection
		self.transparent = transparent

		# Our table
		self.macToPort = {}

		# We want to hear PacketIn messages, so we listen
		# to the connection
		connection.addListeners(self)

		# We just use this to know when to log a helpful message
		self.hold_down_expired = _flood_delay == 0

		#log.debug("Initializing LearningSwitch, transparent=%s",
		#          str(self.transparent))

	def _handle_PacketIn (self, event):
		packet = event.parsed
		portaEntrada = event.port

		def flood (message = None):
			""" Floods the packet """
			msg = of.ofp_packet_out()
			if time.time() - self.connection.connect_time >= _flood_delay:
				# Only flood if we've been connected for a little while...

				if self.hold_down_expired is False:
					# Oh yes it is!
					self.hold_down_expired = True
					log.info("%s: Flood hold-down expired -- flooding",
							dpid_to_str(event.dpid))

				if message is not None: log.debug(message)
				#log.debug("%i: flood %s -> %s", event.dpid,packet.src,packet.dst)
				# OFPP_FLOOD is optional; on some switches you may need to change
				# this to OFPP_ALL.
				msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
			else:
				pass
				#log.info("Holding down flood for %s", dpid_to_str(event.dpid))
			msg.data = event.ofp
			msg.in_port = event.port
			self.connection.send(msg)

		def drop (duration = None):
			if duration is not None:
				if not isinstance(duration, tuple):
					duration = (duration,duration)
				msg = of.ofp_flow_mod()
				msg.match = of.ofp_match.from_packet(packet)
				msg.idle_timeout = duration[0]
				msg.hard_timeout = duration[1]
				msg.buffer_id = event.ofp.buffer_id
				self.connection.send(msg)
			elif event.ofp.buffer_id is not None:
				msg = of.ofp_packet_out()
				msg.buffer_id = event.ofp.buffer_id
				msg.in_port = event.port
				self.connection.send(msg)

		self.macToPort[packet.src] = event.port # 1

		if not self.transparent: # 2
			if packet.type == packet.LLDP_TYPE or packet.dst.isBridgeFiltered():
				drop() # 2a
				return

		if packet.dst.is_multicast:
			flood() # 3a
		else:
			if packet.dst not in self.macToPort: # 4
				flood("Port for %s unknown -- flooding" % (packet.dst,)) # 4a
			else:
				port = self.macToPort[packet.dst]
				if port == event.port: # 5
					# 5a
					log.warning("Same port for packet from %s -> %s on %s.%s.  Drop."
							% (packet.src, packet.dst, dpid_to_str(event.dpid), port))
					drop(10)
					return
				# 6
				log.debug("installing flow for %s.%i -> %s.%i" %
									(packet.src, event.port, packet.dst, port))
				msg = of.ofp_flow_mod()
				msg.match = of.ofp_match.from_packet(packet, event.port)
				msg.idle_timeout = 10
				msg.hard_timeout = 30
				msg.actions.append(of.ofp_action_output(port = port))
				eths = [1, 5, 8, 9]
				if (portaEntrada not in eths):
					ip_packet = packet.find('ipv4')
					if ip_packet is not None:
						portaDesvio2 = inserirFluxo(listaIDS, msg.match)
						msg.actions.append(of.ofp_action_output(port = portaDesvio2))
						msg.flags = of.OFPFF_SEND_FLOW_REM
				msg.data = event.ofp # 6a
				self.connection.send(msg)

	def _handle_FlowRemoved(self, event):
		#print 'fluxo removido'
		removerFluxo(listaIDS, event.ofp.match)
		#print listaIDS
		
		
class l2_learning (object):
	def __init__ (self, transparent):
		core.openflow.addListeners(self)
		self.transparent = transparent

	def _handle_ConnectionUp (self, event):
		log.debug("Connection %s" % (event.connection,))
		thread.start_new_thread(servidorSocket, tuple([]))
		thread.start_new_thread(servidorSocketSobrecarga, tuple([]))
		thread.start_new_thread(servidorProcessamento, tuple([]))
		print event.dpid
		LearningSwitch(event.connection, self.transparent)


def launch (transparent=False, hold_down=_flood_delay):
	"""
	Starts an L2 learning switch.
	"""
	try:
		global _flood_delay
		_flood_delay = int(str(hold_down), 10)
		assert _flood_delay >= 0
	except:
		raise RuntimeError("Expected hold-down to be a number")

	core.openflow.addListenerByName("FlowStatsReceived", listarFluxosIp)
	core.openflow.addListenerByName("FlowStatsReceived", redistribuirFluxos)
	core.registerNew(l2_learning, str_to_bool(transparent))

