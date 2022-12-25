class Aimd:
  ssthresh = 32
  cwnd = 1

  def receiveNewAck(self):
    if self.cwnd < self.ssthresh:
      # Partida lenda
      self.cwnd += 1
    else:
      # Prevenção de congestionamento
      self.cwnd = self.cwnd + 1 / self.cwnd
  
  def receiveThreeDuplicatedAck(self):
    self.ssthresh = self.cwnd / 2
    self.cwnd = self.ssthresh + 3
  
  def timeout(self):
    self.ssthresh = self.cwnd / 2
    self.cwnd = 1
    