import pipeutils

result = pipeutils.hz2wavelength(23e9)
expectedresult = 0.0130344546957
if not expectedresult == result:
    print "pipeutils.hz2wavelength failed"
    print result-expectedresult
