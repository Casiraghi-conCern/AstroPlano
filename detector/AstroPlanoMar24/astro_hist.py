# -*- coding: utf-8 -*-
"""
Created on Fri Jan 31 17:20:15 2020

@author: fontanel
"""
import math
import numpy as np
import matplotlib.pyplot as plt
#import matplotlib.mlab as mlab

class myhist():
    def __init__(self,titolo,lx,ly):
        self.titolo =titolo
        self.lx=lx
        self.ly=ly
        self.minimo=None
        self.massimo=None
        self.num_bins=None
        self.ndati=0
        self.dat=[]
    def add_data(self, x):
        self.dat.append(x)
        self.ndati = self.ndati+1
    
    def plot_histo(self, num_bins):
        if self.ndati==0:
            print ('\n\nIstogramma %s vuoto\n\n'%self.titolo)
            return
        self.minimo = min (self.dat)
        self.massimo = max (self.dat)
        self.num_bins = num_bins
        if self.ndati>0:
            print ('\n\nIstogramma: %s'% self.titolo)
            print ('N. di elementi: %d,  Minimo: %.1f,  massimo:  %.1f, n. canali: %d'%
               (self.ndati, self.minimo, self.massimo, self.num_bins))
        # the histogram of the data
        n, bins, patches = plt.hist(self.dat, self.num_bins, density=False, \
                facecolor='blue', alpha=1)

#        # add a 'best fit' line
#        
#        y = mlab.normpdf(bins, mu, sigma)
#        plt.plot(bins, y, 'r--')
        plt.xlabel(self.lx)
        plt.ylabel(self.ly)
        plt.title(self.titolo)

        # Tweak spacing to prevent clipping of ylabel
        plt.subplots_adjust(left=0.15)
        plt.show()

#scatter plot
class myscatter():
    def __init__(self,titolo,lx,ly, color):
        self.titolo =titolo
        self.lx=lx
        self.ly=ly
        self.minimo=None
        self.massimo=None
        self.num_bins=None
        self.ndati=0
        self.datx=[]
        self.daty=[]
        self.color=color
    def add_data(self, x, y):
        self.datx.append(x)
        self.daty.append(y)
        self.ndati = self.ndati+1
    
    def plot_scatter(self, num_binsx, num_binsy):
        if self.ndati==0:
            print ('\n\nScatter plot %s vuoto\n\n'%self.titolo)
            return
        self.num_binsx = num_binsx
        self.num_binsy = num_binsy
        if self.ndati>0:
            print ('\n\nIstogramma: %s'% self.titolo)
            print ('N. di elementi: %d,  n. canali X: %d, n. canali y: %d'%
               (self.ndati, self.num_binsx, self.num_binsy))
        # the histogram of the data
        plt.scatter(self.datx, self.daty, c=self.color, marker=".", s=1, alpha=1)

        plt.xlabel(self.lx)
        plt.ylabel(self.ly)
        plt.title(self.titolo)

        plt.show()
        



if __name__ == "__main__":
    misto = myhist('esempio', 'assex ', 'asse y')
    for i in range(1000): misto.add_data(np.random.randint(0, 10000))
    misto.plot_histo(25)
    
    np.random.seed(19680801)
    scat= myscatter ('esempio2', 'asse X', 'asse Y', 'blue')
    x, y = np.random.rand(2, 1000)
    for i in range(1000):
        scat.add_data(x[i], y[i])
    scat.plot_scatter(50, 50)
    
