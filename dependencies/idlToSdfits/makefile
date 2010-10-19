# File MakeSpecIdl, version 1.12, released  05/12/07 at 11:56:34 
#   retrieved by SCCS 06/01/18 at 19:39:14     
# Makefile for GBT spectrometer unix components
#
#HISTORY
#081013 GIL try a different Cfits IO library
#051207 GIL add include file dependancies for makeIdlToAipsSdfits
#050901 GIL add findGbtFiles.c
#050715 GIL add readScanInfo.o
#050715 GIL add idlToSdfits
#050503 GIL make fitTauNonLin
#050429 GIL optimize fft routines
#050426 GIL exportGbt
#050418 GIL add functions in writeSdfits to selectSpecIdl
#050415 GIL add medianPeak
#050215 GIL add testSpecIdl
#050209 GIL replace all .f programs with .c version
#050131 GIL try to fix retrieve again
#050126 GIL add reference to libcfitsio.a
#050103 GIL add selectSdfits
#041222 GIL add printerror.o
#041222 GIL add testWriteSdfits
#040803 GIL remove specDataIdl, replace with selectSpecIdl.
#040422 GIL make all the .so file
#040422 GIL add fixDoubleSlash.o
#040416 GIL add inIntList.o, findScanFits.o
#040415 GIL add selectSpecIdl.o
#040412 GIL add fillSpecIdl.o
#040412 GIL add nextState.o, support specDataIdl.so, setSpecIntensity.o
#031217 GIL add medianVectors() and median4Spectrometer()
#030715 GIL add makeVariance
#030626 GIL use findScanInfo.c
#030625 GIL use smoothVector.c
#030129 GIL use splitMcVersion.o
#021212 GIL make compatible with linux
#021108 GIL rename plot.c plotHagen.c
#021003 GIL try to make compatible with gmake ($$() -> $())
#020826 GIL add updateIntensity.o
#020411 GIL add initVan.o (.f)
#020328 GIL add readLo
#020314 GIL add fitLags
#020218 GIL unify holography and dcr support
#020215 GIL add dcr support
#020214 GIL add modelAzElOffset()
#020207 GIL add loadHolography()
#020130 GIL add medianSpectrometer()
#020118 GIL add makeHtml()
#020117 GIL add median4()
#011110 GIL add plotGnu()
#011031 GIL add adjust3Level()
#011024 GIL add vEarth, vBary
#011023 GIL add naifVelocities
#011018 GIL add angularDistance
#011018 GIL add velocity support
#011008 GIL use findGbtFiles, readIf.o
#010913 GIL move main.o to spec.o
#010831 GIL add plotStack.o, offStack.o
#010704 GIL add aveSpectrometer.o
#010704 GIL make complete file for spectrometer plotting
#010214 GIL add readSpectrometer.o, readSP.o
#010214 GIL add chooseBinary to FITS list
#010130 GIL add chooseFits
#010103 GIL add lagsToFits
#001114 GIL add fits file writing.
#001100 GIL initial version based on Jeff Hagens code


.KEEP_STATE:

CFLAGS= -O -Wall -g -I/opt/local/X11R6/include -I./xlib -I/home/gbt1/fitsio
#CFAST= -O3 -Wall -g -I/opt/local/X11R6/include -I./xlib -I/home/gbt1/fitsio
CFAST= -O -Wall -g -I/opt/local/X11R6/include -I./xlib -I/home/gbt1/fitsio
TARGET_ARCH=
CC=gcc
LINK.c= $(CC) $(CFLAGS) $(CPPFLAGS) $(LDFLAGS) -static
#COMPILE.c= $(CC) $(CFLAGS) $(CPPFLAGS) -c
COMPILE.c= $(CC) $(CFAST) $(CPPFLAGS) -c
#SPICELIB = /home/ovlbi/ovlbi/naif/toolkit/lib/spicelib.a
SPICELIB = /users/glangsto/naif/toolkit/lib/spicelib.a
#FITSLIB = /home/gbt1/fitsio/i386-linux/libcfitsio.a 
FITSLIB = /home/gbt1/cfitsio-2.440b/libcfitsio.a 

COMPILE.f= g77 -O -Wall -c

