#UDP Server
import socket
import random
import string
from constants import *

#Função que gerar uma string aleatória
def randomString(chars = string.ascii_letters+string.digits ,stringLength=10):
    return ''.join(random.choice(chars) for _ in range(stringLength))

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 4455
    buffer = []
    addressBuffer = []
    rwnd = bufferSize

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
        msg_received_str = msg_bytes.decode("utf-8")
      

        #Adiciona no Buffer
        buffer.append(msg_received_str)
        addressBuffer.append(address)
        rwnd = rwnd - 1

        #Verifica se a mensagem recebida existe
        msg_received_int = int(buffer[0])
        

        if buffer[0] !="":
            integer_length = len(buffer[0])

            print(f"Mensagem recebida do cliente: {buffer[0]} \n | Número recebido: {msg_received_int}")

            msg_to_answer = randomString(stringLength=integer_length)

            msg_to_send = msg_to_answer + " Janela de recepção: " + str(rwnd)
            

            #Envia a mensagem para o cliente
            server.sendto(msg_to_send.encode("utf-8"), addressBuffer[0])
            print(f"Mensagem enviada para o cliente: {msg_to_answer}")

            buffer.pop(0)
            addressBuffer.pop(0)
            rwnd = rwnd + 1

            #Recebe a mensagem do cliente
            msg_bytes, address = server.recvfrom(1024)

            #Converte a mensagem recebida
            msg_received_str = msg_bytes.decode("utf-8")

            print(f"Mensagem recebida do cliente: {msg_received_str}")
            print("#"*15)

