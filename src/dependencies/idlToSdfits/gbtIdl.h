/* File gbtIdl.h, version 1.3, released  11/02/03 at 14:17:10 
   retrieved by SCCS 14/04/23 at 15:50:47     

%% describe IF settings, sky frequencies and bandwidths in GB-IDL format

HISTORY
091230 GIL add dMjd date+time
040415 GIL add GO parameters discussed with Tom
040413 GIL initial version based on gbtLo.h

DESCRIPTION:
gbtIdl.h contains a structure definition compatible with the GB-IDL
data format, to allow passing filled data directly to IDL plotting
functions
*/

/* below is the IDL code that must be matched by the GBTIDL structure def 
;  Define the basic 3-Helium internal data structure format
;
;             IDL single dish package requires at least these variables
;
gbt = {gbt_data,    $                 ;  # bytes -> total # bytes
       source:bytarr(32), $           ;     4          32
       scan_num:0L, $                 ;     4          36
       off_scan:0L, $                 ;     4          40
       line_id:bytarr(32), $          ;    32          72
       pol_id:bytarr(32), $            ;     4          76
       scan_type:bytarr(32), $        ;    32         108
       lst:0.0D, $                    ;     8         116       
       date:bytarr(32), $             ;    32         148
       ra:0.0D, $                     ;     8         156
       dec:0.0D, $                    ;     8         164
       az:0.0D, $                     ;     8         172
       el:0.0D, $                     ;     8         180
       vel:0.0D, $                    ;     8         188
       sky_freq:0.0D, $               ;     8         196
       rest_freq:0.0D, $              ;     8         204
       ref_ch:0.0D, $                 ;     8         212
       delta_x:0.0D, $                ;     8         220
       vel_def:bytarr(32), $          ;    32         236
       bw:0.0D, $                     ;     8         260
       tsys:0.0D, $                   ;     8         268
       tcal:0.0D, $                   ;     8         272
       tintg:0.0D, $                  ;     8         280
       data_points:!data_points, $    ;     4         284
       max_points: !max_points, $     ;     4         288
       history:bytarr(256), $         ;    48         336        
       epoch:bytarr(32), $            ;    48         384        
       procSeqn: 0L,     $            ;     4         392
       procSize: 0L,     $            ;     4         396
       iState: 0L,     $              ;     4         396  0=cal On/calibated
       nStates: 0L,    $              ;     4         396  
       iSampler: 0L,     $            ;     4         396  0 to nSamplers-1
       nSamplers: 0L,    $            ;     4         396
       iBeam: 0L,    $                ;     4         396  0 to nBeams-1
       nBeams: 0L,   $                ;     4         396
       iIntegration: 0L,    $         ;     4         396  0 to nIntegrations-1
       nIntegrations: 0L,   $         ;     4         396
       channels:bytarr(256), $        ;    48         396        
       calibrate:bytarr(256), $       ;    48         396        
       flag:bytarr(256), $            ;    48         396        
       data:fltarr(!max_points) $  ;   16,384      16,708
;  --> size = 4 * !data_points : 4096 -->
}                        ; end of definition
*/
#define MAXIDLNAME    32
#define MAXIDLANOTATE 256
#define MAXIDLPOINTS 32768

typedef struct {                      /* definition of IDL Data */
  char source[MAXIDLNAME];                 
  long scan_num;                      /* current scan number */
  long off_scan;                      /* scan of associated reference */
  char line_id[MAXIDLNAME];           /* name of line */
  char pol_id[MAXIDLNAME];            /* name of polarization ie: L,R,X,Y */
  char scan_type[MAXIDLNAME];         /* GBT Proceedure name: ie NOD */
  double lst;                         /* LST of integration start */
  char date[MAXIDLNAME];              /* string date name */
  double ra;                          /* J2000 RA */
  double dec;                         /* J2000 DEC */
  double az;                          /* Az at start of integration */
  double el;                          /* El at start of integration */
  double vel;                         /* source velocity (km/sec) */
  double sky_freq;                    /* ref_ch frequency (Hz) */
  double rest_freq;                   /* line frequency (Hz) for velocities */
  double ref_ch;                      /* reference channel */
  double delta_x;                     /* ? */
  char vel_def[MAXIDLNAME];           /* velocity definition: ie LSRK */
  double bw;                          /* band width (Hz) */
  double tsys;                        /* T system K */
  double tcal;                        /* T Cal ref channel (K) */
  double tintg;                       /* itegration time (s) */
  double dMjd;                        /* fractional modified Julian Day */
  long data_points;                   /* number of actual points in data[] */
  long max_points;                    /* maximum in data[] == MAXIDLPOINTS */
  char history[MAXIDLANOTATE];        /* plot anotation string */
  long procSeqn;
  long procSize;
  long iState;
  long nStates;
  long iSampler;
  long nSamplers;
  long iBeam;
  long nBeams;
  long iIntegration;
  long nIntegrations;
  char epoch[MAXIDLNAME];
  char channels[MAXIDLANOTATE];        /* channel selection string */
  char calibrate[MAXIDLANOTATE];       /* calibration selection string */
  char flag[MAXIDLANOTATE];
  float data[MAXIDLPOINTS];           /* data of interest */
} GBTIDL;