SPICELIB_Linux = /home/ovlbi/naif-linux/cspice/lib/cspice.a
SPICELIB_SunOS = /home/ovlbi/naif/toolkit/lib/spicelib.a
#FITSIO_Linux = /home/gbt1/fitsio/i386-linux/libcfitsio.a
FITSIO_Linux = /home/gbt1/cfitsio/libcfitsio.so
FITSIO_SunOS = /home/gbt1/fitsio/libcfitsio.a
XLIB_Linux = -L/usr/X11R6/lib -L/lib -lnsl -lm -lg2c -lXt
XLIB_SunOS = -L/usr/X11/lib -lnsl -lm -lg2c -lXt -lsocket -lX11

#try to link in the correct libraries with the operating system
OSTYPE=$(shell /bin/uname)
#OSTYPE should be either SunOS or Linux
ifeq ($(OSTYPE),SunOS)
  FITSIO = $(FITSIO_SunOS)
  SPICELIB = $(SPICELIB_SunOS)
  XLIB = $(XLIB_SunOS)
else
  FITSIO = $(FITSIO_Linux)
  SPICELIB = $(SPICELIB_Linux)
  XLIB = $(XLIB_Linux)
endif

# function to find source code and place it in the current directory
.DEFAULT: 
	retrieve $(@:.o=.c)
	$(COMPILE.c) $(@:.o=.c)

.c.o :
	@ $(RM) $@
	retrieve $<
	$(COMPILE.c) $<

.f.o :
	@ $(RM) $@
	$(COMPILE.c) -i4 -ansi -w -e -misalign $<

all: selectSpecIdl.so

#
FV = button.o block.o check.o color.o fonts.o frame.o gauge.o toggle.o \
libHagen.o list.o menu.o optionsHagen.o scroll.o speed.o text.o plotspec.o \
therm.o trig.o xargs.o \
plotStack.o offStack.o writePS.o lagsToFits.o \
showGo.o plotGnu.o plotLabels.o showStack.o spectraStack.o \
makeHtml.o printSpec.o plotIntensity.o updateIntensity.o 

#MATH functions
MATHFUNC = vanvleck.o fourier.o median4.o \
adjust3Level.o linearFit.o smoothVector.o findScanInfo.o \
medianFilter.o medianVectors.o medianVector.o median5.o median3.o

#GUIFITS are functions that read fits files, and perform graphics ops
GUIFITS = chooseFits.o loadSpectrometer.o chooseBinary.o loadSP.o \
	aveSP.o findGaussians.o fitCal.o velocityWeight.o

#FITS FILES are GBT functions that do 
FITS = readSpectrometer.o readSPData.o calSpectrometer.o ftData.o \
	modelRefraction.o aveSpectrometer.o calcAveRmsRange.o \
	findGbtFiles.o readIf.o readTCal.o checkSpecFile.o \
	readHolography.o readGo.o readDcr.o \
	readAntenna.o modelAzElOffset.o readScanInfo.o \
	readLo.o splitMcVersion.o findTableExtension.o FITSTableR.o \
	extractName.o fileSize.o median4Spectrometer.o nextState.o \
	setSpecIntensity.o findScanFits.o loadAntenna.o

HOLOGRAPHY = plotHolography.o fitHolography.o loadHolography.o 
VARIANCE = makeVariance.o aVariance.o 

DCR = loadDcr.o printIntensity.o 

FITGAUSS = mrqmin.o mrqcof.o fgauss.o gaussj.o covsrt.o nrutil.o \
	convlv.o twofft.o ludcmp.o lubksb.o savgol.o
#	fitLagsNonLin.o 
#	fitGaussiansNonLin.o fitGaussians.o fitGaussNonLin.o \

STDDEFS.H : 
	  retrieve STDDEFS.H

MATHCNST.H : 
	  retrieve MATHCNST.H

VLBAH = STDDEFS.H MATHCNST.H

vlb.h : STDDEFS.H
	ln -s STDDEFS.H vlb.h

#SOCK = sock/socklib.o sock/loglib.o sock/socknoxvlib.o sock/mbdef.o
SOCK = socklib.o loglib.o socknoxvlib.o mbdef.o

$(SOCK): mbdef.h 

VLBASTRINGS = str2mjd.o str2rad.o  stripWhite.o time2str.o mjd2str.o \
	srclist.o cvrtuc.o dateObs2DMjd.o today2mjd.o inIntList.o \
	fixDoubleSlash.o addSlash.o

VELOCITY = rectpol.o dprint.o d_mod.o position.o aberrat.o \
	velocities.o nutrotn.o prcesj2.o dircos.o dotpr3.o rotate3.o \
	transformObliquity.o gastm.o nutate.o obliq.o angularDistance.o \
	now2J2000.o matinvert.o helioToLsr.o radec2azel.o \
	gLatLon2RaDec.o angleRange.o

