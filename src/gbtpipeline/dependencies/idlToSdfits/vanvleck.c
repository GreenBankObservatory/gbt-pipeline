/* File vanvleck.c, version 1.9, released  02/04/11 at 08:34:59 
   retrieved by SCCS 14/04/23 at 15:51:04     

%% VanVleck Correction utility
:: collection of spectrometer signal processing routines 

HISTORY
020307 GIL fix input level convention for vanvleck9*(), add comments
011210 GIL remove printfs
011127 GIL try to fix 9 level van vleck.
011115 GIL revert to orignianl vanvleck 9 level
011024 GIL update vanvleck 9
010205 GIL test intensity 
001218 GIL add comments
000000 J?H initial version

DESCRIPTION:

Hi Glen,

You might have heard that I left NRAO last summer for a permanant 
job at Arecibo.

The 12m never supported 9-level modes so we never needed a 9-level 
correction, but you are in luck. At Arecibo we do have a 9-level
correlator. Appended at the end is the code we use for power computation
and quantization correction for both 3 and 9 level modes. 

This code was written by Andy Dowd when he was here.

Also check out this link for a technical description.

http://www.naic.edu/techinfo/teltech/upgrade/corrhelp.htm


Jeff Hagen
Arecibo Observatory
jeffh@naic.edu
787-878-2612 x223
*/

/*--------------------------------------------------*
 * Important signal processing routines
 *
 *   Note - ALL of these functions work on raw correlation values
 *  which have been normalized such that  -1 <rho < 1
 *  i.e. any offset is removed and then it is divided by the
 *  maximum possible correlation.   
 *  This normalized value will (in general) be refered to as rho
 *  while the zerloag version will be zho
 *
 * Optimum thresholds (vthres = first threshold above 0)
 *    and resulting zerolag (normalized to 0:1)
 *   vthres 3 level = 0.6120003/sigma  -> zho = 0.5418
 *   vthres 9 level = 0.266916/sigma ->   zho = 0.2126
 *--------------------------------------------------*/
#include <stdio.h> 
#include <math.h> 

double inverse_cerf(double);
double attndb3lev(double);
double attndb9lev(double);
double pow3lev(double);
double pow9lev(double);
long vanvleck3lev(double *,long);
long vanvleck3levf(float *,long);
void vanvleck9lev(double *,long);
void vanvleck9levf(float *,long);
long makefactor2(long);
double hamming(long,long);


#ifndef M_PI
#define M_PI 3.1415926535
#endif

#define OPTIMUM3LEVEL 0.5418
#define OPTIMUM9LEVEL 0.2126
#define NO    0
#define YES   1

/*-----------------------------------------------------------------------*
 * Compute Necessary Adjustment to Power Levels for 3 level sampling
 *  
 * Note: Optimum Level Vthres = 0.612003 
 *     or 20*log10(0.6120003) = -4.26497 
 * This routine routines the required change in ATTENUATION required to achieve
 *   optimum performance.
 * THUS a positive result means MORE attenuation is required (reduce power)
 *      a negative result means LESS attenuation is required (increase power)
 *
 *-----------------------------------------------------------------------*/
double attndb3lev(double zho)
{
  double db;
  db = -4.26497 - 20*log10(sqrt(2)*inverse_cerf(zho));
  return(db);
}
/*-------------------------------------------------------------------*
 * Converts zerolag into an unbiased estimate of input power (sigma^2)
 * output is unitless: (sigma/vthre)^2
 * NOTE this value is scaled by vthres, such that pow =1 when threshold is
 * optimum
 *--------------------------------------------------------------------*/
double pow3lev(double zho)
{
  double tmp = inverse_cerf(zho);

  return(0.3745443672/(tmp*tmp*2.));
}
/*-----------------------------------------------------------------------*
 * Convert zerolag into an unbiased estimate of power
 * NOTE this value is scaled by vthres, such that pow =1 when threshold is
 * optimum
 *-----------------------------------------------------------------------*/
double pow9lev(double zho)
{
  static double coef[8] = {-0.03241744594,4.939640303,-5.751574913, 34.83143031,-78.66637472, 213.7108496, -317.1011469, 245.8618017  };

  double pow = 
    ((((((coef[7]*zho + coef[6])*zho + coef[5])*zho +coef[4])*zho + coef[3])*
      zho + coef[2])*zho +coef[1])*zho +coef[0];

  return(pow);
}

