# Spectral optimization through BO with adaptive target setting


The Bayesian Optimization (BO) framework is build in $torch$, using $Botorch$.

Run <b>VarTBO_nb.ipynb</b> to play : https://github.com/arpanbiswas52/varTBO/blob/main/varTBO_nb.ipynb 

Version of the <b>modified BO spectral recommendation system to connect with microscope<b>: [https://github.com/arpanbiswas52/varTBO/blob/main/varTBO_microscopeversion_nb.ipynb](https://github.com/arpanbiswas52/varTBO/blob/main/BO_spectral_MicroscopyVersion.ipynb)


Brief Problem Description

- Here we have a image data, where X is the input location of the image

- Each location in the image, we have a spectral data, from where user select if the data is good/bad. We define target spectral from chosen good spectral

- The goal is to build a optimization (BO) model where we adaptively sample towards region (in image) of good spectral, and find optimal location point closest to the current chosen target spectral (as per user voting).

<i> Please let me know if you have questions, find any bugs, issues, or want another option/feature added at either biswasar@ornl.gov, arpanbiswas52@gmail.com.