FELOCITY = vsun.o sunposition.o sunperigee.o naifVelocities.o \
	 eccentricity.o sumterms.o powers.o sunmeananom.o sunmeanlong.o \
	 vEarth.o getgbt.o getbry.o spksum.o dispsp.o getrot.o getpre.o \
	nutrot.o
$(FELOCITY) : $(@:.o=.f)

#### gcc -ansi -w -e -misalign -fno-common -c initVan.c 

initVan.o: initVan.f

#### gcc -ansi -w -e -misalign -fno-common -c initVan.c 

FRED = initVan.o splint.o vanVleck3Fred.o

SPEC = spec.o plotHagen.o tests.o config.o showdata.o medianSpectrometer.o
###$(SPEC)	: plot.h MATHCNST.H $(@:.o=.c)

### not needed for linux: 

spec: $(SPEC) $(FITS) $(FV) $(VLBASTRINGS) $(SOCK) $(VARIANCE) \
	$(FITGAUSS) $(VELOCITY) $(FELOCITY) $(HOLOGRAPHY) $(DCR) $(FRED) \
	$(GUIFITS) $(MATHFUNC)
	gcc -g -o spec $(SPEC) $(SOCK) $(VARIANCE) \
$(FV) $(FITS) $(VLBASTRINGS) $(FITGAUSS) $(VELOCITY) $(FELOCITY) \
$(HOLOGRAPHY) $(DCR) $(FRED) $(FITSIO) $(SPICELIB) $(GUIFITS) $(MATHFUNC) \
-L/opt/local/lib/X11 -L/opt/local/lib $(XLIB) -ansi -w

testVanVleck: testVanVleck.o vanvleck.o $(FRED)
	gcc -g -o testVanVleck testVanVleck.o vanvleck.o $(FRED) \
-L/opt/local/lib/X11 -L/opt/local/lib $(XLIB) -ansi -w

################################### specDataIDL ##########################

FITSHOME = /users/glangsto/fitsio
FITSIOLIST  = $(FITSHOME)/buffers.o \
$(FITSHOME)/cfileio.o \
$(FITSHOME)/checksum.o \
$(FITSHOME)/compress.o \
$(FITSHOME)/editcol.o \
$(FITSHOME)/edithdu.o \
$(FITSHOME)/f77_iter.o \
$(FITSHOME)/f77_wrap.o \
$(FITSHOME)/fitscore.o \
$(FITSHOME)/getcolb.o \
$(FITSHOME)/getcold.o \
$(FITSHOME)/getcole.o \
$(FITSHOME)/getcoli.o \
$(FITSHOME)/getcolj.o \
$(FITSHOME)/getcolk.o \
$(FITSHOME)/getcoll.o \
$(FITSHOME)/getcol.o \
$(FITSHOME)/getcols.o \
$(FITSHOME)/getcolui.o \
$(FITSHOME)/getcoluj.o \
$(FITSHOME)/getkey.o \
$(FITSHOME)/modkey.o \
$(FITSHOME)/putcolb.o \
$(FITSHOME)/putcold.o \
$(FITSHOME)/putcole.o \
$(FITSHOME)/putcoli.o \
$(FITSHOME)/putcolj.o \
$(FITSHOME)/putcolk.o \
$(FITSHOME)/putcoll.o \
$(FITSHOME)/putcol.o \
$(FITSHOME)/putcols.o \
$(FITSHOME)/putcolui.o \
$(FITSHOME)/putcoluj.o \
$(FITSHOME)/putcolu.o \
$(FITSHOME)/putkey.o \
$(FITSHOME)/scalnull.o \
$(FITSHOME)/swapproc.o \
$(FITSHOME)/wcsutil.o 

FITSIO = libcfitsio.a

GBTH   = gbtDcr.h gbtIf.h gbtSP.h gbtGo.h gbtLo.h gbtTCal.h gbtHolography.h \
gbtScanInfo.h gbtAntenna.h gbtIdl.h gbtSpectrometer.h

DATAIDL = writeSdfits.o medianPeak.o calcRMS.o fftFilter.o printerror.o \
idlStack.o

SPECDATAIDL = loadSpecIdl.o fillSpecIdl.o selectSpecIdl.o median4Vectors.o \
$(DATAIDL)

$(SPECDTATAIDL): $(GBTH) $(VLBAH) nr.h $(@:.o=.c)

