import socket
from threading import Thread

QUEUE_SIZE = 1000
queue = []

router = None

#Função que adiciona um pacote na fila
def queueAdd(packet):
  global queue
  if len(queue) <= QUEUE_SIZE:
    queue.append(packet)

#Função que remove o primeiro pacote na fila
def queueRemove():
  global queue
  queue.pop(0)

#Função que desempacota o primeiro pacote da fila e envia para o endereço de destino
def handlePacket():
  packet = queue[0]

  # Desempacota o pacote
  message = packet.split("|")

  # Obtém o endereço de destino
  ip_destination = message[1].split(":")
  address = (ip_destination[0], int(ip_destination[1]))

  # Envia o pacote para o endereço correto
  router.sendto(packet.encode("utf-8"), address)

  # Remove o pacote da fila
  print("Pacote repassado:", packet)
  queueRemove()

#Função que fica só lendo pacotes e adicionando na fila
def receivePacket():
  while True:
    print("Aguardando pacote...")
    # Recebe o pacote e decodifica
    packet, _ = router.recvfrom(1024)
    message = packet.decode("utf-8")

    # Adiciona o pacote na fila e lê o pacote
    print("Pacote recebido:", message)
    queueAdd(message)

if __name__ == "__main__":
  router = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  router.bind(("127.0.0.1", 8100))

  #Inicializa uma thread para receber pacotes
  receive_packet_thread = Thread(None, receivePacket)
  receive_packet_thread.start()

  #Quando algum pacote chegar na fila será repassado
  while True:
    if len(queue) > 0:
      handlePacket()
  
    