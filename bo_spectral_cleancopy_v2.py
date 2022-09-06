# -*- coding: utf-8 -*-
"""BO_spectral_cleancopy_v2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mCPhG0nAYTYW8cLPWuctwHdz39vbsufM
"""

#pip install torch torchvision
#pip install botorch #version 0.5.1
#pip install gpytorch #version 1.6.0
#pip install smt
#pip install streamlit

import streamlit as st
import numpy as np
import torch
from torchvision import datasets, transforms
import matplotlib as mpl
import numpy as np
import matplotlib.pyplot as plt
import pickle
import numpy as np
import random
#import streamlit as st
#import kornia as K
#import kornia.metrics as metrics
from PIL import Image
from typing import Tuple
#import ipywidgets as widgets
#from IPython.display import display
import pylab as pl
#from IPython.display import clear_output
#import pdb
from skimage.transform import resize
from mpl_toolkits.axes_grid1 import make_axes_locatable
#import gpim
#from sklearn.decomposition import PCA
import matplotlib.gridspec as gridspec
#from copy import deepcopy
#import pyroved as pv
#import atomai as aoi
#from typing import Union



# Import GP and BoTorch functions
#import gpytorch as gpt
#from botorch.models import SingleTaskGP, ModelListGP
#from botorch.models import gpytorch
#from botorch.fit import fit_gpytorch_model
#from botorch.models.gpytorch import GPyTorchModel
#from botorch.utils import standardize
#from gpytorch.distributions import MultivariateNormal
#from gpytorch.kernels import ScaleKernel, RBFKernel, MaternKernel
#from gpytorch.likelihoods import GaussianLikelihood
#from gpytorch.means import ConstantMean, LinearMean
#from gpytorch.mlls import ExactMarginalLogLikelihood
#from botorch.acquisition import UpperConfidenceBound
#from botorch.optim import optimize_acqf
#from botorch.acquisition import qExpectedImprovement
#from botorch.acquisition import ExpectedImprovement
#from botorch.sampling import IIDNormalSampler
#from botorch.sampling import SobolQMCNormalSampler
#from gpytorch.likelihoods.likelihood import Likelihood
#from gpytorch.constraints import GreaterThan
#from gpytorch.utils.broadcasting import _mul_broadcast_shape

#from botorch.generation import get_best_candidates, gen_candidates_torch
#from botorch.optim import gen_batch_initial_conditions


#from gpytorch.models import ExactGP
from mpl_toolkits.axes_grid1 import make_axes_locatable
from smt.sampling_methods import LHS
from torch.optim import SGD
from torch.optim import Adam
from scipy.stats import norm
from scipy.interpolate import interp1d

def main(df):
    st.title('Spectral optimization through BO with adaptive target setting')
    st.subheader('by Arpan Biswas, Rama Vasudevan')
    st.markdown(
    """
        
    <br><br/>
    #Problem Description

    Build a BO framework-

    - Here we have a image data, where X is the input location of the image

    - Each location in the image, we have a spectral data, from where user select if the data is good/bad (discrete choice). We take the means of all good loops only to generate the target loop.

    - The goal is to build a optimization (BO) model where we adaptively sample towards region (in image) of good spectral, and find optimal location point closest to the current chosen target spectral (as per user voting). 
    """
    , unsafe_allow_html=True)

    Details = st.button('Details')
    if Details:
      detail_info()
      st.markdown('---')
      

    else:
      st.markdown('---')
      interactive_BO(df)

def detail_info():
    st.title('Building the Model')

    st.button('Back to analysis') 

