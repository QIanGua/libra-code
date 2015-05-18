#include "Control_Parameters.h"
#include "Model_Parameters.h"
#include "units.h"

/*********************************************************************************
  This file contains the following functions:


  void set_parameters_eht(Control_Parameters& prms, Model_Parameters& modprms)
  

*********************************************************************************/

void set_parameters_eht(Control_Parameters& prms, Model_Parameters& modprms){

  //---------------------------- Reading parameters file --------------------------------------

  int i,j,k;
  std::string filename = prms.parameters;
  std::string st;
  vector< vector<std::string> > file;
  vector<std::string> file_raw;

  cout<<"Reading EHT parameters file = "<<filename<<endl;
  ifstream in(filename.c_str(), ios::in);
  if(in.is_open()){
    while(!in.eof()){
      getline(in,st); 
      file_raw.push_back(st);

      vector<std::string> line;
      stringstream ss(st,stringstream::in|stringstream::out);
      while(ss>>st){ line.push_back(st);}

      file.push_back(line);


    }// while
  }else{ cout<<"Error: Can not open file\n";}
  in.close();


  cout<<"Echo tokenized EHT parameters file content\n";
  int sz = file.size();
  for(i=0;i<sz;i++){
    for(j=0;j<file[i].size();j++){
      cout<<file[i][j]<<"  ";
    }
    cout<<endl;
  }// i

  int n_extra_params = 0;
  if(prms.eht_params_format=="eht+0"){ n_extra_params = 0; }
  else if(prms.eht_params_format=="eht+1"){ n_extra_params = 1; }
  else if(prms.eht_params_format=="eht+2"){ n_extra_params = 2; }
  else if(prms.eht_params_format=="eht+3"){ n_extra_params = 3; }
  else if(prms.eht_params_format=="eht+4"){ n_extra_params = 4; }
  else{
    cout<<"Error: eht_params_format = "<<prms.eht_params_format<<" is not known\n";
    exit(0);
  }

  //--------- Some sanity check --------
  if(prms.eht_sce_formula==1 && n_extra_params<2){
    cout<<"Error: sce_formula = 1 requires at least 2 additional parameters: 1) slope for positive charges, 2) slope for negative charges\n";
    cout<<"Change eht_params_format to \"eht+2\" or more and ensure that the parameters file has required number of fields in a line\n";
    exit(0);
  }
  //------------------------------------
  

  for(i=0;i<sz;i++){

    //>>>>>>>>>>> Reading atomic parameters <<<<<<<<<<<<<<
    if(file[i].size()>0){
    if(file[i][0]=="<At_constants>"){

      // search for end of this group
      int end_i = i;
      for(int i1=i+1;i1<sz;i1++){
        if(file[i1].size()>0){  if(file[i1][0]=="</At_constants>"){ end_i = i1; break; }    }// non-empty line
      }// for i1



      // now analyze all lines in between
      for(int i1=i+1;i1<end_i;i1++){

        std::string elt = file[i1][0];
        modprms.PT[elt].Nval = atoi(file[i1][1].c_str());
        int nsh = atoi(file[i1][2].c_str());
        modprms.PT[elt].Zeff = (double)modprms.PT[elt].Nval;


        cout<<"Reading parameters for element "<<elt<<endl; 
        cout<<"Nval = "<<modprms.PT[elt].Nval<<endl;
        cout<<"Zeff = "<<modprms.PT[elt].Zeff<<endl;
        cout<<"  reading parameters for "<<nsh<<" orbital shells"<<endl;


        for(j=1;j<=nsh;j++){
          // Example of format:
          //Li  1  2
          //1   2  0  2s    -5.342   1     1.0000  0.6450   0.000   0.000   0.000   0.000
          //2   2  1  2p    -3.499   1     1.0000  0.5240   0.000   0.000   0.000   0.000
          // This will set:
          // elt = Li   - element symbol
          // Nval = 1   - number of valence electrons 
          // nsh = 2    - number of shells
          // Zeff = 2.0 - effective charge of the atomic core
          //
          // then for j = 1, 2
          //    for j = 1:
          //    sh = 2s      - name of this shell
          //    Nquant = 2   - principal quantum number
          //    IP = -5.342  - negative of the valence state ionization energy (orbital energy)
          //    Nzeta = 1    - number of zetas for this orbital, ost often 1, rare 2


          std::string sh = file[i1+j][3];
  
          modprms.PT[elt].Nquant[sh] = atoi(file[i1+j][1].c_str());
          modprms.PT[elt].IP[sh]     = atof(file[i1+j][4].c_str())*eV;
          modprms.PT[elt].Nzeta[sh]  = atoi(file[i1+j][5].c_str());
  
          modprms.PT[elt].coeffs[sh] = vector<double>(2,0.0);
          modprms.PT[elt].zetas[sh]  = vector<double>(2,0.0);
  
          cout<<"    j= "<<j<<" sh= "<<sh<<" Nquant= "<<modprms.PT[elt].Nquant[sh]
              <<" IP= "<<modprms.PT[elt].IP[sh]/eV<<" eV Nzeta= "<<modprms.PT[elt].Nzeta[sh]<<"  ";
  
          for(k=0;k<modprms.PT[elt].Nzeta[sh];k++){
            modprms.PT[elt].coeffs[sh][k] = atof(file[i1+j][6+2*k].c_str());
            modprms.PT[elt].zetas[sh][k]  = atof(file[i1+j][6+2*k+1].c_str());
            cout<<" coeff["<<k<<"]= "<<modprms.PT[elt].coeffs[sh][k]
                <<" zetas["<<k<<"]= "<<modprms.PT[elt].zetas[sh][k]<<" Bohr^-1  ";
          }//for k
          cout<<endl;
  
  
          if(modprms.PT[elt].Nzeta[sh]==1){    
  
            if(file[i1+j].size()>=(8+n_extra_params)){ ;; } // all is fine
            else{  cout<<"Error in parameters file: line \n"
                       <<file_raw[i1+j]
                       <<"\n is not complient with expected format which is = "
                       <<prms.eht_params_format<<endl;
                   cout<<"Missing "<<(8+n_extra_params)-file[i1+j].size()<<" more parameter(s)\n";
              exit(0);
            }
  
            if(n_extra_params>0){ modprms.PT[elt].J_param1[sh] = atof(file[i1+j][8].c_str()) * eV;  }// slope for positive charges, SC-EHT
            if(n_extra_params>1){ modprms.PT[elt].J_param2[sh] = atof(file[i1+j][9].c_str()) * eV;  }// slope for negative charges, SC-EHT
            if(n_extra_params>2){ modprms.PT[elt].J_param3[sh] = atof(file[i1+j][10].c_str()); }
            if(n_extra_params>3){ modprms.PT[elt].J_param4[sh] = atof(file[i1+j][11].c_str()); }
  
          }
          else if(modprms.PT[elt].Nzeta[sh]==2){
  
            if(file[i1+j].size()>=(10+n_extra_params)){ ;; } // all is fine
            else{  cout<<"Error in parameters file: line \n"
                       <<file_raw[i1+j]
                       <<"\n is not complient with expected format which is = "
                       <<prms.eht_params_format<<endl;
                   cout<<"Missing "<<(10+n_extra_params)-file[i1+j].size()<<" more parameter(s)\n";
              exit(0);
            }
    
            if(n_extra_params>0){ modprms.PT[elt].J_param1[sh] = atof(file[i1+j][10].c_str()) * eV; }// slope for positive charges, SC-EHT
            if(n_extra_params>1){ modprms.PT[elt].J_param2[sh] = atof(file[i1+j][11].c_str()) * eV; }// slope for negative charges, SC-EHT
            if(n_extra_params>2){ modprms.PT[elt].J_param3[sh] = atof(file[i1+j][12].c_str()); }
            if(n_extra_params>3){ modprms.PT[elt].J_param4[sh] = atof(file[i1+j][13].c_str()); }
  
          }// Nzeta==2
        }// for j

        i1 += (nsh+1);

      }// for i1

      i = end_i + 1;
    }// <At_constants>

    else if(file[i][0]=="<K_constants>"){
      // search for end of this group
      int end_i = i;
      for(int i1=i+1;i1<sz;i1++){
        if(file[i1].size()>0){  if(file[i1][0]=="</K_constants>"){ end_i = i1; break; }    }// non-empty line
      }// for i1


      // now analyze all lines in between
      for(int i1=i+1;i1<end_i;i1++){

        if(file[i1].size()>=7){  


 
          cout<<"Adding K, K1 and K2 parameters: "
              <<file[i1][0]<<"  "<<file[i1][1]<<"  "<<file[i1][2]<<"  "<<file[i1][3]<<"  "
              <<"  K (unitless) = "<<atof(file[i1][4].c_str())
              <<" K1 (eV) = "<<atof(file[i1][5].c_str())
              <<" K2 (eV) = "<<atof(file[i1][6].c_str());
                                                                                                                 
          modprms.eht_k.set_K_value(file[i1][0],file[i1][1],file[i1][2],file[i1][3], atof(file[i1][4].c_str()) );
          modprms.eht_k.set_K1_value(file[i1][0],file[i1][1],file[i1][2],file[i1][3], atof(file[i1][5].c_str())*eV ); // convert into a.u.
          modprms.eht_k.set_K2_value(file[i1][0],file[i1][1],file[i1][2],file[i1][3], atof(file[i1][6].c_str())*eV ); // convert into a.u.


          if(file[i1].size()>=8){
            cout<<" K3 (eV) = "<<atof(file[i1][7].c_str());
            modprms.eht_k.set_K3_value(file[i1][0],file[i1][1],file[i1][2],file[i1][3], atof(file[i1][7].c_str())*eV ); // convert into a.u.



            if(file[i1].size()>=9){
              cout<<" K4 (Angst) = "<<atof(file[i1][8].c_str());
              modprms.eht_k.set_K4_value(file[i1][0],file[i1][1],file[i1][2],file[i1][3], atof(file[i1][8].c_str())*Angst ); // convert into a.u. of length

            }// >=9


          }// >=8
          cout<<endl;
        }// >=7


//        cout<<"i1 = "<<i1<<endl;
//          if(i1==21){  cout<<"file = "<<file[i1].size()<<endl;  exit(0);          }

      }// for i1

      i = end_i + 1;
    }// <K_constants>

  }// for i
  }// if file[i].size>0

  cout<<"End of set_parameters_eht function\n";

}

