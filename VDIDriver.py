import random
import pyExcelerator
import time

global_zid = 0 #zone id
global_hit = 0 #


class Switch():

	'''Switch class,
	setting the attributes of Switch according to the param DESC'''

	def __init__(self, DESC):
		self.switch_list = DESC["node_list"][:-1]
		self.bandwidth_list = DESC["bandwidth_list"]
		self.pkg_size = DESC["pkg_size"]
		self.pps = DESC["pps"]


class VDI():

	'''Virtual Disk Image class, generate templates'''

	def __init__(self, DESC):
		self.templates = DESC["templates"]
		self.chunks = DESC["chunks"]
		self.chunk_size = DESC["chunk_size"]
		self.chunk_tpye = DESC["chunk_tpye"]
		self.cache_size = DESC["cache_size"]

		self.__gen_template(4)

	'''def __gen_template_random(self):
		for i in range(self.templates):
			template_dict = {}
			for j in range(self.chunk_tpye[i][0], self.chunk_tpye[i][1]):
				template_dict[j] = 0
			self.template_list.append(template_dict)

		for i in range(len(self.template_list)):
			for j in range(self.chunks):
				chunk = random.randint(self.chunk_tpye[i][0], self.chunk_tpye[i][1] - 1)
				#chunk = self.chunk_tpye[i][0] + j / (self.chunk_tpye[i][1] \
				- self.chunk_tpye[i][0])
				self.template_list[i][chunk] += 1'''

	#input: templates, number of clsters; cluster, number of images in one cluster
	#output: chunk_tpye = [(1500, 2500), (1600, 2600), (start, start+chunks), ...]
	def __gen_template(self, cluster):

		'''
			function: VDI.__gen_template, generating the image templates and clusters
			parama: cluster, number of the images in one cluster
			return null
		'''

#***tempates, cluster, 20 templates, 4 cluster, 20*4=80 ****#
		for i in range(self.templates): #generate clusters
			start = 1500 + i * 900
			for j in range(cluster):
			#generate the images in one cluser, each image;
			#s size is from start to start+chunks
				self.chunk_tpye.append((start, start + self.chunks))
				start += 100
#*****************************************************************************#
		'''special tempaltes clusters
		'''
		self.chunk_tpye.append((0, 1000))
		self.chunk_tpye.append((100, 1100))
		self.chunk_tpye.append((200, 1200))
		self.chunk_tpye.append((300, 1300))


class Zone():

	''''''

	def __init__(self, zone_attr):
		global global_zid
		global_zid += 1
		self.zid = global_zid
		self.inner_host_list = []
		self.node_list = zone_attr["node_list"]
		self.layers = len(self.node_list)
		self.chunk_tpye = zone_attr["chunk_tpye"]
		self.chunks = zone_attr["chunks"]
		self.sim = 0
		self.cache_size = zone_attr["cache_size"]
		self.cache_content = []

	def append_host(self, source_tuple):
		self.inner_host_list.append(source_tuple)

	def remove_host(self, source_tuple):
		self.inner_host_list.remove(source_tuple)

	#input: inner_host_list, [(1, 100), (2, 99), (host, image)...]
	#output: a random host id in this inner_host_list, 1 or 2 ...
	def access_cache(self):
		'''
			function: Zone.access_cache, random access a host;s cache
			param: inner_host_list, a host zone
			return: a host id
		'''
		hid = random.randint(0, len(self.inner_host_list) - 1)

		return self.inner_host_list[hid][0]

	#input: source, (1, 100); inner_host_list, [(1, 100), (2, 101), (host, image)...]
	#output: True or False
	def get_host_in_zone(self, source):
		for zone in self.inner_host_list:
			if source == zone:
				return True

		return False


	#input: cache placement policy
	#output: cache_content = [999, 110, 300, 200, ...]
	def comp_cache_content(self, pattern='FIFO'):
		'''
			function: Zone.comp_cache_content, computing all hosts' chaches content in one zone
			params: pattern, cache placement policy; inner_host_list, [(1, 100), (host id, image id), ...]; 
					chunk_tpye, [(100, 1199), (start chunk, end chunk), ...]
			return: null
		'''
		self.cache_content = []
		if pattern == 'random':
			for i in range(self.cache_size): #fill the chache to the full, 0...x
				ran_host_index = random.randint(0, len(self.inner_host_list) - 1)
				ran_host = self.inner_host_list[ran_host_index] #random one host in this zone, (1, 100), (host id, image id), then we can know the image's chunks
				ran_chunk_id = random.randint(self.chunk_tpye[ran_host[1]][0], self.chunk_tpye[ran_host[1]][1]) #random chunk in one image chunks, for example, (100, 1100)
				self.cache_content.append(ran_chunk_id)
				#cache_content = [999, 110, 300, 200, ...]

