# File MakeSpecIdl, version 1.12, released  05/12/07 at 11:56:34 
#   retrieved by SCCS 06/01/18 at 19:39:14     
# Makefile for GBT spectrometer unix components
#
#HISTORY
#140715 RWG Stripped down to just idlToSdfits depencies
#111026 GIL use standard cfitsio setup
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


SHELL =		/bin/sh
RANLIB =	ranlib
CC =		cc
CFLAGS =	-g -O2 -Dg77Fortran -fPIC
FC =		gfortran
LDFLAGS =	$(CFLAGS)
DEFS =		-DPACKAGE_NAME=\"\" -DPACKAGE_TARNAME=\"\" -DPACKAGE_VERSION=\"\" -DPACKAGE_STRING=\"\" -DPACKAGE_BUGREPORT=\"\" -DPACKAGE_URL=\"\" -DSTDC_HEADERS=1 -DHAVE_SYS_TYPES_H=1 -DHAVE_SYS_STAT_H=1 -DHAVE_STDLIB_H=1 -DHAVE_STRING_H=1 -DHAVE_MEMORY_H=1 -DHAVE_STRINGS_H=1 -DHAVE_INTTYPES_H=1 -DHAVE_STDINT_H=1 -DHAVE_UNISTD_H=1 -DHAVE_STDLIB_H=1 -DHAVE_STRING_H=1 -DHAVE_MATH_H=1 -DHAVE_LIMITS_H=1 -D_LARGEFILE_SOURCE=1 -D_FILE_OFFSET_BITS=64 -DHAVE_FTRUNCATE=1 -DHAVE_LONGLONG=1 -DHAVE_SHMEM_SERVICES=1 -DHAVE_NET_SERVICES=1
LIBS =		
FLEX =		flex
BISON =		bison

SHLIB_LD =	cc -shared
SHLIB_SUFFIX =	.so

#.c.o:
#		$(CC) -c $(CFLAGS) $(DEFS) $<


SOURCES = ${CORE_SOURCES} ${FITSIO_SRC}

OBJECTS = 	${SOURCES:.c=.o}

CORE_OBJECTS = 	${CORE_SOURCES:.c=.o}


FITSIO_SRC =	f77_wrap1.c f77_wrap2.c f77_wrap3.c f77_wrap4.c

CFLAGS= -O -Wall -g -I/opt/local/X11R6/include -I./xlib -I$/home/gbtpipeline/include
CFAST= -O -Wall -g -I/opt/local/X11R6/include -I./xlib -I/home/gbtpipeline/include
TARGET_ARCH=
CC=gcc
LINK.c= $(CC) $(CFLAGS) $(CPPFLAGS) $(LDFLAGS) -static
#COMPILE.c= $(CC) $(CFLAGS) $(CPPFLAGS) -c
COMPILE.c= $(CC) $(CFAST) $(CPPFLAGS) -c

COMPILE.f= g77 -O -Wall -c

# function to find source code and place it in the current directory
.DEFAULT: 
	$(COMPILE.c) $(@:.o=.c)

.c.o :
	@ $(RM) $@
	$(COMPILE.c) $<

.f.o :
	@ $(RM) $@
	$(COMPILE.c) -i4 -ansi -w -e -misalign $<

all: idlToSdfits

#MATH functions
MATHFUNC = vanvleck.o fourier.o median4.o \
adjust3Level.o vanvleck.o linearFit.o smoothVector.o findScanInfo.o \
medianFilter.o medianVectors.o medianVector.o median5.o median3.o

FITGAUSS = mrqmin.o mrqcof.o fgauss.o gaussj.o covsrt.o nrutil.o \
	convlv.o twofft.o ludcmp.o lubksb.o savgol.o

vlb.h : STDDEFS.H
	ln -s STDDEFS.H vlb.h

VLBASTRINGS = str2mjd.o str2rad.o  stripWhite.o time2str.o mjd2str.o \
	srclist.o cvrtuc.o dateObs2DMjd.o today2mjd.o inIntList.o \
	fixDoubleSlash.o addSlash.o

VELOCITY = rectpol.o dprint.o d_mod.o position.o aberrat.o \
	velocities.o nutrotn.o prcesj2.o dircos.o dotpr3.o rotate3.o \
	transformObliquity.o gastm.o nutate.o obliq.o angularDistance.o \
	now2J2000.o matinvert.o helioToLsr.o radec2azel.o \
	gLatLon2RaDec.o angleRange.o

GBTH   = gbtDcr.h gbtIf.h gbtSP.h gbtGo.h gbtLo.h gbtTCal.h gbtHolography.h \
gbtScanInfo.h gbtAntenna.h gbtIdl.h gbtSpectrometer.h

DATAIDL = writeSdfits.o medianPeak.o calcRMS.o fftFilter.o printerror.o \
idlStack.o

################################# idlToSdfits ###############################
IDLTOSDFITS = mainIdlToAipsSdfits.o plotIdl.o $(DATAIDL) \
	    readIdlFits.o FITSTableR.o findTableExtension.o readScanInfo.o \
	    calcAveRmsRange.o fileSize.o findFitsTable.o quickPlot.o \
	    findGbtFiles.o

IDLHEADERS = STDDEFS.H MATHCNST.H KEYWORD.H vlb.h nrutil.h ABPTRB.H $(GBTH)

idlToSdfits: $(IDLHEADERS) $(IDLTOSDFITS) $(VLBASTRINGS) $(MATHFUNC) \
$(FITGAUSS) $(VELOCITY) 
	gcc -g $(IDLTOSDFITS) $(VLBASTRINGS) -L$(DESTDIR) $(MATHFUNC) $(FITGAUSS) $(VELOCITY) -L/home/gbtpipeline/lib/ -lcfitsio -lm -o idlToSdfits


clean:
	rm -f *.o vlb.h