/*-----------------------------------------------------------------------*
 * Compute Necessary Adjustment to Power Levels for 9 level sampling
 *   Optimum zerolag occurs when sigma = 1 and
 *      x1 = 0.266916 and vthres = +/- {1,3,5,7)*x1
 *      i.e. {0.266916, 0.800748, 1.33458, 1.86841} 
 *    see samp9lev.c for details
 *   this will produce a zho = 0.2125855237
 * 
 * Note a positive result means MORE attenuation is needed (power is high)
 *      a negative result means LESS attenuation is needed (power is low)
 *
 *-----------------------------------------------------------------------*/
double attndb9lev(double zho)
{
  static double coef[8] = {-0.03241744594,4.939640303,-5.751574913, 34.83143031,-78.66637472, 213.7108496, -317.1011469, 245.8618017  };
  double db,pow;
  pow = ((((((coef[7]*zho + coef[6])*zho + coef[5])*zho +coef[4])*zho + coef[3])*zho + coef[2])*zho +coef[1])*zho +coef[0];
  db = 10*log10(pow);
  return(db);
}
/*----------------------------------------------------------------*
 *  round an integer UP to the next factor of two
 * this used to ensure an fft is applied on factors of 2, 
 * even if number of lags is an odd value
 *   Thus 1000 -> 1024 or 33 -> 64, etc
 *----------------------------------------------------------------*/
long makefactor2(long in)
{
   double tmp;
   long if2;
   tmp = ceil( log10((double)in)/log10(2.0));
   if2 = rint(pow(2.0,tmp));
   return(if2); 
}
/*-----------------------------------------------------------------*
 * Hamming Window Function - Standard time domain version:
 *              +  +
 *           +        + 
 *     +  +              +  +
 *   ----------------------------------------
 *     0  1  2  3  4  5  6  7   npts = 8
 *   Return the hanning window factor for index x, 
 * note index is "C" type i.e. index = 0,1,2, ... N-1
 *  Reference "Signals and Systems" by Ziemer, et al
 *-----------------------------------------------------------------*/
double hamming(long index, long npts)
{
  return( 0.54 - 0.46*cos(2*M_PI*((double)index + 0.5)/((double)npts)));
}
/*----------------------------------------------------------*
 * Approximation for Inverse Complementary Error Function 
 *  Uses Defintion of erfc given by Numerical Recipes
 *----------------------------------------------------------*/
double inverse_cerf(double input)
/* the inverse erfc() is used to calculate the power corresponding to a */
/* auto-correllation function according to the relation ship            */
/* Power = 0.5 * erfc(autocorr)^-2                                      */
/* note that the complimentary erf function input must be less than 1   */
{
    static double numerator_constants[3] = 
      {1.591863138,-2.442326820, 0.37153461};
    static double denominator_constants[3] = 
      {1.467751692,-3.013136362, 1.0};
    double temp_data = 1, temp_data_srq = 1, erf_data = 1, numerator = 1,
      denominator = 1;

    if (input >= 1.)                            /* exit on illegal values */
      return(100.);

    erf_data = 1.0-input;                       /* set up input values */
    temp_data = (erf_data*erf_data - 0.5625);
    temp_data_srq = temp_data*temp_data;

    numerator = numerator_constants[0]+
      (temp_data*numerator_constants[1])+
      (temp_data_srq*numerator_constants[2]);

    denominator = denominator_constants[0]
      + (temp_data*denominator_constants[1])
      + (temp_data_srq*denominator_constants[2]);

    temp_data = erf_data*numerator/denominator;

    return(temp_data);
} /* inverse_cerf() */