#**********************code can be optimized****************#
		elif pattern == 'FIFO':
			for host in self.inner_host_list:
				for chunk_id in range(self.chunk_tpye[host[1]][0], self.chunk_tpye[host[1]][1]): #from start to start+size, sequentially
					if len(self.cache_content) >= self.cache_size: break
					self.cache_content.append(chunk_id)
#***********************************************************#

#********************algorithm can be optimized*************#               
		elif pattern == 'normal':
			for host in self.inner_host_list:
				for chunk_id in range(self.chunk_tpye[host[1]][0] + 400, self.chunk_tpye[host[1]][1] - 400): #first, consider middle chunks
					if len(self.cache_content) >= self.cache_size: break
					self.cache_content.append(chunk_id)
			for host in self.inner_host_list:
				if len(self.cache_content) >= self.cache_size: break
				chunk_id = random.randint(self.chunk_tpye[host[1]][0], self.chunk_tpye[host[1]][0] + 400) #then, consider start to start+400
				self.cache_content.append(chunk_id)
			for host in self.inner_host_list:
				if len(self.cache_content) >= self.cache_size: break
				chunk_id = random.randint(self.chunk_tpye[host[1]][1] - 400, self.chunk_tpye[host[1]][1]) #last, consider last-400 to last
				self.cache_content.append(chunk_id)
#**********************************************************#

	#input: inner_host_list, [(1, 100), (host id, image id), ...]
	#output: total intersection value
	def __comp_intersection(self):
		'''
			function: Zone.__comp_intersection
			params: 
			return: intersection, number of the same chunks
		'''
		set_list = []
		intersection = 0

		for host in self.inner_host_list: #inner_host_list = [(1, 100), (host id, image id), ...]
			set_list.append(self.chunk_tpye[host[1]]) #set_list = [(0, 1000), (100, 1100), ...]
		#print "set_list:" + str(set_list)

#************ complexity n*(c+n+c) = n^2 ****************#
		for i in range(len(set_list)):
			set_dict = {}
			for k in range(set_list[i][0], set_list[i][1]):
				set_dict[k] = 0

			for j in range(len(set_list)):
				single_set = set_list[i]
				if i == j: continue
				if (single_set[0] > set_list[j][1]) or (single_set[1] < set_list[j][0]): continue #tow sets has no intersection
				if single_set[0] < set_list[j][0]: 
					single_set = (set_list[j][0], single_set[1]) #get the intersection
				if single_set[1] > set_list[j][1]:
					single_set = (single_set[0], set_list[j][1])
				
				for k in range(single_set[0], single_set[1]):
					set_dict[k] = 1 # set the same positions' value = 1

			for k in set_dict:
				if set_dict[k] == 1: intersection += 1 # compute the intersection value of set_list[i] with others, add to previous intersection value

		#print "intersection:" + str(intersection)
		return intersection # total intersection value of the inner_host_list
