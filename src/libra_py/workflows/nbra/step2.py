#***********************************************************
# * Copyright (C) 2017-2019 Brendan A. Smith, Wei Li, and Alexey V. Akimov
# * This file is distributed under the terms of the
# * GNU General Public License as published by the
# * Free Software Foundation; either version 3 of the
# * License, or (at your option) any later version.
# * http://www.gnu.org/copyleft/gpl.txt
#***********************************************************/

"""
.. module:: step2
   :platform: Unix, Windows
   :synopsis: This module implements functions for doing NAC calculaitons in the 1-electron
       basis of KS orbitals, withe the QE package

.. moduleauthor:: Brendan A. Smith, Wei Li, and Alexey V. Akimov

"""

import os
import sys

# Fisrt, we add the location of the library to test to the PYTHON path
if sys.platform=="cygwin":
    from cyglibra_core import *
elif sys.platform=="linux" or sys.platform=="linux2":
    from liblibra_core import *
from libra_py import QE_methods
from libra_py import QE_utils
from libra_py import units

#import libra_py.common_utils as comn
import util.libutil as comn

from . import compute_properties
from . import compute_hprime



def run(params):
    """This function is the main driver for the NAC calculations withing the workflows/nbra

    Args:
        params ( dictionary ): Simulation control parameters

        * **params["start_indx"]** ( int ): index of the starting datapoint in the trajectory to compute
            the NACs [default: 0]
        * **params["stop_indx"]** ( int ): index of the final datapoint in the trajectory to compute
            the NACs [default: 1]
        * **params["dt"]** ( double ): time step between two adjacent datapoint a the trajectory [units: a.u.; default: 41.0]
        * **params["wd"]** ( string ): the name of a "working directory (can be removed once the calculatons
            are done)" that will be created during this function execution - this is where the temporary files
            are written to 
        * **params["rd"]** ( string ): the name of a "results directory" - this is where all the output files 
            files will be written to [ default: "res" ]
        * **params["nac_method"]** ( int ): selects the type of output to analyze:

            - 0 : non-spin-polarized calculations [default]
            - 1 : spin-polarized calculations
            - 2 : non-collinear calculation (SOC) only 
            - 3 : spin-polarized and non-collinear calculation (SOC)

        * **params["compute_Hprime"]** ( Boolean ): the flag to compute the <i|H'|j> matrices [ default: False]
        * **params["verbosity"]** ( int ): the verbosity level regarding the execution of the current function [default: 0]


        ..seealso:: parameters of ::funct::```run_qe``` function
            * **params["BATCH_SYSTEM"]**
            * **params["NP"]**
            * **params["EXE"]**
            * **params["EXE_EXPORT"]**
            * **params["prefix0"]**
            * **params["prefix1"]**

        ..seealso:: parameters of ::funct::```read_all``` function

            * **params["read_wfc"]** 
            * **params["read_grid"]**
            * **params["verb0"]** 
            * **params["verb1"]**
            * **params["verb2"]**

        ..seealso:: parameters of ::funct::```read_wfc_grid``` function
            * **params["maxband"]**
            * **params["minband"]**
            * **params["maxband_soc"]**
            * **params["minband_soc"]**



    Returns:
        None: but generates the files with couplings, energies and transition density matrices
            The matrices are of  2N x 2N dimensions, where N = maxband - minband + 1
 
    """

    # Now try to get parameters from the input
    critical_params = [ "rd" ]
    default_params = { "start_indx":0, "stop_indx":1, "dt":1.0*units.fs2au, 
                       "wd":"wd",
                       "nac_method":0,
                       "pdos_flg":0,
                       "compute_Hprime":False, 
                       "verbosity":0
                     }
    comn.check_input(params, default_params, critical_params)


    rd = params["rd"]

    start_indx = int(params["start_indx"]) 
    stop_indx  = int(params["stop_indx"]) 
    dt = params["dt"]
    wd = params["wd"]
    nac_method = params["nac_method"]
    compute_Hprime = params["compute_Hprime"]
    verbosity = params["verbosity"]    
    pdos_flg = params["pdos_flg"]

    if verbosity>0:
        print( "Starting trajectory.run")
    tim = Timer()

    # Sanity/Convention check
        
    if nac_method == 0:        
        if verbosity>0:
            print( "non-relativistic, non-spin-polarized calculations \n")
    elif nac_method == 1:
        if verbosity>0:
            print( "non-relativistic, spin-polarized calculations \n")
    elif nac_method == 2:
        if verbosity>0:
            print( "fully relativistic, non-collinear calculations \n")
    elif nac_method == 3:
        if verbosity>0:
            print( "same as 2 + 1, followed by the projections  \n")
    else:
        print( "Error: nac_method must be one of the values in [0,1,2,3]  \n")
        sys.exit(0)



    # Initialize variables
    curr_index = start_indx - 1
    t = start_indx

    if verbosity>0:
        print( "In trajectory.run: current working directory for python: ",os.getcwd())
        print( "In trajectory.run: current working directory for sh:",os.system("echo $(pwd)"))

    # Create the working directory where all output files will be written
    # The results directory should already exist
    os.system("mkdir %s" % wd)  
    while t<=stop_indx:

        if verbosity>0:
            print( ">>>>>>>>>>>>>>>>>>>>  t= ", t, " <<<<<<<<<<<<<<<<<<<<<")

            print( "stop_indx", stop_indx)
            print( "start_indx", start_indx)

        dirname = ""
        if t==start_indx:
           if verbosity>0:
               print( "Starting first point in this batch")
           dirname0, dirname1 = "curr0", "curr1"

        if t>start_indx:
           if verbosity>0:
               print( "Continuing with other points in this batch")
           dirname0, dirname1 = "next0", "next1"


        # Run the QE calculations       
        QE_methods.run_qe(params, t, dirname0, dirname1)

        
        if curr_index>=start_indx:

            # Update curr_index in params - this may be useful
            params["curr_index"] = curr_index

            # First see wether the calculation is what we wanted
            info0, all_e_dum0, info1, all_e_dum1 = QE_methods.read_info(params)

            # Read present and next electronic structure (es) in a formatted way
            es_curr, es_next = QE_methods.read_wfc_grid(params) 

            # Finally,  using the current and the next wavefunctions to compute the properties of interest

            # For the non-relativistic and either spin or non-spin-polarized case

            if nac_method == 0 or nac_method == 1 or nac_method == 3:
                if ( info0["nspin"]==1 and info0["nk"]==1 ) or ( info0["nspin"]==2 and info0["nk"] == 2) : # Non-SOC case

                    # Only one k-point. For the spin-polarized case, the beta orbtials are as if they were computed using 2 K-points
                    # (nk = 2). However, they are not. This is just the QE format for expressing alpha and beta orbitals at a single K-point 
                    #if info0["nk"]==1 or info0["nk"] == 2:  

                    if verbosity>0:
                        print( "Computing various properies of the spin-diabatic (non-relativistic) KS orbitals using a single K-point")

                    # Compute various properties of the spin-diabatic (non-relativistic) KS orbitals at a single K-point 
                    compute_properties.compute_properties_onekpt(params, es_curr, es_next, curr_index)

                else: 

                    # Compute various properies of the spin-diabatic (non-relativistic) KS orbitals using multiple K-point
                    if verbosity>0:
                        print( "Computing various properies of the spin-diabatic (non-relativistic) KS orbitals using multiple K-points")
                        print( "Warning: This capabilitiy is under development and not fully tested")

                    print ("This capability is temporarily disabled. Please use only a single K-point for now")
                    print ("Exiting now")
                    sys.exit(0)
                    #compute_properties.compute_properties_general(params, es_curr, es_next, curr_index)
           
                if compute_Hprime == True:

                    # Compute the transition dipole moment along the nuclear trajectory
                    if verbosity>0:
                        print( "Computing the transition dipole moment along the nuclear trajectory")
                        print( "Warning: This capabilitiy is under development and not fully tested")

                    # C++ implementation
                    compute_hprime.compute_hprime_dia(es_curr, info0, "%s/0_Hprime_%d" % (rd, curr_index) )

                    # Python implementation
                    #compute_hprime.hprime_py(es_curr, info0, "%s/0_Hprime_%d" % (rd, curr_index) )
               

            # For the relativistic case
            if nac_method == 2 or nac_method == 3:

                # Only one k-point
                if info1["nk"]==1:

                    if verbosity>0:
                        print( "Computing various properies of the spin-adiabatic (relativistic) KS orbitals using a single K-point")

                    # Compute various properties of the spin-adiabatic (relativistic) KS orbitals at a single K-point              
                    compute_properties.compute_properties_onekpt(params, es_curr, es_next, curr_index)
                    #compute_properties.compute_properties_adi_gamma(params, es_curr, es_next, curr_index)

                else:
                    print( "Multiple k-points scheme with SOC is not yet implemented")
                    sys.exit(0)

            
            # Checking if spin-adiabtic and spin-diabatic cases were using the same sized P\plane wave basis
            if  nac_method == 3:

                print( "nac_method == 3: Entering check for whether the adiabatic and diabatic basis have the same number of plane waves")
             
                # Check whether the adiabatic and diabatic basis have the same number of plane waves
                # the reason why I used the read_qe_wfc_info is because I will need the ngw 
                # to check the consistency 
                # But the read_qe_index does not read it, so in order to avoid the changes in the Libra code, 
                # I use the read_qe_wfc_info.

                info_wfc0 = QE_methods.read_qe_wfc_info("%s/curr0/x0.export/wfc.1" % wd,0)
                info_wfc1 = QE_methods.read_qe_wfc_info("%s/curr1/x1.export/wfc.1" % wd,0)

                if info_wfc0["ngw"] != info_wfc1["ngw"]:
                    print( "Error: The number of plane waves of diabatic and adiabatic functions should be equal")
                    sys.exit(0)
                else:
                    print( "Pass: The number of plane waves of diabatic and adiabatic functions are equal")
 
                params1 = {"do_orth": 0, "root_directory": rd, "curr_index": curr_index, "print_overlaps": 1, "dt": dt}
                compute_ovlps(coeff_curr0, coeff_next0, coeff_curr1, coeff_next1, e_curr0, e_next0, e_curr1, e_next1, params1)

            #-----------------------------------------------------------------

            # Remove current run, make next run to be the current one
            if nac_method == 0 or nac_method == 1 or nac_method==3:
                os.system("rm -rf %s/curr0" % wd )
                os.system("mv %s/next0 %s/curr0" % (wd, wd) )
            
            if nac_method==2 or nac_method==3:
                os.system("rm -rf %s/curr1" % wd )
                os.system("mv %s/next1 %s/curr1" % (wd, wd) )
            
            if verbosity>0:
                print( "old files deleted, new have become old")
       
      
        # Move the index files to the results directory, just don't copy the very last one - it is a repetition
        #if t<stop_indx:
        if nac_method == 0 or nac_method == 1 or nac_method==3:
            # The input file template defined in params["prefix0"] should have   prefix = 'x0' !
            os.system("cp %s/curr0/x0.export/index.xml %s/x0_index_%i.xml" % (wd, rd, t))
            os.system("cp %s/curr0/x0.save/data-file-schema.xml %s/x0_data-file-schema_%i.xml" % (wd, rd, t))
            os.system("cp %s/curr0/%s.%d.out %s/%s.%d.out" % (wd, params["prefix0"], t, rd, params["prefix0"], t))

            if pdos_flg == 1:
                print ("Entering pdos_flag == 1: Outputting files necessary for computing pDOS calculations with projwfc.x")
                print ("Warning: Crashes at this point may result from QE versioning. This flag is currently compatable with QE v6.2.1")
                print ("Warning: This flag is tested only for non-relativisitic cases")

                os.system("cp %s/curr0/x0.save/charge-density.dat %s/x0_charge-density_%i.dat" % (wd, rd, t))
                os.system("cp %s/curr0/x0.save/wfcdw1.dat %s/x0_wfcdw1_%i.dat" % (wd, rd, t))
                os.system("cp %s/curr0/x0.save/wfcup1.dat %s/x0_wfcup1_%i.dat" % (wd, rd, t))

        if nac_method == 2 or nac_method == 3:
            # The input file template defined in params["prefix1"] should have   prefix = 'x1' !
            os.system("cp %s/curr1/x1.export/index.xml %s/x1_index_%i.xml" % (wd, rd, t))
            os.system("cp %s/curr1/x1.save/data-file-schema.xml %s/x1_data-file-schema_%i.xml" % (wd, rd, t))
            os.system("cp %s/curr1/%s.%d.out %s/%s.%d.out" % (wd, params["prefix1"], t, rd, params["prefix1"], t))
      
    
        # ACHTUNG!!! Restoring wfc makes some complications, so we might need to destroy wfc objects
        # after each round of operations and create new objects from the beginning - thia may be safer!

        curr_index = curr_index + 1
               
        if verbosity>1:
            print( "End of step t=", t)

        t = t + 1


