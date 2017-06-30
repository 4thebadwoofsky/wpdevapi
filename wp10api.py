#!/usr/bin/python
# Copyright 2017 @ 4thebadwoofsky
import sys,os,subprocess,re,json,base64
from time import sleep
class IPAddress:
	A = 0
	B = 0
	C = 0
	D = 0
	Text = ""
	def __init__(self,a,b = -1,c = 0,d = 0):
		if b == -1:
	                ints = str(a).split('.')
        	        if len(ints) == 4:
        	        	self.__create(int(ints[0]),int(ints[1]),int(ints[2]),int(ints[3]));
		else:
			self.__create(a,b,c,d)
	def __create(self,a,b,c,d):
		self.A = a
		self.B = b
		self.C = c
		self.D = d
		self.Text = str(a)+"."+str(b)+"."+str(c)+"."+str(d)
class WindowsPhone_App:
	Name = ""
	PackageRelativeId = ""
	PackageFullName = ""
	def __init__(self,package):
		self.Name = package["Name"]
		self.PackageRelativeId = package["PackageRelativeId"]
		self.PackageFullName = package["PackageFullName"]
	def Start(self,phone):
		os.system("curl --http1.1 \"http://" + phone.IPAddress.Text + "/api/taskmanager/app?appid=" + base64.b64encode(self.PackageRelativeId) + "\" -d \"\"")
	def Stop(self,phone):
		os.system("curl --http1.1 \"http://" + phone.IPAddress.Text + "/api/taskmanager/app?package=" + base64.b64encode(self.PackageFullName) + "\" -X DELETE")
class WindowsPhone_Power:
	PluggedIn = 0
	Battery = 0
	Charging = 0
	MaxCapacity = 0
	CurCapacity = 0
	EstimatedTime = 0
	def Percentage(self):
		return (self.CurCapacity / self.MaxCapacity) * 100
class NetworkConfig:
	Static = None
	Broadcast = None
	Mask = None
	def __init__(self,static,broadcast,subnet):
		self.Static = IPAddress(static)
		self.Broadcast = IPAddress(broadcast)
		self.Mask = IPAddress(subnet)
class WindowsPhone:
	IPAddress = {}

	Name = ""
	Language = ""
	OsEdition = ""
	OsEditionId = 0
	OsVersion = ""
	Type = ""

	Power = WindowsPhone_Power()
	Apps = {}
	def __init__(self,ip):
		self.IPAddress = ip
		self.init()
	def init(self):
		os_info = self.__callRest("/os/info")
		os_devicefamily = self.__callRest("/os/devicefamily")
		power_battery = self.__callRest("/power/battery")

		self.Name = os_info["ComputerName"]
		self.Language = os_info["Language"]
		self.OsEdition = os_info["OsEdition"]
		self.OsEditionId = int(os_info["OsEditionId"])
		self.OsVersion = os_info["OsVersion"]
		self.Type = os_devicefamily["DeviceType"]

		self.Power = WindowsPhone_Power()
		self.Power.PluggedIn = int(power_battery["AcOnline"])
		self.Power.Battery = (int(power_battery["BatteryPresent"]) == 1)
		self.Power.Charging = int(power_battery["Charging"])
		self.Power.MaxCapacity = float(power_battery["MaximumCapacity"])
		self.Power.CurCapacity = float(power_battery["RemainingCapacity"])
		self.Power.EstimatedTime = int(power_battery["EstimatedTime"])
	def __callRest(self,fn):
		output = subprocess.check_output("curl http://" + self.IPAddress.Text + "/api" + fn + " -s",shell=True,stderr=None)
		return json.loads(output)
	def __callRestPost(self,fn):
		output = subprocess.check_output("curl http://" + self.IPAddress.Text + "/api" + fn + " -d \"\" -X POST -s",shell=True,stderr=None)
		return json.loads(output) if output.find("{") == 0 else output
	def SaveFile(self,filename):
		file = open(filename,"w")
		file.write(self.IPAddress.Text)
		file.close()
	def Shutdown(self,restart=False):
		self.__callRestPost("/control/" + ("restart" if restart else "shutdown"))
	def StartApp(self,app):
		app.Start(self)
	def StopApp(self,app):
		app.Stop(self)
	def GetApps(self):
		data = self.__callRest("/app/packagemanager/packages")
		for package in data["InstalledPackages"]:
			self.Apps[package["PackageFamilyName"]] = WindowsPhone_App(package)
	def PrintInfoTrace(self):
		print "Windows Phone ist erreichbar: " + self.IPAddress.Text
		print "Geraete-Informationen:"
		print "\tName => " + self.Name
		print "\tType => " + self.Type
		print "\tLanguage => " + self.Language
		print "\tPower:"
		print "\t\tPluggedIn => " + str(self.Power.PluggedIn)
		print "\t\tBattery => " + str(self.Power.Battery)
		print "\t\tCharging => " + str(self.Power.Charging)
		print "\t\tMaxCapacity => " + str(self.Power.MaxCapacity) + " mWh"
		print "\t\tCurCapacity => " + str(self.Power.CurCapacity) + " mWh"
		print "\t\tPercentage => " + str(self.Power.Percentage()) + "%"
		print "\t\tEstimatedTime => " + str(self.Power.EstimatedTime)