#******************************************************#

	#input: host id, 1; node_list, [1, 4, 8, 8]
	#output: (1, 0, 0)
	def __comp_location(self, host):
		'''
			function: Zone.__comp_location, compute one host's access switch and aggregate switch
			param: host id
			return (host, access, aggregate)
		'''

		access_switch = host / self.node_list[self.layers - 1]
		aggre_switch = access_switch / self.node_list[self.layers - 2]

		return (host, access_switch, aggre_switch)

	#input: similarity threshold
	#output: True or False
	def check_similarity(self, sim_threshold):
		'''
			function: Zone.check_similarity, check the images' similarity that one inner_host_list's hosts access
			param: sim_threashold, 0 =< value <= 1
			return True, or False
		'''
		if len(self.inner_host_list) <= 1: 
			self.sim = 1.0
			return True

		self.sim = float(self.__comp_intersection()) / \
						(len(self.inner_host_list) * (len(self.inner_host_list) - 1) * self.chunks)
		#print "sim:" + str(self.sim)
		#self.__comp_cache_content()
		if self.sim > sim_threshold:
			return True
		else:
			return False


	#input: location threshold
	#output: True or False
	def check_location(self, loc_threshold):
		'''
			function: Zone.check_location, check the hosts' location in one inner_host_list
			param: loc_threshold, "host", "access", "aggre"
			return: True or False
		'''
		location_list = []
		for host in self.inner_host_list: #inner_host_list=[(1, 100), (2, 101), (host, image)...]
			location_list.append(self.__comp_location(host[0])) #location_list=[(1, 0, 0), (2, 0, 0), ...]

		host_dict = {}
		access_dict = {}
		aggre_dict = {}


		for location in location_list:
			if not host_dict.has_key(location[0]): #host
				host_dict[location[0]] = 1

			host_dict[location[0]] += 1 #same host
			if not access_dict.has_key(location[1]): #access
				access_dict[location[1]] = 1 
			access_dict[location[1]] += 1 #same access
			if not aggre_dict.has_key(location[2]): #aggregate
				aggre_dict[location[2]] = 1
			aggre_dict[location[2]] += 1 #same aggregate

		#return access_dict,aggre_dict
		if loc_threshold == 'host': #must be same host
			if len(host_dict.keys()) > 1: return False
			else: return True
		elif loc_threshold == 'access': #must be same access
			if len(access_dict.keys()) > 1: return False
			else: return True
		elif loc_threshold == 'aggre': #must be same aggregate
			if len(aggre_dict.keys()) > 1: return False
			else: return True


class Topo(Switch, VDI):

	''' '''

	def __init__(self, DESC):
		Switch.__init__(self, DESC)
		VDI.__init__(self, DESC)
		self.node_list = DESC["node_list"]
		self.nodes = 0
		self.layers = len(self.node_list)
		self.comp_node = DESC["host_list"][0]
		self.stor_node = DESC["host_list"][1]

		lay = 1
		for i in self.node_list:
			lay *= i
			self.nodes += lay


	#input: 0, 252
	#output: [(3, 0), (2, 0), (1, 0), (0, 0), (0, 0), (1, 3), (2, 31), (3, 252)]
	def trace_hop(self, source, dest):

		'''
			function: Topo.trace_hop, compute the trace nodes from source node to destination node
			params: source, source node, generally a computing node; dest, destination node;
			return: the nodes list
		'''

		source_list = []
		dest_list = []
		route_source = []
		route_dest = []

		source_list.append((self.layers - 1, source)) #[(3, 0)]
		dest_list.append((self.layers - 1, dest)) #[(3, 252)]

		# 4 layers, lay = 3,2,1; range(start, stop, step)
		for lay in range(self.layers - 1, 0, -1):
			source = source / self.node_list[lay] #upper layer of source
			source_list.append((lay - 1, source)) #[(3, 0), (2, 0), (1, 0), (0, 0)]
			dest = dest / self.node_list[lay] #upper layer of dest
			dest_list.append((lay - 1, dest)) #[(3, 252), (2, 31), (1, 3), (0, 0)]
		#source_list.append((0, 0))
		#dest_list.append((0, 0))

#********************code can be optimized**************#
		for i in range(len(source_list)): # 4, i = 0,1,2,3
			if source_list[i] == dest_list[i]: #source node == dest node
				route_source.append(source_list[i]) 
				break
			else:
				route_source.append(source_list[i])
				route_dest.insert(0, dest_list[i]) # reverse

		return route_source + route_dest
	#[(3, 0), (2, 0), (1, 0), (0, 0), (0, 0), (1, 3), (2, 31), (3, 252)]
