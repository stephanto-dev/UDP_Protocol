#UDP Client
import socket
import random
import time
import sys
import atexit
from threading import Timer, Thread
from aimd import Aimd

client = None
addr = None
connectedWithServer = False

BUFFER_SIZE = 3
buffer = []
order = 0
duplicated_acks_count = ("", 0)

timer = None
resend = False
rwnd = 1
aimd = Aimd()

buffer_rtt = {}
estimated_rtt = 1
dev_rtt = 1
timeout_interval = 5

qtd_timeouts = 0
qtd_3_duplicated_acks = 0

#Função que gerar um número aleatório
def generateRandomNumber(begin_number, number_of_decimals):
    random_int = random.randrange(begin_number, ((10**number_of_decimals) -1))
    return random_int

#Função que inicia o timer
def newTimer():
    global timer
    timer = Timer(timeout_interval, timeout)

#Função que reseta o timer
def resetTimer():
    global timer
    if timer != None: 
        timer.cancel()
    newTimer()
    timer.start()

#Função executada quando ocorre timeout
def timeout():
    global buffer
    global resend
    global timeout_interval
    global qtd_timeouts

    resend = True
    qtd_timeouts += 1
    print('timeout')

    aimd.timeout()
    resendPacket()

#Função que calcula o intervalo de timeout
def calculateTimeoutInterval():
    global estimated_rtt
    global dev_rtt
    global timeout_interval
    global buffer_rtt

    sum_rtt = 0
    qtd_rtt = 0

    theta = 0.125
    beta = 0.25

    #Obtém a soma dos RTT
    for message in buffer_rtt:
        if "stop" in buffer_rtt[message]:
            rtt = buffer_rtt[message]["stop"] - buffer_rtt[message]["start"]
            sum_rtt += rtt
            qtd_rtt += 1  
    
    #Realiza a média dos RTT e faz a estimação
    if qtd_rtt > 0:
        sample_rtt = sum_rtt / qtd_rtt
        estimated_rtt = (1 - theta) * estimated_rtt + theta * sample_rtt
        dev_rtt = (1 - beta) * dev_rtt + beta * abs(sample_rtt - estimated_rtt)
        timeout_interval = estimated_rtt + 4 * dev_rtt + 3

    #Reseta o buffer
    buffer_rtt = {}

#Função para adicionar um cabeçalho IP e enviar o pacote para o roteador
def sendPacket(address, message):
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
      buffer_rtt[message] = {
        "start": time.perf_counter()
      }

    #Envia o pacote para o roteador
    router = ("127.0.0.1", 8100)
    client.sendto(packet.encode("utf-8"), router)

    # print(f"Mensagem enviada para o servidor: {message}")

#Função que reenvia os pacotes do buffer caso ocorra timeout
def resendPacket():
    global rwnd
    global timer
    global buffer
    global resend    

    if rwnd > 0:
        print('----------------- Pacotes reenviados ----------------')    
        #Obtém endereço da instância
        source_ip = client.getsockname()
        source_ip = source_ip[0] + ":" + str(source_ip[1])

        #Adiciona o cabeçalho IP no pacote
        destination_ip = addr[0] + ":" + str(addr[1])
        IP_header = source_ip + "|" + destination_ip

        #Se tiver pacote no buffer, reenvia
        for message in buffer:
            #Coleta a mensagem do buffer e empacota
            packet = IP_header + "|" + message
            
            router = ("127.0.0.1", 8100)

            print(f"Mensagem re-enviada para o servidor: {message}")
            client.sendto(packet.encode("utf-8"), router)
        print('-------------------------------------------------')

        resend = False
        # resetTimer()

#Função para lidar com ACKs
def handleACK(message):
    global duplicated_acks_count
    global buffer
    global resend
    global rwnd
    global qtd_3_duplicated_acks

    #Obtém o tipo e conteúdo da mensagem e a janela de recepção
    splitted_message = message.split("-")
    message_type = splitted_message[0]
    message_content = splitted_message[1]
    rwnd = int(splitted_message[2][4:])

    #Verifica se mensagem não é um ACK para remover do buffer
    if message_type == "ack":
        print(f"ACK da mensagem {message_content} recebido")
        message_content = "message-" + message_content

        #Se a mensagem estiver no buffer, é retirada e o timer é resetado
        if message_content in buffer:
            buffer.remove(message_content)
            buffer_rtt[message_content] = {
                "start": buffer_rtt[message_content]["start"],
                "stop": time.perf_counter()
            }
            aimd.receiveNewAck()
            resetTimer()
        else:
            if duplicated_acks_count[0] == message_content:
                duplicated_acks_count = (message_content, duplicated_acks_count[1] + 1)
            else:
                duplicated_acks_count = (message_content, 1)
            #Se receber 3 acks duplicados reenvia os pacotes
            if duplicated_acks_count[1] == 3:
                qtd_3_duplicated_acks += 1
                print('3 acks')
                duplicated_acks_count = ("", 0)
                aimd.receiveThreeDuplicatedAck()
                if resend == False:
                    resend_packet_thread = Thread(None, resendPacket)
                    resend_packet_thread.start()
                resend = True

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

#Função que desconecta o cliente e fecha o programa
def close():
    global qtd_timeouts
    global qtd_3_duplicated_acks

    print("Quantidade de timeouts ocorridos:", qtd_timeouts)
    print("Quantidade de 3 ACKs duplicados ocorridos:", qtd_3_duplicated_acks)
    exitHandler()
    sys.exit()

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 4455
    addr = (host, port)

    #Interrompe o programa em 10 minutos
    stop_program = Timer(600, close)
    stop_program.start()

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
        msg_received_string = ""
        
        # print(f"Mensagens sem ACK: {buffer}")

        #Se não tiver mensagens no buffer e não estiver re-enviando mensagens,
        #Então envia vários pacotes de uma vez limitado pelo mínimo entre cwnd e rwnd
        if len(buffer) == 0 and resend == False:
            #Recalcula o intervalo de timeout a cada aproximadamente 64 pacotes
            if len(buffer_rtt) > 64:
                calculateTimeoutInterval()
            print('----------------- Pacotes enviados ----------------')
            print('cwnd', aimd.cwnd, 'rwnd', rwnd)
                
            while len(buffer) < min(aimd.cwnd, rwnd):
                #Gera número aleatório de até 10 casas
                random_int_to_send = generateRandomNumber(
                    begin_number = 1,
                    number_of_decimals = random.randrange(1, 10)
                )

                #Converte o número para string e envia com o tipo message
                msg_to_send = "message-" + str(random_int_to_send) + "?" + str(order)
                sendPacket(addr, msg_to_send)
                resetTimer()
                order = order + 1
            print('-------------------------------------------------')

        #Recebe a mensagem do servidor
        msg_received_string, address = receivePacket()

        handleACK(msg_received_string)

        # print(f"Mensagem recebida do servidor: {msg_received_string}")

        #Aguarda período de tempo de acordo com a janela de recepção
        # if rwnd == 0:
        #     for i in range(10):
        #         print(str(10-i) + "s")
        #         time.sleep(1)
        # elif len(buffer) == 0:
        #     for i in range(3):
        #         print(str(3-i) + "s")
        #         time.sleep(1)
