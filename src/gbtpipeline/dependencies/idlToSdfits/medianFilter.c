/* File medianFilter.c, version 1.17, released  04/02/18 at 08:46:40 
   retrieved by SCCS 14/04/23 at 15:51:08     

%% function to return median of an array

:: GBES-C point antenna peakUp
 
History:
  010206 GIL - increase array max sizes
  010130 GIL - change select() to medianSelect() to avoid name conflicts
  960403 GIL - fix error in calling SWAP
  950719 GIL - median calculated is exactly median defintion.
  950629 GIL - remove positive bias in filter
  941220 GIL - medianFilter returns smoothed median, new functions minArray(),
               maxArray()
  941117 GIL - select() returns average of central 4 points 
  941116 GIL - medianFilter uses even number of points, excludes current.
  940902 GIL - use select for medianFilter, not shellSort()
  940812 GIL - moved shellSort into this function and removed *.H dependencies
  940408 GIL - fix calculations at ends
  940406 GIL - initial version taken from fitMax.c
               make the median calculation symetric, write median and value
 
DESCRIPTION:
Take the median value of a double precision array.
*/
#define MAXMEDIAN  3000 /* maximum median window */
#define HALFMEDIAN 1500 /* half maximum median window */

void shellSort(long n, double a[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* The standard shell sort of an array. Good sort for data already           */
/* nearly in order.  NOTE!!!! this routine sorts elements of a[1..n],        */
/* NOT a[0..n-1], The a[0] value is not used.                                */
/* See Knuth, D.E. 1973, Sorting and Searching. or Numerical Recipes in C    */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ long i,j,inc = 1;
  double v;

  do {                                 /* initialize index */
    inc *= 3;
    inc++;
  } while (inc <= n);
	
  do {
    inc /= 3;
    for (i=inc+1;i<=n;i++) {
      v=a[i];
      j=i;
      while (a[j-inc] > v) {
	a[j]=a[j-inc];
	j -= inc;
	if (j <= inc) break;
      }
      a[j]=v;
    }
  } while (inc > 1);
} /* end of shellSort() */

#define SWAP(a,b) {temp=(a);(a)=(b);(b)=temp;}

double minArray(unsigned long n, double arr[])
{ double minV = arr[0];
  int i;

  for (i=1; i < n; i++)
    if (arr[i] < minV)
      minV = arr[i];
  return(minV);
}

double maxArray(unsigned long n, double arr[])
{ double maxV = arr[0];
  int i;

  for (i=1; i < n; i++)
    if (arr[i] > maxV)
      maxV = arr[i];
  return(maxV);
}

double medianSelect(unsigned long k, unsigned long n, double arr[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* select the Kth largest value in an array arr[1..n] of length n            */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ unsigned long i, ir=n, j, l=1, mid;
  double a,temp;                            /* temp is only used by SWAP */

  for(;;) {                                 /* forever */
    if (ir <= l+1) {                        /* if found last two values */
      if (ir == l+1 && arr[ir] < arr[l])    /* sort last two values */
        SWAP(arr[l],arr[ir])
      return (arr[k]);                      /* return Kth */
    } 
    else {                                  /* else not down to last 2 */
      mid=(l+ir) >> 1;                      /* average by trick, shift a bit */

      SWAP(arr[mid],arr[l+1])
      if (arr[l+1] > arr[ir]) 
	SWAP(arr[l+1],arr[ir])
      if (arr[l] > arr[ir])
	SWAP(arr[l],arr[ir])
      if (arr[l+1] > arr[l])
	SWAP(arr[l+1],arr[l])
      i=l+1;
      j=ir;
      a=arr[l];
      for(;;) {
	do i++; while (arr[i] < a);
	do j--; while (arr[j] > a);
	if (j < i) break;              /* if inorder, stop */
	SWAP(arr[i],arr[j])            /* else swap */
	} /* end of forever */
      arr[l]=arr[j];
      arr[j]=a;
      if (j >= k) ir=j-1;
      if (j <= k) l=i;
    } /* end else not last two values */
  } /* end of forever */
} /*end of medianSelect() */

void medianFilter ( int count, int medWid2, double inarr[], double outarr[])
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
/* median produces a median filter of inarr and places the result in outarr[]*/
/* INPUTS  count   int    Number of values in input array                    */
/*         medWid2 int    Half Width of median filter array                  */
/*         inarr[] double Input array not modified by filtering              */
/*         MAXMEDIAN      define  in and output array size                   */
/* OUTPUT  outarr[] double  Output median filtered array                     */
/* Later version will utilize previous sorting of data                       */
/*  *    *    *    *    *    *    *    *    *    *    *    *    *    *    *  */
{ int i, j, medBeg, medEnd, k1 = count - 1, k2 = count - 2;
  long  n, no2;
  double medTemp[MAXMEDIAN];

  if (medWid2 < 1) 
    medWid2 = 1;                        /* must have some data in range */
  else if (medWid2 > count/2) 
    medWid2 = count/2;                  /* but not too much data */
  else if (medWid2 > HALFMEDIAN) 
    medWid2 = HALFMEDIAN - 1;

  outarr[0]  = 0.3333333*(inarr[0] + inarr[0] + inarr[1]); /* ends ave of 3 */
  outarr[1]  = 0.3333333*(inarr[0] + inarr[1] + inarr[2]); /* ends ave of 3 */
  outarr[k2] = 0.3333333*(inarr[k1] + inarr[k2] + inarr[k2-1]); 
  outarr[k1] = 0.3333333*(inarr[k1] + inarr[k1] + inarr[k2]); 
           
  for (i=2; i < k2; i++) {              /* for all other points, find median */
    medBeg = i - medWid2;               /* set range for median */
    medEnd = i + medWid2;               /* collect an even number of points */
    n = 0;                              /* sorted array entries range 1 to k */
    if (medBeg < 0) {                   /* keep median symetric about point */
      medEnd += medBeg;
      medBeg = 0;
    }
    else if (medEnd > count) {          /* else check other end */
      medBeg -= (count - medEnd);
      medEnd = count;
    } /* end if bounds beyond data */
    for (j=medBeg; j < i; j++) {        /* copy data to temp for median */
      n++;                              /* else insert next value */
      medTemp[n] = inarr[j];            /* median temp range 1..k not 0..k-1 */
      }
    n++;                                /* mid point */
    medTemp[n] = inarr[i];
    for (j=i+1; j < medEnd; j++) {      /* copy data to temp for median */
      n++;                              /* else insert next value */
      medTemp[n] = inarr[j];            /* median temp range 1..k not 0..k-1 */
    } /* end of median temp copy */
    no2 = n/2;
    /* select median of temp array */
    outarr[i] = medianSelect( no2, n, medTemp);   
    if (2*no2 == n) {                       /* if n even */
      outarr[i] += medianSelect( no2+1, n, medTemp);
      outarr[i] *= 0.5;
    }
  } /* end of calculation of median */

} /* end of medianFilter() */