#******************************************************#


	#input: [(3, 0), (2, 0), (1, 0), (0, 0), (0, 0), (1, 3), (2, 31), (3, 252)]
	#output: [(2.0.3.0), (1.0.2.0), ...]
	def trace_route(self, hop_list):

		'''
			function: Topo.trace_route, converting the trace nodes list to the trace route/link list
			param: hop_list, trace nodes list
			return: route_list
		'''

		route_list = []
		for hop in range(len(hop_list) - 1): # 7, hop=0,1,2,3,4,5,6
			route_tuple = hop_list[hop] + hop_list[hop+1] #(3,0,2,0) ...
			route_str = ""
			if route_tuple[0] > route_tuple[2]: #(3,0,2,0) will equal to (2,0,3,0)
				route_str += (str(route_tuple[2]) + '.')
				route_str += (str(route_tuple[3]) + '.')
				route_str += (str(route_tuple[0]) + '.')
				route_str += str(route_tuple[1])
			else:
				route_str += (str(route_tuple[0]) + '.')
				route_str += (str(route_tuple[1]) + '.')
				route_str += (str(route_tuple[2]) + '.')
				route_str += str(route_tuple[3]) #(2.0.3.0)

			route_list.append(route_str)

		return route_list #[(2.0.3.0), (1.0.2.0), ...]


	#input: {(2.0.3.0):x, (1.0.2.0):y, ...}
	#output: total lantency ms   
	def comp_latency(self, route, traffic_dict):

		'''
			transfer lantency = pkg_size / bandwidth ms
			queue lantency = 1 / (pro - traffic) ms
		'''

		lantency = 0.0
		for i in range(len(route)):
			lay = int(route[i][0])
			link =  route[i]
			trans_lat = float(self.pkg_size) / (self.bandwidth_list[lay] * 1000)
			if not traffic_dict.has_key(link):
				traffic_dict[link] = 0
			queue_lat = float(1) / (self.bandwidth_list[lay] * 1000 / self.pkg_size - traffic_dict[link])
			lantency += (trans_lat + queue_lat) 
			#print '%s hop trans:%s,queue:%s,prop:%s' % (i,trans_lat,queue_lat,prop_lat)

		return lantency * 1000


	#input: [(0, 252), (1, 253), ...]
	#output: {(2.0.3.0):x, (1.0.2.0):y, ...}
	def comp_traffic(self, req_list):
		'''
			function: Topo.comp_traffic, computing each link's(route's) traffic according to req_list
			param: req_list, many requests from source node to dest node
			return: traffic_dict
		'''
		traffic_dict = {}
		for req in req_list:
			#call trace_hop and trace_route, get the route_list from req[0] to req[1]
			route_list = self.trace_route(self.trace_hop(req[0], req[1])) #[(2.0.3.0), (1.0.2.0), ...]
			for route in route_list:                
				if not traffic_dict.has_key(route):
					traffic_dict[route] = 0 #{(2.0.3.0):0, (1.0.2.0):0, ...}
				traffic_dict[route] += self.pps #{(2.0.3.0):1, (1.0.2.0):1, ...}

				lay = int(route[0])
				if traffic_dict[route] * self.pkg_size > self.bandwidth_list[lay] * 1000:
					return ['system overload']

		return traffic_dict
	
	
	def comp_redundancy(self, zone_list, vms):
		''' r = (zones * cache_size + vms * 200M) / (vms * 8G)
		'''
		#*********************************************************************#
		r = float(len(zone_list) * self.cache_size + vms * 200) / (vms * 8000)
		#*********************************************************************#
		return (len(zone_list), self.cache_size, r)


	def comp_redundancy_new(self, zone_list, vms, templates, pattern):
		if pattern == 'cenbased':
			r = float((vms * 200)) / (templates * 8000)
			print 'cenbased redundancy: ' + str(r)
		elif pattern == 'distributed':
			r = float(vms) / templates
			print 'distributed redundancy: ' + str(r)
		elif pattern == 'disbased':
			r = 1.0 + float((vms * 200)) / (templates * 8000)
			print 'disbased redundancy: ' + str(r)
		elif pattern == 'zone':
			r = float((len(zone_list) * self.cache_size + vms * 200)) / (templates * 8000)
			print 'zone redundancy: ' + str(r)
		else:
			r = 0.0
			print 'central redundancy: ' + str(r)
		return r


	def comp_migration(self, latency, size=200000):
		''' migration overhead = (VDI size / pkg_size) / lantency ms
		'''
		overhead = size / self.chunk_size * latency
		return overhead


	def comp_distribution_aver(self, topo, traffic_list, access_list, size=200000):
		source_dest_list = []
		for source_image in access_list:
			source_dest_list.append((source_image[0], random.randint(\
				self.comp_node, self.comp_node + self.stor_node - 1)))
		lat = 0.0
		for access in source_dest_list:
			route = topo.trace_route(topo.trace_hop(access[0], access[1]))
			#print route
			lat += topo.comp_latency(route, traffic_list)
		lat /= len(access_list)
		distribution_overhead = lat * size
		return distribution_overhead


	def comp_migration_aver(self, topo, traffic_list, size=200000):
		comp1_comps_list = []
		for i in range(self.comp_node):
			comp1_comps_list.append((0, i))
		lat = 0.0
		for access in comp1_comps_list:
			route = topo.trace_route(topo.trace_hop(access[0], access[1]))
			#print route
			lat += topo.comp_latency(route, traffic_list)
		lat /= self.comp_node
		migration_overhead = lat * size
		return migration_overhead


	#input: params
	#output: [(0, 10), (1, 5), ..., (0, 8), (2, 5), ...]
	def vm_deploy(self, load_type, pattern, vms):

		'''
			fumction: Topo.vm_deploy, deploy vms to host, and make their access list
			params: load_type, VM placement type; pattern, Image repository pattern; vms, number of VMs
			return: list of [(vm's host ID, vm's template ID), ...], host ID and template ID may be repeated
		'''

		access_list = []

		for vm in range(vms):
			if load_type == 'random':
				source = random.randint(0, self.comp_node - 1)
				vdi = random.randint(0, self.templates * 4 - 1)
			elif load_type == 'minload':
				source = vm % self.comp_node
				vdi = random.randint(0, self.templates * 4 - 1)
			elif load_type == 'friendly':
				source = random.randint(0, self.comp_node - 1)
				source_access = source / self.node_list[3]
				vdi = random(4 * (source_access % self.templates)\
						, 4 * (source_access % self.templates + 1) - 1)
				#pass

			#a vm access a random template
			
			access_list.append((source, vdi))
		#[(host ID, template ID), ...], every host may has multiple vms, every template may be access by multiple vms
		return access_list


	#input: [(0, 100),(1, 180),(host, image),...], 0.6, 0.6, "FIFO"
	#output: zone_list = [zone1, zone2, ...]
	def zone_partition(self, source_list, sim_threshold, loc_threshold, cache_policy):
		'''
			function: Topo.zone_partition
			params: source, [(host, image), ...]; sim_threshold, similarity; loc_theshold, location; cache_policy
			return:
		'''
		zone_attr = {"node_list":self.node_list, "chunk_tpye":self.chunk_tpye \
					, "chunks":self.chunks, "cache_size":self.cache_size}

		zone_list = []
		zone = Zone(zone_attr)
		zone.append_host(source_list[0])
		zone_list.append(zone)

		#souce_list has no more than 1 host
		if len(source_list) <= 1:
			zone.check_similarity(sim_threshold)
			zone.comp_cache_content(cache_policy) 
			return zone_list


		#source_list has more than 1 hosts        
		for i in range(1, len(source_list)):
			flag = False

			#check the host with every zone
			for z in zone_list:

				z.append_host(source_list[i]) #first, append host into the zone
				#then, check the zone's similarity and lication
				if z.check_similarity(sim_threshold) and z.check_location(loc_threshold):
					flag = True 
					break

				else:
					z.remove_host(source_list[i])
					#z.check_similarity(sim_threshold)
					#z.comp_cache_content() 

			 #the host is not suitable for exist zones, then create a new zone
			if not flag:
				zone = Zone(zone_attr)
				zone.append_host(source_list[i])
				zone_list.append(zone)
				zone.check_similarity(sim_threshold)
				zone.comp_cache_content(cache_policy) 

		#for zone in zone_list:
		#   print zone.check_location(1)
		return zone_list


	#input: source_list = [(0, 100), (1, 150), (host, image), ...]
	#out_put: access_list = [(0, 250), (0, 251), (host, dest_node), ...]

	def traditional_access(self, source_list, pattern, rate=50):

		"""
			function: Topo.tradition_access, four method to access image node
			params: source_list, [(host id, image id), ...]; pattern, access mmethod
			return: access_list, [(host id, dest id), ...]
		"""

		access_list = []

		zss_seed = random.Random()
		zss_seed.seed(1)
		dis_seed = random.Random()
		dis_seed.seed(1)

		for source in source_list:
			if pattern == 'central': #central access mode, images are stored in stor_node, (250, 255)
				dest = random.randint(self.comp_node, self.comp_node + self.stor_node - 1)
			elif pattern == 'cenbased': #cenbased access mode, access stor_node or self comp_node
				if random.randint(0, 99) > rate:
					dest = source[0]
				else:
					dest = random.randint(self.comp_node, self.comp_node + self.stor_node - 1)
			#******************************************************************#
			elif pattern == 'distributed': #distributed access mode, image is stored in self comp_node
					dest = source[0]
			elif pattern == 'disbased': #disbased access mode, access self comp_node or other comp_node
				if random.randint(0, 99) > rate:
					dest = source[0]
				else:
					dest = random.randint(0, self.comp_node - 1)

			source = list(source)
			#(host, image)-->(host, dest_node)
			source[1] = dest
			source = tuple(source)

			access_list.append(source)

		return access_list


	#input: source_list, [(host id, image id), ...]; zone_list, [zone1, zone2, ...]
	#output: access_list = [(0, 250), (0, 251), (host, dest_node), ...]

	def zone_access(self, source_list, zone_list, rate=50):

		'''
			function: Topo.zone_access, images are stored in self comp_nodes, zone and stor_nodes
			param: source_list, [(host id, image id), ...]; zone_list, [zone1, zone2, ...]
			return: access_list
		'''

		access_list = []

		zss_seed = random.Random()
		zss_seed.seed(1)

		for source in source_list:
			if random.randint(0, 99) > rate:
				dest = source[0] #access self comp_node
			else:
				for zone in zone_list:
					if zone.get_host_in_zone(source): 
						dest_zone = zone
						break
				if dest_zone.cache_content.count(self.trace_driver(source[1], 'normal')):
					global global_hit
					global_hit += 1
					dest = dest_zone.access_cache() #access zone cacha
				else:
					dest = random.randint(self.comp_node, self.comp_node + self.stor_node - 1)
					#access stor_node

			source = list(source)
			source[1] = dest
			source = tuple(source)

			access_list.append(source)

		return access_list

	#input: template, the image id; pattern, 'random' or 'normal'
	#output: chunk id, 500
	def trace_driver(self, template, pattern):
		chunk_tuple = self.chunk_tpye[template] #(100, 1100)

		if pattern == 'random':
			chunk_id = random.randint(chunk_tuple[0], chunk_tuple[1]) #(100, 1100)
		elif pattern == 'normal':
			rate = random.randint(0, 99)
			if rate > 90: # 10%
				chunk_id = random.randint(chunk_tuple[0], chunk_tuple[0] + 400) #(100, 500)
			elif rate >= 10 or rate <= 90: # 80%
				chunk_id = random.randint(chunk_tuple[0] + 400, chunk_tuple[1] - 400) #(500, 700)
			else: # 10%
				chunk_id = random.randint(chunk_tuple[1] - 400, chunk_tuple[1]) #(700, 1100)

		return chunk_id



