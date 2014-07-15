/*  @(#)rotate3.c  version 1.1  created 90/04/02 14:32:12
                fetched from SCCS 95/11/13 10:26:32
%% function to multiply a vector by a rotation matrix
LANGUAGE: C
ENVIRONMENT: Any
:: matrix multiply vector rotate
*/

/* externals */
double dotpr3 ();

/*++****************************************************************************
*/
void rotate3 (out_vector, matrix, in_vector)
double out_vector[3];      /* output product-vector */
double matrix[3][3];       /* input matrix */
double in_vector[3];       /* input vector */
/*
* Multiplies a 3 x 3 matrix by a 3-component (column) vector to obtain another 
* 3-component (column) vector.  In matrix notation:
*           (product_vector) = (matrix) * (input_vector).
*
* Typical use would be co-ordinate transformation.
-*/
{
    int i;
 
    for (i = 0; i < 3; i++)
        out_vector[i] = dotpr3 (matrix[i], in_vector);
}
