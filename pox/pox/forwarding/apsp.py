

"""
POX-PLUS
"""


from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.Graph import Graph
from pox.Graph import SPT
from pox.lib.revent import *
from collections import defaultdict
from pox.host_tracker import host_tracker
from pox.lib.addresses import EthAddr
import copy
from time import sleep

log = core.getLogger()

G = Graph()
G.addVertex(0)
Forest = {}



# sending out all port
all_ports = of.OFPP_FLOOD


#MUTEB

updated = False
s_h = defaultdict(lambda: list()) # sw  <-> hosts,,,,  s_h = [ s1: {h1, h2, ..}, .......]
host_sw = defaultdict() # host <-> sw,,,  host_sw = [h1: (s1, pt1), h2: (s1,pt2), .....]
def _handle_HostEvent ( event):
    global host_sw
    """ Here is the place where is used the listener"""
    dpid = event.entry.dpid
    hostMAC = event.entry.macaddr
    host_sw[hostMAC] = (dpid,event.entry.port)
    s_h[dpid].append(hostMAC)

  
def cal_SPT(): 
  n = G.numVertices

  for i in range(n):
    tree = SPT()
    tree.init_SPT(n)
    Forest[i] = tree.build_SPT(G,i)

    
def _handle_ConnectionUp(event):
  global updated
  if event.dpid not in G.vertList:
    G.addVertex(event.dpid)

def collect_vertices(tree, v):
  aff = list()
  listW = list()
  listW.append(v)
  while listW:
    v = listW.pop()
    aff.append(v)
    for key in tree.treeList[v].children.keys():
      listW.append(key)
  return aff
    
updated_linkes = defaultdict()
def _handle_LinkEvent (event):
  global  G, Forest, updated_linkes
  l = event.link
  sw1 = l.dpid1
  sw2 = l.dpid2
  pt1 = l.port1
  pt2 = l.port2
  if not updated:
    if event.added:
        G.addEdge(sw1, (sw2,pt1))
        G.addEdge(sw2,(sw1,pt2))
    elif event.removed:
        G.rmEdge(sw1,(sw2,pt1))
        G.rmEdge(sw2,(sw1,pt2))
  elif event.removed:
    G.rmEdge(sw1,(sw2,pt1))
    G.rmEdge(sw2,(sw1,pt2))
    ###########################
    if sw2 not in updated_linkes.keys(): # if not, then it was already updated
      updated_linkes[sw1] = sw2
      for i in range(len(Forest)):
        # removing flows of hosts connecting to the source (i.e. switch) of this tree to all other switches in t(v)
        if s_h[i]:
          tree = Forest[i]
          parent = tree.treeList[sw1].parent
          if parent and parent.id == sw2:
            flip = sw1
            sw1 = sw2
            sw2 = flip
          if tree.treeList[sw2].parent<>tree.treeList[sw1]: # not a tree edge on the tree t(i)
            continue
          affected = collect_vertices(tree, sw2 )  # collect vertices in t(v)
          hosts = list()
          for v in affected:
            if v in s_h and s_h[v]:
              hosts = hosts+ s_h[v]
          u = tree.treeList[sw1]
          while u is not None: # we collect vertices in the path between v and source
            affected.append(u.id)
            u = u.parent
          
          while affected:
            u = affected.pop()
            for host in s_h[i]: 
              #msg to sw to remove flows starting from affected
              msg = of.ofp_flow_mod(match=of.ofp_match(),command=of.OFPFC_DELETE_STRICT)
              msg.match.dl_src = host
              for host2 in hosts:
                msg.match.dl_dst = host2 
                switch = core.openflow.getConnection(u)
                switch.send(msg)
        Forest[i].decremental(G, sw1, sw2)
    else:
      del updated_linkes[sw2]
  elif event.added:
    G.addEdge(sw1, (sw2,pt1))
    G.addEdge(sw2,(sw1,pt2))
    if sw2  not in updated_linkes.keys(): # if not, then it was already updated
      updated_linkes[sw1] = sw2
      for i in range(len(Forest)):
        # removing flows of hosts connecting to the source (i.e. switch) of this tree to all other switches in t(v)
        tree = copy.deepcopy(Forest[i])
        
        wieght_u = tree.treeList[sw1].wieght
        wieght_v = tree.treeList[sw2].wieght
        if wieght_v < wieght_u:
          flip = sw1
          sw1 = sw2
          sw2 = flip
        Forest[i].incremental(G, sw1, sw2)
        if s_h[i]:
          if (tree.treeList[sw1].wieght +1) >= tree.treeList[sw2].wieght: # not a tree edge on the tree t(i)
            continue

          affected = collect_vertices(Forest[i], sw2 )  # collect vertices in t'(v)
          
          while affected:
            u = affected.pop()
            if s_h[u]:
              u_copy = tree.treeList[u]
              while u_copy:
                for host in s_h[i]:
                  msg = of.ofp_flow_mod(match=of.ofp_match(),command=of.OFPFC_DELETE_STRICT)
                  msg.match.dl_src = host
                  for host2 in s_h[u]:
                    msg.match.dl_dst = host2
                    switch = core.openflow.getConnection(u_copy.id)
                    switch.send(msg)
                u_copy = u_copy.parent
    else:
      del updated_linkes[sw2]
    

# Handle messages the switch has sent us because it has no
# matching rule.
def _handle_PacketIn (event):
  global updated, G, Forest
  packet = event.parsed
  if not updated:
    cal_SPT()
    updated = True

  if packet.dst in host_sw.keys(): # We know the distnation MAC Add. ,So, We apply DR-APSP 
    targetSW_PT = host_sw[packet.dst]
    pt = Forest[event.dpid].treeList[targetSW_PT[0]].port
    if not pt:
      pt = targetSW_PT[1]

    msg = of.ofp_flow_mod()
    msg.data = event.ofp # Forward the incoming packet
    msg.match.dl_src = packet.src
    msg.match.dl_dst = packet.dst
    msg.actions.append(of.ofp_action_output(port = pt))
    event.connection.send(msg)

  
  
  else:  # send the packet to all ports since we do not have the distnation MAC Add. yet.

    msg = of.ofp_packet_out(data = event.ofp)
    msg.actions.append(of.ofp_action_output(port =all_ports))
    event.connection.send(msg)

def launch (disable_flood = False):
  global all_ports, updated
  if disable_flood:
    all_ports = of.OFPP_ALL
  def start():
    core.host_tracker.addListenerByName("HostEvent", _handle_HostEvent)  # listen to host_tracker
    core.openflow_discovery.addListenerByName("LinkEvent", _handle_LinkEvent)
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.call_when_ready(start, ('openflow','openflow_discovery','host_tracker'))
  log.info("Pair-Learning switch running.")