/*------------------------------------------------------------------------*
 * Van Vleck Correction for 9-level sampling/correlation
 *  Samples {-4,-3,-2,-1,0,1,2,3,4}
 * Uses Zerolag to adjust correction
 *   data_array -> Points into autocorrelation function of at least 'count' points
 * this routine takes the first value as the zerolag and corrects the remaining
 * count-1 points.  Zerolag is set to a normalized 1
 * NOTE - The available routine works on lags normaized to -16<rho<16, so
 *  I need to adjust the values before/after the fit
 * Coefficent ranges
 *   c1 
 *     all
 *   c2
 *     r0 > 4.5
 *     r0 < 2.1
 *     rest 
 * NOTE - correction is done INPLACE ! Original values are destroyed
 * As reported by M. Lewis -> the polynomial fits are OK, but could be improved
 *
 * Documentation by Glen Langston on 02 March 07:
 * The input array, rho[], should have values near the optimum 9 level value
 * (~.21 for the zero lag and smaller for larger lags).  
 * These values are scaled by the optimum 9 level, to yield an array with
 * correction values near unity, if lags have optimum value.  
 *------------------------------------------------------------------------*/
void vanvleck9lev(double rho[],long npts)
{ long i = 0;
  double acoef[5] = {0, 0, 0, 0, 0}, dtmp = 0, zl = rho[0] * 16., ro = rho[0];
  static long printCount = 0;
  static double coef1[5] = 
    { 1.105842267, -0.053258115, 0.011830276,-0.000916417, 0.000033479 };

  static double coef2rg4p5[5] = 
    { 0.111705575, -0.066425925, 0.014844439, -0.001369796, 0.000044119 };
  static double coef2rl2p1[5] =  
    { 1.285303775, -1.472216011, 0.640885537, -0.123486209, 0.008817175 };
  static double coef2rother[5] = 
    { 0.519701391, -0.451046837, 0.149153116, -0.021957940, 0.001212970 };

  static double coef3rg2p0[5] = 
    { 1.244495105, -0.274900651, 0.022660239, -0.000760938, -1.993790548 };
  static double coef3rother[5] = 
    { 1.249032787, 0.101951346, -0.126743165, 0.015221707, -2.625961708 };

  static double coef4rg3p15[5] = 
    { 0.664003237, -0.403651682,  0.093057131, -0.008831547, 0.000291295 };
  static double coef4rother[5] = 
    { 9.866677289, -12.858153787, 6.556692205, -1.519871179, 0.133591758 };

  static double coef5rg4p0[4] = 
    { 0.033076469, -0.020621902,  0.001428681, 0.000033733};
  static double coef5rg2p2[4] = 
    { -5.284269565, 6.571535249, -2.897741312, 0.443156543};
  static double coef5rother[4] = 
    {-1.475903733,  1.158114934, -0.311659264, 0.028185170};

  if (ro == 0)                             /* avoid divide by zero*/
    return;

  /* the van vleck correction implimented here depends lags normalized to 1 */
  for(i=1; i <npts; i++) 
    rho[i] /= ro;
  
  acoef[0] = ((((((coef1[4]*zl) + coef1[3])*zl) + coef1[2])*zl + coef1[1])*zl) +
    coef1[0];

  /* find the correct coefficicents for scaled zero lag value */
  if( zl > 4.50)
    acoef[1] =(((((((coef2rg4p5[4]*zl) + coef2rg4p5[3])*zl) + coef2rg4p5[2])*zl) + 
		coef2rg4p5[1])*zl) + coef2rg4p5[0];
  else if (zl < 2.10)  
    acoef[1] =(((((((coef2rl2p1[4]*zl) + coef2rl2p1[3])*zl) + coef2rl2p1[2])*zl) + 
		coef2rl2p1[1])*zl) + coef2rl2p1[0];
  else
    acoef[1] =(((((((coef2rother[4]*zl) + coef2rother[3])*zl) + coef2rother[2])*zl) + 
		 coef2rother[1])*zl) + coef2rother[0];

  if( zl > 2.00)
    acoef[2] = (coef3rg2p0[4]/zl) + 
      (((((coef3rg2p0[3]*zl) +  coef3rg2p0[2])*zl) +  coef3rg2p0[1])*zl) +  coef3rg2p0[0];
  else
    acoef[2] = (coef3rother[4]/zl) + 
      (((((coef3rother[3]*zl) + coef3rother[2])*zl) + coef3rother[1])*zl) + coef3rother[0];  
  
  if( zl > 3.15)
    acoef[3] = (((((((coef4rg3p15[4]*zl) + coef4rg3p15[3])*zl) + coef4rg3p15[2])*zl) + coef4rg3p15[1])*zl)
      + coef4rg3p15[0];
  else
    acoef[3] = (((((((coef4rother[4]*zl) + coef4rother[3])*zl) + coef4rother[2])*zl) + coef4rother[1])*zl)
      + coef4rother[0];  

  if( zl > 4.00)
    acoef[4] = (((((coef5rg4p0[3]*zl)  + coef5rg4p0[2])*zl)  + coef5rg4p0[1])*zl)  + coef5rg4p0[0];
  else if (zl < 2.2)  
    acoef[4] = (((((coef5rg2p2[3]*zl)  + coef5rg2p2[2])*zl)  + coef5rg2p2[1])*zl)  + coef5rg2p2[0]; 
  else
    acoef[4] = (((((coef5rother[3]*zl) + coef5rother[2])*zl) + coef5rother[1])*zl) + coef5rother[0];

  if (zl > 1.) {
    for(i=1; i<npts; i++) {
      dtmp = rho[i];
      rho[i] =(((((acoef[4]*dtmp) + acoef[3])*dtmp + acoef[2])*dtmp + acoef[1])*dtmp + acoef[0])*dtmp;
    }
  }
  else {
    if (printCount < 0) {
      fprintf (stderr, "VanVleck9(%6.3f)->1 %6.3f %6.3f %6.3f ... %6.3f\n",
	     ro, rho[1], rho[2], rho[3], rho[npts/2]);
      fprintf( stderr, "(0)-> %g (1)-> %g (2)-> %g (3)-> %g (4)-> %g for %g\n",
	       acoef[0],acoef[1],acoef[2],acoef[3],acoef[4], zl); 
      printCount++;
    }
  }
  rho[0] = 1.0;                          /* by definition, unity lag data */
  return;
} /* end of vanvleck9lev()*/

