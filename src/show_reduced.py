import pyfits
import pylab
from matplotlib.font_manager import FontProperties
import sys
import numpy as np

INFILE = sys.argv[1]

fd = pyfits.open(INFILE)

nspec = len(fd[1].data)

targets = sorted(fd[1].data['OBJECT'])

for idx,target in enumerate(targets):
    pylab.subplot(nspec,1,idx+1)

    print 'target',target
    mask = fd[1].data['OBJECT']==target
    spec = fd[1].data[mask]['DATA'][0]
    pylab.plot(spec)
    freereg=spec[:.35*len(spec)]
    freereg = np.ma.masked_array(freereg,np.isnan(freereg))
    rms = np.sqrt((freereg**2).mean())
    pylab.ylabel('Jy')
    pylab.xlabel('channel')
    pylab.title(target+' '+str(rms))
    
fd.close()

title = pylab.gcf().text(0.5,0.95, INFILE,
    horizontalalignment='center',
    fontproperties=FontProperties(size=16))

pylab.show()

#pylab.savefig(INFILE+'.svg')
