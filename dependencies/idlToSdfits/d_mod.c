
double d_mod( double * inValue, double * inMax)
{ double outValue = *inValue;

  if ( *inMax <= 0)
    return(0.);

  while ( outValue < 0.)
    outValue += *inMax;

  while ( outValue >= *inMax)
    outValue -= *inMax;

  return(outValue);
}