void vanvleck9levf(float rho[],long npts)
{ long i = 0;
  double acoef[5] = {0, 0, 0, 0, 0}, dtmp = 0, zl = *rho * 16;
  static double coef1[5] = 
    { 1.105842267, -0.053258115, 0.011830276,-0.000916417, 0.000033479 };
  static double coef2rg4p5[5] = 
    { 0.111705575, -0.066425925, 0.014844439, -0.001369796, 0.000044119 };
  static double coef2rl2p1[5] =  
    { 1.285303775, -1.472216011, 0.640885537, -0.123486209, 0.008817175 };
  static double coef2rother[5] = 
    { 0.519701391, -0.451046837, 0.149153116, -0.021957940, 0.001212970 };

  static double coef3rg2p0[5] = 
    { 1.244495105, -0.274900651, 0.022660239, -0.000760938, -1.993790548 };
  static double coef3rother[5] = 
    { 1.249032787, 0.101951346, -0.126743165, 0.015221707, -2.625961708 };

  static double coef4rg3p15[5] = 
    { 0.664003237, -0.403651682, 0.093057131, -0.008831547, 0.000291295 };
  static double coef4rother[5] = 
    { 9.866677289, -12.858153787, 6.556692205, -1.519871179, 0.133591758 };
  static double coef5rg4p0[4] = 
    { 0.033076469, -0.020621902, 0.001428681, 0.000033733};
  static double coef5rg2p2[4] = 
    { -5.284269565, 6.571535249, -2.897741312, 0.443156543};
  static double coef5rother[4] = 
    {-1.475903733, 1.158114934, -0.311659264, 0.028185170};

  /* the van vleck correction implimented here depends lags normalized to 1 */
  for(i=0; i<npts; i++)                    
    rho[i] /= OPTIMUM9LEVEL; 
  
  acoef[0] = coef1[0] +
    ((((coef1[4]*zl + coef1[3])*zl + coef1[2])*zl +coef1[1])*zl);

  /* find the correct coefficicents for scaled zero lag value */
  if( zl > 4.50)
    acoef[1] =((((coef2rg4p5[4]*zl + coef2rg4p5[3])*zl + coef2rg4p5[2])*zl + coef2rg4p5[1])*zl + coef2rg4p5[0]);
  else if(zl < 2.10)  
    acoef[1] =((((coef2rl2p1[4]*zl + coef2rl2p1[3])*zl + coef2rl2p1[2])*zl + coef2rl2p1[1])*zl + coef2rl2p1[0]);
  else
    acoef[1] =((((coef2rother[4]*zl + coef2rother[3])*zl + coef2rother[2])*zl + coef2rother[1])*zl + coef2rother[0]);

  if( zl > 2.00)
    acoef[2] = coef3rg2p0[4]/zl + (((coef3rg2p0[3]*zl + coef3rg2p0[2])*zl + coef3rg2p0[1])*zl + coef3rg2p0[0]);
  else
    acoef[2] = coef3rother[4]/zl + (((coef3rother[3]*zl + coef3rother[2])*zl + coef3rother[1])*zl + coef3rother[0]);  
  
  if( zl > 3.15)
    acoef[3] = ((((coef4rg3p15[4]*zl + coef4rg3p15[3])*zl + coef4rg3p15[2])*zl + coef4rg3p15[1])*zl + coef4rg3p15[0]);
  else
    acoef[3] = ((((coef4rg3p15[4]*zl + coef4rother[3])*zl + coef4rother[2])*zl + coef4rother[1])*zl + coef4rother[0]);  

  if( zl > 4.00)
    acoef[4] =(((coef5rg4p0[3]*zl + coef5rg4p0[2])*zl + coef5rg4p0[1])*zl + coef5rg4p0[0]);
  else if(zl < 2.2)  
    acoef[4] =(((coef5rg2p2[3]*zl + coef5rg2p2[2])*zl + coef5rg2p2[1])*zl + coef5rg2p2[0]);
  else
    acoef[4] =(((coef5rother[3]*zl + coef5rother[2])*zl + coef5rother[1])*zl + coef5rother[0]);
  
  /*  fprintf( stderr, "(0)-> %g (1)-> %g (2)-> %g (3)-> %g (4)-> %g for %g\n",
      acoef[0],acoef[1],acoef[2],acoef[3],acoef[4], zl); */

  for(i=1; i<npts; i++) {
    dtmp = rho[i];
    rho[i] =(((((acoef[4]*dtmp) + acoef[3])*dtmp + acoef[2])*dtmp + acoef[1])*dtmp + acoef[0])*dtmp;
  }

  rho[0] = 1.0;                          /* by definition, unity lag data */
  return;
} /* end of vanvleck9levf() */


