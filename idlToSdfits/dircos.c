/*  @(#)dircos.c  version 1.1  created 90/04/02 14:25:26
                fetched from SCCS 95/11/13 10:21:08
%% function convert equatorial (ra, dec) to rectangular (direction cosines).
LANGUAGE: C
ENVIRONMENT: Any
:: polar equatorial rectangular xyz coordinates convert direction
*/
/* externals */
double sin ();
double cos ();

/*++***************************************************************************
*/
void dircos (ra, dec, dc_vector)
double ra, dec;          /* input:  ra and dec in radians */
double dc_vector[3];     /* output:  direction cosine vector
                                   x = dc_vector[0], y = dc_vector[1] */
/*
* Compute direction cosines from right ascension and declination.  Z-axis is 
* the polar axis; x-axis passes thru vernal equinox (ra = 0).
-*/
{
    double cosdec = cos (dec);
    register double *v = dc_vector;
 
    *v++ = cos (ra) * cosdec;
    *v++ = sin (ra) * cosdec;
    *v   = sin (dec);
}
