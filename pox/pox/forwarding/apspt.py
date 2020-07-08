# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A super simple OpenFlow learning switch that installs rules for
each pair of L2 addresses.
"""

# These next two imports are common POX convention
from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.Graph import Graph
from pox.Graph import SPT
from pox.lib.revent import *
from collections import defaultdict
from pox.host_tracker import host_tracker
from pox.lib.addresses import EthAddr
#import event
# Even a simple usage of the logger is much nicer than print!
log = core.getLogger()

G = Graph()
G.addVertex(0)
Forest = {}
#tree = SPT()
# This table maps (switch,MAC-addr) pairs to the port on 'switch' at
# which we last saw a packet *from* 'MAC-addr'.
# (In this case, we use a Connection object for the switch.)
table = {}


# To send out all ports, we can use either of the special ports
# OFPP_FLOOD or OFPP_ALL.  We'd like to just use OFPP_FLOOD,
# but it's not clear if all switches support this, so we make
# it selectable.
all_ports = of.OFPP_FLOOD


#MUTEB

updated = False
s_h = defaultdict(lambda: list()) # sw  <-> hosts  s_h = [ s1: {h1, h2, ..}, .......]
host_sw = defaultdict() # host <-> sw host_sw = [h1: (s1, pt1), h2: (s1,pt2), .....]
def _handle_HostEvent ( event):
    global host_sw
    """ Here is the place where is used the listener"""
    print ("Host, switchport and switch...", event.entry.macaddr.toStr(),(event.entry.dpid,event.entry.port))
    #print (type(event.entry))
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
  print ("COnecctionUp")
  global updated
  


def collect_vertices(tree, s, v):
  aff = list()
  listW = list()
  listW.append(v)
  #tree = Forest[s]
  while listW:
    v = listW.pop()
    aff.append(v)
    for key in tree.treeList[v].children.keys():
      listW.append(key)
  return aff
    
#set_of_MACADD = list()
updated_linkes = defaultdict()
def _handle_LinkEvent (event):
  global  G, Forest, updated_linkes, s_h_h
  l = event.link
  sw1 = l.dpid1
  sw2 = l.dpid2
  pt1 = l.port1
  pt2 = l.port2
  
  if not updated:
    #G.addVertex(sw1)
    #G.addVertex(sw2)
    G.addEdge(sw1, (sw2,pt1))
    G.addEdge(sw2,(sw1,pt2))
  elif event.removed:
    G.rmEdge(sw1,(sw2,pt1))
    G.rmEdge(sw2,(sw1,pt2))
    ###########################                                                                 1111111111
    print ("  000           000000    sw%i,  sw%i                     000000000          dec"%(sw1,sw2))
    if sw2 not in updated_linkes.keys(): # if not, then it was already updated
      updated_linkes[sw1] = sw2
      for i in range(len(Forest)):
        #Forest[i].build_ports(i)
        # removing flows of hosts connecting to the source (i.e. switch) of this tree to all other switches in t(v)
        if s_h[i]:
          tree = Forest[i]
          print "In tree  ", i
          parent = tree.treeList[sw1].parent
          if parent and parent.id == sw2:
            flip = sw1
            sw1 = sw2
            sw2 = flip
          if tree.treeList[sw2].parent<>tree.treeList[sw1]: # not a tree edge on the tree t(i)
            continue
          affected = collect_vertices(tree, sw1, sw2 )  # collect vertices in t(v)
          hosts = list()
          for v in affected:
            if v in s_h and s_h[v]:
              hosts = hosts+ s_h[v]
          u = tree.treeList[sw1]
          while u is not None: # we collect vertices in the path between v and source
            affected.append(u.id)
            u = u.parent
          print "       TTTTTTTTTTTTTTTTTTTT   YYYYYYYYYYYYYYYYY  ",len(hosts)
          
          while affected:
            u = affected.pop()
            for host in s_h[i]: 
              #msg to sw to remove flows starting from affected
              msg = of.ofp_flow_mod(match=of.ofp_match(),command=of.OFPFC_DELETE_STRICT)
              msg.match.dl_src = host
              for host2 in hosts:
                msg.match.dl_dst = host2 #s_h_h[u][host.toStr()]
                switch = core.openflow.getConnection(u)
                switch.send(msg)
        Forest[i].decremental(G, sw1, sw2)
    else:
      del updated_linkes[sw2]
    #############################           1111                                                1111111
  elif event.added:
    G.addEdge(sw1, (sw2,pt1))
    G.addEdge(sw2,(sw1,pt2))
    #########################                                           00000000000000000
    print ("  000           000000    sw%i,  sw%i   inc            0000  inc"%(sw1,sw2))    
    if sw2  not in updated_linkes.keys(): # if not, then it was already updated
      updated_linkes[sw1] = sw2
      for i in range(len(Forest)):
        tree = Forest[i]
        if tree.treeList[sw1].wieght > tree.treeList[sw2].wieght:
          flip = sw1
          sw1 = sw2
          sw2 = flip
        u = tree.treeList[sw1]
        affected = list()
        while u is not None: # we collect vertices in the path between v and source
          affected.append(u.id)
          u = u.parent

        Forest[i].decremental(G, sw1, sw2)
        Forest[i].build_ports(i)          
        affected = collect_vertices(tree, sw1, sw2 )  # collect vertices in t(v) after the update operation

        # removing flows of hosts connecting to the source (i.e. switch) of this tree to all other switches
        if s_h[i]:
          while affected:
            u = affected.pop()
            if u in s_h:
              for host in s_h[u]: 
                print (" deleting flow from (%s) in sw%i" %(host.toStr(), u))#msg to sw to remove flows starting from affected
                msg = of.ofp_flow_mod(match=of.ofp_match(),command=of.OFPFC_DELETE)
                msg.match.dl_src = host
                #print "TTTTTTTTTTTTTTTTTTTTTTTT0                TTTTTT ,",len(s_h_h)
                #print  "   00    ", len(s_h_h[u])
                if host.toStr() in s_h_h.keys():
                  msg.match.dl_dst = s_h_h[u][host.toStr()]
                  del s_h_h[u][host.toStr()]
                  print "TTTTTTTTTTTTTTTTTTTTTTTT0                TTTTTT ,"
                  print "TTTTTTTTTTTTTTTTTTTTTTTT0                TTTTTT ,"
                  msg.match.dl_type = 0x800
                  msg.match.nw_proto = 6
                  #msg.match.dl_type = 0x800
                  switch = core.openflow.getConnection(u)
                  switch.send(msg)
    else:
      del updated_linkes[sw2]
    

# Handle messages the switch has sent us because it has no
# matching rule.
s_h_h = defaultdict(lambda:defaultdict(lambda:[]))
def _handle_PacketIn (event):
  global updated, G, Forest, s_h_h
  packet = event.parsed
  if not updated:
    cal_SPT()
    #update_SPT()
    #update_Table()
    updated = True
    print_F()
  
  #####################
  
  
  # learn the source
  #sw_host[packet.dst.toStr()] = (event.port,event.dpid)
  
  if packet.dst in host_sw.keys(): # We know the distnation MAC Add. ,So, We apply APSP 
    targetSW_PT = host_sw[packet.dst]
    pt = Forest[event.dpid].treeList[targetSW_PT[0]].port
    if not pt:
      pt = targetSW_PT[1]
    print ("sending a packet from %s to %s through port %i              0000    0 "%(packet.src.toStr(), packet.dst.toStr(), pt)) 
    msg = of.ofp_flow_mod()
    msg.match.dl_dst = packet.src
    msg.match.dl_src = packet.dst
    msg.actions.append(of.ofp_action_output(port = event.port))
    event.connection.send(msg)

    '''
    if packet.dst.toStr() in s_h_h[event.dpid]:
      s_h_h[event.dpid][packet.dst.toStr()].append(packet.src)
    else:
      s_h_h[event.dpid] = {packet.dst.toStr():packet.src}


    if packet.src.toStr() in s_h_h[event.dpid]: 
       s_h_h[event.dpid][packet.src.toStr()].append(packet.dst)
    else:
       s_h_h[event.dpid] = {packet.src.toStr():packet.dst}
    '''
    if packet.src not in s_h_h[event.dpid][packet.dst.toStr()]:
      s_h_h[event.dpid][packet.dst.toStr()].append(packet.src)
    if packet.dst not in s_h_h[event.dpid][packet.src.toStr()]:
      s_h_h[event.dpid][packet.src.toStr()].append(packet.dst)
    #s_h_h[event.dpid] = {packet.src.toStr():packet.dst}
    msg = of.ofp_flow_mod()
    msg.data = event.ofp # Forward the incoming packet
    msg.match.dl_src = packet.src
    msg.match.dl_dst = packet.dst
    msg.actions.append(of.ofp_action_output(port = pt))
    event.connection.send(msg)
    print 
    print
    print s_h_h
  
  
  else:  # send the packet to all ports since we do not have the distnation MAC Add. yet.
    msg = of.ofp_packet_out(data = event.ofp)
    msg.actions.append(of.ofp_action_output(port = all_ports))
    event.connection.send(msg)
    print "       000                 111111                 1111111               111111          sending all ports"    

def launch (disable_flood = False):
  global all_ports, updated
  #core.registerNew(
  if disable_flood:
    all_ports = of.OFPP_ALL
  def start():
    core.host_tracker.addListenerByName("HostEvent", _handle_HostEvent)  # listen to host_tracker
    core.openflow_discovery.addListenerByName("LinkEvent", _handle_LinkEvent)
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.call_when_ready(start, ('openflow','openflow_discovery','host_tracker'))
  #core.call_when_ready(start, "openflow")
  log.info("Pair-Learning switch running.")

