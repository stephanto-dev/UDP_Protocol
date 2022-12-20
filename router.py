import socket

router = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
router.bind(("127.0.0.1", 8100))

while True:
  print("Aguardando pacote...")
  # Recebe o pacote e decodifica
  packet, address = router.recvfrom(1024)
  message = packet.decode("utf-8")
  print("Pacote recebido:", message)

  # Desempacota o pacote
  message = message.split("|")
  
  # Obtém o endereço de destino
  ip_destination = message[1].split(":")
  address = (ip_destination[0], int(ip_destination[1]))

  # Envia o pacote para o endereço correto
  router.sendto(packet, address)
