/* File fourier.c, version 1.3, released  05/04/07 at 09:22:04 
   retrieved by SCCS 14/04/23 at 15:51:05     

%% numerical functions
:: spectrometer 

HISTORY
010130 GIL use longs not ints
001129 GIL use ansi calling argument convention

DESCRIPTION:
Fourier transform data
*/
#include "stdio.h"
#include "math.h"

double cos(double);
double sin(double);

/* #define	M_PI		((double)3.14159265358979323846) */
#define  SWAP(a,b)  tempr=(a);(a)=(b);(b)=tempr

/*
  FFT - 
   Replace data by its discrete Fourier transform, if isign is input
   as 1; or replaces data by nn times its inverse discrete Fourier
   transform, if isign is input as -1. data is a complex array of
   length nn, input as a real array data[1..2*nn]. nn MUST be an
   integer power of 2 (this is not checked for!).
*/
void four1(float *data, long nn, long isign)
{
     long n = 2 * nn, mmax = 0, m = 0, j = 1, istep = 0, i = 0;
     double wtemp,wr,wpr,wpi,wi,theta;     /* Double precision for the   */
                                           /*  trigonometric recurrences */
     double tempr,tempi;

     for (i=1;i<n;i+=2)             /* This is the bit-reversal section */
     {                              /*  of the routine                  */
          if (j > i) 
          {
               SWAP(data[j],data[i]);              /* Exchange the two  */
               SWAP(data[j+1],data[i+1]);          /* complex numbers   */
          }
          m = n / 2;
          while (m>=2 && j>m) 
          {
               j -= m;
               m = m / 2;
          }
          j += m;
     }
     mmax=2;                     /* Here begins the Danielson-Lanczos */
                                 /* section of the routine            */
     while (n > mmax)            /* Outer loop executed log2 nn times */
     {
          istep=2*mmax;
          theta=(2*M_PI)/(isign*mmax); 
                              /* Initialize for the trigonometric recurrence */
          wtemp=sin(0.5*theta);
          wpr = -2.0*wtemp*wtemp;
          wpi=sin(theta);
          wr=1.0;
          wi=0.0;
          for (m=1;m<mmax;m+=2)  /*     Here are two nested loops  */
          {
               for (i=m;i<=n;i+=istep) 
               {
                   j=i+mmax;     /*  This is the Danielson-Lanczos formula */
                   tempr=wr*data[j]-wi*data[j+1];
                   tempi=wr*data[j+1]+wi*data[j];
                   data[j]=data[i]-tempr;
                   data[j+1]=data[i+1]-tempi;
                   data[i] += tempr;
                   data[i+1] += tempi;
               }                              /* Trigonometric recurrence */
               wr=(wtemp=wr)*wpr-wi*wpi+wr;
               wi=wi*wpr+wtemp*wpi+wi;
          }
          mmax=istep;
     }
} /* end of four1() */

/*
  REAL FFT routine 
  Calculates the Fourier Transform of a set of 2n real-valued data points.  
  Replaces this data (which is stored in array data[1..2n] by the positive 
  frequency half of its complex Fourier Transform.  The real-valued first 
  and last components of the complex transform are returned as elements 
  data[1] and data[2] respectively.  n must be a power of 2.  
  This routine also calculates the inverse transform of a 
  complex data array if it is the transform of real data.  (Result
  in this case must be multiplied by 1/n.)
*/
void realft2(float *data, long n, long isign)
{
    long i,i1,i2,i3,i4,n2p3;
    double c1=0.5;
    double c2,h1r,h1i,h2r,h2i;
    double wr,wi,wpr,wpi,wtemp,theta;   /*  Double for the trigonometric  */
                                        /*     recurrences.               */

    theta=M_PI/(double) n;  /* Initializes the recurrence */
    if (isign == 1) 
    {
         c2 = -0.5;
         four1(data,n,1);     /*  The forward transform is here    */
    } else {
         c2=0.5;             /*  Otherwise set up for an inverse transform */
         theta = -theta;
    }
    wtemp=sin(0.5*theta);
    wpr = -2.0*wtemp*wtemp;
    wpi=sin(theta);
    wr=1.0+wpr;
    wi=wpi;
    n2p3=2*n+3;
    for (i=2;i<=n/2;i++) 
    {                                   /* Case i=1 done separately below */
         i4=1+(i3=n2p3-(i2=1+(i1=i+i-1)));
         h1r=c1*(data[i1]+data[i3]);    /* The two separate transforms are */
                                        /*  separated out of data.         */
         h1i=c1*(data[i2]-data[i4]);
         h2r = -c2*(data[i2]+data[i4]);
         h2i=c2*(data[i1]-data[i3]);
         data[i1]=h1r+wr*h2r-wi*h2i;  /* recombine to form the true transform*/
                                      /* of the original real data */
         data[i2]=h1i+wr*h2i+wi*h2r;
         data[i3]=h1r-wr*h2r+wi*h2i;
         data[i4] = -h1i+wr*h2i+wi*h2r;
         wr=(wtemp=wr)*wpr-wi*wpi+wr;      /*  The recurrence */
         wi=wi*wpr+wtemp*wpi+wi;
    }
    if (isign == 1) 
    {
       data[1] = (h1r=data[1])+data[2];   /* Squeeze first and last together */
                                          /* to get them all within original */
                                          /* array */
         data[2] = h1r-data[2];
    } else 
    {
        data[1]=c1*((h1r=data[1])+data[2]);
        data[2]=c1*(h1r-data[2]);
        four1(data,n,-1);            /* This is the inverse transform for the */
                                     /*  case isign=-1 */
    }
} /* end of realft2() */

/* realft[] is a expects a 1 based array ie data[i] ranges from 1 to n, */
/* not the usual 0 to n - 1.   Therefore when calling with 0 based arrays */
/* use  realft( &data[-1], n, isign)                                      */
void realft(float data[], long n, int isign)
{
   long i = 0, i1 = 0, i2 = 0, i3 = 0, i4 = 0, np3 = n+3, no2 = n / 2, 
     no4 = n / 4;
   double c1=0.5,c2,h1r,h1i,h2r,h2i;
   double wr = 0, wi = 0, wpr = 0, wpi = 0, wtemp = 0, theta = 0;

   theta=3.141592653589793/(double) (no2);
   if (isign == 1) {
     c2 = -0.5;
     four1(data,no2,1);
   } 
   else {
     c2=0.5;
     theta = -theta;
   }
   wtemp=sin(0.5*theta);
   wpr = -2.0*wtemp*wtemp;
   wpi=sin(theta);
   wr=1.0+wpr;
   wi=wpi;
   for (i=2;i<=no4;i++) {
     i4=1+(i3=np3-(i2=1+(i1=i+i-1)));
     h1r=c1*(data[i1]+data[i3]);
     h1i=c1*(data[i2]-data[i4]);
     h2r = -c2*(data[i2]+data[i4]);
     h2i=c2*(data[i1]-data[i3]);
     data[i1]=h1r+wr*h2r-wi*h2i;
     data[i2]=h1i+wr*h2i+wi*h2r;
     data[i3]=h1r-wr*h2r+wi*h2i;
     data[i4] = -h1i+wr*h2i+wi*h2r;
     wr=(wtemp=wr)*wpr-wi*wpi+wr;
     wi=wi*wpr+wtemp*wpi+wi;
   }
   h1r=data[1];
   if (isign == 1) {
     data[1] = h1r+data[2];
     data[2] = h1r-data[2];
   } else {
     data[1]=c1*(h1r+data[2]);
     data[2]=c1*(h1r-data[2]);
     four1(data,no2,-1);
   }
} /* end of realft() */