def rst_output_txt(rst_list, name):
	f = open(name, 'a')
	for rst_line in rst_list:
		for rst_col in rst_line:
			f.write(str(rst_col))
			f.write(' ')
		f.write('\n')

def rst_output_xls(rst_list):
	w = pyExcelerator.Workbook() 
	wf = w.add_sheet(u'firstsheet')
	for x in range(len(rst_list)):
		for y in range(len(rst_list[0])):
			wf.write(x,y,rst_list[x][y]) 
	w.save('rst_tmp.xls')


def tradition_exp(topo, rst_line, placement, deploy, vms, templates):
	''' test [central, cenbased, disbased] model
		placement: [random, minload, zss-friendly]
		deploy: [central, cenbased, disbased]
		vms: [100, 500, 1000, 1500, 2000, 2500]
	'''
	#[(comp id), (image id), ...]
	access_list = topo.vm_deploy(placement, deploy, vms)
	
	#[(comp id), (dest id), ...]
	traditional_list = topo.traditional_access(access_list, deploy)
	
	#{(1.0.2.0):x, (2.0.3.0):y, ...}
	traffic_list = topo.comp_traffic(traditional_list)
	
	lat = 0.0
	for access in traditional_list:
		route = topo.trace_route(topo.trace_hop(access[0], access[1]))
		#print route
		lat += topo.comp_latency(route, traffic_list)
	lat /= vms
	redundancy = topo.comp_redundancy_new([], vms, templates, deploy)
	distribution_overhead = topo.comp_distribution_aver(topo, traffic_list, \
			access_list, 200000)
	migration_overhead = topo.comp_migration_aver(topo, traffic_list, 200000)
	#overhead = topo.comp_migration(lat)
	#print lat,overhead
	#print lat
	rst_line.append((lat, redundancy, distribution_overhead, migration_overhead))


