#UDP Server
import socket
import random
import string

LIMIT = 2
BUFFER_SIZE = 3
connections = []
server = None
buffer = []
addressBuffer = []
rwnd = BUFFER_SIZE 
order = 0
orderBuffer = []

#Função que adiciona mensagem ao buffer
def bufferAdd(message, address):
    global buffer
    global addressBuffer
    global rwnd

    buffer.append(message)
    addressBuffer.append(address)
    rwnd = rwnd - 1

#Função que retira mensagem do buffer
def bufferDrop():
    global buffer
    global addressBuffer
    global rwnd

    buffer.pop(0)
    addressBuffer.pop(0)
    rwnd = rwnd + 1

#Função que gerar uma string aleatória
def randomString(chars = string.ascii_letters+string.digits ,stringLength=10):
    return ''.join(random.choice(chars) for _ in range(stringLength))

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

    bufferAdd(msg_received_str, address)

    handleMessage(buffer[0], address)

#Função que envia ACK de mensagem recebida para o cliente
def sendAck(msg_received_str, address):

    msg_order_split = msg_received_str[1].split("?")
    msg_received_int = int(msg_order_split[0])

    #Verifica se a mensagem recebida existe
    if msg_received_str !="":
        print(f"Mensagem recebida do cliente: {msg_received_str[1]} \n | Número recebido: {msg_received_int}")

        #Envia ACK para o cliente
        msg_to_answer = "ack-" + msg_received_str[1]
        sendPacket(address, msg_to_answer)
        print(f"Mensagem enviada para o cliente: {msg_to_answer}")

#Função que interpreta e responde mensagem do cliente
def handleMessage(msg_received_str, address):
    #Verifica se a mensagem recebida existe
    if msg_received_str !="":
        integer_length = len(msg_received_str[1])

        msg_to_answer = "message-" + randomString(stringLength=integer_length)
        msg_to_send = msg_to_answer + " Janela de recepção: " + str(rwnd)

        #Envia a mensagem para o cliente
        sendPacket(address, msg_to_send)
        print(f"Mensagem enviada para o cliente: {msg_to_send}")

#Função que manipula solicitações de conexão do cliente
def handleConnection(message_content, address):
    global rwnd
    bufferDrop()
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
    msg_to_answer = "connected"
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
    msg_to_send = msg_to_answer + " Janela de recepção: " + str(rwnd)
    sendPacket(address, msg_to_send)
    print(f"Desconexão com o cliente: {message_content}")

    bufferDrop()

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
        rwnd = BUFFER_SIZE

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
            print(f"MESSAGE ORDER: {message_order}")
        
        print(f"-----ORDER: {order}----")

        if message_type == "message" and message_order != order:
            sendAck(last_message, address)
            order = int(last_message[1].split("?")[1]) + 1
            continue


        bufferAdd(message, address)

        #Verifica tipo da mensagem para tratativa adequada
        if message_type == "connect":
            handleConnection(message_content, address)
        elif message_type == "disconnect":
            handleDisconnection(message_content, address)
        elif message_type == "message":
            sendAck(message, address)
            handleMessage(message, address)
        else:
            print("Tipo de mensagem não suportado.")
        
        last_message = message
        order = order + 1
    return message_content, address

#Função que envia solicitação de conexão para o servidor
def connectWithServer(client_id):
    message = "connect-" + str(client_id)

    sendPacket(addr, message)

#Função executada antes do programa ser finalizado
def exitHandler():
    if not connectedWithServer: return

    message = "disconnect-" + str(client_id)

    sendPacket(addr, message)

#Registro da função executada antes do programa ser finalizado
atexit.register(exitHandler)

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 4455
    addr = (host, port)

    #AF_INET = indica que é um protocolo de endereço ip
    #SOCK_DGRAM = indica que é um protocolo da camada de transporte UDP
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #Vincula uma porta ao cliente
    client.bind(("127.0.0.1", 0))

    #Gera identificador do cliente
    client_id = generateRandomNumber(
        begin_number = 1,
        number_of_decimals = random.randrange(1, 10)
    )

    #Envia solicitação de conexão para o sevidor
    connectWithServer(client_id)

    #Recebe a mensagem do servidor
    msg_received_string, address = receivePacket()

    # Verifica resposta de conexão enviada pelo servidor
    if msg_received_string == "connected":
        print("Conexao estabelecida com o servidor")
        connectedWithServer = True
    else:
        print("Conexao nao estabelecida com o servidor")

        #Encerra o programa caso conexão não tenha sido estabelecida
        sys.exit()

    while True:
        #Reseta variáveis
        msg_to_answer = ""
        msg_received_string = ""

        #Gera número aleatório de até 10 casas
        random_int_to_send = generateRandomNumber(
            begin_number = 1,
            number_of_decimals = random.randrange(1, 10)
        )

        #Converte o número para string e envia com o tipo message
        msg_to_send = "message-" + str(random_int_to_send) + "?" + str(order)

        #Envia a mensagem para o servidor
        sendPacket(addr, msg_to_send)

        order = order + 1

        #Recebe a mensagem do servidor
        msg_received_string, address = receivePacket()

        print(f"Mensagem recebida do servidor: {msg_received_string}")

        #Aguarda período de tempo de acordo com a janela de recepção
        if(msg_received_string.__contains__("Janela de Recepção: 0")):
            for i in range(10):
                print(str(10-i) + "s")
                time.sleep(1)
        else:
            for i in range(3):
                print(str(3-i) + "s")
                time.sleep(1)
