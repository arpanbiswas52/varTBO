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
from IPython.display import display
import pylab as pl
from IPython.display import clear_output
import pdb
from skimage.transform import resize
from mpl_toolkits.axes_grid1 import make_axes_locatable
#import gpim
#from sklearn.decomposition import PCA
import matplotlib.gridspec as gridspec
#from copy import deepcopy
#import pyroved as pv
#import atomai as aoi
#from typing import Union
#import pickle


# Import GP and BoTorch functions
import gpytorch as gpt
from botorch.models import SingleTaskGP, ModelListGP
#from botorch.models import gpytorch
from botorch.fit import fit_gpytorch_model
from botorch.models.gpytorch import GPyTorchModel
from botorch.utils import standardize
from gpytorch.distributions import MultivariateNormal
from gpytorch.kernels import ScaleKernel, RBFKernel, MaternKernel
from gpytorch.likelihoods import GaussianLikelihood
from gpytorch.means import ConstantMean, LinearMean
from gpytorch.mlls import ExactMarginalLogLikelihood
from botorch.acquisition import UpperConfidenceBound
from botorch.optim import optimize_acqf
from botorch.acquisition import qExpectedImprovement
from botorch.acquisition import ExpectedImprovement
from botorch.sampling import IIDNormalSampler
from botorch.sampling import SobolQMCNormalSampler
from gpytorch.likelihoods.likelihood import Likelihood
from gpytorch.constraints import GreaterThan

from botorch.generation import get_best_candidates, gen_candidates_torch
from botorch.optim import gen_batch_initial_conditions

from gpytorch.models import ExactGP
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
    num_start = st.sidebar.slider('Starting Samples', 2, 30, 10)
    N = st.sidebar.slider('Total BO samples', 10, 200, 100)

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
    bepfm_lowres_image = np.resize(bepfm_image, (grid_dim, grid_dim))
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
