/* File median4.c, version 1.2, released  12/07/17 at 11:46:40 
   retrieved by SCCS 14/04/23 at 15:51:06     

%% Simple function to median 4 values
:: general purpose

HISTORY
120712 GIL add min4 and max4 analogus functions
020117 GIL initial version

DESCRIPTON
median4() returns the median of 4 values, which is the average of
the two middle values.
*/

double median4( double a, double b, double c, double d)
{ double theMedian = a + b + c + d, minValue = a, maxValue = a;

  /* find the min and max and subtract from average */
  if (b < minValue)
    minValue = b;
  else if (b > maxValue)
    maxValue = b;

  if (c < minValue)
    minValue = c;
  else if (c > maxValue)
    maxValue = c;

  if (d < minValue)
    minValue = d;
  else if (d > maxValue)
    maxValue = d;

  theMedian = (theMedian - minValue - maxValue)*.5;

  return(theMedian);
} /* end of median4() */

double min4( double a, double b, double c, double d)
{ double minValue = a;

  if (b < minValue)
    minValue = b;

  if (c < minValue)
    minValue = c;

  if (d < minValue)
    minValue = d;

  return(minValue);
} /* end of min4() */

double max4( double a, double b, double c, double d)
{ double maxValue = a;

  if (b > maxValue)
    maxValue = b;

  if (c > maxValue)
    maxValue = c;

  if (d > maxValue)
    maxValue = d;

  return(maxValue);
} /* end of max4() */
