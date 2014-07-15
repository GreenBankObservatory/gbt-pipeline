/* File twofft.c, version 1.2, released  01/10/03 at 08:51:19 
   retrieved by SCCS 14/04/23 at 15:51:13     

%% utility function to perform fourier tranform of two arrays
:: test program

HISTORY
010907 GIL inital Version

DESCRIPTON
twofft() as in numerical recipes.

OMISSIONS
Slightly changed to use double precision values when possible
*/

void twofft(float data1[], float data2[], float fft1[], float fft2[], long n)
{
	void four1(float data[], long nn, long isign);
	long nn3 = 3+n+n, nn2=2+n+n, jj = 0, j = 0;
	double rep = 0, rem = 0, aip = 0, aim = 0;

	for (j=1,jj=2;j<=n;j++,jj+=2) {
	  fft1[jj-1] = data1[j];
	  fft1[jj]   = data2[j];
	}
	four1(fft1,n,1);
	fft2[1]=fft1[2];
        /* phase of zero frequency part is zero */
	fft1[2]=fft2[2]=0.0;
	for (j=3;j<=n+1;j+=2) {
		rep=0.5*(fft1[j]+fft1[nn2-j]);
		rem=0.5*(fft1[j]-fft1[nn2-j]);
		aip=0.5*(fft1[j+1]+fft1[nn3-j]);
		aim=0.5*(fft1[j+1]-fft1[nn3-j]);
		fft1[j]=rep;
		fft1[j+1]=aim;
		fft1[nn2-j]=rep;
		fft1[nn3-j] = -aim;
		fft2[j]=aip;
		fft2[j+1] = -rem;
		fft2[nn2-j]=aip;
		fft2[nn3-j]=rem;
	}
}
/* (C) Copr. 1986-92 Numerical Recipes Software 'Yas1. */
