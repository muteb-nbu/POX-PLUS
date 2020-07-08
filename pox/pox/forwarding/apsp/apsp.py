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
    #print ("     HHHHHHHHHHHH            ", sw_host)
    sw_host[event.entry.macaddr.toStr()] = (event.entry.dpid,event.entry.port)
    print ("     HHHHHHHHHHHH            ", sw_host) 
'''
def cal_G(n):
  for l in core.openflow_discovery.adjacency:
    G.addVertex(l.dpid1)
    G.addVertex(l.dpid2)
    G.addEdge(l.dpid1, (l.dpid2, l.port2))
'''  
  
  
def cal_SPT(): 
  global G, Forest
  n = G.numVertices
  print "  000000000000000000000000    0   0 0  0   0  0  ", n
  for i in range(n):
    tree = SPT()
    tree.init_SPT(n)
    Forest[i] = tree.build_SPT(G,i)

    
def _handle_ConnectionUp(event):
  print ("COnecctionUp")
  global updated
  
  #update False
  


def _handle_LinkEvent (event):
  global  G, Forest
  l = event.link
  sw1 = l.dpid1 -1
  sw2 = l.dpid2-1
  pt1 = l.port1
  pt2 = l.port2
  #f not G.getVerteg(sw1):
  #print "                000                     000                 000"
  #print "         0              0                           0                   0", G.numVertices
  #if ((sw2,pt1) not in G.vertList(sw1).connectedTo):
  G.addVertex(sw1)
  G.addVertex(sw2)
  G.addEdge(sw1, (sw2,pt1))
  G.addEdge(sw2,(sw1,pt2))
  #print "         0              0                           0                   0", G.numVertices 

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

def print_F():
  for j in range(G.numVertices):
    print ("  *********************  TREE  %i    *******************"%j)
    tree = Forest[j]
    for i in tree.treeList:
      print (tree.treeList[i].id, tree.treeList[i].wieght)
      for rr in tree.treeList[i].children:
          print ("******** children **", rr.id)

  #print (" IN _handle_ConnectionUp   ********************************************************************")  

# Handle messages the switch has sent us because it has no
# matching rule.
dst_port = defaultdict(lambda : defaultdict(lambda : None))

def _handle_PacketIn (event):
  global updated, G, Forest
  packet = event.parsed
  if not updated:
    cal_SPT()
    #update_SPT()
    #update_Table()
    updated = True
  print ("        0000                         000                    000                    00", event.connection)
  print ("        0000                         000                    000        dpid        00", event.dpid)  
  ''' table[(event.connection,packet.src)] = event.port
  print ("                                         ------------------- distnation    ", packet.dst.toStr(), type(event), type(packet)) 
  sw_host[packet.src.toStr()] = (event.dpid, event.port)
  print ("      **************                                          *")
  print ("      **************                                          *")
  print ("      **************                                          *")
  print ("      *              *        ",packet.src.toStr(), (event.dpid, event.port) )
  print ("      **************                                          *")
  print ("      **************                                          *")
  print ("      **************                                          *")
  '''
  print ("                                         ------------------- distnation    ", event.connection)
  if packet.dst.toStr() in sw_host.keys() and packet.dst.toStr()<>'ff:ff:ff:ff:ff:ff':
    print("   packet.dst.toStr()      *******************         *************    *", packet.dst.toStr())  
    targetSW_PT = sw_host[packet.dst.toStr()]
    target_port = targetSW_PT[1]
    target_sw = targetSW_PT[0]
    #print "--------------       TTTTTTTTTTTTTTTTTTT          TTT   ",type(pt)
    pt = Forest[event.dpid -1].treeList[target_sw - 1].port
    print "--------------       TTTTTTTTTTTTTTTTTTT          TTT   ",pt,  type(pt)
    if not pt:
      pt = target_port    
    msg = of.ofp_flow_mod()
    msg.match.dl_dst = packet.src
    msg.match.dl_src = packet.dst
    msg.actions.append(of.ofp_action_output(port = pt))
    event.connection.send(msg)
    msg = of.ofp_flow_mod()
    msg.data = event.ofp # Forward the incoming packet
    msg.match.dl_src = packet.src
    msg.match.dl_dst = packet.dst
    msg.actions.append(of.ofp_action_output(port = pt))
    event.connection.send(msg)
    print "--------------       TTTTTTTTTTTTTTTTTTT    pt, dst      TTT   ",pt,packet.dst  
    print (" 000000000000000000000000000000000000000000000000000000000000000   ")
    print (" 000000000000000000000000000000000000000000000000000000000000000   ", event.dpid, pt)
    print (" 000000000000000000000000000000000000000000000000000000000000000   ")
    #end
    
    
    #print("    packet.dst.toStr()    ***********************************",  packet.dst.toStr(),  packet.dst, type( packet.dst))
  
  # Learn the source
  else:
  
  #if True:
    print "*************                      00      ************************   SKIP    *"
    table[(event.connection,packet.src)] = event.port
  
  
    dst_port = table.get((event.connection,packet.dst))
    print "*************                      00      ************************   SKIP    *", type(dst_port)
    if dst_port is None:
      # We don't know where the destination is yet.  So, we'll just
      # send the packet out all ports (except the one it came in on!)
      # and hope the destination is out there somewhere. :)
      msg = of.ofp_packet_out(data = event.ofp)
      msg.actions.append(of.ofp_action_output(port = all_ports))
      event.connection.send(msg)
    else:
      # Since we know the switch ports for both the source and dest
      # MACs, we can install rules for both directions.
      msg = of.ofp_flow_mod()
      msg.match.dl_dst = packet.src
      msg.match.dl_src = packet.dst
      msg.actions.append(of.ofp_action_output(port = event.port))
      event.connection.send(msg)

      # This is the packet that just came in -- we want to
      # install the rule and also resend the packet.
      msg = of.ofp_flow_mod()
      msg.data = event.ofp # Forward the incoming packet
      msg.match.dl_src = packet.src
      msg.match.dl_dst = packet.dst
      msg.actions.append(of.ofp_action_output(port = dst_port))
      event.connection.send(msg)
      
  log.debug("Installing %s <-> %s" % (packet.src, packet.dst))
  

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