def interactive_BO(df):
    st.sidebar.markdown('## Initialization')
    num_start = st.sidebar.slider('Starting Samples', 2, 30, 5)
    N = st.sidebar.slider('Total BO samples', 10, 200, 30)

    #Get data
    loop_mat = df[0]
    dc_vec = df[1]
    bepfm_image = df[2]

    n_spectral = 2 # Consider the final loop measurement
    loop_mat_grid = np.reshape(loop_mat,(60, 60, loop_mat.shape[1], loop_mat.shape[2]))
    loop = loop_mat_grid[:, :, :, n_spectral] 
    #print(loop.shape)

    #Tranform the image data to map with spectral data
    grid_dim = loop.shape[1]
    bepfm_lowres_image = resize(bepfm_image, (grid_dim, grid_dim))
    #print(bepfm_lowres_image.shape)

    #Consider single sweep of voltage to generate hysteresis loop
    l_vsweep= loop.shape[2]
    V= dc_vec[:l_vsweep]
    #print(V.shape)

    #Normalize loop data (avoiding drift in data)
    loop_norm = np.zeros((loop.shape))
    for i in range(0, loop.shape[0]):
      for j in range(0, loop.shape[1]):
        loop_norm[i, j, :] = (loop[i,j,:]- np.mean(loop[i,j,:]))*1e4

    #print(loop.shape, loop_norm.shape)

    #tranform data into torch
    loop_norm = torch.from_numpy(loop_norm)
    V = torch.from_numpy(V)
    bepfm_lowres_image= torch.from_numpy(bepfm_lowres_image)

    #print(loop_norm.shape, bepfm_lowres_image.shape, V.shape)
    #latent parameters for defining KL trajectories
    grid_x1 = torch.arange(0, bepfm_lowres_image.shape[0])
    grid_x2 = torch.arange(0, bepfm_lowres_image.shape[1])

    X= torch.vstack((grid_x1, grid_x2))

    #Fixed parameters of VAE model
    fix_params = [loop_norm, bepfm_lowres_image, V]
    X_opt, X_opt_GP, var_params, explored_locs, final_GP_estim = BO_vartarget(X, fix_params, num_start, N)      
        

#@title
##@title objective function evaluation- We maximize the similarity index(negative mse) between target and sampled spectral and maximize the reward as per user voting of sampled spectral
def func_obj(X, spec_norm, V, wcount_good, target_func, vote):
    idx1 = int(X[0, 0])
    idx2 = int(X[0, 1])
    rf = 1
    if (wcount_good == 0): #We dont find a good loop yet from all initial sampling and thus target is unknown
        mse_spectral = torch.rand(1)*(1)+1 # Unif[1, 2] A sufficiently large value as we want to avoid selecting bad loops,
        # When we have a target, we will recalculate again to get more accuract estimate
        R = vote*rf
      
    else:
        #Calculate dissimilarity (mse) between target and ith loop shape
        dev2_spectral = (target_func-spec_norm[idx1, idx2, :])**2
        mse_spectral = torch.mean(dev2_spectral)
        #Calculate reward as per voting, this will minimize the risk of similar function values of good and bad loop shape with similar mse
        R = vote*rf
    
    #This is the basic setting of obj func-- we can incorporate more info as per domain knowledge to improve
    #Into maximization problem
    obj = R - mse_spectral #Maximize reward and negative mse

    return obj

