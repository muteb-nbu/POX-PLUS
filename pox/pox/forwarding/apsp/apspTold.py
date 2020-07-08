
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
#from pox.core import core
#import event
# Even a simple usage of the logger is much nicer than print!
log = core.getLogger()

G = Graph()
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

sw_host = defaultdict()
def _handle_HostEvent ( event):
    global sw_host
    """ Here is the place where is used the listener"""
    print ("Host, switchport and switch...", event.entry.macaddr.toStr(),(event.entry.dpid,event.entry.port))
    #print (type(event.entry))
    sw_host[event.entry.macaddr.toStr()] = (event.entry.dpid,event.entry.port)

'''
def cal_G(n):
  for l in core.openflow_discovery.adjacency:
    G.addVertex(l.dpid1)
    G.addVertex(l.dpid2)
    G.addEdge(l.dpid1, (l.dpid2, l.port2))
'''  
  
  
def cal_SPT(): 
  n = G.numVertices
  print_G()
  for i in range(n):
    tree = SPT()
    tree.init_SPT(n)
    Forest[i] = tree.build_SPT(G,i)

    
def _handle_ConnectionUp(event):
  print ("COnecctionUp")
  global updated
  
  #update False
  


def _handle_LinkEvent (event):
  '''
  if event.added:
    print "000"
    print "000           00                  00              TTTTTTTTTTTTTTTTTTTTTTTTTTT    added"
    print "0000"
  else:
    print ("000  (from_sw, pt)  ..   (to_sw,pt2)", (event.link.dpid1,event.link.port1), (event.link.dpid2,event.link.port2))
    print "000           00                  00              TTTTTTTTTTTTTTTTTTTTTTTTTTT    removed", type(event)
    print "0000"
  '''

  l = event.link
  sw1 = l.dpid1 -1
  sw2 = l.dpid2-1
  pt1 = l.port1
  pt2 = l.port2
  #f not G.getVerteg(sw1):
  
  #if (G.numVertices and (sw2,pt1) not in G.vertList(sw1).connectedTo):
  G.addVertex(sw1)
  G.addVertex(sw2)
  G.addEdge(sw1, (sw2,pt1))
  G.addEdge(sw2,(sw1,pt2))

  if updated:
    #update_SPT()
    for j in range(G.numVertices):
      #tree = Forest[j]
      if ((sw2,pt1) in G.getVertex(sw1).getConnections()):
        G.rmEdge(sw1,(sw2,pt1))
        G.rmEdge(sw2,(sw1,pt2))
        Forest[j].decremental(G, sw1,sw2)
      else:
        Forest[j].incremental(G, sw1,sw2)
def print_G():
  for i in G.vertList:
    print (G.vertList[i].id)
    for rr in G.vertList[i].getConnections():
      print ("******** nbr  **", rr)
def print_F():
  for j in range(G.numVertices):
    print ("  *********************  TREE  %i    *******************"%j)
    tree = Forest[j]
    for i in tree.treeList:
      print (tree.treeList[i].id, tree.treeList[i].wieght)
      for rr in tree.treeList[i].children:
          print ("******** children **", rr)

  #print (" IN _handle_ConnectionUp   ********************************************************************")  
def _handle_ConnectionDown(event):
  print "connection Down 000      1111111111111111111111111111111111111111111111111111111111"

def _handle_PortStatus (event):
    if event.added:
        action = "added"
    elif event.deleted:
        action = "removed"
    else:
        action = "modified"
    print "Port %s on Switch %s has been %s." % (event.port, event.dpid, action)
    '''
    for i in range(G.numVertices):
      #sw = event.connection(sw)
      con = core.openflow.getConnection(i+1)
      print ("IN SW%i        00000000000000000000000000000000000000000000000000000000     111111111111"%con.dpid)
    print (type(event), "   <- event    000    event.parsed0")     
   '''

# Handle messages the switch has sent us because it has no
# matching rule.

def _handle_PacketIn (event):
  global updated, G, Forest
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
  
  if packet.dst.toStr() in sw_host.keys(): # We know the distnation MAC Add. ,So, We apply APSP 
    targetSW_PT = sw_host[packet.dst.toStr()]
    pt = Forest[event.dpid -1].treeList[targetSW_PT[0] - 1].port
    if not pt:
      pt = targetSW_PT[1]
    
    msg = of.ofp_flow_mod()
    msg.match.dl_dst = packet.src
    msg.match.dl_src = packet.dst
    msg.actions.append(of.ofp_action_output(port = event.port))
    event.connection.send(msg)
    
    #print
    print
    print ("111111111 1 1 1  1 1 1 1 1 1 1 1 1 1 11 1 1 1 1 1 1 1 1 1 1  (%i,%i,%i)        USING APSP ***" %(event.dpid,pt,event.port))
    msg = of.ofp_flow_mod()
    msg.data = event.ofp # Forward the incoming packet
    msg.match.dl_src = packet.src
    msg.match.dl_dst = packet.dst
    msg.actions.append(of.ofp_action_output(port = pt))
    event.connection.send(msg)
  
  
  
  else:  # send the packet to all ports since we do not have the distnation MAC Add. yet.
    msg = of.ofp_packet_out(data = event.ofp)
    msg.actions.append(of.ofp_action_output(port = all_ports))
    event.connection.send(msg)
    print   ("00        00                     00                 00                      00         NOT    USING apsp*  ***")
  

def launch (disable_flood = False):
  global all_ports, updated
  #core.registerNew(
  if disable_flood:
    all_ports = of.OFPP_ALL
  def start():
    core.host_tracker.addListenerByName("HostEvent", _handle_HostEvent)  # listen to host_tracker
    core.openflow_discovery.addListenerByName("LinkEvent", _handle_LinkEvent)
    core.openflow.addListenerByName("PortStatus", _handle_PortStatus)
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("ConnectionDown", _handle_ConnectionDown)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
  core.call_when_ready(start, ('openflow','openflow_discovery','host_tracker'))
  #core.call_when_ready(start, "openflow")
  log.info("Pair-Learning switch running.")




