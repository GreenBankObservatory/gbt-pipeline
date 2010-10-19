/* File median4.c, version 1.1, released  02/01/18 at 10:02:03 
   retrieved by SCCS 09/12/30 at 16:44:55     

%% Simple function to median 4 values
:: general purpose

HISTORY
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
