
'''
	Graph implememntation
    Dynamic APSP  implememntation
    
    
    M. Alshammari and A. Rezgui, “An all pairs shortest path algorithm for
        dynamic graphs,” International Journal of Mathematics and Computer
        Science, vol. 15, no. 1, pp. 347–365, 2020.
	
	
'''
from  random import randint
from heapq import heappush, heappop
from collections import defaultdict
class Vertex:
    def __init__(self,key):
        self.id = key
        self.heapIndex = float('inf')
        self.connectedTo = set()

    def addNeighbor(self,nbr):
        self.connectedTo.add(nbr)

    def remNeighbor(self,nbr):
        self.connectedTo.remove(nbr)

    def __str__(self):
        return str(self.id) + ' connectedTo: ' + str([x.id for x in self.connectedTo])

    def getConnections(self):
        return self.connectedTo

    def getId(self):
        return self.id
    def getIndex(self):
        return self.heapIndex
    def getWeight(self,nbr):
        return self.connectedTo[nbr]
		
		
class Graph:
    def __init__(self):
        self.vertList = {}
        self.numVertices = 0

    def addVertex(self,key):
      if key not in self.vertList:
        self.numVertices = self.numVertices + 1
        newVertex = Vertex(key)
        self.vertList[key] = newVertex
        return newVertex

    def getVertex(self,n):
        if n in self.vertList:
            return self.vertList[n]
        else:
            return None

    def __contains__(self,n):
        return n in self.vertList

    def addEdge(self,f,t):
        if f == t[0]:
          return
        if f not in self.vertList:
            nv = self.addVertex(f)
        if t[0] not in self.vertList:
            nv = self.addVertex(t[0])
        self.vertList[f].addNeighbor(t)
    def rmEdge(self, f, t):
		if t in self.vertList[f].connectedTo:
			self.vertList[f].remNeighbor(t)
            

    def getVertices(self):
        return self.vertList

    def __iter__(self):
        return iter(self.vertList.values())		


  
 #			HEAP 
class HeapV:
    def __init__(self, vertex, key):
	  self.id = vertex
	  self.key = key

	  
class Heap:

    def __init__(self):
	  self.heapList = {}
	  self.len = 0
	  
    def shiftUp(self, G, length):
      child = length

      while child>0:
        if self.heapList[child].key < self.heapList[((child-1)/2)].key:
           flip = self.heapList[child]
           self.heapList[child] = self.heapList[(child-1)/2]
           self.heapList[(child-1)/2] = flip
           # update indexes
           G.vertList[self.heapList[child].id].heapIndex = child
           G.vertList[self.heapList[(child-1)/2].id].heapIndex = (child-1)/2
           # move pointer ups
           child = (child-1)/2
        else:
           return



    def shiftDown(self, G, newV):
      length = self.len-1
      child = newV*2+1
      while newV*2+1<=length:
        try:
            child = newV*2+1
            if (child+1 <= length) and (self.heapList[child].key > self.heapList[child+1].key):
              child+=1
            if (child <= length) and (self.heapList[newV].key > self.heapList[child].key):
               flip = self.heapList[child]
               self.heapList[child] = self.heapList[newV]
               self.heapList[newV] = flip
               # update indexes
               G.vertList[self.heapList[child].id].heapIndex = child
               G.vertList[self.heapList[newV].id].heapIndex =newV
               newV = child
            else:
               return self
        except:
            pass

    def push(self, G, vertex, key):
      self.len+=1
      G.vertList[vertex].heapIndex = self.len-1
      self.heapList[self.len-1] = HeapV(vertex, key)#newV
      self.shiftUp(G, self.len-1)
      
	
    def update(self, G,  key, index):
      if self.heapList[index].key > key:
        self.heapList[index].key = key
        return self.shiftUp(G, index)
      else:
        self.heapList[index].key = key
        return self.shiftDown(G, index)
      return self
    def heap (self):
      return self.len
	  
    def pop(self, G):
      self.len-=1
      popped = self.heapList[0]
      if (self.len ==0):
        del self.heapList[0]
        G.vertList[popped.id].heapIndex = float('inf')
        return popped
      self.heapList[0] = self.heapList[self.len]
      G.vertList[self.heapList[0].id].heapIndex = 0 
      del self.heapList[self.len]
      self.shiftDown(G, 0)
      G.vertList[popped.id].heapIndex = float('inf')
      return popped
	  

class treeV:
    def __init__(self, vertex):
        self.id = vertex
        self.wieght = float('inf')
        self.port = None
        self.parent = None
        self.children = defaultdict()
    
