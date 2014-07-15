/* File medianVectors.c, version 1.1, released  04/03/18 at 10:39:37 
   retrieved by SCCS 14/04/23 at 15:51:08     

%% utility function for median of a variable number of vectors
:: spectrometer program

HISTORY
031217 GIL a series of medians on spectrometer data.  No narrow line

DESCRIPTION:
medianVectors() accepts up to 6 vectors and returns the
a vector containing the median of those vectors
*/

#include "stdio.h"
#include "string.h"
#include "STDDEFS.H"

/* externals */
extern double median3( double a, double b, double c);
extern double median4( double a, double b, double c, double d);
extern double median5( double a, double b, double c, double d, double e);
extern double median6( double a, double b, double c, 
		       double d, double e, double f);
extern double medianLow3( double a, double b, double c);
extern double medianLow4( double a, double b, double c, double d);
extern double medianLow5( double a, double b, double c, double d, double e);
extern double medianLow6( double a, double b, double c, 
		       double d, double e, double f);

char * medianVectors( long nVectors, long nItems, double * vectors[], 
		      double outVector[]) 
/* medianVectors() takes a number of vectors with nItems in each vector     */
/* and returns a single vector with the median value of the input vector    */
{ long i = 0;
  double * inVector = vectors[0], * in1Vector = vectors[1], 
    * in2Vector = vectors[2], * in3Vector = NULL, 
    * in4Vector = NULL, * in5Vector = NULL;
    
  if (nVectors <= 1) {
    for (i = 0; i < nItems; i++) {
      outVector[i] = inVector[i];
    }
  }
  else if (nVectors == 2) {
    for (i = 0; i < nItems; i++) {
      outVector[i] = 0.5*(inVector[i]+in1Vector[i]);
    }
  }
  else if (nVectors == 3) {
    for (i = 0; i < nItems; i++) {
      outVector[i] = median3(inVector[i], in1Vector[i], in2Vector[i]);
    }
  }
  else if (nVectors == 4) {
    in3Vector = vectors[3];
    for (i = 0; i < nItems; i++) {
      outVector[i] = median4(inVector[i], in1Vector[i], in2Vector[i],
			     in3Vector[i]);
    }
  }
  else if (nVectors == 4) {
    in3Vector = vectors[3];
    in4Vector = vectors[4];
    for (i = 0; i < nItems; i++) {
      outVector[i] = median5(inVector[i], in1Vector[i], in2Vector[i],
			     in3Vector[i], in4Vector[i]);
    }
  }
  else {
    in3Vector = vectors[3];
    in4Vector = vectors[4];
    in5Vector = vectors[5];
    for (i = 0; i < nItems; i++) {
      outVector[i] = median6(inVector[i], in1Vector[i], in2Vector[i],
			     in3Vector[i], in4Vector[i], in5Vector[i]);
    }
  }
     
  return(NULL);
} /* end of medianVectors() */
    
char * medianLowVectors( long nVectors, long nItems, double * vectors[], 
		      double outVector[]) 
/* medianLowVectors() takes a number of vectors with nItems in each vector  */
/* and returns a single vector with the "lower" median value of input vectors*/
{ long i = 0;
  double * inVector = vectors[0], * in1Vector = vectors[1], 
    * in2Vector = vectors[2], * in3Vector = NULL, 
    * in4Vector = NULL, * in5Vector = NULL;
    
  if (nVectors <= 1) {
    for (i = 0; i < nItems; i++) {
      outVector[i] = inVector[i];
    }
  }
  else if (nVectors == 2) {
    for (i = 0; i < nItems; i++) {
      if (inVector[i] > in1Vector[i])
        outVector[i] = in1Vector[i];
      else
        outVector[i] = inVector[i];
    }
  }
  else if (nVectors == 3) {
    for (i = 0; i < nItems; i++) {
      outVector[i] = medianLow3(inVector[i], in1Vector[i], in2Vector[i]);
    }
  }
  else if (nVectors == 4) {
    in3Vector = vectors[3];
    for (i = 0; i < nItems; i++) { 
      outVector[i] = medianLow4(inVector[i], in1Vector[i], in2Vector[i],
			     in3Vector[i]);
    }
  }
  else if (nVectors == 4) {
    in3Vector = vectors[3];
    in4Vector = vectors[4];
    for (i = 0; i < nItems; i++) {
      outVector[i] = medianLow5(inVector[i], in1Vector[i], in2Vector[i],
			     in3Vector[i], in4Vector[i]);
    }
  }
  else {
    in3Vector = vectors[3];
    in4Vector = vectors[4];
    in5Vector = vectors[5];
    for (i = 0; i < nItems; i++) {
      outVector[i] = medianLow6(inVector[i], in1Vector[i], in2Vector[i],
			     in3Vector[i], in4Vector[i], in5Vector[i]);
    }
  }
     
  return(NULL);
} /* end of medianLowVectors() */
    