####	gcc -g -shared -lm -all $(SPECDATAIDL) $(VLBASTRINGS) $(FITSIOLIST)
#####   -L/usr/lib/libc.a -L/usr/lib/libf2c.a -o selectSpecIdl.so
####	gcc -g -shared -all $(SPECDATAIDL) $(VLBASTRINGS) $(FITSIOLIST) \

selectSpecIdl.so: $(SPECDATAIDL) $(VLBASTRINGS) $(FITS) $(MATHFUNC) $(FRED) \
$(FITGAUSS) $(VELOCITY) $(@:.o=.c)
	gcc -g -shared -all $(SPECDATAIDL) $(VLBASTRINGS) $(FITSIOLIST) \
$(FITS) $(MATHFUNC) $(FRED) $(FITGAUSS) $(VELOCITY) \
-lm -o selectSpecIdl.so
	mv selectSpecIdl.so /home/astro-util/idlTest/bin

FITTAUNONLIN = mainFitTau.o fitTauNonLin.o calcRMS.o calcAveRmsRange.o \
	     fourier.o gasdev.o medianVector.o medianFilter.o median3.o \
	     median5.o quickPlot.o

fitTauNonLin: $(FITTAUNONLIN) $(VLBASTRINGS) $(FITGAUSS) $(@:.o=.c)
	gcc -g -lm $(FITTAUNONLIN) $(VLBASTRINGS) $(FITGAUSS) -o fitTauNonLin

testSpecIdl: testSpecIdl.o plotIdl.o $(SPECDATAIDL) $(VLBASTRINGS) $(FITS) $(MATHFUNC) $(FRED) \
$(FITGAUSS) $(VELOCITY) $(@:.o=.c)
	gcc -g testSpecIdl.o plotIdl.o $(SPECDATAIDL) $(VLBASTRINGS) $(FITSIOLIST) \
$(FITS) $(MATHFUNC) $(FRED) $(FITGAUSS) $(VELOCITY) \
-lm -o testSpecIdl

################################# writeSdfits ###############################
IDLTOSDFITS = mainIdlToAipsSdfits.o plotIdl.o $(DATAIDL) \
	    readIdlFits.o FITSTableR.o findTableExtension.o readScanInfo.o \
	    calcAveRmsRange.o fileSize.o findFitsTable.o quickPlot.o \
	    findGbtFiles.o

IDLHEADERS = STDDEFS.H MATHCNST.H KEYWORD.H vlb.h nrutil.h ABPTRB.H $(GBTH)

idlToSdfits: $(IDLHEADERS) $(IDLTOSDFITS) $(VLBASTRINGS) $(MATHFUNC) \
$(FITGAUSS) $(VELOCITY) 
	gcc -g -lm $(IDLTOSDFITS) $(VLBASTRINGS) $(FITSIOLIST) \
$(MATHFUNC) $(FITGAUSS) $(VELOCITY) \
-o idlToSdfits

################################# writeSdfits ###############################
WRITESDFITS = mainWriteSdfits.o plotIdl.o $(SPECDATAIDL) fitTauNonLin.o

writeSdfits: $(WRITESDFITS) $(VLBASTRINGS) $(FITS) $(MATHFUNC) $(FRED) \
$(FITGAUSS) $(VELOCITY)
	gcc -g -lm $(WRITESDFITS) $(VLBASTRINGS) $(FITSIOLIST) \
$(FITS) $(MATHFUNC) $(FRED) $(FITGAUSS) $(VELOCITY) \
-o writeSdfits

################################## selectSdfits #############################
selectSdfits: selectSdfits.o $(SPECDATAIDL) $(VLBASTRINGS) \
	$(FITS) $(MATHFUNC) $(FRED) $(FITGAUSS) $(VELOCITY)
	gcc -g -lm selectSdfits.o $(SPECDATAIDL) $(VLBASTRINGS) $(FITSIO) \
$(FITS) $(MATHFUNC) $(FRED) $(FITGAUSS) $(VELOCITY) \
-o selectSdfits

################################## exportGbt #############################

exportGbt.o: STDDEFS.H MATHCNST.H vlb.h $(@:.o=.c)

exportGbt: exportGbt.o $(VLBASTRINGS) 
	retrieve exportGbt.c
	gcc -c exportGbt.c -o exportGbt.o
	gcc -g -lm exportGbt.o $(VLBASTRINGS) -o exportGbt

clean:
	rm -f *.o
