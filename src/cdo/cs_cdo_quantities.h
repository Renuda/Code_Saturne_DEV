#ifndef __CS_CDO_QUANTITIES_H__
#define __CS_CDO_QUANTITIES_H__

/*============================================================================
 * Manage geometrical quantities needed in CDO schemes
 *============================================================================*/

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

/*----------------------------------------------------------------------------
 *  Local headers
 *----------------------------------------------------------------------------*/

#include "cs_base.h"
#include "cs_math.h"
#include "cs_mesh.h"
#include "cs_mesh_quantities.h"
#include "cs_cdo.h"
#include "cs_cdo_connect.h"

/*----------------------------------------------------------------------------*/

BEGIN_C_DECLS

/*============================================================================
 * Macro definitions
 *============================================================================*/

/* Information useful to get simpler algo. */
#define CS_CDO_ORTHO      (1 << 0)  // Orthogonality condition is checked

/*============================================================================
 * Type definitions
 *============================================================================*/

/* Type of algorithm to compute geometrical quantities */
typedef enum {

  CS_CDO_CC_MEANV,   // Cell center is computed as the mean of cell vertices
  CS_CDO_CC_BARYC,   // Cell center is computed as the real cell barycenter
  CS_CDO_CC_SATURNE, // Cell center is given by Code_Saturne
  CS_CDO_CC_ORTHO,   /* Cell center is optimized to enforce orthogonality
                        between cell-face edge and face plane */
  CS_CDO_N_CC_ALGOS

} cs_cdo_cc_algo_t;

/* Structure storing information about variation of entities accros the
   mesh for a given type of entity (cell, face and edge) */
typedef struct {

  double   meas_min;  // Min. value of the entity measure (vol, surf or lenght)
  double   meas_max;  // Max. value of the entity measure (vol, surf or lenght)
  double   h_min;     // Estimation of the min. value of the diameter
  double   h_max;     // Estimation of the max. value of the diameter

  cs_lnum_t   min_id; // Entity if related to the min. value
  cs_lnum_t   max_id; // Entity if related to the max. value

} cs_quant_info_t;

/* For primal vector quantities (edge or face) */
typedef struct {

  double  meas;       /* length or area */
  double  unitv[3];   /* unitary vector: tangent or normal to the element */
  double  center[3];

} cs_quant_t;

/* For dual face quantities. Add also a link to entity id related to this dual
   quantities */

typedef struct { /* TODO: remove what is the less necessary in order to
                    save memory comsumption */

  cs_lnum_t   parent_id[2];  /* parent entity id of (primal) faces f0 and f1 */
  cs_nvec3_t  sface[2];      /* area and unit normal vector for each
                                triangle s(e,f,c) for f in {f0, f1} */
  double      vect[3];       /* dual face vector */

} cs_dface_t;

typedef struct { /* Specific mesh quantities */

  /* Global mesh quantities */
  double           vol_tot;

  /* Cell-based quantities */
  cs_lnum_t        n_cells;
  cs_real_t       *cell_centers;
  cs_real_t       *cell_vol;
  cs_quant_info_t  cell_info;
  cs_flag_t       *cell_flag;

  /* Face-based quantities */
  cs_lnum_t        n_i_faces;
  cs_lnum_t        n_b_faces;
  cs_lnum_t        n_faces;   /* n_i_faces + n_b_faces */
  cs_quant_t      *face;      /* Face quantities */
  cs_nvec3_t      *dedge;     /* Dual edge quantities (length and unit vector)
                                 Scan with the c2f connectivity */
  cs_quant_info_t  face_info;

  /* Edge-based quantities */
  cs_lnum_t        n_edges;
  cs_quant_t      *edge;      /* Edge quantities */
  cs_dface_t      *dface;     /* For each edge belonging to a cell, two
                                 contributions coming from 2 triangles
                                 s(x_cell, x_face, x_edge) for face in Face_edge
                                 are considered.
                                 Scan with the c2e connectivity */
  cs_quant_info_t  edge_info;

  /* Vertex-based quantities */
  cs_lnum_t   n_vertices;
  double     *dcell_vol;       /* Dual volume related to each vertex.
                                  Scan with the c2v connectivity */
  const cs_real_t  *vtx_coord; /* Pointer to the one stored in cs_mesh_t */


} cs_cdo_quantities_t;

