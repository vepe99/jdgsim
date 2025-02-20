from typing import Optional, Tuple, Callable, Union, List
from functools import partial

import jax
import jax.numpy as jnp
from jax import vmap, jit
from jax import random

DIRECT_ACC = 0


def single_body_acc(particle_i, particle_j, mass_i, mass_j, config, params) -> jnp.ndarray:
    """
    Compute acceleration of particle_i due to particle_j.
    
    Parameters
    ----------
    particle_i : jnp.ndarray
        Position and velocity of particle_i.
    particle_j : jnp.ndarray
        Position and velocity of particle_j.
    mass_i : float
        Mass of particle_i.
    mass_j : float
        Mass of particle_j.
    config: NamedTuple
        Configuration parameters.
    params: NamedTuple
        Simulation parameters.
    
    Returns
    -------
    Tuple
        - Acceleration: jnp.ndarray 
            Acecleration of particle_i due to particle_j.
        - Potential: jnp.ndarray
            Potential energy of particle_i due to particle_j
    """
    
    r_ij = particle_i[0, :] - particle_j[0, :]
    r_mag = jnp.linalg.norm(r_ij)   # Avoid division by zero and close encounter with config.softening

    return - params.G * (mass_j) * (r_ij/(r_mag**2 + config.softening**2)**(3/2)), - params.G * mass_j / (r_mag + config.softening)
    

@partial(jax.jit, static_argnames=['config', 'return_potential'])
def direct_acc(state, mass, config, params, return_potential=False):
    """
    Compute acceleration of all particles due to all other particles by vmap of the single_body_acc function.

    Parameters
    ----------
    state : jnp.ndarray
        Array of shape (N_particles, 6) representing the positions and velocities of the particles.
    mass : jnp.ndarray
        Array of shape (N_particles,) representing the masses of the particles.
    config: NamedTuple
        Configuration parameters.
    params: NamedTuple
        Simulation parameters.
    
    Returns
    -------
    Tuple
        - Acceleration: jnp.ndarray 
            Acecleration of all particles due to all other particles.
        - Potential: jnp.ndarray
            Potential energy of all particles due to all other particles
            Returned only if return_potential is True.   
    
    """

    def net_force_on_body(particle_i, mass_i):
        
        acc, potential = vmap(lambda particle_j, mass_j: single_body_acc(particle_i, particle_j, mass_i, mass_j, config, params))(state, mass)
        if return_potential:
            return jnp.sum(acc, axis=0), jnp.sum(potential, )
        else:
            return jnp.sum(acc, axis=0)

    return vmap(net_force_on_body)(state, mass)
