/*  @(#)dotpr3.c  version 1.1  created 90/04/02 14:25:27
                fetched from SCCS 95/11/13 10:21:17
%% function to calc dot product of two 3-dimensional vectors
LANGUAGE: C
ENVIRONMENT: Any
:: vector dot product multiply
*/
/*++****************************************************************************
*/
double dotpr3 (vector1, vector2)
double vector1[3];
double vector2[3];
/*
-*/
{
    register int i;
    register double *v1 = vector1;
    register double *v2 = vector2;
    double sum = 0.0;
 
    for (i = 0; i < 3; i++)
        sum += *v1++ * *v2++;
    return (sum);
}