class SPT:
    def __init__(self):
        self.treeList = {}
        
    # cal tree
    def init_SPT (self,n):
        for i in range(n):
            self.treeList[i]=treeV(i)
            
    def build_pointers(self, G):
        for i in self.treeList:
            currT = self.treeList[i]
            if i in G.vertList:
              currG = G.vertList[i]
              for nbr in currG.getConnections():
                if nbr[0] in self.treeList:
                  nbrT = self.treeList[nbr[0]]
                  if (currT.wieght+1 == nbrT.wieght) and (currT.wieght <> float('inf')):
                      if nbrT.parent == None:
                          self.treeList[i].children[nbr[0]] = nbr[1] 
                          self.treeList[nbrT.id].parent = self.treeList[i]
    def build_ports(self, s):
      
      for i in self.treeList[s].children:
        port = self.treeList[s].children[i]
        l = list() 
        l.append(i)
        while l:
          u = l.pop()
          self.treeList[u].port = port
          for child in self.treeList[u].children:
            l.append(child)
      
    def build_SPT(self, G, t):
        
        heap = Heap()
        source = G.getVertex(t)
        self.treeList[t].wieght=0
        heap.push(G, t, 0)
        while (heap.heap()):   # u , nbr , source are graph vertices
            u = heap.pop(G)
            distU = u.key +1
            u = G.vertList[u.id]
            G.vertList[u.id].heapIndex = float('inf')
            for nbr in u.getConnections(): # nbrT is a tree vertex 
              if  nbr[0] in self.treeList:
                nbrT = self.treeList[nbr[0]]
                nbrG = G.getVertex(nbrT.id)
                distN = nbrT.wieght 
                
                if (distU  < distN):
                    self.treeList[nbrT.id].wieght=distU
                    index = nbrG.heapIndex
                    if index == float('inf'):
                        heap.push(G, nbrT.id, distU)
                    else:
                        heap.update(G, distU, index)
        self.build_pointers(G)
        self.build_ports(t)
        return self        

    def subTree (self, u):
        affected = list()
        affected.append(u)
        while affected:
            u = affected.pop()
            self.treeList[u].wieght = float('inf')
            for i in self.treeList[u].children:
                affected.append(i)
					
    def decremental(self, G, u, v): # deleting edge or decreasing an edge wieght
      
      if self.treeList[u].parent == self.treeList[v]: # u->v is a tree edge
        flip = u
        u = v
        v = flip
      if self.treeList[v].parent<>self.treeList[u]: # u->v is a tree edge
        return
      self.subTree(v)
      heap = Heap()
      affected = G.getVertex(v)
      heap.push(G, affected.id, self.treeList[v].wieght)
      while (heap.heap()):
          u = heap.pop(G)
          u = G.vertList[u.id]
          G.vertList[u.id].heapIndex = float('inf')
          uT = self.treeList[u.id]
          if uT.parent:
              del self.treeList[uT.parent.id].children[uT.id]
              self.treeList[u.id].parent = None
          distU = self.treeList[u.id].wieght
          bestN = None
          for nbr in u.getConnections(): # nbrT is a tree vertex 
              nbrT = self.treeList[nbr[0]]
              distN = nbrT.wieght
              if (distN +1 <= distU):
                  distU = distN +1
                  bestN = nbr
          if bestN and distU<float('inf'):
              self.treeList[bestN[0]].children[u.id] = bestN[1]
              self.treeList[u.id].parent = self.treeList[bestN[0]]
              self.treeList[u.id].wieght=distU ######
              if self.treeList[bestN[0]].port:
                self.treeList[u.id].port = self.treeList[bestN[0]].port
              else:
                self.treeList[u.id].port = self.treeList[bestN[0]].children[u.id]

          for nbr in u.getConnections():
              nbrT = self.treeList[nbr[0]]
              nbrG = G.getVertex(nbr[0])
              distN = nbrT.wieght
              if (distU +1 < distN) or (nbrT.parent and nbrT.parent.id == u.id):
                  self.treeList[nbr[0]].wieght=distU+1
                  index = nbrG.heapIndex
                  if index == float('inf'):
                      heap.push(G, nbr[0], distU+1)
                  else:
                      heap.update(G, distU+1, index)

    def incremental(self, G, u, v): # deleting edge or decreasing an edge wieght
      
      if self.treeList[u].wieght > self.treeList[v].wieght:
        flip = u
        u = v
        v = u 
      
      if self.treeList[v].wieght > (self.treeList[u].wieght+1): # u->v is a tree edge
        heap = Heap()
        affectedT = self.treeList[v]
        self.treeList[v].wieght = self.treeList[u].wieght+1
        if affectedT.parent:
            del self.treeList[affectedT.parent.id].children[v] # remove old parent
        self.treeList[v].parent = self.treeList[u] #assigning u as the new parent of v
        for i in G.vertList[u].getConnections():
          if i[0] == v:
            port = i[1]
            break
        self.treeList[u].children[v] = port 
        if self.treeList[u].port:
          self.treeList[v].port = self.treeList[u].port
        else:
          self.treeList[v].port = self.treeList[u].children[v]
        affected = G.getVertex(v)
        heap.push(G, affected.id, self.treeList[v].wieght)
        while (heap.heap()):
            u = heap.pop(G)
            distU = u.key 
            u = G.vertList[u.id]
            G.vertList[u.id].heapIndex = float('inf')
            uT = self.treeList[u.id]
            for nbr in u.getConnections():
                nbrT = self.treeList[nbr[0]] # nbrT is a tree vertex
                nbrG = G.getVertex(nbr[0])
                distN = nbrT.wieght
                if (distU +1 < distN):
                    self.treeList[nbrT.id].wieght=distU+1
                    if nbrT.parent:
                        del self.treeList[nbrT.parent.id].children[nbrT.id]
                    self.treeList[nbrT.id].parent = uT
                    self.treeList[u.id].children[nbr[0]] =nbr[1] 
                    self.treeList[nbr[0]].port = self.treeList[u.id].port
                    index = nbrG.heapIndex
                    if index == float('inf'):
                        heap.push(G, nbr[0] ,  distU+1)
                    else:
                        heap.update(G, distU+1, index)
      else:
        return 
      
   


