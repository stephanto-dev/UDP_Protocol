#UDP Server
import socket
import random
import string
import math

LIMIT = 2
connections = []
server = None

#Função que gerar uma string aleatória
def randomString(chars = string.ascii_letters+string.digits ,stringLength=10):
    return ''.join(random.choice(chars) for _ in range(stringLength))

#Função que abre canal para ouvir próxima mensagem do cliente
def listenMessages():
    msg_bytes, address = server.recvfrom(1024)
    msg_received_str = msg_bytes.decode("utf-8").split("-")

    handleMessage(msg_received_str[1], address)

#Função que interpreta e responde mensagem do cliente
def handleMessage(msg_received_str, address):
    msg_received_int = int(msg_received_str)

    #Verifica se a mensagem recebida existe
    if msg_received_str !="":
        integer_length = int(math.log10(msg_received_int))+1
        print(f"Mensagem recebida do cliente: {msg_received_str} \n | Número recebido: {msg_received_int}")

        msg_to_answer = randomString(stringLength=integer_length)

        #Envia a mensagem para o cliente
        server.sendto(msg_to_answer.encode("utf-8"), address)
        print(f"Mensagem enviada para o cliente: {msg_to_answer}")

        #Recebe a mensagem do cliente
        msg_bytes, address = server.recvfrom(1024)

        #Converte a mensagem recebida
        msg_received_str = msg_bytes.decode("utf-8")

        print(f"Mensagem recebida do cliente: {msg_received_str}")
        print("#"*15)

#Função que manipula solicitações de conexão do cliente
def handleConnection(message_content, address):
    if message_content in connections: return

    #Devolve mensagem de falha na conexão, caso limite de sockets tenha sido atingido
    if len(connections) >= LIMIT:
      msg_to_answer = "failed"
      server.sendto(msg_to_answer.encode("utf-8"), address)
      print(f"Conexao recusada com o cliente: {message_content}")

      return

    #Adiciona cliente ao array de conexões
    connections.append(message_content)

    #Devolve mensagem de sucesso na conexão
    msg_to_answer = "connected"
    server.sendto(msg_to_answer.encode("utf-8"), address)
    print(f"Conexao estabelecida com o cliente: {message_content}")

    #Ativa listen para a próxima mensagem
    listenMessages()

#Função que remove conexões de cliente
def handleDisconnection(message_content, address):
    if message_content in connections:
        connections.remove(message_content)

    msg_to_answer = "disconnected"
    server.sendto(msg_to_answer.encode("utf-8"), address)
    print(f"Desconexão com o cliente: {message_content}")

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
        msg_bytes, address = server.recvfrom(1024)

        #Converte a mensagem recebida
        message = msg_bytes.decode("utf-8").split("-")

        #Extrai tipo e conteúdo da mensagem
        message_type = message[0]
        message_content = message[1]

        #Verifica tipo da mensagem para tratativa adequada
        if message_type == "connect":
            handleConnection(message_content, address)
        elif message_type == "disconnect":
            handleDisconnection(message_content, address)
        elif message_type == "message":
            handleMessage(message_content, address)
        else:
            print("Tipo de mensagem não suportado.")