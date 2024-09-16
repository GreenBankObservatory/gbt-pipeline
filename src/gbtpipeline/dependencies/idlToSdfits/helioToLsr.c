/* File helioToLsr.c, version 1.1, released  01/11/01 at 22:44:53 
   retrieved by SCCS 14/04/23 at 15:51:22     

%% function to calculate velocites relative to a direction

:: GBES-C position point J2000 epoch apparent
 
History:
  011030 GIL initial version 
              
DESCRIPTION:
helioToLsr computes the projected barycentric to Lsr velocity in
the direction of raJ2000, decJ2000
*/
#include "stdio.h"	/* add io definitions */
#include "math.h"	/* add mathmatics definitions */
#include "MATHCNST.H"	/* define TWOPI */
#include "STDDEFS.H"	/* define TWOPI */

/* externals */

extern double angularDistance( double raA, double decA, 
			       double raB, double decB);
void rectpol (
double dir_vector[3],    /* input, xyz co-ordinates */
double *ra,              /* returned ra in radians, where 0 <= ra < TWOPI */
double *dec);            /* returned dec in radians */

/* internals */
#define RALSR  (270.99532*DEGREE)  /* direction of Sun in J2000 components */
#define DECLSR (30.81517*DEGREE)   /* ==> l = 57 +/- 4, b = 23 +/- 4 */
#define VLSR   (-20.0)             /* km/sec;  doing away from direciton is +*/
#define CKMPERSEC      (C_LIGHT*.001)  /* velocity of light in km/sec */

char * magnitude( double v[3], double * mag )
{ double sum = (v[0]*v[0])+(v[1]*v[1])+(v[2]*v[2]);

  if (sum > 0)
    sum = sqrt(sum);
  else 
    sum = 0;

  * mag = sum;

  return(NULL);
} /* end of magnitude */

char * relativisticVectorSum( double v1[3], double v2[3], double vSum[3])
/* input velocities are in km/sec, so that relativistic scaling works */
{ double gammaInverse = 1, vDot = 0;

  vSum[0] = v1[0] + v2[0];
  vSum[1] = v1[1] + v2[1];
  vSum[2] = v1[2] + v2[2];

  vDot = (v1[0]*v2[0]) + (v1[1]*v2[1]) + (v1[2]*v2[2]);

  gammaInverse = (1 - (vDot/(CKMPERSEC*CKMPERSEC)));

  if (gammaInverse > 0.)
    gammaInverse = sqrt( gammaInverse);
  else 
    gammaInverse = 0;

  vSum[0] *= gammaInverse;
  vSum[1] *= gammaInverse;
  vSum[2] *= gammaInverse;
  return(NULL);
} /* relativisticVectorSum() */

char * helioToLsr( double raJ2000, double decJ2000, double vHelio,
		   double * vLsrOut)
/* helioToLsr() takes input angle coordinates and barycentric velocity */
/* and calculates the projected velocity in the LSR frame */
{ char * errMsg = NULL;
  double vLsr = VLSR, vRa = 0, vDec = 0, dV = 0, 
    vectorBary[3] = { 0, 0, 0}, sumV[3] = {0, 0, 0};
  static double vectorLsr[3] = { 0, 0, 0};

  if (vectorLsr[0] == 0) {
    vectorLsr[0] = VLSR * cos( RALSR) * cos( DECLSR);
    vectorLsr[1] = VLSR * sin( RALSR) * cos( DECLSR);
    vectorLsr[2] = VLSR * sin( DECLSR);
  }

  vectorBary[0] = vHelio * cos( raJ2000) * cos( decJ2000);
  vectorBary[1] = vHelio * sin( raJ2000) * cos( decJ2000);
  vectorBary[2] = vHelio * sin( decJ2000);

  errMsg = relativisticVectorSum( vectorBary, vectorLsr, sumV);

  magnitude ( sumV, &dV);

  if (dV > 0) {
    sumV[0] /= dV;
    sumV[1] /= dV;
    sumV[2] /= dV;
  }

  /* now convert to J2000 angles and velocity magnitude */
  rectpol( sumV, &vRa, &vDec);
 
  /* compute projected velocity in direction of the source */
  vLsr = dV * cos( angularDistance( vRa, vDec, raJ2000, decJ2000));

  *vLsrOut = vLsr;

  return(errMsg);
} /* helioToLsr() */


