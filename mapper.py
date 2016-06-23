import sys
import SocketServer
import struct
import socket
import math
import os, urllib
import re
import threading


hostnames = ['ec2-54-85-32-37.compute-1.amazonaws.com',
             'ec2-54-193-70-31.us-west-1.compute.amazonaws.com',
             'ec2-52-38-67-246.us-west-2.compute.amazonaws.com',
             'ec2-52-51-20-200.eu-west-1.compute.amazonaws.com',
             'ec2-52-29-65-165.eu-central-1.compute.amazonaws.com',
             'ec2-52-196-70-227.ap-northeast-1.compute.amazonaws.com',
             'ec2-54-169-117-213.ap-southeast-1.compute.amazonaws.com',
             'ec2-52-63-206-143.ap-southeast-2.compute.amazonaws.com',
             'ec2-54-233-185-94.sa-east-1.compute.amazonaws.com']
dic = {}

#Class to fetch RTT from different replica servers.
class Mapper(threading.Thread):
    def __init__(self, hostname, source_ip, execute_lock):
        threading.Thread.__init__(self)
        self.host = hostname
        self.source = source_ip
        self.lock = execute_lock

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip = socket.gethostbyname(self.host)
        try:
            sock.connect((ip, 45557))
            sock.sendall(self.source)
            latency = sock.recv(1024)
        except socket.error as e:
            latency = 'inf'
        finally:
            sock.close()

        with self.lock:
             dic.update({ip:latency})

#Compute Active measurement by getting RTT's from replica servers
def replica_active(source_ip):
    
    lock = threading.Lock()
    threads = []

    for i in range(len(hostnames)):
        t = Mapper(hostnames[i], source_ip, lock)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    return dic
#Fetch lat and long with API
def fetch_lat_long(source_ip):

        KEY = '3354ce1d65dc75497a150436101899f1e4429dfff0ab58dd3bf9bab20c828359'
        data = urllib.urlopen(url = 'http://api.ipinfodb.com/v3/ip-city/?key=' + KEY + '&ip=' + str(source_ip))

        geo_info = data.read().split(';')
        return float(geo_info[8]), float(geo_info[9])
        
def distance_meas(lat1,long1,lat_long):


            lat2 = lat_long[0]
            long2 = lat_long[1]
            #Converting to spherical coordinates.
            degrees_to_radians = math.pi/180.0
            phi1 = (90.0 - lat1)*degrees_to_radians
            phi2 = (90.0 - lat2)*degrees_to_radians


            theta1 = long1*degrees_to_radians
            theta2 = long2*degrees_to_radians
            # Computing spherical distance based on spherical coordinates.
            cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) +  math.cos(phi1)*math.cos(phi2))    
            arc = math.acos( cos )
            # Converting into kilometers
            return arc * 6373


def fetch_nearest_replica(lat1,long1,client_mapping_geo,request_ip):


        replica_servers_dict = {
                                '54.85.32.37':[39.018,-77.539],
                                '54.193.70.31':[37.3394,-121.895],
                                '52.38.67.246':[45.7788,119.529],
                                '52.51.20.200':[53.3331,-6.2489],
                                '52.29.65.165':[50.1167,8.6833],
                                '52.196.70.227':[35.685,139.7514],
                                '54.169.117.213':[1.2931,103.8558],
                                '52.63.206.143':[-33.8615,151.2055],
                                '54.233.185.94':[-23.5475,-46.6361]}
        for each_replica in replica_servers_dict:
           replica_servers_dict[each_replica] = distance_meas(lat1,long1,replica_servers_dict[each_replica])

        nearest_ip = min(replica_servers_dict, key=replica_servers_dict.get)
        client_mapping_geo[request_ip] = nearest_ip
        return nearest_ip,client_mapping_geo

#Computing nearest replica based on geolocation.
def replica_geo(source_ip, client_mapping_geo):
        
        if source_ip in client_mapping_geo:
                        nearest_ip = client_mapping_geo[source_ip]
        else:
           lat1,long1 = fetch_lat_long(source_ip)
           nearest_ip,client_mapping_geo = fetch_nearest_replica(lat1,long1,client_mapping_geo,source_ip)
	dict1={nearest_ip:'1'}
        return dict1,client_mapping_geo

#Computing nearest replica based on active measurement or geolocation.
def select_replica(client_ip,client_mapping_geo):
   result = replica_active(client_ip)

   if len(set(result.values())) <= 1:
       result,client_mapping_geo = replica_geo(client_ip,client_mapping_geo)
   sorted_result = sorted(result.items(), key=lambda e: e[1])
   return sorted_result[0][0],client_mapping_geo
