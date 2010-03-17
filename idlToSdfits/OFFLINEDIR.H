/* File OFFLINEDIR.H, version 1.12, released  07/05/17 at 13:44:18 
   retrieved by SCCS 07/11/17 at 16:05:56     


%% definition of default directories

:: doppler checkLogFiles
 
HISTORY:
  070310 Gil - new ovlbi home
  010622 AHM - put deltaT file in ~ovlbi/ftp/out rather than ~ovlbi/prerelease
  991208 AHM - change paths so that /ovlbi becomes /home/ovlbi for OS upgrade
  980818 AHM - add dir for ftp
  980215 AHM - ftp directories moved
  971125 AHM - clockModel.dat put under SCCS and in new directory
  970924 ahm - by default put deltaT files into /ovlbi/ovlbi/prerelease
  970702 ahm - ovlbi account moved to /ovlbi disk
  961204 ahm - add srt and cmd file default directories
  961010 AHM - initial version
 
DESCRIPTION:
  Definition of default directories where to look for and put input and 
  output files
*/

/* define default directories */
#define FTPOUTDIR      "/home/ovlbi/ftp/out/"
#define FTPINDIR       "/home/ovlbi/ftp/in/"
#define DOPPLERDIR     "/home/ovlbi/ftp/out/"
#define DELTATDIR      "/home/ovlbi/ftp/out/"
#define ORBITDIR       "/home/ovlbi/in/"
#define TWTDIR         "/home/ovlbi/out/"
#define LOGDIR         "/home/ovlbi/out/"
#define SRTDIR         "/home/ovlbi/ftp/in/"
#define CMDDIR         "/home/ovlbi/in/"
#define BINDIR         "/home/ovlbi/bin/"


/* define where some files can be found */
#define SOLARFLUX      "/home/ovlbi/offline/scriptFiles/solarFlux.dat"
#define CLOCKMODEL     "/home/ovlbi/in/clockModel.dat"
#define OLDTAPEHIST    "/home/ovlbi/offline/scriptFiles/oldTapeHistory"
#define LASTTAPEHIST   "/home/ovlbi/offline/scriptFiles/lastTapeHistory"
#define NEWTAPEHIST    "/home/ovlbi/offline/scriptFiles/newTapeHistory"
#define FTPCOMMANDFILE "/home/ovlbi/out/logMerge.ftpCommands"