/*------------------------------------------------------------------------*
 * Van Vleck Correction for 3-level sampling/correlation
 *  Samples {-1,0,1}
 * Uses Zerolag to adjust correction
 *   data_array -> Points into autocorrelation function of at least 'count' points
 * this routine takes the first value as the zerolag and corrects the remaining
 * count-1 points.  Zerolag is set to a normalized 1
 * 
 * NOTE - correction is done INPLACE ! Original values are destroyed
 *------------------------------------------------------------------------*/
long vanvleck3lev(double *rho,long npts)
{
    static double lo_constants[3][4] = {
         { 0.939134371719, -0.567722496249, 1.02542540932, 0.130740914912 },
         { -0.369374472755, -0.430065136734, -0.06309459132, -0.00253019992917},
         { 0.888607422108, -0.230608118885, 0.0586846424223, 0.002012775510695}
         };
    static double high_constants[5][4] = {
         {-1.83332160595, 0.719551585882, 1.214003774444, 7.15276068378e-5},
         {1.28629698818, -1.45854382672, -0.239102591283, -0.00555197725185},
         {-7.93388279993, 1.91497870485, 0.351469403030, 0.00224706453982},
         {8.04241371651, -1.51590759772, -0.18532022393, -0.00342644824947},
         {-13.076435520, 0.769752851477, 0.396594438775, 0.0164354218208}
         };

    double lo_u[3],lo_h[3];
    double high_u[5],high_h[5];
    double lo_coefficient[3];
    double high_coefficient[5];
    double zho = rho[0], zho_3 = 0, temp_data = 0, temp_data_1 = 0;
    long  ichan = 0, ico = 0, flag_any_high  = NO;

    /* temporarily work around 3level problem */
    if (zho < .45) {
      for (ichan = 0; ichan < npts; ichan++) 
	rho[ichan] /= zho;
      return(0);
    }

/* Perform Lo correction on All data that is not flaged for high correction -*/
    zho_3=zho*zho*zho;

    lo_u[0]=zho;
    lo_u[1]=zho_3-(61.0/512.0);
    lo_u[2]=zho-(63.0/128.0);

    lo_h[0]=zho*zho;
    lo_h[2]=zho_3*zho_3*zho;                      /* zlag ^7 */
    lo_h[1]=zho*lo_h[2];                          /* zlag ^8 */
/* determine lo-correct coefficents -*/
    for(ico=0; ico<3; ico++) {
         lo_coefficient[ico] =
	   (lo_u[ico]*(lo_u[ico]*((lo_u[ico]*lo_constants[ico][0])+lo_constants[ico][1])+lo_constants[ico][2])+lo_constants[ico][3])/lo_h[ico];
    }
/* perform correction --*/
    for(ichan=1,flag_any_high=NO; ichan<npts; ichan++) {
      
      temp_data=(double)rho[ichan];                  /* hold last value */
      if(fabs(temp_data) > 0.199) {
	if(flag_any_high==NO) {                      /* if first time using high */
	  high_u[0]=lo_h[2];                         /* zlag ^7 */
	  high_u[1]=zho-(63.0/128.0);
	  high_u[2]=zho*zho-(31.0/128.0);
	  high_u[3]=zho_3-(61.0/512.0);
	  high_u[4]=zho-(63.0/128.0);
	  
	  high_h[0]=lo_h[1];                          /* zlag ^8 */
	  high_h[1]=lo_h[1];                          /* zlag ^8 */
	  high_h[2]=lo_h[1]*zho_3*zho;                /* zlag ^12 */
	  high_h[3]=lo_h[1]*lo_h[1]*zho;              /* zlag ^17 */
	  high_h[4]=high_h[3];                        /* zlag ^17 */
	  for(ico=0; ico<5; ico++) {
	    high_coefficient[ico] = 
	      (high_u[ico]*(high_u[ico]*((high_u[ico]*high_constants[ico][0])+
					 high_constants[ico][1])+
			    high_constants[ico][2])+high_constants[ico][3]) /
	       high_h[ico];
	  }
	  flag_any_high=YES;
	}
	temp_data_1 = fabs(temp_data*temp_data*temp_data);
	rho[ichan]=(temp_data*(temp_data_1*(temp_data_1*(temp_data_1*(temp_data_1*high_coefficient[4]+high_coefficient[3])+high_coefficient[2])+high_coefficient[1])+high_coefficient[0]));
      } 
      else {
	temp_data_1=temp_data*temp_data;
	rho[ichan]=(temp_data*(temp_data_1*((temp_data_1*lo_coefficient[2])+lo_coefficient[1])+lo_coefficient[0]));
      }
    } /* end for all values but first */

    rho[0] = 1.0;

    return(0);
} /* end of vanvleck3lev() */