##@title generate/update target loop
def generate_targetobj(X, spec_norm, lowres_image, V, wcount_good, target_func, m1, m2, m3):
    #count_good= 0
    

    idx1 = int(X[0, 0])
    idx2 = int(X[0, 1])
    #print(idx1, idx2)
    #target_loop = torch.empty(loop_norm.shape[2])
    if (wcount_good == 0):
    # Figure for user choice
        fig1,ax=plt.subplots(ncols=2,figsize=(12,4))
        ax[0].plot(V,spec_norm[idx1, idx2, :])
        ax[0].set_title('loc:' +str(idx1) +"," + str(idx2))
        ax[1].imshow(lowres_image.detach().numpy())
        ax[1].plot(idx1, idx2, 'x', color="red")
        #plt.show()
        st.pyplot(fig1, clear_figure ="True")

    else:
    # Figure for user choice
        fig2,ax=plt.subplots(ncols=3,figsize=(12,4))
        ax[0].plot(V,spec_norm[idx1, idx2, :])
        ax[0].set_title('loc:' +str(idx1) +"," + str(idx2))
        ax[1].imshow(lowres_image.detach().numpy())
        ax[1].plot(idx1, idx2, 'x', color="red")
        ax[2].plot(V,target_func)
        ax[2].set_title('Current target function')
        #plt.show()
        st.pyplot(fig2, clear_figure ="True")


    st.markdown('Rating: 0-Bad, 1-Good, 2-Very good')
    #"st.session_state object:", st.session_state
    #if 'r' not in st.session_state:
    #    st.session_state['r'] = 0
    #vote = st.sidebar.slider('Rate', 0, 2, 0)
    #vote = st.sidebar.number_input('Rate', min_value=0, max_value=2, value=1, key= number)
    #count = count + 1
    options = ["Bad", "Good", "Very Good"]
    Rate = st.radio('Rate', options, key= m1)
   
    if Rate == "Bad":
        vote = 0
        wcount_good = wcount_good + vote
        st.write('Vote given for current spectral', Rate)
        #st.write(st.session_state.key)
    
    elif Rate == "Good":
        vote = 1
        #wcount_good = wcount_good + vote
        st.write('Vote given for current spectral', Rate)
        newspec_wt = 1
        if ((wcount_good) > 0): #Only if we already have selected good spectral in early iterations
            st.markdown('Do you want to update preference to new spectral over prioir mean target (Y/N)?')
            newspec_pref = st.radio("Select",('Yes', 'No'), index=1, key=m2)
            st.write('You selected', newspec_pref)
            #newspec_pref = str(input("Do you want to update preference to new spectral over prioir mean target (Y/N): "))
            if (newspec_pref == 'Yes'):
                st.markdown('Provide weights between 0 and 1: 1 being all the weights to new spectral as new target')
                newspec_wt = st.number_input('Weight', min_value=0.0, max_value=1.0, value =1.0, step =0.1, key= m3)
                st.write('You choose weight for new spectral:', newspec_wt)
                #print("Provide weights between 0 and 1: 1 being all the weights to new spectral as new target")
                #newspec_wt = float(input("enter weightage: "))
            else:
                newspec_wt = 0.5
                st.write('Default weight for new spectral: 0.5')
        wcount_good =wcount_good + vote
        target_func = (((1-newspec_wt)*target_func*(wcount_good-vote))\
                       + (newspec_wt*vote*spec_norm[idx1, idx2, :]))/(((wcount_good-vote)*(1-newspec_wt))\
                       + (vote*newspec_wt))
        #st.write(st.session_state.key)
        
    else:
        vote = 2
        #wcount_good = wcount_good + vote
        st.write('Vote given for current spectral', Rate)
        newspec_wt = 1
        if ((wcount_good) > 0): #Only if we already have selected good spectral in early iterations
            st.markdown('Do you want to update preference to new spectral over prioir mean target (Y/N)?')
            newspec_pref = st.radio("Select",('Yes', 'No'), index =1, key=m2)
            st.write('You selected', newspec_pref)
            #newspec_pref = str(input("Do you want to update preference to new spectral over prioir mean target (Y/N): "))
            if (newspec_pref == 'Yes'):
                st.markdown('Provide weights between 0 and 1: 1 being all the weights to new spectral as new target')
                newspec_wt = st.number_input('Weight', min_value=0.0, max_value=1.0, value = 1.0, step =0.1, key= m3)
                st.write('You choose weight for new spectral:', newspec_wt)
                #print("Provide weights between 0 and 1: 1 being all the weights to new spectral as new target")
                #newspec_wt = float(input("enter weightage: "))
            else:
                newspec_wt = 0.5
                st.write('Default weight for new spectral: 0.5')
        wcount_good =wcount_good + vote
        target_func = (((1-newspec_wt)*target_func*(wcount_good-vote))\
                       + (newspec_wt*vote*spec_norm[idx1, idx2, :]))/(((wcount_good-vote)*(1-newspec_wt))\
                       + (vote*newspec_wt))
        #st.write(st.session_state.key)
        
        #st.write(st.session_state.key)

    
    #target_func =0
    return vote, wcount_good, target_func  