def zss_exp(topo, rst_line, placement, vms, cache_size, sim_threshold, loc_threshold, cache_policy, templates):
	''' test [central, cenbased, disbased] model
		placement: [random, minload, zss-friendly]
		vms: [100, 500, 1000, 1500, 2000, 2500]
		cache_size: [100, 500, 1000, 1500, 2000, 2500, 3000]
		sim_threshold: [0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
		loc_threshold: [host, access, aggre]
		cache_policy: [random, FIFO, normal]
	'''
	topo.cache_size = cache_size

	#[(comp id), (image id), ...]
	access_list = topo.vm_deploy(placement, 'zss', vms)
	#topo.trace_driver(access_list)
	#print "access_list:" + str(access_list)
	
	#[zone1, zone2, ...]
	zone_list = topo.zone_partition(access_list, sim_threshold, loc_threshold, cache_policy)
	'''for zone in zone_list:
		print str(zone.zid) + ":" + str(zone.inner_host_list)
		#if zone.sim < 1:
		#   print "sim:" + str(zone.sim)
		print "content:" + str(zone.cache_content)
		#print "cache:" + str(zone.cache_rate)'''
	#print "zones:" + str(len(zone_list))
	
	#[(comp id), (dest id), ...]
	zss_access_list = topo.zone_access(access_list, zone_list)
	#print "zss_access:" + str(zss_access_list)
	
	#{(1.0.2.0):x, (2.0.3.0):y, ...}
	traffic_list = topo.comp_traffic(zss_access_list)
	#print traffic_list
	lat = 0.0
	for access in zss_access_list:
		route = topo.trace_route(topo.trace_hop(access[0], access[1]))
		lat += topo.comp_latency(route, traffic_list)
	lat /= vms
	redundancy = topo.comp_redundancy_new(zone_list, vms, templates, 'zone')
	distribution_overhead = topo.comp_distribution_aver(topo, traffic_list, access_list, 200000)
	migration_overhead = topo.comp_migration_aver(topo, traffic_list, 200000)
	#print lat
	rst_line.append((lat, redundancy, distribution_overhead, migration_overhead))
	#redundancy = topo.comp_redundancy(zone_list, vms)
	#rst_line.append(str(redundancy))

