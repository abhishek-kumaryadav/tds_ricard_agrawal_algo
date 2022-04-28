# BT18CSE106
# Abhishek Kumar Yadav
# Lamport’s Distributed Mutual Exclusion Algorithm

from ast import arg
from socket import socket, AF_INET, SOCK_STREAM
from queue import Queue
from threading import Thread
import argparse
import time
import sys


class Node:
    def __init__(self, port, other_ports, log_file):
        self.log_file = log_file
        self.request_queue = []
        self.timestamp = 0
        self.port = port
        self.canStart = dict()
        self.isCritical = False
        for other_port in other_ports:
            self.canStart[other_port] = 0
            print(time.strftime("%H:%M:%S", time.localtime()), other_port)
            self.log_file.flush()
        self.other_ports = other_ports
        self.isRequesting = False
        self.socket = socket(AF_INET, SOCK_STREAM)
        self.socket.bind(("", port))
        self.socket.listen()
        connection_acceptor = Thread(target=self.connectin_acceptor)
        connection_acceptor.start()
        self.criticalTime = 0
        r = Thread(target=self.requestor)
        r.start()

    def __repr__(self) -> str:
        return "Port: {}, Other ports: {}, {}, Log file: {}".format(
            self.port, self.other_ports[0], self.other_ports[1], self.log_file
        )

    def requestor(self):
        print(
            time.strftime("%H:%M:%S", time.localtime()),
            "Requestor started on port: ",
            self.port,
        )
        self.log_file.flush()
        while True:
            x = input("Enter s to send critical section requests")
            self.log_file.flush()
            if x != "S" and x != "s":
                continue
            print(
                time.strftime("%H:%M:%S", time.localtime()),
                "Will send requests to get critical section",
            )
            self.isRequesting = True
            if self.isCritical:
                self.criticalTime += 1
            else:
                for port in self.other_ports:
                    with socket(AF_INET, SOCK_STREAM) as s:
                        print(
                            time.strftime("%H:%M:%S", time.localtime()),
                            "Sending request from: ",
                            self.port,
                            ", to: ",
                            port,
                        )
                        self.log_file.flush()
                        s.connect(("127.0.0.1", port))
                        s.send("C".encode("utf-8"))
                        s.send(int.to_bytes(self.port, 2, "little"))
                        s.send(int.to_bytes(self.timestamp, 1, "little"))

    def critical(self):
        while self.criticalTime > 0:
            self.criticalTime -= 1
            print(
                time.strftime("%H:%M:%S", time.localtime()),
                "Entering critical section!!",
            )
            self.isCritical = True
            time.sleep(5)
            print(
                time.strftime("%H:%M:%S", time.localtime()),
                "Releasing critical section!!",
            )
            self.log_file.flush()
            self.isCritical = False

    def talker(self, address, connection):
        type = connection.recv(1).decode("utf-8")
        print(time.strftime("%H:%M:%S", time.localtime()), "Got", type, "from", address)
        self.log_file.flush()

        if type == "C":
            other = int.from_bytes(connection.recv(2), "little")
            timestamp = int.from_bytes(connection.recv(1), "little")
            while self.isCritical:
                time.sleep(2)
            if self.isRequesting:
                if self.timestamp > timestamp:
                    with socket(AF_INET, SOCK_STREAM) as s:
                        print(
                            time.strftime("%H:%M:%S", time.localtime()),
                            "Sending reply from: ",
                            self.port,
                            ", to: ",
                            other,
                        )
                        self.log_file.flush()
                        s.connect(("127.0.0.1", other))
                        s.send("A".encode("utf-8"))
                        s.send(int.to_bytes(self.port, 2, "little"))
            else:
                with socket(AF_INET, SOCK_STREAM) as s:
                    print(
                        time.strftime("%H:%M:%S", time.localtime()),
                        "Sending reply from: ",
                        self.port,
                        ", to: ",
                        other,
                    )
                    self.log_file.flush()
                    s.connect(("127.0.0.1", other))
                    s.send("A".encode("utf-8"))
                    s.send(int.to_bytes(self.port, 2, "little"))

        elif type == "A":
            other = int.from_bytes(connection.recv(2), "little")
            self.canStart[int(other)] = 1
            print(time.strftime("%H:%M:%S", time.localtime()), "Got ack from :", other)
            print(time.strftime("%H:%M:%S", time.localtime()), self.canStart)
            self.log_file.flush()
            if sum(self.canStart.values()) == len(self.other_ports):
                self.isRequesting = False
                for other_port in self.other_ports:
                    self.canStart[other_port] = 0
                self.timestamp += 1
                self.criticalTime += 1
                self.critical()
                print(self.request_queue)
                self.log_file.flush()
                for port in self.request_queue:
                    with socket(AF_INET, SOCK_STREAM) as s:
                        print(
                            time.strftime("%H:%M:%S", time.localtime()),
                            "Sending reply from: ",
                            self.port,
                            ", to: ",
                            port,
                        )
                        self.log_file.flush()
                        s.connect(("127.0.0.1", port))
                        s.send("A".encode("utf-8"))
                        s.send(int.to_bytes(self.port, 2, "little"))
                while len(self.request_queue):
                    self.request_queue.pop(0)

    def connectin_acceptor(self):
        while True:
            c, addr = self.socket.accept()
            print(
                time.strftime("%H:%M:%S", time.localtime()),
                "Connection Recieved from ",
                addr,
            )
            connection_thread = Thread(target=self.talker, args=(addr, c))
            connection_thread.start()
            self.log_file.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i")
    args = parser.parse_args()
    ports = [8000, 9000, 10000]
    i = int(args.i)
    log_file = open("ricard{}.log".format(i), "w")
    sys.stdout = log_file
    port = ports[i]
    ports.remove(ports[i])
    node = Node(port, ports, log_file)
    print(time.strftime("%H:%M:%S", time.localtime()), node)
