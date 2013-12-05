from hashlib import sha1
from numpy import *

# This is a Numpy array (i.e. a vector in the math sense) that can be used
# with sets and dicts, because it is hashable; otherwise it behaves exactly
# the same as a normal NP array, and can be used interchangeably (watch out
# for operation order however, because automatic casting can hurt!)

class HashableArray(ndarray):

   def __new__(cls, data, dtype=None):
      return array(data, dtype).view(cls)

   # def __init__(self, data):
   #    self._hash = int(sha1(self).hexdigest(), 16)

   def __hash__(self):
      return int(sha1(self).hexdigest(), 16)
      #return self._hash

   def __eq__(self, other):
      return all(ndarray.__eq__(self, other))
      #return allclose(self, other)

   def __setitem__(self, key, value):
      raise Exception('HashableArray is read-only')

def hround(h, n_decimals):
   return harray(round_(h, n_decimals))

harray = HashableArray    

if __name__ == '__main__':

    a = array((1,2,3))
    b = HashableArray((2,3,4))
    c = a - b #HashableArray(a-b)
    d = HashableArray((2,3,4))
    e = HashableArray((0,0,1))
    f = HashableArray((0.,0.,1.))

    s = set()
#    s.add(a)
    s.add(b)
    s.add(c)
    s.add(d)
    s.add(e)
    s.add(f)
    #print s

    h = harray([0.12345, 0.12345])
    print hround(h, 2)