long vanvleck3levf(float *rho,long npts)
{
    static double lo_constants[3][4] = {
         { 0.939134371719, -0.567722496249, 1.02542540932, 0.130740914912 },
         { -0.369374472755, -0.430065136734, -0.06309459132, -0.00253019992917},
         { 0.888607422108, -0.230608118885, 0.0586846424223, 0.002012775510695}
         };
    static double high_constants[5][4] = {
         {-1.83332160595, 0.719551585882, 1.214003774444, 7.15276068378e-5},
         {1.28629698818, -1.45854382672, -0.239102591283, -0.00555197725185},
         {-7.93388279993, 1.91497870485, 0.351469403030, 0.00224706453982},
         {8.04241371651, -1.51590759772, -0.18532022393, -0.00342644824947},
         {-13.076435520, 0.769752851477, 0.396594438775, 0.0164354218208}
         };

    double lo_u[3],lo_h[3];
    double high_u[5],high_h[5];
    double lo_coefficient[3];
    double high_coefficient[5];
    double zho,zho_3;
    double temp_data;
    double temp_data_1;
    long  ichan,ico,flag_any_high;
/* Perform Lo correction on All data that is not flaged for high correction --*/
    zho=(double)rho[0];
    
    zho_3=zho*zho*zho;

    lo_u[0]=zho;
    lo_u[1]=zho_3-(61.0/512.0);
    lo_u[2]=zho-(63.0/128.0);

    lo_h[0]=zho*zho;
    lo_h[2]=zho_3*zho_3*zho;         /* zlag ^7 */
    lo_h[1]=zho*lo_h[2];               /* zlag ^8 */
/* determine lo-correct coefficents -*/
    for(ico=0; ico<3; ico++)
    {
         lo_coefficient[ico]=(lo_u[ico]*(lo_u[ico]*(lo_u[ico]*lo_constants[ico][0]+lo_constants[ico][1])+lo_constants[ico][2])+lo_constants[ico][3])/lo_h[ico];
    }
/* perform correction --*/
    for(ichan=1,flag_any_high=NO; ichan<npts; ichan++)
    {
        temp_data=(double)rho[ichan];
        if(fabs(temp_data) > 0.199)
        {
            if(flag_any_high==NO)
            {
                   high_u[0]=lo_h[2];                  /* zlag ^7 */
                   high_u[1]=zho-(63.0/128.0);
                   high_u[2]=zho*zho-(31.0/128.0);
                   high_u[3]=zho_3-(61.0/512.0);
                   high_u[4]=zho-(63.0/128.0);

                   high_h[0]=lo_h[1];               /* zlag ^8 */
                   high_h[1]=lo_h[1];               /* zlag ^8 */
                   high_h[2]=lo_h[1]*zho_3*zho;   /* zlag ^12 */
                   high_h[3]=lo_h[1]*lo_h[1]*zho;  /* zlag ^17 */
                   high_h[4]=high_h[3];             /* zlag ^17 */
                   for(ico=0; ico<5; ico++)
                   {
                      high_coefficient[ico]=(high_u[ico]*(high_u[ico]*(high_u[ico]*high_constants[ico][0]+high_constants[ico][1])+high_constants[ico][2])+high_constants[ico][3])/high_h[ico];
                   }
                   flag_any_high=YES;
              }
              temp_data_1=fabs(temp_data*temp_data*temp_data);
              rho[ichan]=(temp_data*(temp_data_1*(temp_data_1*(temp_data_1*(temp_data_1*high_coefficient[4]+high_coefficient[3])+high_coefficient[2])+high_coefficient[1])+high_coefficient[0]));
         } else
         {
              temp_data_1=temp_data*temp_data;
              rho[ichan]=(temp_data*(temp_data_1*(temp_data_1*lo_coefficient[2]+lo_coefficient[1])+lo_coefficient[0]));
         }
    }
    rho[0] = 1.0;
    return(0);
} /* end of vanvleck3levf() */

