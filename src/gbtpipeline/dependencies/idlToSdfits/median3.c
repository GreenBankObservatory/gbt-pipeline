/* File median3.c, version 1.1, released  03/09/24 at 08:48:14 
   retrieved by SCCS 14/04/23 at 15:51:10     

%% Simple function to median 3 values
:: general purpose

HISTORY
030922 GIL initial version based on median 4.

DESCRIPTON
median3() returns the median of 3 values, which is the average of
the two middle values.
*/

double median3( double a, double b, double c)
{ double theMedian = a + b + c, minValue = a, maxValue = a;

  /* find the min and max and subtract from average */
  if (b < minValue)
    minValue = b;
  else if (b > maxValue)
    maxValue = b;

  if (c < minValue)
    minValue = c;
  else if (c > maxValue)
    maxValue = c;

  theMedian = (theMedian - minValue - maxValue);

  return(theMedian);
} /* end of median3() */
