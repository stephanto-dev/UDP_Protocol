#UDP Server
import socket

LIMIT = 2
BUFFER_SIZE = 32
connections = []
server = None
buffer = []
rwnd = BUFFER_SIZE 

#Função que adiciona mensagem ao buffer
def bufferAdd(message, address):
    global buffer
    global rwnd

    buffer.append((address, message))
    rwnd -= 1

#Função que retira mensagem do buffer
def bufferRemove(packet):
    global buffer
    global rwnd

    buffer.remove(packet)
    rwnd += 1

#Função que remove todos pacotes de um endereço do buffer
def bufferAddressDrop(address):
    global buffer
    global rwnd

    filteredBuffer = [i for i in buffer if i[0] != address]

    buffer = filteredBuffer

    rwnd = BUFFER_SIZE - len(buffer)

#Função que retorna a última tupla do buffer a partir de um endereço
def getLastPacketFromAddressInBuffer(address):
    global buffer

    packets = [i for i in buffer if i[0] == address]
    return packets[len(packets) - 1]

#Função para adicionar um cabeçalho IP e enviar o pacote para o roteador
def sendPacket(address, message):
    #Adiciona o cabeçalho IP no pacote
    source_ip = "127.0.0.1:4455"
    destination_ip = address[0] + ":" + str(address[1])
    IP_header = source_ip + "|" + destination_ip
    packet = IP_header + "|" + message

    #Envia o pacote para o roteador
    router = ("127.0.0.1", 8100)
    server.sendto(packet.encode("utf-8"), router)

#Função que decodifica o pacote do roteador
def receivePacket():
    #Recebe a mensagem do cliente
    packet, _ = server.recvfrom(1024)

    #Converte a mensagem recebida
    message = packet.decode("utf-8").split("|")
    
    # Obtém o endereço de origem
    ip_source = message[0].split(":")
    address = (ip_source[0], ip_source[1])

    # Retorna o conteúdo da mensagem e o endereço de origem
    return message[2], address

#Função que abre canal para ouvir próxima mensagem do cliente
def listenMessages():
    msg_received_str, address = receivePacket()
    msg_received_str = msg_received_str.split("-")

    bufferAdd("".join(msg_received_str), address)

    sendAck(msg_received_str, address)

#Função que envia ACK de mensagem recebida para o cliente
def sendAck(msg_received_str, address):
    msg_order_split = msg_received_str[1].split("?")
    msg_received_int = int(msg_order_split[0])

    #Verifica se a mensagem recebida existe
    if msg_received_str !="":
        print(f"Mensagem recebida do cliente: {msg_received_str[1]} \n | Número recebido: {msg_received_int}")

        #Envia ACK para o cliente
        msg_to_answer = "ack-" + msg_received_str[1] + "-rwnd" + str(rwnd)
        sendPacket(address, msg_to_answer)
        print(f"Mensagem enviada para o cliente: {msg_to_answer}")

#Função que manipula solicitações de conexão do cliente
def handleConnection(message_content, address):
    global rwnd
    if message_content in connections: return

    #Devolve mensagem de falha na conexão, caso limite de sockets tenha sido atingido
    if len(connections) >= LIMIT:
      msg_to_answer = "failed"
      sendPacket(address, msg_to_answer)
      print(f"Conexao recusada com o cliente: {message_content}, Janela de Recepção:{rwnd}")

      return

    #Adiciona cliente ao array de conexões
    connections.append(message_content)

    #Devolve mensagem de sucesso na conexão
    msg_to_answer = "connected-rwnd" + str(rwnd)
    sendPacket(address, msg_to_answer)
    print(f"Conexao estabelecida com o cliente: {message_content}, Janela de Recepção:{rwnd}")

    #Ativa listen para a próxima mensagem
    listenMessages()

#Função que remove conexões de cliente
def handleDisconnection(message_content, address):
    global rwnd

    if message_content in connections:
        connections.remove(message_content)

    msg_to_answer = "disconnected"
    msg_to_send = msg_to_answer
    sendPacket(address, msg_to_send)
    print(f"Desconexão com o cliente: {message_content}")

    bufferAddressDrop(address)

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 4455

    #AF_INET = indica que é um protocolo de endereço ip
    #SOCK_DGRAM = indica que é um protocolo da camada de transporte UDP
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((host, port))

    print("Servidor UDP iniciado")

    while True:
        #Reseta o valor das variáveis
        msg_to_answer = ""
        msg_received_str = ""

        print("Aguardando mensagem do cliente...")

        #Recebe a mensagem do cliente
        message, address = receivePacket()
        message = message.split("-")
        
        #Extrai tipo e conteúdo da mensagem
        message_type = message[0]
        message_content = message[1]

        if message_type == "message":
            message_order = (message_content.split("?"))[1]
            message_order = int(message_order)

            last_message = getLastPacketFromAddressInBuffer(address)
            last_message_order = (last_message[1].split("?"))[1]
            last_message_order = int(last_message_order)

            print(f"LAST MESSAGE ORDER: {last_message_order}, MESSAGE ORDER: {message_order}")

            #Se a ordem estiver errada, descarta o pacote e envia ACK do pacote anterior
            if message_order != last_message_order + 1 and message_order > last_message_order:
                sendAck(last_message[1].split('-'), address)
                continue
            #Caso uma mensagem antiga apareça, só envia o ack
            elif message_order <= last_message_order:
                sendAck(message, address)
                continue

        #Verifica tipo da mensagem para o tratamento adequado
        if message_type == "connect":
            handleConnection(message_content, address)
        elif message_type == "disconnect":
            handleDisconnection(message_content, address)
        elif message_type == "message":
            sendAck(message, address)
            bufferRemove(getLastPacketFromAddressInBuffer(address))
            bufferAdd("-".join(message), address)
        else:
            print("Tipo de mensagem não suportado.")