class WindowsPhoneLocator:
	Phones = {}
	def LoadFile(self,filename):
		file = open(filename,"r")
		ip = file.readline()
		file.close()
		ip = IPAddress(ip)
		id = ip.D + ip.C*100 + ip.B*10000 + ip.A*1000000
		self.Phones[id] = WindowsPhone(ip)
		return id
	def Locate(self,multi=False):
		networks = self.__readnetcfg()
		for ifName in networks.keys():
			network = networks[ifName]
        	self.Phones = self.__scanNetwork(network,multi)
	def __ifnames(self):
		return subprocess.check_output("ifconfig",shell=True)
	def __getips(self,line):
		return re.findall(r"\b(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[0-9][0-9]|[0-9])(?:\.(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[0-9][0-9]|[0-9])){3}\b",line)
	def __readnetcfg(self):
		networks = {}
		interfaceName = ""
		for line in self.__ifnames().split("\n"):
			if line.find("Hardware") > 2:
				interfaceName = line[0:line.find(" ")]
			if interfaceName != "":
				if line.find("inet ") > 2:
					interfaceAddresses = self.__getips(line)
					if len(interfaceAddresses) != 3:
						continue
					interfaceIP = interfaceAddresses[0]
					interfaceBroadcast = interfaceAddresses[1]
					interfaceSubmask = interfaceAddresses[2]
					networks[interfaceName] = NetworkConfig(interfaceIP,interfaceBroadcast,interfaceSubmask)
		return networks
	def __checkPhone(self,a,b,c,d):
		ip = str(a) +"."+ str(b) +"."+ str(c) +"."+ str(d)
		try:
			output = subprocess.check_output("curl http://" + ip + "/api/os/machinename --max-time 2 -s",shell=True,stderr=None)
			if output.find("{") == 0:
				return True
			else:
				return False
		except Exception as e:
			return False
	def __scanNetwork(self,net,multi = False):
		phones = {}
		mask = net.Mask
		broadcast = net.Broadcast
		ip = net.Static

		broadcastBlockA = broadcast.A
		broadcastBlockB = broadcast.B
		broadcastBlockC = broadcast.C
		broadcastBlockD = broadcast.D

		scanBlockA = (mask.A != 255)
		scanBlockB = (mask.B != 255)

		scanBlockC = (mask.C != 255)
		scanBlockD = (mask.D != 255)

		blockA = 0 if scanBlockA else broadcastBlockA
		blockB = 0 if scanBlockB else broadcastBlockB
		blockC = 0 if scanBlockC else broadcastBlockC
		blockD = 0 if scanBlockD else broadcastBlockD

		targetA = 255 if scanBlockA else broadcastBlockA
		targetB = 255 if scanBlockB else broadcastBlockB
		targetC = 255 if scanBlockC else broadcastBlockC
		targetD = 255 if scanBlockD else broadcastBlockD
		while (blockA == targetA & blockB == targetB & blockC == targetC & blockD == targetD) == False:
			if self.__checkPhone(blockA,blockB,blockC,blockD):
				id = blockD + blockC*100 + blockB*10000 + blockA*1000000
				phones[id] = WindowsPhone(IPAddress(blockA,blockB,blockC,blockD))
				if multi == False:
					return phones
			if scanBlockD:
				blockD = blockD + 1
			if blockD > 255:
				blockD = 0
				if scanBlockC:
					blockC = blockC + 1
				else:
					break
			if blockC > 255:
				blockC = 0
				if scanBlockB:
					blockB = blockB + 1
				else:
					break
			if blockB > 255:
				blockB = 0
				if scanBlockA:
					blockA = blockA + 1
				else:
					break
			if blockA > 255:
				break
		return phones

