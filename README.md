# human-augmented Bayesian optimized spectral recommendation system: A "human-in-the-loop Automated Experiment framework"
<b>MLExchange Project funded by Berkeley Lab, award number 107514</b>


<i> **Brief Problem Description** </i>
![image](https://user-images.githubusercontent.com/19354142/225442105-9e040b14-fa3d-43de-b359-ae5e6c9601b9.png)

- Here we have a image data, where X is the input location of the image

- Each location in the image, we have a spectral data, from where user select if the data is good/bad. We define target spectral from user votes and feature preference on good sampled spectral

- The goal is to build a optimization (BO) model where we adaptively learn the target features/properties of the material sample and simultaneously maximize the structural sim of spectral to the target at the current state of BO process.

Different architectures of <b>BO spectral recommendation system</b>: 
  
<b>BOSRS with standard GP and 2D co-ordinate as input X</b> (in torch)
https://github.com/arpanbiswas52/varTBO/blob/main/BO_spectral_(Notebookversion).ipynb

<b> BOSRS with standard GP and high-dim image patch as input X</b> (in torch)
https://github.com/arpanbiswas52/varTBO/blob/main/BO(image_patch)_(Notebookversion).ipynb
  
<b> dKLBOSRS with dKLGP (deep learning kernel GP) and high-dim image patch as input X</b> (in numpy)
https://github.com/arpanbiswas52/varTBO/blob/main/dKLBO_spectral_(Notebookversion).ipynb
https://github.com/arpanbiswas52/varTBO/blob/main/dKLBO_spectral_MicroscopyVersionv2.ipynb

<b>Note*</b> the deep learning kernel (dKL) function in this architecture is developed by Maxim Ziatdinov (in AtomAI Python library). Details on dkL model can be found here https://atomai.readthedocs.io/en/latest/atomai_models.html#atomai.models.dklGPR

**Please feel free to use these notebooks for your research, however, please cite the github repository**

<i> Please let me know if you have questions, find any bugs, issues, or want another option/feature added at either biswasar@ornl.gov, arpanbiswas52@gmail.com.


