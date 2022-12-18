#UDP Client
import imp
import socket
import random
import time
from constants import *

#Função que gerar um número aleatório
def generateRandomNumber(begin_number, number_of_decimals):
    random_int = random.randrange(begin_number, ((10**number_of_decimals) -1))
    return random_int

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 4455
    addr = (host, port)

    while True:
        #Reseta variáveis
        msg_to_answer = ""
        msg_received_string = ""

        #AF_INET = indica que é um protocolo de endereço ip
        #SOCK_DGRAM = indica que é um protocolo da camada de transporte UDP
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #Gera número aleatório de até 10 casas
        random_int_to_send = generateRandomNumber(
            begin_number = 1,
            number_of_decimals = random.randrange(1, 10)
        )

        #Converte o número para string
        msg_to_send = str(random_int_to_send)
        print(f"Mensagem enviada para o servidor: {msg_to_send}")

        #Envia a mensagem para o servidor
        client.sendto(msg_to_send.encode("utf-8"), addr)

        #Recebe a mensagem do servidor
        msg_bytes, address = client.recvfrom(1024)

        #Converte a mensagem recebida
        msg_received_string = msg_bytes.decode("utf-8")
        print(f"Mensagem recebida do servidor: {msg_received_string}")

        msg_to_send = msg_received_string + " ACK"
        print(f"Mensagem enviada para o servidor: {msg_to_send}")

        #Envia a mensagem para o servidor
        client.sendto(msg_to_send.encode("utf-8"), addr)

        #Fecha a conexão e aguarda 10 segundos
        client.close()
        if msg_received_string.__contains__("Janela de recepção: 0"):
            for i in range(3):
                print(str(10-i) + "s")
                time.sleep(1)
