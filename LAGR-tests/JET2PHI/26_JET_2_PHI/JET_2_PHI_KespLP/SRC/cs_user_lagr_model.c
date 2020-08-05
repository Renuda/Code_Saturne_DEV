/*============================================================================
 * Lagrangian model options.
 *============================================================================*/

/* VERS */

/*
  This file is part of Code_Saturne, a general-purpose CFD tool.

  Copyright (C) 1998-2017 EDF S.A.

  This program is free software; you can redistribute it and/or modify it under
  the terms of the GNU General Public License as published by the Free Software
  Foundation; either version 2 of the License, or (at your option) any later
  version.

  This program is distributed in the hope that it will be useful, but WITHOUT
  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
  FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
  details.

  You should have received a copy of the GNU General Public License along with
  this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
  Street, Fifth Floor, Boston, MA 02110-1301, USA.
*/

/*----------------------------------------------------------------------------*/

#include "cs_defs.h"

/*----------------------------------------------------------------------------
 * Standard C library headers
 *----------------------------------------------------------------------------*/

#include <stdio.h>

/*----------------------------------------------------------------------------
 *  Local headers
 *----------------------------------------------------------------------------*/

#include "cs_lagr.h"
#include "cs_lagr_post.h"
#include "cs_lagr_stat.h"
#include "cs_lagr_particle.h"
#include "cs_lagr_prototypes.h"
#include "cs_prototypes.h"

/*---------------------------------------------------------------------------*/
/*
 * \brief User function of the Lagrangian particle-tracking module
 *
 *  User input of physical, numerical and post-processing options.
 */
/*----------------------------------------------------------------------------*/

void
cs_user_lagr_model(void)
{
  /*
   * Trick to average the statistics at iteration nstist
   * starting from an unsteady two-coupling calculation
   *
   * It is placed here to be consistant with previous calculation in case of
   * restarted calculation.
   */
  if (cs_glob_time_step->nt_cur > cs_glob_lagr_stat_options->nstist) {

    cs_glob_lagr_source_terms->nstits = cs_glob_lagr_stat_options->nstist;
    cs_glob_lagr_time_scheme->isttio = 1;

  }
}

/*----------------------------------------------------------------------------*/

END_C_DECLS