/*---------------------------------------------------------------------*
 * return modified julian date given a gregorian calendar - based on slalib
 * routine sla_cldj which itself is based on Hatcher (1984) QJRAS 25, 53-55 
 * creation date 1999/07/10 [mjd=51639] (dunc@naic.edu) 
 *---------------------------------------------------------------------*/
double cal2mjd(long iy, long im, long id) 
{
  long leap;
  /* month lengths in days for normal and leap years */
  static long mtab[2][13] = {
    {0,31,28,31,30,31,30,31,31,30,31,30,31},
    {0,31,29,31,30,31,30,31,31,30,31,30,31}
  };

  /*validate year*/
  if (iy<-4699) {
    fprintf(stderr,"Invalid year passed to caldj.... HELP!\n");
    exit(1);
  } else {
    /* validate month */
    if (im<1 || im>12) {
      fprintf(stderr,"Invalid month passed to caldj.... HELP!\n");
      exit(1);
    } else {
      /* allow for leap year */
      leap = ((iy%4 == 0) && (iy%100 != 00)) || iy%400 == 0;
      /* validate day */
      if (id<1 || id>mtab[leap][im]) {
	fprintf(stderr,"Invalid day passed to caldj.... HELP!\n");
	exit(1);
      }
    }
  }
  return ((1461*(iy-(12-im)/10+4712))/4+(5+306*((im+9)%12))/10
           -(3*((iy-(12-im)/10+4900)/100))/4+id-2399904);
}
