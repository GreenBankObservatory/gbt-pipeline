/* File convlv.c, version 1.2, released  01/10/03 at 08:50:24 
   retrieved by SCCS 14/04/23 at 15:51:13     

%% utility function to perform convolution s
:: test program

HISTORY
010907 GIL inital Version

DESCRIPTON
convlv() as in numerical recipes.

OMISSIONS
Slightly changed to use different type of argument to realft()
*/

#define NRANSI
#include "nrutil.h"

void convlv(float data[], long n, float respns[], long m,
	long isign, float ans[])
{
	void realft(float data[],  long n, long isign);
	void twofft(float data1[], float data2[], float fft1[], float fft2[],
		long n);
	long i = 0, no2 = n/2, nFft = 2*n;
	double dum = 0, mag2 = 0;
	float *fft;

	fft=vector(1, nFft);

	for (i=1;i<=(m-1)/2;i++)
	  respns[n+1-i] = respns[m+1-i];
	for (i=(m+3)/2;i<=n-(m-1)/2;i++)
	  respns[i]=0.0;

	twofft(data,respns,fft,ans,n);

	for (i=2; i<=n+2; i+=2) {
	  if (isign == 1) {
	    ans[i-1]=(fft[i-1]*(dum=ans[i-1])-fft[i]*ans[i])/no2;
	    ans[i]=(fft[i]*dum+fft[i-1]*ans[i])/no2;
	  } 
	  else if (isign == -1) {
	    if ((mag2=SQR(ans[i-1])+SQR(ans[i])) == 0.0)
	      nrerror("Deconvolving at response zero in convlv");
            dum=ans[i-1];
	    mag2 *= no2;
	    ans[i-1]=((fft[i-1]*dum)+(fft[i]  *ans[i]))/mag2;
	    ans[i]  =((fft[i]  *dum)-(fft[i-1]*ans[i]))/mag2;
	  } 
          else 
	    nrerror("No meaning for isign in convlv");
	}
	ans[2]=ans[n+1];
	realft( ans, n, -1);
	free_vector(fft,1,nFft);
}
#undef NRANSI
/* (C) Copr. 1986-92 Numerical Recipes Software 'Yas1. */
