/* File gaussj.c, version 1.4, released  02/02/13 at 08:56:10 
   retrieved by SCCS 14/04/23 at 15:51:11     

%% numerical recipies functions

:: Offline Numerical Recipes fitting
 
HISTORY:
  020211 GIL - print a maximum number of error messages
  950808 GIL - ignore certain problems
  950131 GIL - initial version

DESCRIPTION:
Numerical Recipes function
*/
#include <math.h>
#include <stdio.h>
#define NRANSI
#include "nrutil.h"
#define SWAP(a,b) {temp=(a);(a)=(b);(b)=temp;}

#define SMALL 1.0E-10
#define MAXPRINTCOUNT 2

void gaussj(float **a, int n, float **b, int m)
{
  static long printCount = 0;
  int *indxc,*indxr,*ipiv;
  int i = 0, icol = 0, irow = 0, j = 0, k = 0, l = 0, ll = 0;
  double big = 0, dum = 0, pivinv = 0, temp = 0;

  indxc=ivector(1,n);
  indxr=ivector(1,n);
  ipiv=ivector(1,n);
  for (j=1;j<=n;j++) 
    ipiv[j]=0;

  for (i=1;i<=n;i++) {
    big=0.0;
    for (j=1;j<=n;j++)
      if (ipiv[j] != 1)
	for (k=1;k<=n;k++) {
	  if (ipiv[k] == 0) {
	    if (fabs(a[j][k]) >= big) {
	      big=fabs(a[j][k]);
	      irow=j;
	      icol=k;
	    }
	  } else if (ipiv[k] > 1) {
	    if (printCount < MAXPRINTCOUNT) {
	      fprintf( stderr, 
		       "gaussj: Singular Matrix-1\n");
	      printCount++;
	    }
	    break;
	  }
	}
    ++(ipiv[icol]);
    if (irow != icol) {
      for (l=1;l<=n;l++) 
	SWAP(a[irow][l],a[icol][l]);
      for (l=1;l<=m;l++) 
	SWAP(b[irow][l],b[icol][l]);
    }
    indxr[i]=irow;
    indxc[i]=icol;
    if (a[icol][icol] == 0.0) {
      if (printCount < MAXPRINTCOUNT) {
	fprintf( stderr, "gaussj: Singular Matrix-2\n");
	printCount++;
      }
      a[icol][icol] = SMALL;
    }
    pivinv=1.0/a[icol][icol];
    a[icol][icol]=1.0;
    for (l=1;l<=n;l++) 
      a[icol][l] *= pivinv;
    for (l=1;l<=m;l++) 
      b[icol][l] *= pivinv;
    for (ll=1;ll<=n;ll++)
      if (ll != icol) {
	dum=a[ll][icol];
	a[ll][icol]=0.0;
	for (l=1;l<=n;l++) a[ll][l] -= a[icol][l]*dum;
	for (l=1;l<=m;l++) b[ll][l] -= b[icol][l]*dum;
      }
  }
  for (l=n;l>=1;l--) {
    if (indxr[l] != indxc[l])
      for (k=1;k<=n;k++)
	SWAP(a[k][indxr[l]],a[k][indxc[l]]);
  }
  free_ivector(ipiv,1,n);
  free_ivector(indxr,1,n);
  free_ivector(indxc,1,n);
} /* end of gaussj() */
#undef SWAP
#undef NRANSI