# placement policy
def exp1(topo):
	''' I/O lantency when deploy vary in 'central, cenbased, distributed, disbased, zone'
	'''
	rst_list = []
	rst_list.append("exp1 start" + str(time.time()))
	rst_line = []
	for deploy in ['central', 'cenbased', 'distributed', 'disbased']:
		tradition_exp(topo, rst_line, 'minload', deploy, 100, 20*4)
		rst_list.append(rst_line)
		rst_line = []

	zss_exp(topo, rst_line, 'minload', 100, 1000, 0.2, 'access', 'FIFO', 20*4)
	rst_list.append(rst_line)

	rst_list.append("exp1 finish" + str(time.time()))
	rst_output_txt(rst_list, 'exp1.txt')


#cache size
def exp2(topo):
	''' I/O lantency when zss vary in cache_size
	'''
	print "exp2 start" + str(time.time())
	rst_list = []
	for cache_size in [100, 500, 1000, 1500, 2000, 2500, 3000]:
		rst_line = []
		zss_exp(topo, rst_line, 'minload', 2500, cache_size, 0.2, 'access', 'FIFO')
		rst_list.append(rst_line)

	rst_list.append('----------------------------------------------------------')
	rst_output_txt(rst_list, 'exp2.txt')
	print "exp2 finish" + str(time.time())

