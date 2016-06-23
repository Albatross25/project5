import SocketServer

#this functio uses scamper to ping the ip address received and returns the RTT
def get_RTT(ip_address):
    command = "scamper -c 'ping -c 1' -i " + ip_address + " |awk 'NR==2 {print $7}'|cut -d '=' -f 2"
    response = commands.getoutput(command)
    if not response:
        response = 'inf'
    return response

#this class is to start the ping server on port 45557
class MeasureHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        ip_client = self.request.recv(1024).strip()
        time = get_RTT(ip_client)
        self.request.sendall(time)

server = SocketServer.TCPServer(('', 45557), MeasureHandler)
server.serve_forever()
