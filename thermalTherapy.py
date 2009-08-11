import sys
import os
import utilities
import jobsetup
import ConfigParser
#the jobid is passed in from the command line
controlfile = sys.argv[1]

#read the main control file
iniFile = utilities.control_defaults(controlfile) 
iniFile.readfp( open("%s" % controlfile , "r") )

#get the jobid
checkid = iniFile.get("compexec","jobid")
jobid   = utilities.checkprevious(checkid)
iniFile.set("compexec","jobid",jobid)
Executable = iniFile.get( "compexec" ,"executable")

print iniFile.get("compexec","comphost")
#get the computation host information
[comphost,loccomphost,compendian,workdir] = \
         utilities.hostinformation(iniFile,"compexec","comphost","workdir")

#constant runtime options
runtime_options = iniFile.get("compexec","runtime_options")

if(Executable == "image"):

  #get input/output parameters
  ExamPath = iniFile.get(   "mrti" ,"exampath")
  DirId    = iniFile.getint("mrti" ,"dirid")
  OutputDir= "mrivis"
  
  # constant runtime options
  base_options = " %s %d %s %s " % (ExamPath,DirId,OutputDir,runtime_options) 
  
  #build list of jobs to run
  JOBS=jobsetup.setupkalman(iniFile) 

elif(Executable == "thermalTherapy" or Executable == "dddas"):

  #build list of jobs to run
  JOBS=jobsetup.setuplitt(iniFile) 

  # constant runtime options
  base_options = runtime_options

else:
  raise ValueError("unknown executable %s " % Executable )

# loop over the job in the list JOBS and run the code for each one
CODEEXEC=[] 
for (namejob,numproc,param_options,cntrlfile,method) in JOBS:
   # write control file with additional parameters
   inifile=open("%s/%s/files/control.ini" % (jobid,namejob) ,"w")
   cntrlfile.write(inifile)
   inifile.close
   inifile.flush() # ensure the entire file is written before continuing
   # code execution on shamu
   if(comphost.split(".")[0] == "shamu"):
      # write a qsub file
      qsubfile=open("%s/%s/%s/%s.qsub" %(workdir,jobid,namejob,namejob) ,"w")
      qsubfile.write("#!/bin/bash              \n"           )
      qsubfile.write("#$ -pe mpich %d          \n" % numproc )
      qsubfile.write("#$ -N %s                 \n" % namejob )
      qsubfile.write("#$ -cwd                  \n"           )
      qsubfile.write("#$ -S /bin/bash          \n"           )
      qsubfile.write("#$ -v LD_LIBRARY_PATH,PATH,WORK,COMPILER\n")
      qsubfile.write("#$ -v MPI_VERSION,METHOD=%s \n" % method)
      qsubfile.write("mpirun -np $NSLOTS -machinefile $TMP/machines $WORK/exec/%s_$COMPILER-$MPI_VERSION-cxx-$METHOD  %s %s" % (Executable,base_options, param_options))
      # ensure entire file written before continuing
      qsubfile.close; qsubfile.flush() 
      execcode="cd %s/%s/%s ; qsub %s.qsub  " %  \
                         (workdir,jobid,namejob,namejob)
   else: # default code execution
      execcode="cd %s/%s/%s ; mpirun -n %d $WORK/exec/%s_$COMPILER-$MPI_VERSION-cxx-$METHOD  %s %s" % (workdir,jobid,namejob,numproc,
                       Executable,base_options,param_options)
   CODEEXEC.append(execcode)

execMETH= ";".join(CODEEXEC)
print "code execution method: %s \n" % execMETH

# sit idle until user inputs ready to continue
utilities.pause_until_ready()

#run the code
os.system(execMETH)

