/* File lubksb.c, version 1.2, released  01/10/03 at 08:52:52 
   retrieved by SCCS 14/04/23 at 15:51:14     

%% utility function to perform linear least squares
:: test program

HISTORY
010927 GIL long arguments
010907 GIL inital Version

DESCRIPTON
lubksb() as in numerical recipes.

OMISSIONS
Slightly changed to use double precision values when possible
*/
void lubksb(float **a, long n, long *indx, float b[])
{
	long i = 0, ii=0, ip = 0, j = 0;
	double sum = 0;

	for (i=1;i<=n;i++) {
		ip=indx[i];
		sum=b[ip];
		b[ip]=b[i];
		if (ii)
		  for (j=ii;j<=i-1;j++) 
		    sum -= a[i][j]*b[j];
		else if (sum) 
		  ii=i;
		b[i]=sum;
	}
	for (i=n;i>=1;i--) {
	  sum=b[i];
	  for (j=i+1;j<=n;j++) 
	    sum -= a[i][j]*b[j];
	  b[i]=sum/a[i][i];
	}
}
/* (C) Copr. 1986-92 Numerical Recipes Software 'Yas1. */