/*============================================================================
 * Global variables
 *============================================================================*/

/*=============================================================================
 * Inline static function prototypes
 *============================================================================*/

/*----------------------------------------------------------------------------*/
/*!
 * \brief  Compute the area of the triangle of base given by q (related to a
 *         segment) with apex located at xa
 *
 * \param[in]  q    pointer to a cs_quant_t structure related to a segment
 * \param[in]  xa   coordinates of the apex to consider
 *
 * \return the value the area of the triangle
 */
/*----------------------------------------------------------------------------*/

inline static double
cs_compute_area_from_quant(const cs_quant_t   q,
                           const cs_real_t   *xa)
{
  double  xef[3], xef_un[3], cp[3];
  xef[0] = xa[0] - q.center[0];
  xef[1] = xa[1] - q.center[1];
  xef[2] = xa[2] - q.center[2];

  const double  xef_len = cs_math_3_norm(xef);
  const double  inv_len = 1/xef_len;

  xef_un[0] = inv_len * xef[0];
  xef_un[1] = inv_len * xef[1];
  xef_un[2] = inv_len * xef[2];

  cs_math_3_cross_product(xef_un, q.unitv, cp);

  /* tef = ||(center -xa) x e||/2 */
  return 0.5 * xef_len * q.meas * cs_math_3_norm(cp);
}

/*============================================================================
 * Public function prototypes
 *============================================================================*/

/*----------------------------------------------------------------------------*/
/*!
 * \brief Build a cs_cdo_quantities_t structure
 *
 * \param[in]  m           pointer to a cs_mesh_t structure
 * \param[in]  mq          pointer to a cs_mesh_quantities_t structure
 * \param[in]  topo        pointer to a cs_cdo_connect_t structure
 *
 * \return  a new allocated pointer to a cs_cdo_quantities_t structure
 */
/*----------------------------------------------------------------------------*/

cs_cdo_quantities_t *
cs_cdo_quantities_build(const cs_mesh_t             *m,
                        const cs_mesh_quantities_t  *mq,
                        const cs_cdo_connect_t      *topo);

/*----------------------------------------------------------------------------*/
/*!
 * \brief Destroy a cs_cdo_quantities_t structure
 *
 * \param[in]  q        pointer to the cs_cdo_quantities_t struct. to free
 *
 * \return a NULL pointer
 */
/*----------------------------------------------------------------------------*/

cs_cdo_quantities_t *
cs_cdo_quantities_free(cs_cdo_quantities_t   *q);

/*----------------------------------------------------------------------------*/
/*!
 * \brief Summarize generic information about the cdo mesh quantities
 *
 * \param[in]  cdoq     pointer to cs_cdo_quantities_t structure
 *
 */
/*----------------------------------------------------------------------------*/

void
cs_cdo_quantities_summary(const cs_cdo_quantities_t  *quant);

/*----------------------------------------------------------------------------*/
/*!
 * \brief Dump a cs_cdo_quantities_t structure
 *
 * \param[in]  cdoq   pointer to cs_cdo_quantities_t structure
 *
 */
/*----------------------------------------------------------------------------*/

void
cs_cdo_quantities_dump(const cs_cdo_quantities_t  *cdoq);

/*----------------------------------------------------------------------------*/
/*!
 * \brief Dump a cs_quant_t structure
 *
 * \param[in]  f         FILE struct (stdout if NULL)
 * \param[in]  num       entity number related to this quantity struct.
 * \param[in]  q         cs_quant_t structure to dump
 */
/*----------------------------------------------------------------------------*/

void
cs_quant_dump(FILE             *f,
              cs_lnum_t         num,
              const cs_quant_t  q);

/*----------------------------------------------------------------------------*/

END_C_DECLS

#endif /* __CS_CDO_QUANTITIES_H__ */