# Normalize all data. It is very important to fit GP model with normalized data to avoid issues such as
# - decrease of GP performance due to largely spaced real-valued data X.
def normalize_get_initialdata_KL(X, fix_params, num, m):
    
    X_feas = torch.empty((X.shape[1]**X.shape[0], X.shape[0]))
    k=0
    spec_norm, lowres_image, V  = fix_params[0], fix_params[1], fix_params[2]
    m1, m2, m3  = m[0], m[1], m[2]
    
    
    for t1 in range(0, X.shape[1]):
        for t2 in range(0, X.shape[1]):
            X_feas[k, 0] = X[0, t1]
            X_feas[k, 1] = X[1, t2]
            k=k+1
    
    X_feas_norm = torch.empty((X_feas.shape[0], X_feas.shape[1]))
    #train_X = torch.empty((len(X), num))
    #train_X_norm = torch.empty((len(X), num))
    train_Y = torch.empty((num, 1))
    pref = torch.empty((num, 1))
   

    # Normalize X
    for i in range(0, X_feas.shape[1]):
        X_feas_norm[:, i] = (X_feas[:, i] - torch.min(X_feas[:, i])) / (torch.max(X_feas[:, i]) - torch.min(X_feas[:, i]))
      
    

    # Select starting samples randomly as training data
    np.random.seed(0)
    idx = np.random.randint(0, len(X_feas), num)
    train_X = X_feas[idx]
    train_X_norm = X_feas_norm[idx]
    #print(train_X)
    #print(train_X_norm)

    #Evaluate initial training data
    x = torch.empty((1,2))
    # First generate target loop, based on initial training data
    wcount_good= 0
    #count=0
    target_func = torch.zeros(spec_norm.shape[2])
    i = 0
    #if st.button("Next spectral", key="next"):
    #for i in range(0, num):
    for i in range(0, num):
        x[0, 0] = train_X[i, 0]
        x[0, 1] = train_X[i, 1]
        #print("Sample #" + str(m + 1))
        st.write("Starting samples", train_X)
        st.write("Sample #", m1+1)
        pref[i, 0], wcount_good, target_func = generate_targetobj(x, spec_norm, lowres_image, V, wcount_good, target_func, m1, m2, m3)
        m1 = m1 + 1
        m2 = m2 + 1
        m3 = m3 + 1
        #i = i + 1
        #st.experimental_rerun()
            
    #else:
    st.markdown("Initial evaluation complete. Start BO")
    idx1 = int(x[0, 0])
    idx2 = int(x[0, 1])
    fig3,ax=plt.subplots(ncols=3,figsize=(12,4))
    ax[0].plot(V,spec_norm[idx1, idx2, :])
    ax[0].set_title('loc:' +str(idx1) +"," + str(idx2))
    ax[1].imshow(lowres_image.detach().numpy())
    ax[1].plot(idx1, idx2, 'x', color="red")
    ax[2].plot(V,target_func)
    ax[2].set_title('Current target function')
    #plt.show()
    st.pyplot(fig3, clear_figure ="True")
    
    # Once target loop is defined (unless are loops are selected bad by user), we compute the obj
    for i in range(0, num):
        x[0, 0] = train_X[i, 0]
        x[0, 1] = train_X[i, 1]

        #print("Function eval #" + str(m + 1))

        train_Y[i, 0] = func_obj(x, spec_norm, V, wcount_good, target_func, pref[i, 0])
        #m = m + 1
    #print(pref)
    #print(train_Y)
    var_params = [wcount_good, pref, target_func]
    m = [m1, m2, m3]
    st.write(train_X, train_X_norm, train_Y, m)
    
    return X_feas, X_feas_norm, train_X, train_X_norm, train_Y, var_params, idx, m


################################Augment data - Existing training data with new evaluated data################################
def augment_newdata_KL(acq_X, acq_X_norm, train_X, train_X_norm, train_Y, fix_params, var_params, m):
    spec_norm, lowres_image, V  = fix_params[0], fix_params[1], fix_params[2]
    wcount_good, pref, target_func = var_params[0], var_params[1], var_params[2]
    

    nextX = acq_X
    nextX_norm = acq_X_norm
    #train_X_norm = torch.cat((train_X_norm, nextX_norm), 0)
    #train_X_norm = train_X_norm.double()
    train_X_norm = torch.vstack((train_X_norm, nextX_norm))
    train_X = torch.vstack((train_X, nextX))
    
    p = torch.empty(1, 1)
    x = torch.empty((1,2))
    x[0, 0] = train_X[-1, 0]
    x[0, 1] = train_X[-1, 1]

    print("Sample #" + str(m + 1))
    #Vote for new spectral sample and update(or not) target spectral function
    p[0, 0], wcount_good, target_func = generate_targetobj(x, spec_norm, lowres_image, V, wcount_good, target_func)
    pref = torch.vstack((pref, p)) #Augment pref matrix
    
    if (p[0, 0] == 0):
      # If target loop is not updated, we eval for the new samples only as the func value for others remain the same

        next_feval = torch.empty(1, 1)
        next_feval[0, 0] = func_obj(x, spec_norm, V, wcount_good, target_func, pref[-1, 0])
        train_Y = torch.vstack((train_Y, next_feval))
    else:
        # If target loop is updated, we reevaluate the obj of old spectral samples and eval for the new samples
        train_Y = torch.empty((train_X.shape[0], 1))
        for i in range(0, train_X.shape[0]):
            x[0, 0] = train_X[i, 0]
            x[0, 1] = train_X[i, 1]
            train_Y[i, 0] = func_obj(x, spec_norm, V, wcount_good, target_func, pref[i, 0])

    
    #print(pref)
    #print(train_Y)
    var_params = [wcount_good, pref, target_func]
    m = m + 1
    return train_X, train_X_norm, train_Y, var_params, m

