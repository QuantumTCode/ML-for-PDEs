import numpy as np
import random
import os.path
import pickle as pkl
import torch


class DataGene:
    def __init__(self,device,n=10,x_max=np.pi,x_min=0.0,num_x=30,T_max=1000.0,beta=5000.0,IC=200,train_cnt=0.75):
        # define basic vars and parms that is reusable
        self.n = n
        self.x_max = x_max
        self.x_min = x_min
        self.num_x = num_x
        self.T_max = T_max
        self.beta = beta
        self.IC = IC
        self.train_cnt = train_cnt
        self.device = device
        # calculation
        self.dx = (self.x_max - self.x_min)/self.num_x
        self.x = np.append([np.arange(self.x_min,self.x_max,self.dx)],[self.x_max])
        self.x_range = self.x.shape[0]
        self.x = np.expand_dims(self.x, axis=0)
        self.x = np.repeat(self.x,IC,axis=0)
        self.x = np.expand_dims(self.x,axis=2)
        self.c = np.zeros((self.IC,n))
        for seed in range(1,self.IC+1,1):
            np.random.seed(seed)
            self.c[seed-1] = np.random.normal(0.0,1.0,self.n)
            
    def DataSplit(self,u):
        allSamples_ = range(u.shape[0])
        num_ = u.shape[0]
        train_cnt_ = int(num_*self.train_cnt)
        np.random.seed(0)
        np.random.shuffle(allSamples_)
        u_train = u[allSamples_[0:train_cnt_]]
        u_test = u[allSamples_[train_cnt_:]]
        
        return u_train, u_test
    
    def DataForTrain(self,u):
        u = torch.tensor(u,device=self.device)
        raw_ = u.transpose(1,2).transpose(1,0).unsqueeze(2)
        x_ = raw_[:-1]
        y_ = raw_[1:]
        x_ = x_.reshape(-1,1,raw_.shape[3])
        y_ = y_.reshape(-1,1,raw_.shape[3])
        
        return x_, y_
        
        
    def DataForTest(self,u,length):
        u = torch.tensor(u,device=self.device)
        raw_ = u.transpose(1,2).transpose(1,0).unsqueeze(2)
        x_ = raw_[:-length]
        y_ = raw_[length:]
        x_ = x_.reshape(-1,1,raw_.shape[3])
        y_ = y_.reshape(-1,1,raw_.shape[3])
        
        return x_, y_
        
        
    # generate stable and unstable cases
    def Plain(self,dt):
        t = np.arange(0.0,self.T_max+dt,dt)
        t_range = t.shape[0]
        t = np.expand_dims(t, axis=0)
        t = np.repeat(t,self.IC,axis=0)

        U = np.zeros((self.IC,self.x_range,t_range))

        t = np.expand_dims(t,axis=1)
        t = np.repeat(t,self.x_range,axis=1)

        x = np.repeat(self.x,t_range,axis=2)

        for i in xrange(self.n):
            temp_c = \
            np.repeat(np.repeat(np.expand_dims(np.expand_dims(self.c[:,i],axis=1),axis=1),self.x_range,axis=1),t_range,axis=2)
            temp_exp = np.exp(-((i+1)**2)/self.beta*t)
            temp_term = temp_c*np.sin((i+1)*x)
            temp = temp_term*temp_exp
            U += (1.0/self.n)*temp
            
        U_train, U_test = self.DataSplit(U)
            
        return U, U_train, U_test
    
   # generate data for the noisy case
    def Noise(self,dt,err_scale):
        t = np.arange(0.0,self.T_max+dt,dt)
        t_range = t.shape[0]
        t = np.expand_dims(t, axis=0)
        t = np.repeat(t,self.IC,axis=0)
        
        U = np.zeros((self.IC,self.x_range,t_range))
        
        t = np.expand_dims(t,axis=1)
        t = np.repeat(t,self.x_range,axis=1)
        
        x = np.repeat(self.x,t_range,axis=2)
        for i in xrange(self.n):
            temp_c = \
            np.repeat(np.repeat(np.expand_dims(np.expand_dims(self.c[:,i],axis=1),axis=1),self.x_range,axis=1),t_range,axis=2)
            temp_exp = np.exp(-((i+1)**2)/self.beta*t)
            temp_term = temp_c*np.sin((i+1)*x)
            temp = temp_term*temp_exp
            U += (1.0/self.n)*temp
        
        # fixing random seed for reproduction
        np.random.seed(0)
        U = U + np.random.randn(self.IC,self.x_range,t_range)*np.abs(U)*err_scale
            
        U_train, U_test = self.DataSplit(U)
            
        return U, U_train, U_test

    # generate data for the forcing case
    def Force(self,dt,f_scale):
        t = np.arange(0.0,self.T_max+dt,dt)
        t_range = t.shape[0]
        t = np.expand_dims(t, axis=0)
        t = np.repeat(t,self.IC,axis=0)
        
        U = np.zeros((self.IC,self.x_range,t_range))
        
        t = np.expand_dims(t,axis=1)
        t = np.repeat(t,self.x_range,axis=1)
        
        x = np.repeat(self.x,t_range,axis=2)
        
        np.random.seed(0)
        d = f_scale*np.random.normal(0.0,1.0,(self.n,1,1,1))
        d = np.repeat(np.repeat(np.repeat(d,self.IC,axis=1),self.x_range,axis=2),t_range,axis=3)
        
        for i in xrange(self.n):
            temp_c = \
            np.repeat(np.repeat(np.expand_dims(np.expand_dims(self.c[:,i],axis=1),axis=1),self.x_range,axis=1),t_range,axis=2)
            temp_d = d[i]
            temp_exp = np.exp(-((i+1)**2)/self.beta*t)
            temp_term1 = (temp_c-(temp_d/((i+1)**2)))*np.sin((i+1)*x)
            temp_term2 = temp_d*np.sin((i+1)*x)/((i+1)**2)
            temp = temp_term1*temp_exp + temp_term2
            U += (1.0/self.n)*temp
        
        U_train, U_test = self.DataSplit(U)
            
        return U, U_train, U_test
        