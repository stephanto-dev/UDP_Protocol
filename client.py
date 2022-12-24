#UDP Client
import socket
import random
import time
import sys
import atexit
from threading import Timer

client = None
addr = None
connectedWithServer = False

BUFFER_SIZE = 3
# cwnd = BUFFER_SIZE
buffer = []
# queue = []
order = 0
duplicated_acks_count = ("", 0)
timer = None
resend = False

#Função que gerar um número aleatório
def generateRandomNumber(begin_number, number_of_decimals):
    random_int = random.randrange(begin_number, ((10**number_of_decimals) -1))
    return random_int

#Função que inicia o timer
def newTimer():
    global timer
    timer = Timer(10, resendPacket)

#Função que reseta o timer
def resetTimer():
    global timer
    if timer != None: 
        timer.cancel()
    newTimer()
    timer.start()

#Função para adicionar um cabeçalho IP e enviar o pacote para o roteador
def sendPacket(address, message):
    global cwnd
    
    print(f"Mensagens sem ACK: {buffer}")

    #Obtém endereço da instância
    source_ip = client.getsockname()
    source_ip = source_ip[0] + ":" + str(source_ip[1])

    #Adiciona o cabeçalho IP no pacote
    destination_ip = address[0] + ":" + str(address[1])
    IP_header = source_ip + "|" + destination_ip
    packet = IP_header + "|" + message

    #Salva mensagem no buffer
    if message.find('connect') == -1:
      buffer.append(message)

    #Envia o pacote para o roteador
    router = ("127.0.0.1", 8100)
    client.sendto(packet.encode("utf-8"), router)

    print(f"Mensagem enviada para o servidor: {message}")

#Função que reenvia os pacotes do buffer caso ocorra timeout
def resendPacket():
    global buffer
    global timer
    global resend

    resend = True
    
    #Obtém endereço da instância
    source_ip = client.getsockname()
    source_ip = source_ip[0] + ":" + str(source_ip[1])

    #Adiciona o cabeçalho IP no pacote
    destination_ip = addr[0] + ":" + str(addr[1])
    IP_header = source_ip + "|" + destination_ip

    if len(buffer) > 0:
        #Coleta a mensagem do buffer
        temporary_message = buffer[0]
        packet = IP_header + "|" + temporary_message

        #Envia para o servidor
        router = ("127.0.0.1", 8100)

        print(f"Mensagem re-enviada para o servidor: {temporary_message}")
        client.sendto(packet.encode("utf-8"), router)

#Função para lidar com ACKs
def handleACK(message):
    global duplicated_acks_count
    global buffer
    global resend

    splitted_message = message.split("-")
    message_type = splitted_message[0]
    message_content = splitted_message[1]
    rwnd = splitted_message[2][4:]

    #Verifica se mensagem não é um ACK para remover do buffer
    if message_type == "ack":
        print(f"ACK da mensagem {message_content} recebido")
        message_content = "message-" + message_content

        #Verifica se tem ack duplicado
        if message_content in buffer:
            buffer.remove(message_content)
            if resend and len(buffer) == 0:
                resend = False
            else:
                resetTimer()
        else:
            duplicated_acks_count = (message_content, duplicated_acks_count[1] + 1)
            if duplicated_acks_count[1] == 3:
                duplicated_acks_count = ("", 0)
                resendPacket()

#Função que decodifica o pacote do roteador
def receivePacket():
    #Recebe a mensagem do cliente
    packet, _ = client.recvfrom(1024)

    #Converte a mensagem recebida
    message = packet.decode("utf-8").split("|")
    message_content = message[2]
    
    # Obtém o endereço de origem
    ip_source = message[0].split(":")
    address = (ip_source[0], ip_source[1])

    # Retorna o conteúdo da mensagem e o endereço de origem
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
    if msg_received_string.find('connected') != -1:
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
        if resend:
            resendPacket()
        else:
            sendPacket(addr, msg_to_send)
            resetTimer()
            order = order + 1
            
        #Recebe a mensagem do servidor
        msg_received_string, address = receivePacket()

        handleACK(msg_received_string)

        print(f"Mensagem recebida do servidor: {msg_received_string}")

        #Aguarda período de tempo de acordo com a janela de recepção
        if msg_received_string.find("-rwnd0") != -1:
            for i in range(10):
                print(str(10-i) + "s")
                time.sleep(1)
        else:
            for i in range(3):
                print(str(3-i) + "s")
                time.sleep(1)