#similarity threahold
def exp3(topo):
	''' I/O lantency when zss vary in sim_threshold
	'''
	print "exp3" + str(time.time())
	rst_list = []
	for sim_threshold in [0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]:
		rst_line = []
		zss_exp(topo, rst_line, 'minload', 2500, 1000, sim_threshold, 'access', 'FIFO')
		rst_list.append(rst_line)

	rst_list.append('----------------------------------------------------------')
	rst_output_txt(rst_list, 'exp3.txt')
	print "exp3 finish" + str(time.time())

#location threshold
def exp4(topo):
	''' I/O lantency when zss vary in loc_threshold
	'''
	start_t = time.time()
	print "exp4" + str(time.time())
	rst_list = []
	for loc_threshold in ['host', 'access', 'aggre']:
		rst_line = []
		zss_exp(topo, rst_line, 'minload', 2500, 1000, 0.2, loc_threshold, 'FIFO')
		rst_list.append(rst_line)

	rst_list.append('----------------------------------------------------------')
	rst_output_txt(rst_list, 'exp4.txt')
	end_t = time.time()
	print "exp4 finish" + str(end_t - start_t)

#cache policy
def exp5(topo):
	''' I/O lantency when zss vary in cache_policy
	'''
	print "exp5" + str(time.time())
	rst_list = []
	for cache_policy in ['normal', 'random', 'FIFO']:
		rst_line = []
		zss_exp(topo, rst_line, 'minload', 2500, 1000, 0.2, 'access', cache_policy)
		rst_list.append(rst_line)

	rst_list.append('----------------------------------------------------------')
	rst_output_txt(rst_list, 'exp5.txt')
	print "exp5 finish" + str(time.time())

#vm numbers
def exp6(topo):
     ''' I/O lantency when zss vary in vms'''
     print "exp6" + str(time.time())
     rst_list = []
     for vms in [100, 500, 1000, 1500, 2000, 2500]:
         rst_line = []
         zss_exp(topo, rst_line, 'minload', vms, 1000, 0.2, 'access', 'FIFO')
         rst_list.append(rst_line)
 
     rst_list.append('-----------------------------------------------    -----------')
     rst_output_txt(rst_list, 'exp6.txt')
     print "exp6 finish" + str(time.time())

def exp7(topo):
     ''' I/O lantency when zss vary in placement'''
     print "exp7" + str(time.time())
     rst_list = []
     for placement in ['random', 'minload', 'friendly']:
         rst_line = []
         zss_exp(topo, rst_line, placement, 2500, 1000, 0.2, 'access', 'FIFO')
         rst_list.append(rst_line)
 
     rst_list.append('-----------------------------------------------    -----------')
     rst_output_txt(rst_list, 'exp7.txt')
     print "exp7 finish" + str(time.time())


if __name__ == '__main__':
	''' node_list: number of root,aggre,access level switches and hosts
		bandwidth_list: bandwidth of root,aggre,access level link (GB)
		pkg_size: size of requests from VM (KB)
		host_list: [0] number of computing nodes, [1] number of storage nodes
		pps: number of packages per second
		templates: number of template VDI in storage nodes
		chunks: number of chunks per VDI
		chunk_size: size of chunks (KB)
		chunk_tpye: type of chunks in VDI
	'''
	DESC = {"node_list":[1,4,8,8], "bandwidth_list":[5,5,50], "pkg_size":2 \
			, "host_list":[250,6], "pps":1, "templates":20, "chunks":1000, "chunk_size":8 \
			, "chunk_tpye":[], "cache_size":1000}

	DESC1 = {"node_list":[1,2,2,2], "bandwidth_list":[1,1,10], "pkg_size":2 \
			, "host_list":[6,2], "pps":1, "templates":5, "chunks":1000, "chunk_size":4 \
			, "chunk_tpye":[(0,50),(30,60),(10,40),(55,80),(20,70)], "cache_size":500}

	topo = Topo(DESC)
	#print topo.chunk_tpye

	for exp in [exp1]:
		exp(topo)

	#print "global_hit:" + str(global_hit)
	#print rst_list
	#rst_output(rst_list)
	#rst_output_txt(rst_list)