##@title Functions to plot KL trajectories at specific BO iterations (Need to revise)
def plot_iteration_results(train_X, train_Y, test_X, y_pred_means, y_pred_vars, fix_params, i):
    spec_norm, lowres_image, V  = fix_params[0], fix_params[1], fix_params[2]
    pen = 10**0
    #Best solution among the evaluated data
    
    loss = torch.max(train_Y)
    ind = torch.argmax(train_Y)
    X_opt = torch.empty((1,2))
    #X_opt = train_X[ind, :]
    X_opt[0, 0] = train_X[ind, 0]
    X_opt[0, 1] = train_X[ind, 1]


    # Best estimated solution from GP model considering the non-evaluated solution

    loss = torch.max(y_pred_means)
    ind = torch.argmax(y_pred_means)
    X_opt_GP = torch.empty((1,2))
    #X_opt = train_X[ind, :]
    X_opt_GP[0, 0] = test_X[ind, 0]
    X_opt_GP[0, 1] = test_X[ind, 1]

    #Objective map
    plt.figure()

    fig,ax=plt.subplots(ncols=3,figsize=(12,4))
    a= ax[0].imshow(lowres_image.detach().numpy(), origin="lower")
    ax[0].scatter(train_X[:,0], train_X[:,1], marker='o', c='g')
    ax[0].scatter(X_opt[0, 0], X_opt[0, 1], marker='x', c='r')
    ax[0].scatter(X_opt_GP[0, 0], X_opt_GP[0, 1], marker='o', c='r')


    a = ax[1].scatter(test_X[:,0], test_X[:,1], c=y_pred_means/pen, cmap='viridis', linewidth=0.2)
    ax[1].scatter(train_X[:,0], train_X[:,1], marker='o', c='g')
    ax[1].scatter(X_opt[0, 0], X_opt[0, 1], marker='x', c='r')
    ax[1].scatter(X_opt_GP[0, 0], X_opt_GP[0, 1], marker='o', c='r')
    divider = make_axes_locatable(ax[1])
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(a, cax=cax, orientation='vertical')
    ax[1].set_title('Objective (GP mean) map')
    #ax[1].colorbar(a)

    b = ax[2].scatter(test_X[:,0], test_X[:,1], c=y_pred_vars/(pen**2), cmap='viridis', linewidth=0.2)
    divider = make_axes_locatable(ax[2])
    cax = divider.append_axes('right', size='5%', pad=0.05)
    fig.colorbar(b, cax=cax, orientation='vertical')
    ax[2].set_title('Objective (GP var) map')
    #ax[2].colorbar(b)
    #plt.show()
    st.pyplot(fig, clear_figure ="True")
    

    return X_opt, X_opt_GP

#BO framework integration
def BO_vartarget(X, fix_params, num_start, N):
    num = num_start
    m1 = 0
    m2 = 1000
    m3 = 100000
    m = [m1, m2, m3]
    # Initialization: evaluate few initial data normalize data
    test_X, test_X_norm, train_X, train_X_norm, train_Y, var_params, idx, m = \
        normalize_get_initialdata_KL(X, fix_params, num, m)


    


@st.cache
def load_data():
    loop_mat = np.load("loop_mat.npy")
    dc_vec = np.load("dc_vec.npy")
    bepfm_image = np.load("bepfm_image.npy")
    df = [loop_mat, dc_vec, bepfm_image]
    return df


if __name__ == '__main__':

    #logging.basicConfig(level=logging.CRITICAL)

    df = load_data()

    main(df)
