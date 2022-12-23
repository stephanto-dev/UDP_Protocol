import socket

QUEUE_SIZE = 10
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
  message = queue[0]
  print("Pacote recebido:", message)

  # Desempacota o pacote
  message = message.split("|")

  # Obtém o endereço de destino
  ip_destination = message[1].split(":")
  address = (ip_destination[0], int(ip_destination[1]))

  # Envia o pacote para o endereço correto
  router.sendto(packet, address)

  # Remove o pacote da fila
  queueRemove()

if __name__ == "__main__":
  router = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  router.bind(("127.0.0.1", 8100))

  while True:
    print("Aguardando pacote...")
    # Recebe o pacote e decodifica
    packet, _ = router.recvfrom(1024)
    message = packet.decode("utf-8")

    # Adiciona o pacote na fila e lê o pacote
    queueAdd(message)
    handlePacket()
    