!-------------------------------------------------------------------------------

!VERS

! This file is part of Code_Saturne, a general-purpose CFD tool.
!
! Copyright (C) 1998-2013 EDF S.A.
!
! This program is free software; you can redistribute it and/or modify it under
! the terms of the GNU General Public License as published by the Free Software
! Foundation; either version 2 of the License, or (at your option) any later
! version.
!
! This program is distributed in the hope that it will be useful, but WITHOUT
! ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
! FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
! details.
!
! You should have received a copy of the GNU General Public License along with
! this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
! Street, Fifth Floor, Boston, MA 02110-1301, USA.

!-------------------------------------------------------------------------------

!===============================================================================
! Purpose:
! -------

!> \file cs_user_initialization.f90 atmospheric example
!>
!-------------------------------------------------------------------------------

!-------------------------------------------------------------------------------
! Arguments
!______________________________________________________________________________.
!  mode           name          role                                           !
!______________________________________________________________________________!
!> \param[in]     nvar          total number of variables
!> \param[in]     nscal         total number of scalars
!> \param[in]     dt            time step (per cell)
!> \param[in]     rtp           calculated variables at cell centers
!>                               (at current time step)
!> \param[in]     propce        physical properties at cell centers
!_______________________________________________________________________________


subroutine cs_user_initialization &
!================================

 ( nvar   , nscal  ,                                              &
   dt     , rtp    , propce )

!===============================================================================

!===============================================================================
! Module files
!===============================================================================

use paramx
use pointe
use numvar
use optcal
use cstphy
use cstnum
use entsor
use parall
use period
use ppppar
use ppthch
use coincl
use cpincl
use ppincl
use atincl
use ctincl
use elincl
use ppcpfu
use cs_coal_incl
use cs_fuel_incl
use mesh

!===============================================================================

implicit none

! Arguments

integer          nvar   , nscal

double precision dt(ncelet), rtp(ncelet,*), propce(ncelet,*)

! Local variables

!< [loc_var_dec]
integer          iel
double precision d2s3
double precision zent,xuent,xvent,xkent,xeent,tpent

integer, allocatable, dimension(:) :: lstelt
!< [loc_var_dec]

!===============================================================================

!---------------
! Initialization
!---------------

!< [init]
allocate(lstelt(ncel)) ! temporary array for cells selection

d2s3 = 2.d0/3.d0

!===============================================================================
! Initialize variables using an input meteo profile
!   (only if we are not doing a restart)
!===============================================================================

if (isuite.eq.0) then

  do iel = 1, ncel

    zent=xyzcen(3,iel)

    call intprf                                                   &
    !==========
   (nbmetd, nbmetm,                                               &
    zdmet, tmmet, umet , zent  , ttcabs, xuent )

    call intprf                                                   &
    !==========
   (nbmetd, nbmetm,                                               &
    zdmet, tmmet, vmet , zent  , ttcabs, xvent )

    call intprf                                                   &
    !==========
   (nbmetd, nbmetm,                                               &
    zdmet, tmmet, ekmet, zent  , ttcabs, xkent )

    call intprf                                                   &
    !==========
   (nbmetd, nbmetm,                                               &
    zdmet, tmmet, epmet, zent  , ttcabs, xeent )

    rtp(iel,iu)=xuent
    rtp(iel,iv)=xvent
    rtp(iel,iw)=0.d0

!     ITYTUR est un indicateur qui vaut ITURB/10
    if    (itytur.eq.2) then

      rtp(iel,ik)  = xkent
      rtp(iel,iep) = xeent

    elseif (itytur.eq.3) then

      rtp(iel,ir11) = d2s3*xkent
      rtp(iel,ir22) = d2s3*xkent
      rtp(iel,ir33) = d2s3*xkent
      rtp(iel,ir12) = 0.d0
      rtp(iel,ir13) = 0.d0
      rtp(iel,ir23) = 0.d0
      rtp(iel,iep)  = xeent

    elseif (iturb.eq.50) then

      rtp(iel,ik)   = xkent
      rtp(iel,iep)  = xeent
      rtp(iel,iphi) = d2s3
      rtp(iel,ifb)  = 0.d0

    elseif (iturb.eq.60) then

      rtp(iel,ik)   = xkent
      rtp(iel,iomg) = xeent/cmu/xkent

    elseif (iturb.eq.70) then

      rtp(iel,inusa) = cmu*xkent**2/xeent

    endif

    if (iscalt.ge.0) then
! On suppose que le scalaire est la temperature potentielle :
      call intprf                                                 &
      !==========
   (nbmett, nbmetm,                                               &
    ztmet, tmmet, tpmet, zent  , ttcabs, tpent )

      rtp(iel,isca(iscalt)) = tpent

    endif
  enddo

endif
!< [init]

!--------
! Formats
!--------

!----
! End
!----

! Deallocate the temporary array
deallocate(lstelt)

return
end subroutine cs_user_initialization
