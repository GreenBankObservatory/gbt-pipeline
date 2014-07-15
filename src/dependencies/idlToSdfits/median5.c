/* File median5.c, version 1.2, released  04/03/18 at 10:38:35 
   retrieved by SCCS 14/04/23 at 15:51:09     

%% Simple function to median 5 values
:: general purpose

HISTORY
031218 GIL add low median functions
030922 GIL initial version based on median 5

DESCRIPTON
median5() returns the median of 5 values, which is the average of
the two middle values.
*/

double median3( double a, double b, double c);
double median4( double a, double b, double c, double d);
void shellSort(long n, double a[]);

double median5( double a, double b, double c, double d, double e)
{ long n = 5; 
  double vs[] = { 0, a, b, c, d, e};

  shellSort( n, vs);
  return ( vs[3]);
} /* end of median5() */

double median6( double a, double b, double c, double d, double e, double f)
{ long n = 6; 
  double vs[] = { 0, a, b, c, d, e, f};

  shellSort( n, vs);

  return( 0.5*(vs[3] + vs[4]));
} /* end of median6() */

double medianLow3( double a, double b, double c)
{ if ((a > b)  && (a > c)) {
    if (b > c) 
      return( c);
    else
      return( b);
  }
  else if ((b > c) && (b > a)) {
    if (a > c) 
      return( c);
    else
      return( a);
  }
  /* else c > a & b */
  if (a > b)
    return( b);
  else
    return( a);
} /* end of medianLow3() */

double medianLow4( double a, double b, double c, double d)
{ long n = 4; 
  double vs[] = { 0, a, b, c, d};

  shellSort( n, vs);
  return ( vs[2]);
} /* end of median5() */

double medianLow5( double a, double b, double c, double d, double e)
{ long n = 5; 
  double vs[] = { 0, a, b, c, d, e};

  shellSort( n, vs);
  return ( 0.5*(vs[2]+vs[3]));
} /* end of median5() */

double medianLow6( double a, double b, double c, double d, double e, double f)
{ long n = 6; 
  double vs[] = { 0, a, b, c, d, e, f};

  shellSort( n, vs);

  return( vs[3]);
} /* end of median6() */
