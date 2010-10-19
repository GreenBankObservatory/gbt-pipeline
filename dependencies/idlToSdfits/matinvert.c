/* @(#)matinvert.c  version 1.1  created 96/08/28 14:13:01
                fetched from SCCS 97/02/10 11:36:54
%% function to invert a 3x3 matrix
LANGUAGE: C
ENVIRONMENT: Any
:: matrix multiply invert
*/
/*++****************************************************************************
*/
void matinvert (a, b)
double a[3][3];       /* input matrix */
double b[3][3];       /* inverted output matrix */
/*
* Inverts a 3x3 matrix
-*/
{
    double detrm, cofact[3][3];
    int i,j;

    /* calculate the cofactors for the 3x3 input matrix, a */
    cofact[0][0] =  a[1][1]*a[2][2] - a[2][1]*a[1][2];
    cofact[0][1] = -a[0][1]*a[2][2] + a[2][1]*a[0][2];
    cofact[0][2] =  a[0][1]*a[1][2] - a[1][1]*a[0][2];
    cofact[1][0] = -a[1][0]*a[2][2] + a[2][0]*a[1][2];
    cofact[1][1] =  a[0][0]*a[2][2] - a[2][0]*a[0][2];
    cofact[1][2] = -a[0][0]*a[1][2] + a[1][0]*a[0][2];
    cofact[2][0] =  a[1][0]*a[2][1] - a[2][0]*a[1][1];
    cofact[2][1] = -a[0][0]*a[2][1] + a[2][0]*a[0][1];
    cofact[2][2] =  a[0][0]*a[1][1] - a[1][0]*a[0][1];
    
    /* calculate the determinant of the input matrix, a */
    detrm = a[0][0] * cofact[0][0]
          + a[0][1] * cofact[1][0]
          + a[0][2] * cofact[2][0];

    /* divide the cofactor matrix by the determinant of a */
    for (i = 0; i < 3; i++)
        for (j = 0; j < 3; j++)
            b[i][j] = cofact[i][j] / detrm;

    return;
}
