/* File covsrt.c, version 1.1, released  95/01/31 at 13:44:29 
   retrieved by SCCS 14/04/23 at 15:51:11     

%% numerical recipies functions

:: Offline Numerical Recipes fitting
 
HISTORY:
  950131 GIL - initial version

DESCRIPTION:
Numerical Recipes function
*/
#define SWAP(a,b) {swap=(a);(a)=(b);(b)=swap;}

void covsrt(float **covar, int ma, int ia[], int mfit)
{
	int i,j,k;
	float swap;

	for (i=mfit+1;i<=ma;i++)
		for (j=1;j<=i;j++) covar[i][j]=covar[j][i]=0.0;
	k=mfit;
	for (j=ma;j>=1;j--) {
		if (ia[j]) {
			for (i=1;i<=ma;i++) SWAP(covar[i][k],covar[i][j])
			for (i=1;i<=ma;i++) SWAP(covar[k][i],covar[j][i])
			k--;
		}
	}
}
#undef SWAP
/* (C) Copr. 1986-92 Numerical Recipes Software 'Yas1. */
