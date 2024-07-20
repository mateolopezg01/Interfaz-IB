
from scipy import signal

def PasaBanda(Fr=10,Fs=250):
    b, a = signal.iirfilter(2, [(Fr-1),(Fr+1)], btype='band', analog=False, ftype='butter',fs=Fs)
    return b, a

print( PasaBanda())